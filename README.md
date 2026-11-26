# Restauración de imágenes mediante inpainting: difusión y ejemplares

Trabajo en grupo de **Procesamiento de Imágenes Digitales** (Universidad de Sevilla).

**Autores:** Juan Luis Rodríguez Artiaga y Alejandro Pineda Martín.

## De qué trata

Comparamos dos algoritmos de *inpainting*, es decir, de reconstrucción de las zonas dañadas o ausentes de una imagen a partir de lo que las rodea:

- **Difusión** (Juan Luis): propaga la información de los bordes del hueco hacia su interior. Parte de la difusión simple, que sustituye cada píxel del hueco por la media de sus cuatro vecinos, y sigue con la propagación a lo largo de las isófotas de Bertalmio et al.
- **Ejemplares** (Alejandro): rellena el hueco copiando parches de la parte conocida de la imagen, siguiendo a Criminisi et al.

Los comparamos en rendimiento (tiempo de cálculo) y en resultados (MSE, PSNR y comparación visual), con huecos de distinto tamaño y forma.

## Estructura del repositorio

```
.
├── README.md
├── requirements.txt
├── src/          código en módulos (máscaras, métricas, difusión, Bertalmio, ejemplares y los scripts de experimentos)
├── notebooks/    cuadernos de Jupyter que explican y prueban cada módulo
├── images/       imágenes de muestra y las usadas en la experimentación
└── resultados/   datos de los experimentos (archivos CSV) y comparación visual en PDF
```

## Cómo ejecutarlo

Hace falta Python 3 (probado con Python 3.14). Desde la carpeta del repositorio:

```bash
python3 -m venv .venv
source .venv/bin/activate        # en Windows: .venv\Scripts\activate
pip install -r requirements.txt
jupyter notebook
```

Después se abre el cuaderno que se quiera ejecutar desde la carpeta `notebooks/`.

### Repetir los experimentos

Para comprobar que los experimentos se pueden repetir, el cuaderno `notebooks/07_verificacion_experimentos.ipynb` (o `python src/verificar.py --imagenes 3`) los vuelve a ejecutar con las mismas imágenes y máscaras, mide tiempo y error en ese momento, guarda el registro en `resultados/verificacion/<fecha>/registro.md` y `registro.csv` y lo compara con `resultados/experimentos.csv`.

Desde la carpeta del repositorio, con el entorno activado. Tardan desde unos minutos hasta unos 30, según el método; el de ejemplares es el más lento.

```bash
# la media, Bertalmio y ejemplares sobre 20 fotos y 8 máscaras (los resultados se añaden al CSV)
python src/experimentos.py --imagenes 20 --ancho 256 --salida resultados/experimentos.csv

# comparación con huecos sobre bordes, textura y rayones, con PDF de original y resultados
python src/comparacion_variada.py --fotos 20 --metodos media Bertalmio ejemplares --csv resultados/comparacion_variada_3metodos.csv --pdf resultados/comparacion_variada_3metodos.pdf
```

Los dos scripts se pueden interrumpir y reanudar. Los tiempos dependen del ordenador: los de los resultados se midieron en un MacBook con chip Apple M4 y 16 GB de memoria.

Versiones con las que se ha probado: NumPy 2.5, OpenCV 5.0 y Matplotlib 3.11.

## Imágenes

Las imágenes de prueba proceden del conjunto **OpenPhoto Restore** (J. Chin, 2025, licencia CC BY 4.0, fotografías de Unsplash):
<https://huggingface.co/datasets/joshuachin/openphoto-restore-dataset>

Usamos sus imágenes originales, a las que aplicamos nuestras propias máscaras para poder medir el error, y sus versiones dañadas solo como ejemplos visuales.

En `images/originales/` hay 100 imágenes originales, elegidas al azar del subconjunto de prueba. Cómo se han elegido y su licencia están en [`images/ORIGEN.md`](images/ORIGEN.md). De ese conjunto saldrán las que se usen en los experimentos.

## Qué es original y qué no

- **Todo el código es nuestro.** No partimos de ningún repositorio existente ni hacemos *fork*: los dos algoritmos se programan desde cero.
- **Librerías usadas:** NumPy, OpenCV (para leer, mostrar y operar con imágenes) y Matplotlib. No se usan funciones de *inpainting* ya hechas.
- **Los métodos no son invención nuestra.** Salen de los artículos de la bibliografía. En la documentación se indica, junto a cada cosa, en qué sección, ecuación y página está.
- **Uso de IA:** se declara en la documentación, en el apartado «Uso de IA en este trabajo».

## Estado

Fase 3 (experimentación) en curso. Está hecho y probado:

- **Máscaras, métricas y tiempos** (`src/mascaras.py` y `src/metricas.py`, cuadernos 01 y 02).
- **Los tres métodos, con la misma interfaz** (entra la imagen dañada y la máscara; salen la imagen restaurada y el número de iteraciones): la media de los cuatro vecinos (`src/difusion.py`, cuaderno 03), el método de Bertalmio et al. (`src/bertalmio.py`, cuaderno 04) y el de ejemplares de Criminisi et al. (`src/ejemplares.py`, cuaderno 05). Los cuadernos 03 y 04 enseñan paso a paso cómo avanza cada iteración.
- **Experimentos** (`src/experimentos.py`, `src/comparacion_variada.py` y cuadernos 06 y 07): cronometraje de los tres métodos, comparación sobre 20 fotos y 8 máscaras, número de ciclos de Bertalmio, número de iteraciones de la media, y huecos colocados sobre bordes, texturas y rayones con controles. Los datos están en `resultados/`.

**Lo que se ha visto hasta ahora**, con el MSE y el PSNR sobre el hueco y fotos reducidas a 256 píxeles de ancho: la media y Bertalmio tienen un error parecido y la media es mucho más rápida; Bertalmio solo mejora de forma clara en el ejemplo sintético de su artículo. Ejemplares tiene más error de media, pero en algunos casos (cuando el hueco corta algo que continúa o se repite en otra parte de la imagen) gana por mucho. Son resultados con pocas fotos y con una métrica que favorece el borrón; el detalle y sus cautelas están en la documentación.

**Autoría:** el método de ejemplares y su cuaderno son de Alejandro Pineda Martín; el resto del código, de Juan Luis Rodríguez Artiaga.

## Bibliografía

1. M. Bertalmio, G. Sapiro, V. Caselles y C. Ballester, «Image inpainting», *Proceedings of the 27th Annual Conference on Computer Graphics and Interactive Techniques (SIGGRAPH)*, 2000, pp. 417–424. DOI 10.1145/344779.344972.
2. J. Chin, «OpenPhoto Restore Dataset», Hugging Face, 2025, licencia CC BY 4.0.
3. A. Criminisi, P. Pérez y K. Toyama, «Region filling and object removal by exemplar-based image inpainting», *IEEE Transactions on Image Processing*, vol. 13, n.º 9, pp. 1200–1212, 2004.
4. T. Shanmukhaprasanthi, S. M. Rayavarapu, Y. L. Lavanya y G. S. Rao, «A comprehensive study of image inpainting techniques with algorithmic approach», *2023 6th International Conference on Information Systems and Computer Networks (ISCON)*, IEEE, 2023. DOI 10.1109/ISCON57294.2023.10112205.
