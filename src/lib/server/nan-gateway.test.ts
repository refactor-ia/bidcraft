import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import {
	createGateway,
	UpstreamError,
	upstreamErrorCode,
	upstreamErrorStatus,
	type GatewayFetch,
	type GatewayRequest
} from './nan-gateway.js';

const baseRequest: GatewayRequest<string> = {
	model: 'whisper',
	body: { method: 'POST', body: new FormData() } as RequestInit,
	url: 'https://api.nan.builders/v1/audio/transcriptions',
	mapResponse: async () => 'ok'
};

function okResponse(): Response {
	return new Response(JSON.stringify({ fine: true }), { status: 200 });
}

/** Fake clock-free backoff: gateway must accept an injected wait function. */
const noWait = () => Promise.resolve();

describe('nan-gateway concurrency bound', () => {
	it('never exceeds the configured concurrent limit', async () => {
		let inFlight = 0;
		let peak = 0;
		const fetchImpl: GatewayFetch = async () => {
			inFlight++;
			peak = Math.max(peak, inFlight);
			await new Promise((r) => setTimeout(r, 20));
			inFlight--;
			return okResponse();
		};
		const gw = createGateway({ fetchImpl, wait: noWait, limits: { whisper: 3 } });
		await Promise.all(Array.from({ length: 12 }, () => gw.request(baseRequest)));
		expect(peak).toBe(3);
	});

	it('queues excess requests and resolves all of them', async () => {
		const fetchImpl: GatewayFetch = async () => {
			await new Promise((r) => setTimeout(r, 10));
			return okResponse();
		};
		const gw = createGateway({ fetchImpl, wait: noWait, limits: { whisper: 2 } });
		const results = await Promise.all(
			Array.from({ length: 8 }, () => gw.request(baseRequest))
		);
		expect(results).toHaveLength(8);
		expect(results.every((r) => r === 'ok')).toBe(true);
	});
});

describe('nan-gateway retry policy', () => {
	it('retries on 429 and eventually succeeds', async () => {
		let calls = 0;
		const fetchImpl: GatewayFetch = vi.fn(async () => {
			calls++;
			return calls < 3 ? new Response('slow down', { status: 429 }) : okResponse();
		});
		const gw = createGateway({ fetchImpl, wait: noWait, limits: { whisper: 2 } });
		const result = await gw.request(baseRequest);
		expect(result).toBe('ok');
		expect(calls).toBe(3);
	});

	it('retries on 5xx and network errors, bounded by maxAttempts', async () => {
		const fetchImpl: GatewayFetch = vi.fn(async () => {
			throw new TypeError('fetch failed');
		});
		const gw = createGateway({
			fetchImpl,
			wait: noWait,
			limits: { whisper: 2 },
			maxAttempts: 3
		});
		await expect(gw.request(baseRequest)).rejects.toThrow(UpstreamError);
		expect(fetchImpl).toHaveBeenCalledTimes(3);
	});

	it('never retries on 4xx validation errors (fails fast)', async () => {
		const fetchImpl: GatewayFetch = vi.fn(async () => new Response('bad key', { status: 401 }));
		const gw = createGateway({ fetchImpl, wait: noWait, limits: { whisper: 2 } });
		await expect(gw.request(baseRequest)).rejects.toThrow(UpstreamError);
		expect(fetchImpl).toHaveBeenCalledTimes(1);
	});
});

describe('nan-gateway timeout', () => {
	it('fails with an UpstreamError when the upstream hangs past the timeout', async () => {
		const fetchImpl: GatewayFetch = () => new Promise(() => {}); // never resolves
		const gw = createGateway({
			fetchImpl,
			wait: noWait,
			limits: { whisper: 2 },
			timeoutMs: 30
		});
		await expect(gw.request(baseRequest)).rejects.toMatchObject({
			name: 'UpstreamError',
			kind: 'timeout'
		});
	});
});

describe('nan-gateway typed errors', () => {
	beforeEach(() => {
		vi.useFakeTimers();
	});
	afterEach(() => {
		vi.useRealTimers();
	});

	it('rate-limit failure reports kind rate_limited with retryAfter', async () => {
		const fetchImpl: GatewayFetch = async () =>
			new Response('too many', { status: 429, headers: { 'retry-after': '7' } });
		const gw = createGateway({
			fetchImpl,
			wait: noWait,
			limits: { whisper: 2 },
			maxAttempts: 2
		});
		await expect(gw.request(baseRequest)).rejects.toMatchObject({
			name: 'UpstreamError',
			kind: 'rate_limited',
			retryAfterSeconds: 7
		});
	});

	it('client 4xx failure reports kind rejected with the upstream status', async () => {
		const fetchImpl: GatewayFetch = async () => new Response('nope', { status: 400 });
		const gw = createGateway({ fetchImpl, wait: noWait, limits: { whisper: 2 } });
		await expect(gw.request(baseRequest)).rejects.toMatchObject({
			name: 'UpstreamError',
			kind: 'rejected',
			status: 400
		});
	});
});

describe('upstreamErrorCode mapping', () => {
	const cases: Array<[UpstreamError['kind'], string]> = [
		['timeout', 'UPSTREAM_TIMEOUT'],
		['rate_limited', 'UPSTREAM_RATE_LIMITED'],
		['rejected', 'UPSTREAM_REJECTED'],
		['unavailable', 'UPSTREAM_UNAVAILABLE']
	];
	for (const [kind, expected] of cases) {
		it(`maps ${kind} to ${expected}`, () => {
			const error = new UpstreamError(kind, 'x');
			expect(upstreamErrorCode(error)).toBe(expected);
		});
	}
});

describe('http status for upstream errors', () => {
	const cases: Array<[UpstreamError['kind'], number]> = [
		['timeout', 504],
		['rate_limited', 429],
		['rejected', 502],
		['unavailable', 503]
	];
	for (const [kind, expected] of cases) {
		it(`gives ${kind} status ${expected}`, () => {
			expect(upstreamErrorStatus(new UpstreamError(kind, 'x'))).toBe(expected);
		});
	}
});
