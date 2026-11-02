# Corrida didáctica: "Del juguete a producción"

Guion de la corrida en vivo (stream público). Este documento apunta al índice
de roadmap como fuente viva del sequencing: `odd/tasks/roadmap-corrida-didactica.md`.
Reglas de la corrida: toda medición se repite igual pre/post; toda evidencia
declara URL + build; "no ejecutado" es un resultado válido que se declara; un
fix sin medición que lo justifique no entra al guion.

## Etapa 1 — "Dónde se rompe el juguete"

**Resultado demostrado:** los límites del sistema actual, medidos con números,
no contados como anécdota.

Escenarios:

1. **Explosión controlada de whisper.** Se acelera el dictado con carga
   concurrente hasta chocar el límite fijo de concurrencia del plan dev de la
   API de NaN. La falla es determinística y esperada: se muestra como dato.
   El umbral exacto NO se revela antes de la escena: medirlo en vivo ES la
   escena (decisión del maintainer: explosión controlada, no spoiler).
2. **Escritura concurrente a SQLite.** Varios clientes escribiendo al mismo
   tiempo; se observa comportamiento real de `node:sqlite` síncrono.
3. **Submit inválido masivo.** Ráfaga de payloads inválidos; la app debe
   rechazar limpio (422 con código), sin corromper datos.

Criterio de éxito: cada límite queda registrado con número observado
(umbral de concurrencia, comportamiento bajo escritura concurrente, tasa de
rechazos limpios). Evidencia con URL + build.

## Etapa 2 — "Escalar lo que la medición pide"

**Resultado demostrado:** cada fix responde a un dato de la Etapa 1. El límite
de la API no se arregla del lado del cliente: se arregla del lado de la app.

Escenarios (solo lo que E1 evidenció):

1. **Cola/semáforo de concurrencia hacia NaN:** la app nunca dispara más
   requests simultáneos que el límite medido.
2. **Timeout + reintento con backoff** en el proxy de transcripción.
3. **Degradación elegante:** si whisper no responde, el usuario ve un mensaje
   útil con código, no un spinner eterno.
4. **Rate limiting propio** para proteger al backend y a la cuota.

Criterio de éxito: misma medición de E1 repetida pre/post — la API nunca
recibe más que el límite, y bajo exceso la app responde con degradación
manejable en vez de error crudo. Comparación antes/después documentada.

## Etapa 3 — "A producción en innit-test"

**Resultado demostrado:** la app corre donde hay que correrla, no en
`localhost:5173`. Dado que la app ya fue verificada, esto es re-verificación
formal de evidencia, no QA desde cero.

Escenarios:

1. **Deploy a innit-test (por SSH):** build de producción adapter-node,
   proceso persistente, `NAN_API_KEY` en el server, nunca en el repo.
   Configuración concreta del server (usuario, ruta, puerto, Node) se define
   en U1.3 del roadmap.
2. **Smoke de los 4 flujos críticos** contra el server real: agregar ítem,
   parse NL, dictado (incluida la trampa secure-context del micrófono fuera
   de localhost), PDF.
3. **Verificación formal:** `pnpm test` + `svelte-check` en verde contra el
   build desplegado.

Criterio de éxito: smoke verde con build ID y URL de innit-test en la
evidencia; verificación con build declarado.
