# Experimento por escenarios: ¿cuándo va mejor cada método?

Generado por `src/escenarios.py` el 2026-11-26 09:32 en macOS-27.0.1-arm64-arm-64bit-Mach-O (arm64), 288 ejecuciones sintéticas y 180 con fotos reales en 642 s.

MSE sobre el hueco: cuanto **menor**, mejor. «Gana» cuenta en cuántos casos cada método tuvo el MSE más bajo.

### Imágenes sintéticas, por familia

| familia | casos | MSE mediano media | MSE mediano Bertalmio | MSE mediano ejemplares | gana (media / Bertalmio / ejemplares) |
|---|---|---|---|---|---|
| liso | 24 | 5.1 | 5.0 | 8.6 | 1 / 11 / 12 |
| borde | 36 | 1057.1 | 785.2 | 310.5 | 0 / 10 / 26 |
| repetición | 36 | 526.3 | 515.9 | 0.0 | 10 / 2 / 24 |

### Imágenes sintéticas, por familia y subtipo

| familia | subtipo | casos | MSE mediano media | MSE mediano Bertalmio | MSE mediano ejemplares | gana (media / Bertalmio / ejemplares) |
|---|---|---|---|---|---|---|
| liso | degradado | 12 | 0.2 | 0.2 | 0.0 | 0 / 0 / 12 |
| liso | cielo con grano | 12 | 10.0 | 9.9 | 19.4 | 1 / 11 / 0 |
| borde | montaña recta | 12 | 993.7 | 647.7 | 93.2 | 0 / 1 / 11 |
| borde | cresta ondulada | 12 | 1005.7 | 660.5 | 832.1 | 0 / 9 / 3 |
| borde | hilo fino | 12 | 1615.6 | 1832.7 | 279.7 | 0 / 0 / 12 |
| repetición | césped en bloques | 12 | 526.3 | 515.9 | 0.0 | 0 / 0 / 12 |
| repetición | césped aleatorio | 12 | 55.8 | 56.8 | 110.3 | 10 / 2 / 0 |
| repetición | rayas | 12 | 1310.2 | 1305.9 | 0.0 | 0 / 0 / 12 |

### Imágenes sintéticas, por familia y tamaño del hueco (px de lado)

| familia | lado | casos | MSE mediano media | MSE mediano Bertalmio | MSE mediano ejemplares | gana (media / Bertalmio / ejemplares) |
|---|---|---|---|---|---|---|
| liso | 16 | 8 | 4.9 | 4.8 | 8.6 | 0 / 4 / 4 |
| liso | 32 | 8 | 4.9 | 4.8 | 9.4 | 1 / 3 / 4 |
| liso | 48 | 8 | 5.3 | 5.3 | 9.3 | 0 / 4 / 4 |
| borde | 16 | 12 | 1100.6 | 1056.1 | 271.4 | 0 / 2 / 10 |
| borde | 32 | 12 | 1041.1 | 691.4 | 313.3 | 0 / 3 / 9 |
| borde | 48 | 12 | 1023.8 | 763.2 | 503.3 | 0 / 5 / 7 |
| repetición | 16 | 12 | 533.9 | 524.1 | 0.0 | 4 / 0 / 8 |
| repetición | 32 | 12 | 504.7 | 493.7 | 0.0 | 2 / 2 / 8 |
| repetición | 48 | 12 | 533.6 | 514.9 | 0.0 | 4 / 0 / 8 |

### Fotos reales, por tipo de zona (hueco de 32 px)

| caso | casos | MSE mediano media | MSE mediano Bertalmio | MSE mediano ejemplares | gana (media / Bertalmio / ejemplares) |
|---|---|---|---|---|---|
| liso | 20 | 15.8 | 15.5 | 86.5 | 11 / 7 / 2 |
| borde | 20 | 1422.2 | 1665.7 | 2254.8 | 10 / 7 / 3 |
| repetición/textura | 20 | 1948.9 | 1823.6 | 2767.6 | 10 / 7 / 3 |
