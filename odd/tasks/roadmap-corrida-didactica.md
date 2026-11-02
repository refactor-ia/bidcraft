# Roadmap: didactic run — scaling the nan budget app (3 stages)

Live-streamed didactic run: scale the `nan/` app from toy to sturdier while
teaching, in 3 stages. Coordination index only — a metadocument, never an
implementation issue. Approved revisions are appended; never rewritten.

## Objective

Define and verify a 3-stage didactic run (for a live YouTube/Twitch audience)
where each stage demonstrates a scaling outcome of the nan app, with measurable
success criteria, executed against the real app running on the remote host.

## Approved order (v1)

| Milestone | Work unit | Status | Readiness conditions |
|---|---|---|---|
| M1 — Didactic script verified over app running on remote host | U1.1 Define 3 stages with measurable scenarios | pending | Script approved by maintainer; each scenario has observable success criteria |
| M1 | U1.2 Blueprint of the scaled app | pending | Architecture target and per-stage introductions written |
| M1 | U1.3 Baseline running on remote host | done | Production build (adapter-node) serving on innit-test:3100 (systemd `nan-app`); tests 326 passed + svelte-check 0 errors on host; smoke: CRUD roundtrip (201/GET/PUT/DELETE/404), 422 QUANTITY_INVALID, parse SSE live, whisper live, kokoro live — all green. Evidence: URL http://192.168.200.6:3100, build from synced source (2026-10-17). Port 3000 was occupied by a pre-existing Docker container (efactura-gestor-app-1). PDF flow is client-side: browser check deferred to dry run. |
| M1 | U1.4 Script dry run | done | Dry run 2026-10-17 against http://192.168.200.6:3100. Whisper burst: 10/10 at 10 concurrent = 200; 30 concurrent = 10x200 + 20x502 → observed limit ≈10 concurrent (the controlled-explosion scene works as designed). SQLite: 20 concurrent valid writes = 20x201, all stored, cleanup 200. Invalid flood: 40/40 clean 422. Parse SSE, kokoro, CRUD re-verified. Findings recorded in v1.1 below. |
| M2 — undefined (stage 2) | — | not planned | Defined only after M1 closes |
| M3 — undefined (stage 3) | — | not planned | Defined only after M2 closes |

## Gates

- M1 complete only when: script approved by maintainer AND dry run green AND
  evidence recorded with URL and build identity.
- No unit is contribution-ready while any of its readiness conditions is
  unresolved; readiness is never announced with a pending decision.

## How to contribute

- Work units are executed ODD-style with feature tracking under `odd/tasks/`.
- Bugs and small tasks stay in the normal issue-first flow; do not force ODD
  treatment by size.
- Each work unit's full plan (scope, acceptance criteria, checks) lives in its
  own task/issue before being linked here.

## Out of flow

- App feature work unrelated to the didactic run (benchmark canonical docs,
  other participants' implementations) does not pass through this index.

## Not prioritized

- Stage 2 and stage 3 outcomes: ideas exist only as conversation; they stay
  here and never create issues automatically until the maintainer approves an
  M2/M3 milestone after M1 closes.

## Revisions

### v1 (approved by maintainer)

- Initial index. M1 approved with units U1.1–U1.4; M2/M3 explicitly not planned
  until M1 closes. No dates, no promised versions.
- Proposal marker: APPROVED-IN-CONVERSATION (live session, maintainer said "dale gas").

### v1.1 (dry-run findings, append-only)

- Finding 1 (E1 scene confirmed): whisper upstream limit ≈ 10 concurrent —
  10/10 at 10 concurrent succeeded; at 30 concurrent, 10 succeeded and 20 got
  502. This is the controlled explosion the maintainer designed for E1.
- Finding 2 (E2 fix target, deliberately NOT fixed now — it is the E2
  teaching moment): `GENERIC_ERROR_CODE = 'EXPORT_CLIENT_INVALID'` in
  `src/lib/server/http.ts` makes every upstream 502 (e.g. whisper rejection)
  surface the user-facing message "Revisá los datos del cliente antes de
  exportar." — a misleading degradation. E2 introduces typed upstream errors
  with accurate codes + retry/backoff.
- Finding 3: SQLite writes are clean under 20-way concurrency (no lost writes,
  no 5xx); the sync `node:sqlite` layer held. E2 scene may de-emphasize DB
  concurrency and focus on the NaN gateway.
- Evidence: all against http://192.168.200.6:3100, build from source synced
  2026-10-17, tests 326 passed + svelte-check 0 errors on host.

### v1.2 (E2 post-fix measurement, append-only)

- Gateway deployed (commits 851e446, 1185a3b, da0d1a7, c93e51a, 737ac7b on
  feat/nan-gateway): per-model semaphore (whisper=10 from E1), timeout, bounded
  transient-only retry with backoff, typed UPSTREAM_* error codes, per-IP rate
  limiting (env-tunable).
- Repeated E1 measurement (30x whisper burst, same 6s wav, same URL):
  BEFORE (E1): 10x200 + 20x502, misleading "Revisá los datos del cliente"
  message. AFTER: 30x200 — all 30 transcriptions correct, ~6s total (3 waves
  of 10), zero errors. The queue absorbed the excess instead of failing.
- Incident during deployment: a T4 wiring race left src/routes/api/transcribe/
  +server.ts empty and it was committed (30x405). Suite/svelte-check did not
  catch it (route modules untested); live smoke did. Fixed in 737ac7b; lesson:
  route-level smoke is part of verification.
- Rate limiter verified: 35 rapid parse requests → 30x422 + 5x429
  UPSTREAM_RATE_LIMITED (limit 30/min per IP).
- Tests: 353 passed (18 files), svelte-check 0 errors, locally and on host.
