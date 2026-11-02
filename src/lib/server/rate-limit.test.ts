import { describe, expect, it } from 'vitest';
import { createRateLimiter } from './rate-limit.js';

function fakeIp(name: string): Request {
	return new Request('http://localhost/x', { headers: { 'x-forwarded-for': name } });
}

describe('rate limiter', () => {
	it('allows up to the limit and rejects beyond it', () => {
		const limiter = createRateLimiter({ limit: 3, windowMs: 60_000 });
		expect(limiter.check(fakeIp('a')).allowed).toBe(true);
		expect(limiter.check(fakeIp('a')).allowed).toBe(true);
		expect(limiter.check(fakeIp('a')).allowed).toBe(true);
		const rejected = limiter.check(fakeIp('a'));
		expect(rejected.allowed).toBe(false);
		expect(rejected.retryAfterSeconds).toBeGreaterThan(0);
	});

	it('counts each client IP separately', () => {
		const limiter = createRateLimiter({ limit: 1, windowMs: 60_000 });
		expect(limiter.check(fakeIp('a')).allowed).toBe(true);
		expect(limiter.check(fakeIp('a')).allowed).toBe(false);
		expect(limiter.check(fakeIp('b')).allowed).toBe(true);
	});

	it('resets after the window elapses', () => {
		let now = 0;
		const limiter = createRateLimiter({ limit: 1, windowMs: 1000, now: () => now });
		expect(limiter.check(fakeIp('a')).allowed).toBe(true);
		expect(limiter.check(fakeIp('a')).allowed).toBe(false);
		now += 1001;
		expect(limiter.check(fakeIp('a')).allowed).toBe(true);
	});

	it('falls back to a stable key when no forwarded header exists', () => {
		const limiter = createRateLimiter({ limit: 1, windowMs: 60_000 });
		const anonymous = new Request('http://localhost/x');
		expect(limiter.check(anonymous).allowed).toBe(true);
		expect(limiter.check(anonymous).allowed).toBe(false);
	});

	it('keeps the map bounded even across thousands of distinct clients', () => {
		let now = 0;
		const limiter = createRateLimiter({ limit: 1, windowMs: 1000, now: () => now });
		for (let i = 0; i < 5000; i++) {
			now += 1001;
			limiter.check(fakeIp(`ip-${i}`));
		}
		// Stale-entry sweeps keep the map at the sweep threshold + current
		// window: it oscillates but never grows with the number of clients.
		expect(limiter.size()).toBeLessThanOrEqual(1001);
	});
});
