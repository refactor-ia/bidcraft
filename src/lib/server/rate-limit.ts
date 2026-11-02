/**
 * Per-client-IP fixed-window rate limiter for the routes that hit the NaN API
 * (E2 piece S4: a single client must not be able to burn the dev-plan quota).
 *
 * In-memory and per-process — same declared limit as the gateway semaphore:
 * correct for the single-process systemd deploy. Configurable per route via
 * env (`NAN_RATE_LIMIT_PARSE`, `NAN_RATE_LIMIT_TRANSCRIBE`, `NAN_RATE_LIMIT_SPEEK`,
 * requests per minute) with conservative defaults.
 */

export type RateLimitOptions = {
	/** Max requests allowed per client IP inside one window. */
	limit: number;
	/** Window length in ms. */
	windowMs: number;
	/** Injectable clock for tests. */
	now?: () => number;
};

export type RateLimitResult = {
	allowed: boolean;
	retryAfterSeconds?: number;
};

export type RateLimiter = {
	check: (request: Request) => RateLimitResult;
	size: () => number;
};

type Entry = { windowStart: number; count: number };

function clientKey(request: Request): string {
	const forwarded = request.headers.get('x-forwarded-for');
	if (forwarded) {
		const first = forwarded.split(',')[0]?.trim();
		if (first) return first;
	}
	return 'anonymous';
}

export function createRateLimiter(options: RateLimitOptions): RateLimiter {
	const { limit, windowMs } = options;
	const now = options.now ?? (() => Date.now());
	const entries = new Map<string, Entry>();
	/** Sweep when the map grows past this; stale entries are one window old. */
	const SWEEP_THRESHOLD = 1000;

	function sweep(current: number): void {
		for (const [key, entry] of entries) {
			if (current - entry.windowStart >= windowMs) entries.delete(key);
		}
	}

	return {
		check(request: Request): RateLimitResult {
			const current = now();
			const key = clientKey(request);
			const existing = entries.get(key);
			if (existing === undefined || current - existing.windowStart >= windowMs) {
				entries.set(key, { windowStart: current, count: 1 });
				if (entries.size > SWEEP_THRESHOLD) sweep(current);
				return { allowed: true };
			}
			existing.count++;
			if (existing.count > limit) {
				const retryAfterSeconds = Math.ceil(
					(existing.windowStart + windowMs - current) / 1000
				);
				return { allowed: false, retryAfterSeconds };
			}
			if (entries.size > SWEEP_THRESHOLD) sweep(current);
			return { allowed: true };
		},
		size: () => entries.size
	};
}

/** Env-tunable requests-per-minute limit; `fallback` is used when unset/invalid. */
export function limitFromEnv(name: string, fallback: number): number {
	const raw = process.env[name];
	const parsed = raw === undefined ? NaN : Number(raw);
	return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}
