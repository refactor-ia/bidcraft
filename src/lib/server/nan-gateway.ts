/**
 * nan-gateway: the single server-side exit point for every NaN API call.
 *
 * Exists because the E1 measurements of the didactic run showed: (a) the dev
 * plan rejects more than ~10 concurrent whisper requests with raw 502s, and
 * (b) upstream failures surfaced the misleading `EXPORT_CLIENT_INVALID`
 * client-data code. The gateway bounds concurrency per model, applies an
 * explicit timeout, retries only transient failures with exponential backoff,
 * and reports typed UpstreamErrors so routes can degrade gracefully.
 *
 * The semaphore is in-memory and per-process — correct for the single-process
 * systemd deploy, a declared limit (see docs/corrida-didactica/blueprint.md).
 */

import type { ErrorCode } from '$lib/domain/validate';

/** A fetch-compatible function the gateway calls; injectable for tests. */
export type GatewayFetch = (url: string, init: RequestInit) => Promise<Response>;

/** Why an upstream call failed, in terms the UI can act on. */
export type UpstreamErrorKind =
	/** The upstream hung past the timeout. */
	| 'timeout'
	/** The upstream is over its own limit (429). */
	| 'rate_limited'
	/** The upstream rejected the call permanently (4xx other than 429). */
	| 'rejected'
	/** 5xx or network failure, exhausted attempts. */
	| 'unavailable';

export class UpstreamError extends Error {
	readonly kind: UpstreamErrorKind;
	readonly status?: number;
	readonly retryAfterSeconds?: number;

	constructor(
		kind: UpstreamErrorKind,
		message: string,
		options: { status?: number; retryAfterSeconds?: number } = {}
	) {
		super(message);
		this.name = 'UpstreamError';
		this.kind = kind;
		this.status = options.status;
		this.retryAfterSeconds = options.retryAfterSeconds;
	}
}

export type GatewayRequest<TResult> = {
	/** Upstream model slug; selects the concurrency limit. */
	model: string;
	url: string;
	/** RequestInit passed to the underlying fetch (headers, body). */
	body: RequestInit;
	/** Extracts the caller's result from a successful Response. */
	mapResponse: (response: Response) => Promise<TResult>;
};

export type GatewayOptions = {
	fetchImpl: GatewayFetch;
	/** Injected wait used for backoff; tests pass an immediate no-op. */
	wait: (ms: number) => Promise<void>;
	/** Concurrent upstream calls allowed per model. */
	limits: Record<string, number>;
	timeoutMs?: number;
	maxAttempts?: number;
	/** Backoff base in ms; doubles per attempt with jitter. */
	backoffBaseMs?: number;
};

type Waiter = () => void;

/** Simple FIFO semaphore: acquire() resolves when a slot frees. */
class Semaphore {
	private inFlight = 0;
	private queue: Waiter[] = [];

	constructor(readonly limit: number) {}

	async acquire(): Promise<() => void> {
		if (this.inFlight < this.limit) {
			this.inFlight++;
			return () => this.release();
		}
		await new Promise<void>((resolve) => this.queue.push(resolve));
		this.inFlight++;
		return () => this.release();
	}

	private release(): void {
		this.inFlight--;
		const next = this.queue.shift();
		if (next) next();
	}
}

function isTransient(status: number): boolean {
	return status === 429 || status >= 500;
}

function parseRetryAfter(response: Response): number | undefined {
	const raw = response.headers.get('retry-after');
	if (raw === null) return undefined;
	const seconds = Number(raw);
	return Number.isFinite(seconds) && seconds >= 0 ? seconds : undefined;
}

function withTimeoutSignal(timeoutMs: number): { signal: AbortSignal; cancel: () => void } {
	const controller = new AbortController();
	const timer = setTimeout(() => controller.abort(), timeoutMs);
	return { signal: controller.signal, cancel: () => clearTimeout(timer) };
}

/** Map an UpstreamError to the domain ErrorCode the UI displays (messages.ts owns the wording). */
export function upstreamErrorCode(error: UpstreamError): ErrorCode {
	switch (error.kind) {
		case 'timeout':
			return 'UPSTREAM_TIMEOUT';
		case 'rate_limited':
			return 'UPSTREAM_RATE_LIMITED';
		case 'rejected':
			return 'UPSTREAM_REJECTED';
		case 'unavailable':
			return 'UPSTREAM_UNAVAILABLE';
	}
}

/** HTTP status the routes answer with for each upstream failure kind. */
export function upstreamErrorStatus(error: UpstreamError): number {
	switch (error.kind) {
		case 'timeout':
			return 504;
		case 'rate_limited':
			return 429;
		case 'rejected':
			return 502;
		case 'unavailable':
			return 503;
	}
}

export function createGateway(options: GatewayOptions) {
	const {
		fetchImpl,
		wait,
		limits,
		timeoutMs = 120_000,
		maxAttempts = 3,
		backoffBaseMs = 300
	} = options;

	const semaphores = new Map<string, Semaphore>();
	function semaphoreFor(model: string): Semaphore {
		const existing = semaphores.get(model);
		if (existing) return existing;
		const created = new Semaphore(limits[model] ?? 5);
		semaphores.set(model, created);
		return created;
	}

	async function attemptOnce<TResult>(request: GatewayRequest<TResult>): Promise<TResult> {
		const { signal, cancel } = withTimeoutSignal(timeoutMs);
		try {
			// Race the fetch against our own timer: a fetch implementation may
			// ignore the AbortSignal (network stacks vary, tests use fakes), so
			// the timeout must not rely on the abort alone.
			const timeoutPromise = new Promise<never>((_, reject) => {
				const t = setTimeout(() => reject(new UpstreamError('timeout', 'upstream timed out')), timeoutMs);
				// Unref so a pending timeout never keeps the process alive.
				t.unref?.();
			});
			const response = await Promise.race([fetchImpl(request.url, { ...request.body, signal }), timeoutPromise]);
			if (!response.ok) {
				const status = response.status;
				if (status === 429) {
					throw new UpstreamError('rate_limited', 'upstream rate limited', {
						status,
						retryAfterSeconds: parseRetryAfter(response)
					});
				}
				if (status >= 400 && status < 500) {
					throw new UpstreamError('rejected', `upstream rejected: ${status}`, { status });
				}
				throw new UpstreamError('unavailable', `upstream error: ${status}`, { status });
			}
			return await request.mapResponse(response);
		} catch (error) {
			if (error instanceof UpstreamError) throw error;
			// AbortError from our own timeout or a network-level TypeError: both
			// count as timeout/unavailable, never as a caller bug.
			if (error instanceof Error && error.name === 'AbortError') {
				throw new UpstreamError('timeout', 'upstream timed out');
			}
			throw new UpstreamError('unavailable', 'upstream network failure');
		} finally {
			cancel();
		}
	}

	async function request<TResult>(request: GatewayRequest<TResult>): Promise<TResult> {
		const release = await semaphoreFor(request.model).acquire();
		try {
			let lastError: unknown;
			for (let attempt = 1; attempt <= maxAttempts; attempt++) {
				try {
					return await attemptOnce(request);
				} catch (error) {
					lastError = error;
					const isLast = attempt === maxAttempts;
					if (isLast || !(error instanceof UpstreamError)) throw error;
					// Retry only transient kinds: rate_limited and unavailable.
					// rejected (4xx) and caller-level mapResponse errors fail fast.
					if (error.kind === 'rejected') throw error;
					const backoff =
						error.kind === 'rate_limited'
							? (error.retryAfterSeconds ?? 1) * 1000
							: backoffBaseMs * 2 ** (attempt - 1);
					const jitter = Math.random() * backoff * 0.25;
					await wait(Math.round(backoff + jitter));
				}
			}
			throw lastError;
		} finally {
			release();
		}
	}

	return { request };
}

export type NanGateway = ReturnType<typeof createGateway>;
