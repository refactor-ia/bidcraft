/**
 * POST /api/transcribe: speech-to-text for budget dictation.
 *
 * The client posts one recorded audio clip as multipart/form-data
 * (`audio` field). The server validates the upload, proxies it to the NaN
 * API (OpenAI-compatible `whisper` transcription endpoint) through the
 * nan-gateway and answers `{ text }` with the plain transcription. The
 * client then feeds that text into the existing /api/parse flow. The API
 * key never reaches the client, so this must stay server-side.
 */

import { env } from '$env/dynamic/private';
import type { RequestHandler } from './$types';
import {
	UPSTREAM_URL,
	buildUpstreamForm,
	extractTranscriptionText,
	isAcceptedAudioType,
	MAX_AUDIO_BYTES
} from '$lib/server/transcribe';
import {
	GENERIC_ERROR_CODE,
	badRequestResponse,
	errorResponse,
	invalidInputResponse
} from '$lib/server/http';
import { getNanGateway, upstreamErrorResponse } from '$lib/server/nan-client';
import { createRateLimiter, limitFromEnv } from '$lib/server/rate-limit';

export const prerender = false;

// Per-IP fixed-window limit (E2 S4): one client must not burn the plan quota.
// Env-tunable, requests per minute.
const rateLimiter = createRateLimiter({
	limit: limitFromEnv('NAN_RATE_LIMIT_TRANSCRIBE', 20),
	windowMs: 60_000
});

export const POST: RequestHandler = async ({ request }) => {
	const gate = rateLimiter.check(request);
	if (!gate.allowed) {
		return errorResponse('UPSTREAM_RATE_LIMITED', 429);
	}

	let form: FormData;
	try {
		form = await request.formData();
	} catch {
		return badRequestResponse();
	}
	const upload = form.get('audio');
	if (!(upload instanceof File) || upload.size === 0) {
		return badRequestResponse();
	}
	if (upload.size > MAX_AUDIO_BYTES || !isAcceptedAudioType(upload.type)) {
		return invalidInputResponse(GENERIC_ERROR_CODE);
	}

	const apiKey = env.NAN_API_KEY ?? process.env.NAN_API_KEY;
	if (!apiKey) {
		return errorResponse(GENERIC_ERROR_CODE, 503);
	}

	try {
		// The gateway bounds concurrency (E1 finding: the dev plan rejects >~10
		// concurrent whisper calls), times the call out, retries transient
		// failures and reports typed errors instead of raw 502s.
		const result = await getNanGateway().request<{ ok: true; text: string } | { ok: false }>({
			model: 'whisper',
			url: UPSTREAM_URL,
			body: {
				method: 'POST',
				headers: { Authorization: `Bearer ${apiKey}` },
				body: buildUpstreamForm(upload)
			},
			mapResponse: async (upstream) => {
				let payload: unknown;
				try {
					payload = await upstream.json();
				} catch {
					return { ok: false as const };
				}
				const text = extractTranscriptionText(payload);
				if (text === null) {
					// The upstream answered but produced no usable text (silence or
					// an unexpected response shape): a domain-level invalid input,
					// not a transport failure.
					return { ok: false as const };
				}
				return { ok: true as const, text: text.slice(0, 2000) };
			}
		});
		return result.ok
			? Response.json({ text: result.text })
			: invalidInputResponse(GENERIC_ERROR_CODE);
	} catch (error) {
		const typed = upstreamErrorResponse(error);
		if (typed) return typed;
		throw error;
	}
};
