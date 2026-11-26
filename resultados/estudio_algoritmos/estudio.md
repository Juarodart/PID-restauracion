# Estudio de cada algoritmo

Medianas sobre los casos de cada fila. MSE sobre el hueco (menor es mejor).

## tamaño

| valor | media: MSE | media: tiempo (s) | media: iteraciones | Bertalmio: MSE | Bertalmio: tiempo (s) | Bertalmio: iteraciones |
|---|---:|---:|---:|---:|---:|---:|
| 8 | 269.5 | 0.00 | 51 | 209.7 | 0.29 | 205 |
| 16 | 432.2 | 0.01 | 129 | 478.2 | 0.92 | 483 |
| 24 | 635.4 | 0.01 | 230 | 599.3 | 1.58 | 600 |
| 32 | 618.1 | 0.03 | 310 | 627.1 | 2.17 | 600 |
| 48 | 949.8 | 0.11 | 564 | 917.4 | 3.59 | 600 |
| 64 | 1394.0 | 0.24 | 719 | 1401.9 | 5.51 | 600 |

## forma

| valor | media: MSE | media: tiempo (s) | media: iteraciones | Bertalmio: MSE | Bertalmio: tiempo (s) | Bertalmio: iteraciones |
|---|---:|---:|---:|---:|---:|---:|
| cuadrado | 618.1 | 0.03 | 310 | 627.1 | 2.18 | 600 |
| círculo | 546.8 | 0.04 | 376 | 494.4 | 2.38 | 600 |
| tira 8×128 | 416.6 | 0.02 | 157 | 495.0 | 2.57 | 600 |
| arañazo | 209.3 | 0.03 | 58 | 203.1 | 17.91 | 600 |
| motas | 288.2 | 0.13 | 189 | 283.2 | 18.66 | 600 |
| irregular | 854.6 | 0.07 | 516 | 859.3 | 2.82 | 600 |

## contraste (borde)

| valor | media: MSE | media: tiempo (s) | media: iteraciones | Bertalmio: MSE | Bertalmio: tiempo (s) | Bertalmio: iteraciones |
|---|---:|---:|---:|---:|---:|---:|
| 10 | 6.9 | 0.01 | 150 | 6.0 | 0.35 | 95 |
| 20 | 24.1 | 0.02 | 213 | 9.3 | 2.16 | 600 |
| 40 | 89.0 | 0.03 | 275 | 31.0 | 2.17 | 600 |
| 80 | 344.7 | 0.03 | 336 | 94.2 | 2.18 | 600 |
| 160 | 1356.9 | 0.04 | 398 | 280.8 | 2.18 | 600 |
| 240 | 3035.1 | 0.04 | 434 | 520.0 | 2.19 | 600 |

## contraste (línea fina)

| valor | media: MSE | media: tiempo (s) | media: iteraciones | Bertalmio: MSE | Bertalmio: tiempo (s) | Bertalmio: iteraciones |
|---|---:|---:|---:|---:|---:|---:|
| 10 | 4.8 | 0.00 | 41 | 5.5 | 0.36 | 100 |
| 20 | 18.4 | 0.01 | 60 | 20.1 | 0.43 | 118 |
| 40 | 73.9 | 0.01 | 86 | 83.6 | 0.62 | 171 |
| 80 | 291.4 | 0.01 | 122 | 322.7 | 0.80 | 218 |
| 160 | 848.3 | 0.02 | 174 | 962.0 | 1.78 | 494 |
| 240 | 1004.1 | 0.02 | 192 | 1137.1 | 1.81 | 504 |

## propio: iteraciones

| valor | media: MSE | media: tiempo (s) | media: iteraciones | Bertalmio: MSE | Bertalmio: tiempo (s) | Bertalmio: iteraciones |
|---|---:|---:|---:|---:|---:|---:|
| 10 | 808.3 | 0.00 | 10 | - | - | - |
| 50 | 606.3 | 0.01 | 50 | - | - | - |
| 100 | 579.3 | 0.01 | 100 | - | - | - |
| 250 | 611.3 | 0.03 | 250 | - | - | - |
| 500 | 617.9 | 0.05 | 500 | - | - | - |
| 1000 | 616.0 | 0.10 | 1000 | - | - | - |
| hasta converger | 616.5 | 0.07 | 665 | - | - | - |

## propio: tolerancia

| valor | media: MSE | media: tiempo (s) | media: iteraciones | Bertalmio: MSE | Bertalmio: tiempo (s) | Bertalmio: iteraciones |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 709.2 | 0.00 | 19 | - | - | - |
| 0.1 | 601.8 | 0.01 | 106 | - | - | - |
| 0.01 | 618.1 | 0.03 | 310 | - | - | - |
| 0.001 | 616.5 | 0.07 | 665 | - | - | - |

## propio: valor de partida

| valor | media: MSE | media: tiempo (s) | media: iteraciones | Bertalmio: MSE | Bertalmio: tiempo (s) | Bertalmio: iteraciones |
|---|---:|---:|---:|---:|---:|---:|
| difusión simple | - | - | - | 627.1 | 2.20 | 600 |
| media plana | - | - | - | 838.9 | 2.15 | 600 |
| ruido | - | - | - | 1862.7 | 2.16 | 600 |

## propio: máximo de ciclos

| valor | media: MSE | media: tiempo (s) | media: iteraciones | Bertalmio: MSE | Bertalmio: tiempo (s) | Bertalmio: iteraciones |
|---|---:|---:|---:|---:|---:|---:|
| 25 | - | - | - | 630.2 | 0.12 | 25 |
| 50 | - | - | - | 630.4 | 0.22 | 50 |
| 100 | - | - | - | 623.5 | 0.39 | 100 |
| 200 | - | - | - | 610.8 | 0.76 | 200 |
| 600 | - | - | - | 627.1 | 2.20 | 600 |

## propio: paso temporal

| valor | media: MSE | media: tiempo (s) | media: iteraciones | Bertalmio: MSE | Bertalmio: tiempo (s) | Bertalmio: iteraciones |
|---|---:|---:|---:|---:|---:|---:|
| 0.05 | - | - | - | 627.3 | 2.20 | 600 |
| 0.1 | - | - | - | 627.1 | 2.19 | 600 |
| 0.2 | - | - | - | 636.9 | 2.19 | 600 |

## propio: pasos de difusión por ciclo

| valor | media: MSE | media: tiempo (s) | media: iteraciones | Bertalmio: MSE | Bertalmio: tiempo (s) | Bertalmio: iteraciones |
|---|---:|---:|---:|---:|---:|---:|
| 0 | - | - | - | 577.6 | 1.98 | 600 |
| 2 | - | - | - | 627.1 | 2.19 | 600 |
| 4 | - | - | - | 642.9 | 2.40 | 600 |
