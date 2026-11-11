"""
Algoritmos de inpainting basados en difusión.

De momento solo está la difusión simple: se rellena el hueco repitiendo la
media de los cuatro vecinos de cada píxel,

    I^{t+1}(p) = 1/4 * suma de I^t(q) para los cuatro vecinos q de p,    p dentro del hueco.

Esta fórmula es una propuesta nuestra como punto de partida: es la iteración
más sencilla de la difusión. No es el método de Bertalmio et al. ni aparece
en el artículo base. Equivale a sumar a cada píxel un cuarto de su laplaciano,
y cuando deja de cambiar, el laplaciano del hueco vale 0.

Los píxeles conocidos no cambian nunca. Si la imagen es en color, cada canal
se trata por separado: como la media de un canal solo usa ese canal, basta
con aplicarla a la matriz entera.

Se usa NumPy.
"""

import numpy as np


def un_paso(imagen, mascara):
    """
    Una iteración de la media de los cuatro vecinos, solo dentro del hueco.

    imagen:  matriz de decimales, en gris (alto, ancho) o en color (alto, ancho, 3).
    mascara: matriz de True y False, con True en el hueco.

    Todos los píxeles del hueco se calculan a la vez, a partir de la imagen
    de la iteración anterior (la fórmula usa I^t(q) a la derecha).
    Devuelve una imagen nueva; la que se pasa no se modifica.
    """
    # Se añade un borde de un píxel que repite el valor del borde de la imagen,
    # para que los píxeles de la orilla tengan también cuatro vecinos.
    relleno = [(1, 1), (1, 1)] + [(0, 0)] * (imagen.ndim - 2)
    ampliada = np.pad(imagen, relleno, mode="edge")

    # Los cuatro vecinos de cada píxel: arriba, abajo, izquierda y derecha.
    arriba = ampliada[:-2, 1:-1]
    abajo = ampliada[2:, 1:-1]
    izquierda = ampliada[1:-1, :-2]
    derecha = ampliada[1:-1, 2:]
    media = (arriba + abajo + izquierda + derecha) / 4

    nueva = imagen.copy()
    nueva[mascara] = media[mascara]
    return nueva


def difusion_simple(imagen, mascara, iteraciones=10000, tolerancia=0.01):
    """
    Rellena el hueco repitiendo la media de los cuatro vecinos.

    imagen:      imagen dañada, en gris o en color. Los valores del hueco no importan.
    mascara:     matriz de True y False, con True en el hueco.
    iteraciones: número máximo de iteraciones.
    tolerancia:  se para antes si, en una iteración, ningún píxel del hueco
                 cambia más que esto.

    Devuelve (restaurada, usadas): la imagen restaurada, con el mismo tipo
    de datos que la entrada, y el número de iteraciones que se han hecho.
    """
    if imagen.shape[:2] != mascara.shape:
        raise ValueError("la imagen y la máscara deben tener el mismo alto y ancho")
    if iteraciones <= 0:
        raise ValueError("iteraciones debe ser positivo")
    if not mascara.any():
        return imagen.copy(), 0
    if mascara.all():
        raise ValueError("la máscara cubre toda la imagen: no hay píxeles conocidos")

    # Solo se trabaja con el rectángulo que contiene el hueco, más un píxel de
    # margen para tener los vecinos de los píxeles de la orilla. Así no se
    # gasta tiempo en el resto de la imagen, que no cambia.
    filas, columnas = np.nonzero(mascara)
    fila_desde = max(filas.min() - 1, 0)
    fila_hasta = min(filas.max() + 2, mascara.shape[0])
    columna_desde = max(columnas.min() - 1, 0)
    columna_hasta = min(columnas.max() + 2, mascara.shape[1])
    zona = (slice(fila_desde, fila_hasta), slice(columna_desde, columna_hasta))

    trabajo = imagen[zona].astype(np.float64)
    hueco = mascara[zona]

    # Valor de partida del hueco: la media de los píxeles conocidos de la zona,
    # en cada canal. El resultado final no depende de este valor, solo el
    # número de iteraciones que hacen falta.
    trabajo[hueco] = trabajo[~hueco].mean(axis=0)

    usadas = 0
    for _ in range(iteraciones):
        siguiente = un_paso(trabajo, hueco)
        cambio = np.abs(siguiente[hueco] - trabajo[hueco]).max()
        trabajo = siguiente
        usadas += 1
        if cambio < tolerancia:
            break

    # Se devuelve la imagen entera, con el mismo tipo que la entrada.
    restaurada = imagen.copy()
    if np.issubdtype(imagen.dtype, np.integer):
        trabajo = np.clip(np.rint(trabajo), np.iinfo(imagen.dtype).min, np.iinfo(imagen.dtype).max)
    restaurada[zona][hueco] = trabajo[hueco].astype(imagen.dtype)
    return restaurada, usadas
