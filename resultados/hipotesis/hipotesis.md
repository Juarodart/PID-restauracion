# Contraste de las hipótesis H1 a H4

Contraste de signos exacto (bilateral): «A < B» es en cuántos casos A tiene menos error que B. p < 0,05 se considera diferencia clara.

## H1: los ejemplares mantienen mejor el resultado en huecos grandes

30 fotos, hueco cuadrado centrado.

| lado | MSE mediano media | MSE mediano ejemplares | cociente ejemplares/media (mediana) | ejemplares < media | ejemplares > media | p |
|---:|---:|---:|---:|---:|---:|---:|
| 64 | 1306 | 2106 | 1.56 | 6 | 24 | 0,001 |
| 96 | 1526 | 2698 | 1.87 | 2 | 28 | < 0,001 |
| 128 | 1766 | 2823 | 1.63 | 5 | 25 | < 0,001 |

El cociente ejemplares/media va de 1.56 a 1.63 al pasar de 64 a 128 píxeles: crece, es decir, los ejemplares empeoran respecto a la media cuando el hueco crece.

| tipo de foto (hueco 128) | fotos | ejemplares < media | ejemplares > media | p |
|---|---:|---:|---:|---:|
| lisa | 10 | 3 | 7 | 0,344 |
| estructura | 10 | 2 | 8 | 0,109 |
| textura | 10 | 0 | 10 | 0,002 |

## H2: tiempo de cálculo (difusión lenta, ejemplares rápidos)

Exponente k de t ∝ (área del hueco)^k, ajustado con las medianas por tamaño de hueco (estudio de tamaño, 8 a 64 px, y huecos grandes, 64 a 128 px):

| método | t con 64 px (s) | t con 128 px (s) | exponente k (8 a 128 px) |
|---|---:|---:|---:|
| media | 0.5 | 3.9 | 1.47 |
| Bertalmio | 10.9 | 37.7 | 0.85 |
| ejemplares | 12.0 | 35.4 | 0.85 |

Tiempo según el tamaño de la imagen (cronometraje B), si el archivo lo contiene:

| método | tamaños de imagen (px de ancho) | tiempos (s) | exponente k (t ∝ ancho^k) |
|---|---|---|---:|
| media | 128, 256, 384, 512, 768 | 0.01, 0.00, 0.01, 0.00, 0.00 | -0.22 |
| Bertalmio | 128, 256, 384, 512, 768 | 1.10, 0.44, 0.38, 0.37, 0.28 | -0.72 |
| ejemplares | 128, 256, 384, 512, 768 | 0.08, 0.45, 0.93, 2.09, 4.70 | 2.27 |

## H3: la difusión reconstruye mal los bordes curvos que cruzan el hueco

Arco de radio R que cruza el hueco de 32 px (4 variantes por radio). MSE mediano y comparación por casos:

| radio R | media | Bertalmio | ejemplares | Bertalmio < media (de 4) | p |
|---:|---:|---:|---:|---:|---:|
| 2000 | 930 | 246 | 158 | 4 | 0,125 |
| 200 | 924 | 261 | 397 | 4 | 0,125 |
| 100 | 924 | 284 | 860 | 4 | 0,125 |
| 50 | 929 | 372 | 1359 | 4 | 0,125 |
| 32 | 951 | 569 | 4399 | 4 | 0,125 |
| 20 | 960 | 1014 | 5089 | 1 | 0,625 |
| 12 | 1377 | 2240 | 4601 | 0 | 0,125 |

En conjunto (28 casos): Bertalmio < media en 21, Bertalmio > media en 7, p = 0,013.

## H4: ejemplares reconstruyen estructura y textura; la difusión, sobre todo estructura

Fotos reales (experimento principal), contraste de signos sobre los casos foto × máscara:

| tipo de foto | comparación | casos | A < B | A > B | p |
|---|---|---:|---:|---:|---:|
| lisa | Bertalmio (A) frente a media (B) | 112 | 53 | 55 | 0,923 |
| lisa | ejemplares (A) frente a media (B) | 112 | 20 | 92 | < 0,001 |
| lisa | ejemplares (A) frente a Bertalmio (B) | 112 | 16 | 96 | < 0,001 |
| estructura | Bertalmio (A) frente a media (B) | 80 | 32 | 48 | 0,093 |
| estructura | ejemplares (A) frente a media (B) | 80 | 25 | 55 | 0,001 |
| estructura | ejemplares (A) frente a Bertalmio (B) | 80 | 19 | 61 | < 0,001 |
| textura | Bertalmio (A) frente a media (B) | 80 | 30 | 50 | 0,033 |
| textura | ejemplares (A) frente a media (B) | 80 | 6 | 74 | < 0,001 |
| textura | ejemplares (A) frente a Bertalmio (B) | 80 | 4 | 76 | < 0,001 |

Repetición exacta más ruido (MSE mediano; el cruce es el ruido a partir del cual la media supera a ejemplares):

| patrón | ruido σ | media | Bertalmio | ejemplares |
|---|---:|---:|---:|---:|
| rayas | 0 | 1204 | 1218 | 0 |
| rayas | 5 | 1230 | 1237 | 50 |
| rayas | 10 | 1307 | 1314 | 196 |
| rayas | 20 | 1600 | 1587 | 768 |
| rayas | 40 | 2569 | 2513 | 2813 |
| rayas | 80 | 5309 | 5182 | 8906 |
| bloques | 0 | 502 | 488 | 0 |
| bloques | 5 | 527 | 515 | 50 |
| bloques | 10 | 602 | 586 | 196 |
| bloques | 20 | 887 | 863 | 773 |
| bloques | 40 | 1872 | 1831 | 3552 |
| bloques | 80 | 4710 | 4630 | 8684 |
