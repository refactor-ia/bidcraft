# BidCraft: de una app de presupuestos a un producto multiusuario

Este documento conserva el contexto del recorrido didáctico de BidCraft en RefactorIA. Partimos del trabajo del stream del viernes y seguimos con la misma app: revisar, probar, corregir, desplegar y operar, hasta tener un sistema usable por múltiples usuarios al mismo tiempo.

No buscamos una demo descartable ni agregar infraestructura para que parezca más seria. Queremos mostrar cómo Juan toma decisiones sobre una aplicación real y qué evidencia pide antes de dar algo por terminado.

## Destino y alcance

El destino es una app de presupuestos con datos íntegros, acceso adecuado para sus usuarios y un proceso de despliegue y operación verificable. La capacidad esperada se definirá con escenarios y mediciones, no con la frase "soporta muchos usuarios".

Esta visión no equivale a alcance ejecutable aprobado. El [roadmap existente](../../odd/tasks/roadmap-corrida-didactica.md) conserva sus hitos y condiciones: M2 y M3 no quedan aprobados automáticamente. No fijamos acá fechas, tecnologías nuevas, cantidad de servidores ni objetivos numéricos de carga.

## Cómo vamos a trabajar y enseñar

En cada sesión mostramos el problema, la revisión de Juan, las pruebas y la decisión. Si usamos IA para implementar o revisar, mostramos qué se le pidió y cómo comprobamos su resultado. La responsabilidad de aceptar el cambio no se delega al modelo.

- Un problema acotado por vez, con código y comportamiento reales.
- Distinguir lo que creemos de lo que pudimos comprobar.
- Mostrar qué falló, qué funcionó y qué límite sigue abierto.
- Verificar después de cambiar y después de desplegar.
- Cerrar con un aprendizaje aplicable y el siguiente paso justificado.

No hace falta resolver todo en una sesión. El orden puede ajustarse según lo que encontremos; las decisiones quedan registradas en la tarea correspondiente.

## Recorrido orientativo

| Tramo | Qué queremos demostrar |
|---|---|
| Punto de partida | Qué versión tenemos, qué flujos funcionan y qué sigue sin comprobarse. |
| Revisión y medición | Cómo Juan cuestiona una solución, pide pruebas y encuentra límites reproducibles. |
| Datos | Integridad de los presupuestos, manejo de errores y recuperación mediante backup y restauración comprobados. |
| Usuarios y acceso | Identidad, permisos y aislamiento de datos según el modelo de uso que definamos. |
| Concurrencia | Qué sucede cuando varios usuarios operan a la vez, incluyendo conflictos y dependencia de servicios externos. |
| Deploy | Una versión identificable en un entorno real, con comprobaciones posteriores y una forma de volver atrás. |
| Operación | Cómo detectamos fallas, investigamos incidentes y recuperamos el servicio o los datos. |
| Escalado | Qué capacidad necesitamos, dónde está el límite medido y qué cambio lo mejora sin romper lo anterior. |

Cada tramo se convierte en tareas acotadas cuando corresponde. No es una lista de funcionalidades implementadas ni una arquitectura decidida de antemano.

## Qué cuenta como evidencia

El roadmap registra una prueba histórica de 30 solicitudes de Whisper exitosas después de corregir el gateway. Eso demuestra un resultado acotado de aquella prueba, no que BidCraft esté preparado para uso multiusuario general.

Para afirmar que algo funciona, registramos versión o commit, entorno, configuración relevante sin secretos, escenario ejecutado y resultado. Una prueba local no certifica un deploy; un deploy exitoso no certifica aislamiento de usuarios, recuperación ni capacidad.

Antes de declarar la app lista para el uso esperado, habrá que definir y verificar condiciones concretas: flujos, usuarios y permisos, carga simultánea, comportamiento ante fallas y recuperación. Los resultados pendientes o fallidos se dicen explícitamente.

## Registro breve de cada sesión

En la tarea o issue correspondiente, dejar:

- **Pregunta y alcance:** qué queremos averiguar o cambiar y qué queda afuera.
- **Punto de partida:** versión/build, entorno y comportamiento previo.
- **Revisión:** qué cuestionó Juan y qué pruebas pidió para decidir.
- **Pruebas y resultados:** escenario, resultado esperado y observado; enlaces a evidencia sin datos privados ni credenciales.
- **Fallos y límites:** qué falló, qué no probamos y qué no permite concluir el resultado.
- **Decisión:** qué aceptamos o rechazamos y por qué.
- **Próximo paso:** la siguiente tarea acotada que justifica esa evidencia.

## Dónde sigue cada cosa

| Documento | Para qué sirve |
|---|---|
| Este contexto | Explica el propósito, el destino y la forma de enseñar y trabajar. |
| [Roadmap](../../odd/tasks/roadmap-corrida-didactica.md) | Coordina hitos, alcance aprobado y evidencia histórica, sin duplicar planes. |
| [Etapas](etapas.md) | Describe la corrida de medir, corregir con fundamento y verificar el deploy. |
| [Blueprint](blueprint.md) | Conserva el diseño de esa corrida; no acredita implementación ni vigencia por sí solo. |
| [Tarea del viernes](../../odd/tasks/presupuestos-viernes.md) | Conserva el contexto y las tareas concretas de esa sesión. |

Los cambios ejecutables llevan alcance, criterios y verificaciones en su propia tarea o issue. No abrimos un issue gigante ni duplicamos los estados del roadmap acá.

## Próximo paso

Contrastar el estado actual de BidCraft con los registros históricos y elegir la siguiente tarea acotada. Esa reconciliación todavía no se hizo como parte de este documento; tampoco se verificó aquí el comportamiento actual de la app.
