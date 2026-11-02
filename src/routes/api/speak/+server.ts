/**
 * POST /api/speak: spoken budget confirmation via Kokoro TTS.
 *
 * The client posts `{ text }` with a short confirmation phrase; the server
 * proxies it to the NaN API speech endpoint (Kokoro, Spanish Santa voice)
 * and streams back the wav audio. The API key never reaches the client,
 * so this must stay server-side.
 */

import { env } from '$env/dynamic/private';
import type { RequestHandler } from './$types';
import { UPSTREAM_URL, buildUpstreamBody, isAcceptableSpeakText } from '$lib/server/speak';
import {
	GENERIC_ERROR_CODE,
	badRequestResponse,
	errorResponse,
	invalidInputResponse,
	parseJsonBody
} from '$lib/server/http';
import { getNanGateway, upstreamErrorResponse } from '$lib/server/nan-client';
import { createRateLimiter, limitFromEnv } from '$lib/server/rate-limit';
import { UpstreamError } from '$lib/server/nan-gateway';

export const prerender = false;

// Per-IP fixed-window limit (E2 S4): one client must not burn the plan quota.
// Env-tunable, requests per minute.
const rateLimiter = createRateLimiter({
	limit: limitFromEnv('NAN_RATE_LIMIT_SPEAK', 20),
	windowMs: 60_000
});

export const POST: RequestHandler = async ({ request }) => {
	const gate = rateLimiter.check(request);
	if (!gate.allowed) {
		return errorResponse('UPSTREAM_RATE_LIMITED', 429);
	}
	const body = await parseJsonBody(request);
	if (!body.ok) {
		return badRequestResponse();
	}
	const source = typeof body.body === 'object' && body.body !== null ? body.body : {};
	const text = (source as Record<string, unknown>).text;
	if (!isAcceptableSpeakText(text)) {
		return invalidInputResponse(GENERIC_ERROR_CODE);
	}

	const apiKey = env.NAN_API_KEY ?? process.env.NAN_API_KEY;
	if (!apiKey) {
		return errorResponse(GENERIC_ERROR_CODE, 503);
	}

	try {
		// Gateway: bounded concurrency, timeout, transient-only retries and
		// typed upstream errors (no raw 502s). The audio passes through untouched.
		const upstream = await getNanGateway().request<Response>({
			model: 'kokoro',
			url: UPSTREAM_URL,
			body: {
				method: 'POST',
				headers: {
					Authorization: `Bearer ${apiKey}`,
					'Content-Type': 'application/json'
				},
				body: buildUpstreamBody(text.trim())
			},
			mapResponse: async (response) => {
				if (!response.ok || response.body === null) {
					throw new UpstreamError('unavailable', 'kokoro returned no audio');
				}
				return response;
			}
		});
		// Pass the synthesized audio straight through: Kokoro already produced a
		// complete wav document, there is nothing to transform downstream.
		return new Response(upstream.body, {
			headers: { 'Content-Type': 'audio/wav', 'Cache-Control': 'no-store' }
		});
	} catch (error) {
		const typed = upstreamErrorResponse(error);
		if (typed) return typed;
		throw error;
	}
};
