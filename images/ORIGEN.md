# Origen de las imágenes

Las 100 imágenes de `originales/` proceden del conjunto **OpenPhoto Restore** (J. Chin, 2025):
<https://huggingface.co/datasets/joshuachin/openphoto-restore-dataset>

## Licencia

El conjunto de datos tiene licencia **CC BY 4.0**, que permite compartir y adaptar con la condición de dar crédito. Las fotografías proceden de **Unsplash** y se usan bajo la [licencia de Unsplash](https://unsplash.com/license). Cada archivo conserva el nombre con el que figura en el conjunto de datos, que es su identificador en Unsplash (`photo-<id>.jpg`).

## Cómo se han elegido

- Del subconjunto de prueba (`test`, 500 parejas) se ha tomado la columna `pristine_image`, que contiene las fotografías originales sin dañar.
- De esas 500 se han elegido 100 al azar, con la semilla 42: `random.Random(42).sample(range(500), 100)`.
- Los archivos se han guardado tal cual vienen en el conjunto de datos, sin recomprimirlos ni redimensionarlos. Tienen tamaños entre 768 y 1344 píxeles de lado.
- `lista_originales.txt` indica, para cada imagen, su posición (de 0 a 499) en el subconjunto de prueba y su nombre.

## Qué se usa de ellas

Se usan solo las imágenes **originales**. Los huecos (máscaras) los generamos nosotros sobre ellas, para poder comparar después el resultado con la imagen sin dañar. No se usan las versiones dañadas del conjunto de datos.

## Cita

J. Chin, «OpenPhoto Restore Dataset», Hugging Face, 2025. Licencia CC BY 4.0.
