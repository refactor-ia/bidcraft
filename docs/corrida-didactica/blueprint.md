# Blueprint: app escalada (arquitectura objetivo por etapa)

Companion de `docs/corrida-didactica/etapas.md`. Define qué tiene la app hoy,
dónde va, y qué se introduce en cada etapa de la corrida — sin revelar en una
etapa lo que otra enseña.

## Estado actual (baseline)

- SvelteKit + adapter-node; UI con tokens refactoria.dev, dictado por voz
  (`/api/transcribe` → whisper en api.nan.builders), confirmación TTS
  (`/api/speak` → kokoro), parse NL en streaming (`/api/parse` → gemma4,
  NDJSON por ítem), persistencia SQLite vía `node:sqlite` síncrono, envío por
  mail.
- Los tres proxies a NaN comparten una shape parecida: fetch directo, sin
  timeout explícito, sin reintento, sin límite de concurrencia propio.
- Error taxonomy: ErrorCode map → HTTP 422 con código+mensaje (`messages.ts`).

## Arquitectura objetivo (lo que E2 introduce)

Un solo módulo de salida hacia NaN (`nan/src/lib/server/nan-gateway.ts`),
usado por los tres proxies:

1. **Semáforo de concurrencia** por modelo (p. ej. whisper): cola FIFO, en
   memoria, con límite configurado por env. La app nunca dispara más
   requests simultáneos que el límite del plan.
2. **Timeout + reintento con backoff** exponencial acotado; reintentos solo
   para errores transitorios (429/5xx/red), nunca para 4xx de validación.
3. **Degradación elegante:** en vez de excepción cruda, respuesta tipada
   `{ ok: false, code, retryAfter? }` que la UI traduce a mensaje útil; el
   flujo de presupuesto nunca queda colgado.
4. **Rate limiting propio** por IP en las rutas que golpean NaN, para
   proteger la cuota del plan dev.

Invariantes: la key nunca llega al cliente; los límites se configuran por
env, no hardcodeados; cada fix de E2 responde a una medición de E1.

## Qué se introduce en cada etapa (regla de no-spoiler)

- **E1:** la app tal cual está + harness de carga (concurrentes desde
  varias pestañas/scripts). Se miden límites, no se corrige nada.
- **E2:** el gateway (`nan-gateway.ts`) con sus 4 piezas, una por una, cada
  una precedida por su medición de E1 y seguida de la misma medición.
- **E3:** nada de código nuevo salvo config de deploy: build de producción,
  proceso persistente, secretos en el server (`NAN_API_KEY`), smoke formal.
  Config concreta de innit-test se define en U1.3 del roadmap.

## Decisiones abiertas (se cierran durante E2, en vivo, con la audiencia)

- Cola en memoria vs persistente: suficiente la de memoria para el alcance
  (proceso único); se declara como decisión y su límite.
- Política exacta de reintentos (cuántos, cuánto backoff): la fija la
  medición de E1, no el gusto.
