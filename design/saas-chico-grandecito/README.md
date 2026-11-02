# De SaaS chico a SaaS grandecito

Material para el stream explicativo de cinco horas de RefactorIA Labs, sin participación de Discord. El crecimiento de la app de presupuestos es el relato principal; las evidencias sostienen cada decisión.

| Archivo | Qué es |
|---|---|
| `01-pizarra.html` | Presentación elegida: 37 diapositivas en 6 bloques. Es lo que se transmite. |
| `guion.html` | Guion de conducción: cronograma de cinco horas, checklist previo y notas por diapositiva. Solo para vos. |

Los dos HTML principales son autónomos: fuentes, logo y braille van embebidos. Funcionan sin conexión.

## Presentar

1. Abrí `01-pizarra.html` en su propia ventana del navegador.
2. `F`: pantalla completa. `P`: abre la vista de presentador en otra ventana (notas, título de la siguiente diapositiva y reloj). Si el navegador bloquea la ventana emergente, permitila para este archivo.
3. En OBS capturá solo la ventana de la presentación.

Teclas: flechas, espacio o RePág/AvPág para navegar; Inicio/Fin para ir a la primera o la última diapositiva. La URL guarda la diapositiva actual (`#12`), así que recargar no te devuelve al principio. Los controles en pantalla aparecen solo al mover el mouse.

El escenario mide 1600×900 y se escala a cualquier ventana, con bandas negras si la proporción no es 16:9.

## Alcance editorial

Los diagramas y los ejemplos son conceptuales. Las diapositivas de demo siempre dicen "por demostrar en vivo": un resultado solo pasa a verificado cuando se ejecuta en pantalla. Lo que las notas dicen sobre el código de presupuestos viene de relevamientos de octubre; confirmalo antes del stream.

## Editar

- Contenido (bloques, diapositivas y notas): `content.py`.
- Diseño y comportamiento: `build.py`.

```sh
python3 design/saas-chico-grandecito/build.py
```

Regenera `01-pizarra.html` y `guion.html`, y actualiza las entradas de `design.json`. No necesita dependencias. Las fuentes se leen de `design/refactoria-design-system/fonts/`.

Tipos de diapositiva: `cover`, `section`, `statement`, `cards`, `flow`, `compare`, `table` y `demo`. En un título, `*palabra*` marca el único acento violeta.

## Verificación realizada

- Capturas de las 37 diapositivas en Chrome headless a 1600×900 y una a 1280×800 para comprobar el escalado.
- Navegación por teclado y botones probada con eventos simulados, incluidos los límites (no pasa de la primera ni de la última).
- Fuentes embebidas cargadas y sin recursos remotos.
- La vista de presentador no se probó de forma interactiva: probala antes de salir al aire.
