/**
 * Shared gateway instance for the app's three NaN proxies (whisper, kokoro,
 * gemma4). Concurrency limits and timeouts come from env with measured
 * defaults: the whisper limit of 10 is the E1 dry-run observation (20 of 30
 * concurrent requests got 502 at 30 in flight), the others are conservative
 * until measured.
 */

import { createGateway, UpstreamError, upstreamErrorCode, upstreamErrorStatus } from './nan-gateway.js';
import { errorResponse } from './http.js';
import type { ErrorCode } from '$lib/domain/validate';

function envNumber(name: string, fallback: number): number {
	const raw = process.env[name];
	const parsed = raw === undefined ? NaN : Number(raw);
	return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

/** Lazy so tests can set env vars before the first request. */
let instance: ReturnType<typeof createGateway> | null = null;

export function getNanGateway() {
	if (instance === null) {
		instance = createGateway({
			fetchImpl: (url, init) => fetch(url, init),
			wait: (ms) => new Promise((resolve) => setTimeout(resolve, ms)),
			limits: {
				whisper: envNumber('NAN_CONCURRENCY_WHISPER', 10),
				kokoro: envNumber('NAN_CONCURRENCY_KOKORO', 5),
				gemma4: envNumber('NAN_CONCURRENCY_GEMMA4', 5)
			},
			timeoutMs: envNumber('NAN_TIMEOUT_MS', 120_000),
			maxAttempts: envNumber('NAN_MAX_ATTEMPTS', 3)
		});
	}
	return instance;
}

/** Turn an UpstreamError into the app's uniform `{ code, message }` JSON response. */
export function upstreamErrorResponse(error: unknown): Response | null {
	if (!(error instanceof UpstreamError)) return null;
	return errorResponse(upstreamErrorCode(error) as ErrorCode, upstreamErrorStatus(error));
}
