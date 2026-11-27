# Experimento principal: los tres métodos sobre fotos clasificadas por tipo

34 fotos (816 ejecuciones), 8 máscaras por foto. MSE sobre el hueco: menor es mejor.

### Por tipo de foto

| tipo de foto | casos | MSE mediano media | MSE mediano Bertalmio | MSE mediano ejemplares | tiempo mediano media (s) | tiempo mediano Bertalmio (s) | tiempo mediano ejemplares (s) | gana (media / Bertalmio / ejemplares) |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| lisa | 112 | 53.5 | 42.4 | 95.1 | 0.05 | 4.49 | 3.45 | 54 / 45 / 13 |
| estructura | 80 | 588.3 | 458.1 | 653.0 | 0.06 | 4.43 | 2.70 | 40 / 23 / 17 |
| textura | 80 | 1184.5 | 1335.2 | 2518.0 | 0.05 | 4.92 | 3.01 | 48 / 29 / 3 |

### Por tipo de máscara

| máscara | casos | MSE mediano media | MSE mediano Bertalmio | MSE mediano ejemplares | tiempo mediano media (s) | tiempo mediano Bertalmio (s) | tiempo mediano ejemplares (s) | gana (media / Bertalmio / ejemplares) |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| cuadrado | 102 | 531.7 | 432.7 | 747.7 | 0.04 | 2.25 | 2.72 | 52 / 38 / 12 |
| circulo | 68 | 252.8 | 244.1 | 452.9 | 0.07 | 4.26 | 3.49 | 34 / 21 / 13 |
| aranazo | 34 | 140.4 | 150.3 | 300.1 | 0.01 | 7.55 | 3.29 | 27 / 5 / 2 |
| motas | 34 | 195.3 | 159.6 | 333.8 | 0.05 | 16.26 | 1.55 | 16 / 17 / 1 |
| irregular | 34 | 550.0 | 507.1 | 1288.0 | 0.20 | 4.46 | 5.65 | 13 / 16 / 5 |

### Por tipo de foto y de máscara

| foto · máscara | casos | MSE mediano media | MSE mediano Bertalmio | MSE mediano ejemplares | tiempo mediano media (s) | tiempo mediano Bertalmio (s) | tiempo mediano ejemplares (s) | gana (media / Bertalmio / ejemplares) |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| lisa · cuadrado | 42 | 47.2 | 20.7 | 131.5 | 0.03 | 2.25 | 3.02 | 19 / 19 / 4 |
| lisa · circulo | 28 | 40.8 | 38.9 | 67.0 | 0.06 | 4.11 | 3.49 | 13 / 10 / 5 |
| lisa · aranazo | 14 | 83.7 | 90.1 | 136.2 | 0.01 | 7.62 | 3.58 | 12 / 2 / 0 |
| lisa · motas | 14 | 43.7 | 25.2 | 35.2 | 0.05 | 23.43 | 1.76 | 5 / 9 / 0 |
| lisa · irregular | 14 | 121.9 | 119.5 | 270.3 | 0.17 | 5.96 | 6.58 | 5 / 5 / 4 |
| estructura · cuadrado | 30 | 1114.9 | 1112.2 | 1504.5 | 0.04 | 2.29 | 2.56 | 14 / 9 / 7 |
| estructura · circulo | 20 | 684.2 | 694.8 | 553.4 | 0.08 | 4.54 | 3.16 | 9 / 4 / 7 |
| estructura · aranazo | 10 | 269.8 | 278.8 | 451.3 | 0.01 | 6.06 | 3.12 | 8 / 1 / 1 |
| estructura · motas | 10 | 271.4 | 253.8 | 470.2 | 0.05 | 13.79 | 1.54 | 5 / 4 / 1 |
| estructura · irregular | 10 | 842.0 | 700.1 | 1377.7 | 0.20 | 4.42 | 5.33 | 4 / 5 / 1 |
| textura · cuadrado | 30 | 1385.5 | 1381.8 | 3441.9 | 0.04 | 2.27 | 2.72 | 19 / 10 / 1 |
| textura · circulo | 20 | 1782.7 | 1866.6 | 2542.6 | 0.13 | 4.70 | 3.25 | 12 / 7 / 1 |
| textura · aranazo | 10 | 224.3 | 234.6 | 460.7 | 0.01 | 7.51 | 3.19 | 7 / 2 / 1 |
| textura · motas | 10 | 528.6 | 611.1 | 1164.4 | 0.05 | 25.82 | 1.54 | 6 / 4 / 0 |
| textura · irregular | 10 | 1703.0 | 1741.9 | 3544.6 | 0.25 | 4.45 | 5.48 | 4 / 6 / 0 |
