# Presupuestos: escalada a SaaS grandecito (stream viernes)

Header: caso de estudio del stream Open Build Room. Auditoría por evidencias,
no por lectura de código. La tabla de decisión del stream sale de este flujo.

## Specs

S1: "Comando único de evidencias: suite + check + build + smokes → reporte" (T1)
S2: "Fijar adapter-node versión exacta (hoy ^5.5.7 contradice EVIDENCE.md que declara adapter-static) + smoke del build de producción, enchufado a T1" (T2)
S3: "Backup programado + restore probado del SQLite embebido" (T3)
S4: "Trigger de migración SQLite → Postgres: métricas, medición actual, decisión documentada" (T4)
S5: "Auth desde cero (no hay session.ts; src/lib/server/ tiene db.ts, budgets.ts, mail.ts, nan-gateway.ts, rate-limit.ts)" (T5)
S6: "Modelo multi-tenant + test de fuga entre tenants" (T6)
S7: "Link compartible del presupuesto + test de que no da acceso a nada más" (T7)
S8: "Destino de deploy (VPS vs PaaS) + pipeline con rollback probado" (T8)

## Tasks

- T1 (S1): comando de evidencias | sin deps | commit: -
- T2 (S2): adapter-node fijado + smoke | T1 | commit: -
- T3 (S3): backup + restore probado | T1 | commit: -
- T4 (S4): trigger de migración documentado | T1, T3 | commit: -
- T5 (S5): auth desde cero | T1 | commit: - (alto riesgo: verificación independiente)
- T6 (S6): multi-tenant + test de fuga | T5 | commit: -
- T7 (S7): link compartible + test de alcance | T5, T6 | commit: -
- T8 (S8): deploy + rollback probado | T2 | commit: - (paralelizable con T5-T7)

## Log

L1: "Estoy creando un evento en discord para el stream de este viernes. No se bien
que titulo ponerle ni la descripción pero la idea es seguir escalando la app de
presupuestos"
L2: Correcciones del repo: no existe session.ts (auth es desde cero, S5) y
adapter-node ^5.5.7 contradice la línea base congelada de EVIDENCE.md (S2).
L3: Orden aprobado: T1-T3 para el stream del viernes; T5+ son grandes y de
riesgo alto, no entran en una sola sesión.
L4: Pedido original de la sesión de planificación (verbatim):
"vamos a planificar la sesión del viernes:

 Acá van los temas del viernes, ya estructurados para volcarlos como tareas ODD en presupuestos:

 Área Datos (SQLite):
 1. Definir el trigger de migración SQLite → Postgres: qué métrica lo dispara (tamaño de DB, escrituras concurrentes, queries que ya no rinden) y qué
    evidencia lo mide hoy.
 2. Estrategia de backup y recovery del SQLite embebido: version chico (backup programado + restore probado) antes de pensar en migrar.

 Área Auth / Multi-tenant:
 3. Auth real para session.ts: reemplazar la sesión actual por auth verificable (OAuth o magic link), con evidencia: tests de sesión expirada, roles,
 sesiones inválidas.
 4. Aislamiento multi-tenant: definir el modelo (row-level con user_id vs esquemas separados) y su test de fuga de datos entre tenants.

 Área Links compartibles:
 5. Link compartible del presupuesto: decidir firmado vs público, con expiración o no, y evidencia de que un link no filtrado no da acceso a nada
 más.

 Área Deploy / Infra:
 6. Smoke del build adapter-node de producción: es el pendiente menor que ya teníamos; correrlo y dejarlo automatizado.
 7. Decidir destino de deploy (VPS vs PaaS): con criterio explícito de costo/rollback/CI, y dejar el pipeline mínimo con rollback probado.

 Área Evidencias (transversal):
 8. Paquete de evidencias del proyecto: un doc/comando que genere de una sola vez el estado verificable del sistema (suite, build, smokes, reportes
 de agentes). Es la base del paradigma del stream: si esto no existe, crearlo ES la primera tarea.

 Nota de prioridad para el stream: los temas 6 y 8 son los que sostienen todo lo demás (sin evidencias no hay auditoría), así que si el ODD permite
 ordenar, van primero."
L5: Estado: planificado. Cero ejecución por decisión del usuario; ninguna tarea iniciada.
L6: Contexto del stream aportado por el usuario (2026-10-26, resumen fiel; no autoriza ejecución):
- Evento: live YouTube https://youtube.com/live/O95RAtUCnGw; Discord https://discord.gg/UGa99UUW?event=1564275099987746876.
  Título "Escalando la app de presupuestos: de SaaS chico a SaaS grandecito". 19 hs UY/AR/CL, 17 CO/PE, 16 MX, 23 ES.
  Playlist Open Build Room. Título, descripción, thumbnail, posts de X y evento de Discord cerrados: "No tocar nada de eso."
- Paradigma (no negociable): "no se audita el código, se auditan las evidencias de que el sistema se comporta. Si no hay evidencia, eso ES el hallazgo."
  No se abre código real en vivo. No se entra en polémica directa con nadie.
- Agenda 90 min: marco (5), auditoría por evidencias verificada / con huecos / sin evidencia (25-30), bifurcaciones SQLite→Postgres,
  auth+multi-tenant, link compartible, VPS vs PaaS con escenario de estrés y evidencia necesaria (30-35), tabla de decisión
  chico / grandecito / trigger + evidencia a vigilar (15, entregable), cierre 3 conclusiones + próximo paso + Discord (5).
- Hallazgo en vivo: adapter-node ^5.5.7 vs línea base de EVIDENCE.md (adapter-static); smoke del build no reproducible hasta fijar versión.
- Estado: nada ejecutado, cero commits. "el arranque de T1 es decisión de él." Viernes cubre T1-T3.
- Pendiente: lista de evidencias concretas para el paquete del viernes (suite, build, reportes a mano antes del stream); thumbnail (Juan, ChatGPT).
