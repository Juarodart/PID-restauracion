# Experimento principal: los tres métodos sobre fotos clasificadas por tipo

18 fotos (432 ejecuciones), 8 máscaras por foto. MSE sobre el hueco: menor es mejor.

### Por tipo de foto

| tipo de foto | casos | MSE mediano media | MSE mediano Bertalmio | MSE mediano ejemplares | tiempo mediano media (s) | tiempo mediano Bertalmio (s) | tiempo mediano ejemplares (s) | gana (media / Bertalmio / ejemplares) |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| lisa | 48 | 10.1 | 9.5 | 21.7 | 0.02 | 2.16 | 2.30 | 25 / 20 / 3 |
| estructura | 48 | 460.9 | 406.3 | 519.5 | 0.03 | 4.35 | 1.78 | 22 / 17 / 9 |
| textura | 48 | 1362.8 | 1472.3 | 2974.5 | 0.05 | 4.42 | 2.63 | 35 / 12 / 1 |

### Por tipo de máscara

| máscara | casos | MSE mediano media | MSE mediano Bertalmio | MSE mediano ejemplares | tiempo mediano media (s) | tiempo mediano Bertalmio (s) | tiempo mediano ejemplares (s) | gana (media / Bertalmio / ejemplares) |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| cuadrado | 54 | 561.0 | 528.9 | 1520.7 | 0.03 | 2.20 | 2.06 | 27 / 21 / 6 |
| circulo | 36 | 195.9 | 228.2 | 403.0 | 0.04 | 2.14 | 2.46 | 24 / 8 / 4 |
| aranazo | 18 | 151.4 | 174.2 | 280.8 | 0.01 | 4.27 | 2.48 | 14 / 2 / 2 |
| motas | 18 | 269.0 | 214.0 | 308.7 | 0.04 | 13.20 | 1.21 | 11 / 7 / 0 |
| irregular | 18 | 564.7 | 469.1 | 1335.0 | 0.17 | 4.38 | 4.16 | 6 / 11 / 1 |

### Por tipo de foto y de máscara

| foto · máscara | casos | MSE mediano media | MSE mediano Bertalmio | MSE mediano ejemplares | tiempo mediano media (s) | tiempo mediano Bertalmio (s) | tiempo mediano ejemplares (s) | gana (media / Bertalmio / ejemplares) |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| lisa · cuadrado | 18 | 7.4 | 7.2 | 25.5 | 0.02 | 1.17 | 2.29 | 7 / 10 / 1 |
| lisa · circulo | 12 | 4.4 | 5.0 | 14.5 | 0.02 | 1.49 | 2.54 | 8 / 3 / 1 |
| lisa · aranazo | 6 | 13.7 | 16.3 | 35.1 | 0.01 | 4.31 | 2.73 | 5 / 1 / 0 |
| lisa · motas | 6 | 20.3 | 4.3 | 14.9 | 0.04 | 10.23 | 1.32 | 2 / 4 / 0 |
| lisa · irregular | 6 | 82.5 | 89.5 | 282.2 | 0.16 | 4.37 | 4.86 | 3 / 2 / 1 |
| estructura · cuadrado | 18 | 943.8 | 1024.9 | 1504.5 | 0.04 | 2.20 | 1.41 | 8 / 5 / 5 |
| estructura · circulo | 12 | 333.4 | 329.8 | 403.0 | 0.06 | 3.44 | 2.38 | 6 / 3 / 3 |
| estructura · aranazo | 6 | 216.9 | 240.4 | 337.0 | 0.01 | 3.94 | 1.66 | 4 / 1 / 1 |
| estructura · motas | 6 | 269.0 | 214.0 | 308.7 | 0.03 | 10.31 | 0.76 | 3 / 3 / 0 |
| estructura · irregular | 6 | 777.8 | 518.9 | 831.3 | 0.19 | 4.38 | 2.85 | 1 / 5 / 0 |
| textura · cuadrado | 18 | 1556.8 | 1660.1 | 3836.5 | 0.04 | 2.21 | 2.63 | 12 / 6 / 0 |
| textura · circulo | 12 | 2031.9 | 2096.2 | 4278.9 | 0.11 | 3.66 | 2.57 | 10 / 2 / 0 |
| textura · aranazo | 6 | 375.8 | 424.9 | 941.4 | 0.01 | 4.90 | 3.18 | 5 / 0 / 1 |
| textura · motas | 6 | 882.6 | 1184.6 | 1400.6 | 0.05 | 14.86 | 1.53 | 6 / 0 / 0 |
| textura · irregular | 6 | 2502.7 | 2446.2 | 4662.3 | 0.19 | 4.39 | 5.27 | 2 / 4 / 0 |
