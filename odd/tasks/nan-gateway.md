# Feature: nan-gateway (E2 "Escalar lo que la medición pide")

Implement the E2 stage of the didactic run: a single server-side gateway for
all NaN upstream calls. Every piece responds to a measured E1 finding, and the
same measurement is repeated after it. Roadmap: `odd/tasks/roadmap-corrida-didactica.md`.

## Specs

S1. "La app nunca dispara más requests simultáneos que el límite" — outbound
    concurrency to the NaN API is bounded by a configurable per-model semaphore
    (default 10 for whisper, from the E1 measurement); excess requests queue
    (FIFO), they are never dropped silently.
S2. "Timeout + reintento con backoff" — every upstream call has an explicit
    timeout; retries (bounded, exponential backoff with jitter) apply only to
    transient failures (429, 5xx, network), never to 4xx validation errors.
S3. "Degradación elegante" — upstream failures produce typed errors with
    accurate, user-facing codes (upstream unavailable / rate limited), never
    the misleading `EXPORT_CLIENT_INVALID` fallback (E1 finding 2: whisper 502
    currently surfaces "Revisá los datos del cliente antes de exportar").
S4. "Rate limiting propio" — routes hitting NaN are rate-limited per client IP
    so a single client cannot burn the plan quota.
S5. Limits are configured by env with defaults, never hardcoded secrets.
S6. The API key never reaches the client; no behavior change for valid happy
    paths (parse SSE protocol unchanged).

## Tasks

- [x] T1 (S1,S2) — `src/lib/server/nan-gateway.ts`: per-model concurrency
      semaphore (FIFO queue), timeout, bounded retry with exponential backoff +
      jitter for transient failures only, typed `UpstreamError` (code + cause).
      Test-first: RED tests for (a) concurrency bound, (b) retry only transient,
      (c) timeout, (d) typed error surfaces.
- [x] T2 (S3) — honest error codes: add upstream codes to the ErrorCode union +
      `messages.ts`; replace `GENERIC_ERROR_CODE` misuse in upstream-failure
      paths (`http.ts` fallback stays for 404/400 only). UI renders the new
      messages.
- [x] T3 (S1,S2,S6) — wire the three proxies through the gateway:
      `/api/transcribe` (whisper, limit 10), `/api/speak` (kokoro), `/api/parse`
      (gemma4, streaming: semaphore wraps the upstream fetch; pump untouched).
- [x] T4 (S4) — per-IP rate limit middleware for NaN-hitting routes (env-tunable).
- [x] T5 (all) — verification: full test suite + svelte-check green; repeat the
      E1 measurements post-fix against innit-test:3100 and record before/after
      in the roadmap revision v1.2 (30x whisper burst must show ≤10 in flight
      and queued requests succeeding or degrading with honest codes, no raw 502).

## Work-unit commits

- T1: 851e446 feat(nan): add nan-gateway with per-model concurrency, timeout and typed upstream errors
- T2: 1185a3b feat(nan): honest upstream error codes (UPSTREAM_*) replacing generic fallback misuse
- T3: da0d1a7 feat(nan): route transcribe/speak/parse through nan-gateway
- T4: c93e51a feat(nan): per-IP rate limiting on NaN-hitting routes
- fix: 737ac7b fix(nan): restore transcribe route lost in wiring race (empty file committed as 405)
- T5 evidence: roadmap-corrida-didactica.md revision v1.2 — 30x whisper burst AFTER = 30x200 (~6s) vs BEFORE = 10x200 + 20x502; rate limiter 5x429 beyond 30/min; 353 tests + svelte-check 0 errors, local and on host.

## Notes / decisions

- Semaphore is in-memory, per-process: correct for the single-process deploy;
  documented as a known limit (declared in blueprint).
- `GENERIC_ERROR_CODE = 'EXPORT_CLIENT_INVALID'` stays only as the documented
  404/400 fallback; upstream failures stop using it (S3).
- E2 keeps the didactic framing: each piece is demoable in isolation, preceded
  by its E1 measurement.
