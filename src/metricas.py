"""
Métricas para evaluar una restauración y cronometrar los algoritmos.

Se comparan dos imágenes: la original (sana, antes de estropearla) y la
restaurada (el resultado del algoritmo). Las fórmulas de MSE y PSNR son las
del artículo base, apartado IV, ecuaciones (1) y (2):

    MSE  = (1 / (M N)) * suma de (original - restaurada)^2 sobre todos los píxeles
    PSNR = 10 * log10( R^2 / MSE )

donde R es el valor máximo posible de un píxel (255 en imágenes de 8 bits).

Todas las funciones aceptan, de forma opcional, la máscara del hueco. Con
máscara, la métrica se calcula solo sobre los píxeles del hueco; sin ella,
sobre toda la imagen.

Se usa NumPy. Para anotar el equipo se intenta usar también OpenCV.
"""

import os
import platform
import time

import numpy as np


def _comprobar(original, restaurada, mascara):
    """Comprueba que las imágenes y la máscara sean compatibles."""
    if original.shape != restaurada.shape:
        raise ValueError("la imagen original y la restaurada deben tener la misma forma")
    if mascara is not None:
        if mascara.shape != original.shape[:2]:
            raise ValueError("la máscara debe tener el mismo alto y ancho que la imagen")
        if not mascara.any():
            raise ValueError("la máscara no tiene ningún píxel de hueco")


def mse(original, restaurada, mascara=None):
    """
    Error cuadrático medio entre la imagen original y la restaurada.

    original:   imagen sana.
    restaurada: resultado del algoritmo, con la misma forma.
    mascara:    opcional. Si se da, solo se miden los píxeles del hueco.

    En una imagen en color se promedian todos los canales.
    Vale 0 si las dos imágenes son iguales y crece cuanto más se diferencian.
    """
    _comprobar(original, restaurada, mascara)

    # Se pasa a decimales antes de restar. Con enteros de 8 bits, 10 - 12 no
    # da -2 sino 254, y el error saldría mal.
    diferencia = original.astype(np.float64) - restaurada.astype(np.float64)

    if mascara is not None:
        diferencia = diferencia[mascara]
    return float(np.mean(diferencia ** 2))


def psnr(original, restaurada, mascara=None, rango=255):
    """
    Relación señal-ruido de pico, en decibelios (dB).

    rango: valor máximo posible de un píxel. Por defecto, 255 (imágenes de 8 bits).

    Cuanto más alto, menos error. Si las imágenes son iguales el MSE es 0 y
    la fórmula divide entre 0: en ese caso se devuelve infinito.
    """
    error = mse(original, restaurada, mascara)
    if error == 0:
        return float("inf")
    return float(10 * np.log10(rango ** 2 / error))


def evaluar(original, restaurada, mascara):
    """
    Las cuatro medidas juntas, en un diccionario:
    MSE y PSNR sobre el hueco, y MSE y PSNR sobre la imagen entera.
    """
    return {
        "mse_hueco": mse(original, restaurada, mascara),
        "psnr_hueco": psnr(original, restaurada, mascara),
        "mse_imagen": mse(original, restaurada),
        "psnr_imagen": psnr(original, restaurada),
    }


def cronometrar(funcion, *argumentos, repeticiones=5):
    """
    Ejecuta una función varias veces y mide cuánto tarda.

    funcion:      la función a medir.
    argumentos:   los argumentos con los que se llama.
    repeticiones: cuántas veces se ejecuta. Se repite porque el tiempo varía
                  de una ejecución a otra.

    Devuelve (resultado, media, tiempos): el resultado de la última
    ejecución, el tiempo medio en segundos y la lista de todos los tiempos.
    """
    if repeticiones <= 0:
        raise ValueError("repeticiones debe ser positivo")

    tiempos = []
    resultado = None
    for _ in range(repeticiones):
        inicio = time.perf_counter()
        resultado = funcion(*argumentos)
        tiempos.append(time.perf_counter() - inicio)
    return resultado, float(np.mean(tiempos)), tiempos


def informacion_equipo():
    """
    Datos del equipo y de las versiones, para anotarlos junto a los tiempos.
    Un tiempo solo se puede comparar con otro si se sabe en qué máquina se midió.
    """
    try:
        # Memoria física total, en GB. No está disponible en todos los sistemas.
        memoria = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1e9
        memoria = round(memoria, 1)
    except (ValueError, OSError, AttributeError):
        memoria = None

    try:
        import cv2
        version_opencv = cv2.__version__
    except ImportError:
        version_opencv = None

    return {
        "sistema": platform.platform(),
        "procesador": platform.processor() or platform.machine(),
        "nucleos": os.cpu_count(),
        "memoria_gb": memoria,
        "python": platform.python_version(),
        "numpy": np.__version__,
        "opencv": version_opencv,
    }
