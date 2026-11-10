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
├── src/          código en módulos (máscaras, métricas, difusión, ejemplares)
├── notebooks/    cuadernos de Jupyter que explican y prueban cada módulo
└── images/       imágenes de muestra y las usadas en la experimentación
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

Versiones con las que se ha probado: NumPy 2.5, OpenCV 5.0 y Matplotlib 3.11.

## Imágenes

Las imágenes de prueba proceden del conjunto **OpenPhoto Restore** (J. Chin, 2025, licencia CC BY 4.0, fotografías de Unsplash):
<https://huggingface.co/datasets/joshuachin/openphoto-restore-dataset>

Usamos sus imágenes originales, a las que aplicamos nuestras propias máscaras para poder medir el error, y sus versiones dañadas solo como ejemplos visuales.

## Qué es original y qué no

- **Todo el código es nuestro.** No partimos de ningún repositorio existente ni hacemos *fork*: los dos algoritmos se programan desde cero.
- **Librerías usadas:** NumPy, OpenCV (para leer, mostrar y operar con imágenes) y Matplotlib. No se usan funciones de *inpainting* ya hechas.
- **Los métodos no son invención nuestra.** Salen de los artículos de la bibliografía. En la documentación se indica, junto a cada cosa, en qué sección, ecuación y página está.
- **Uso de IA:** se declara en la documentación, en el apartado «Uso de IA en este trabajo».

## Estado

Seguimiento 2 en curso. De momento solo está creada la estructura del repositorio. Este apartado se irá actualizando según se añadan los módulos.

## Bibliografía

1. M. Bertalmio, G. Sapiro, V. Caselles y C. Ballester, «Image inpainting», *Proceedings of the 27th Annual Conference on Computer Graphics and Interactive Techniques (SIGGRAPH)*, 2000, pp. 417–424. DOI 10.1145/344779.344972.
2. J. Chin, «OpenPhoto Restore Dataset», Hugging Face, 2025, licencia CC BY 4.0.
3. A. Criminisi, P. Pérez y K. Toyama, «Region filling and object removal by exemplar-based image inpainting», *IEEE Transactions on Image Processing*, vol. 13, n.º 9, pp. 1200–1212, 2004.
4. T. Shanmukhaprasanthi, S. M. Rayavarapu, Y. L. Lavanya y G. S. Rao, «A comprehensive study of image inpainting techniques with algorithmic approach», *2023 6th International Conference on Information Systems and Computer Networks (ISCON)*, IEEE, 2023. DOI 10.1109/ISCON57294.2023.10112205.
