"""
Generador de máscaras para el trabajo de inpainting.

Una máscara es una matriz de True y False con el mismo alto y ancho que la
imagen. True marca los píxeles del hueco, los que hay que rellenar, y False
los píxeles buenos, que no se tocan nunca.

Criterios comunes a todas las funciones:
  - "forma" es el tamaño de la imagen como (alto, ancho).
  - Las posiciones se dan como (fila, columna), con el origen arriba a la izquierda.
  - Si una forma se sale de la imagen, se recorta por el borde.
  - Las funciones con azar reciben una semilla, para poder repetir las mismas
    máscaras en todos los experimentos.

Solo se usa NumPy.
"""

import numpy as np


def _comprobar_forma(forma):
    """Comprueba que la forma sea (alto, ancho) con valores positivos."""
    if len(forma) != 2 or forma[0] <= 0 or forma[1] <= 0:
        raise ValueError("forma debe ser (alto, ancho) con valores positivos")


def _centro_por_defecto(forma, centro):
    """Si no se da centro, se usa el centro de la imagen."""
    if centro is None:
        return (forma[0] // 2, forma[1] // 2)
    return centro


def mascara_cuadrada(forma, lado, centro=None):
    """
    Hueco cuadrado.

    forma:  (alto, ancho) de la imagen.
    lado:   lado del cuadrado en píxeles.
    centro: (fila, columna) del centro del cuadrado. Por defecto, el centro de la imagen.

    Si el cuadrado se sale de la imagen, se recorta.
    """
    _comprobar_forma(forma)
    if lado <= 0:
        raise ValueError("lado debe ser positivo")
    alto, ancho = forma
    fila_centro, columna_centro = _centro_por_defecto(forma, centro)

    # El cuadrado ocupa "lado" filas y "lado" columnas a partir de esta esquina.
    fila_inicio = fila_centro - lado // 2
    columna_inicio = columna_centro - lado // 2

    # Se recorta con los límites de la imagen.
    fila_desde = max(fila_inicio, 0)
    fila_hasta = min(fila_inicio + lado, alto)
    columna_desde = max(columna_inicio, 0)
    columna_hasta = min(columna_inicio + lado, ancho)

    mascara = np.zeros((alto, ancho), dtype=bool)
    mascara[fila_desde:fila_hasta, columna_desde:columna_hasta] = True
    return mascara


def mascara_circular(forma, radio, centro=None):
    """
    Hueco redondo.

    forma:  (alto, ancho) de la imagen.
    radio:  radio del círculo en píxeles.
    centro: (fila, columna) del centro. Por defecto, el centro de la imagen.

    Un píxel está en el hueco si su distancia al centro es como mucho el radio.
    """
    _comprobar_forma(forma)
    if radio <= 0:
        raise ValueError("radio debe ser positivo")
    alto, ancho = forma
    fila_centro, columna_centro = _centro_por_defecto(forma, centro)

    # filas y columnas valen, en cada píxel, su número de fila y de columna.
    filas, columnas = np.ogrid[0:alto, 0:ancho]
    distancia_al_cuadrado = (filas - fila_centro) ** 2 + (columnas - columna_centro) ** 2
    return distancia_al_cuadrado <= radio ** 2


def mascara_aranazo(forma, inicio, fin, grosor):
    """
    Arañazo: un segmento recto con un grosor.

    forma:  (alto, ancho) de la imagen.
    inicio: (fila, columna) del primer extremo.
    fin:    (fila, columna) del segundo extremo.
    grosor: ancho del arañazo en píxeles.

    Un píxel está en el hueco si su distancia al segmento es como mucho
    la mitad del grosor.
    """
    _comprobar_forma(forma)
    if grosor <= 0:
        raise ValueError("grosor debe ser positivo")
    alto, ancho = forma
    fila_a, columna_a = inicio
    fila_b, columna_b = fin

    filas, columnas = np.mgrid[0:alto, 0:ancho]

    # Vector del segmento y su longitud al cuadrado.
    vector_fila = fila_b - fila_a
    vector_columna = columna_b - columna_a
    longitud_al_cuadrado = vector_fila ** 2 + vector_columna ** 2

    if longitud_al_cuadrado == 0:
        # Si los dos extremos coinciden, el "segmento" es un punto.
        distancia_al_cuadrado = (filas - fila_a) ** 2 + (columnas - columna_a) ** 2
    else:
        # t dice dónde cae la proyección de cada píxel sobre la recta:
        # 0 es el inicio, 1 es el fin. Se limita a [0, 1] para quedarse en el segmento.
        t = ((filas - fila_a) * vector_fila + (columnas - columna_a) * vector_columna) / longitud_al_cuadrado
        t = np.clip(t, 0, 1)
        # Punto del segmento más cercano a cada píxel.
        fila_cercana = fila_a + t * vector_fila
        columna_cercana = columna_a + t * vector_columna
        distancia_al_cuadrado = (filas - fila_cercana) ** 2 + (columnas - columna_cercana) ** 2

    return distancia_al_cuadrado <= (grosor / 2) ** 2


def mascara_motas(forma, cantidad, radio, semilla):
    """
    Varias motas redondas pequeñas en posiciones al azar.

    forma:    (alto, ancho) de la imagen.
    cantidad: número de motas.
    radio:    radio de cada mota en píxeles.
    semilla:  número que fija el azar, para repetir las mismas motas.
    """
    _comprobar_forma(forma)
    if cantidad <= 0 or radio <= 0:
        raise ValueError("cantidad y radio deben ser positivos")
    alto, ancho = forma
    if alto <= 2 * radio or ancho <= 2 * radio:
        raise ValueError("la imagen es demasiado pequeña para ese radio")

    generador = np.random.default_rng(semilla)
    mascara = np.zeros((alto, ancho), dtype=bool)

    # Cada mota entera cabe dentro de la imagen (el centro queda a "radio" del borde).
    for _ in range(cantidad):
        fila_centro = generador.integers(radio, alto - radio)
        columna_centro = generador.integers(radio, ancho - radio)
        mascara = mascara | mascara_circular(forma, radio, (fila_centro, columna_centro))
    return mascara


def mascara_irregular(forma, tamano, centro=None, semilla=0):
    """
    Hueco de forma irregular: la unión de varios círculos solapados.

    forma:   (alto, ancho) de la imagen.
    tamano:  tamaño aproximado del hueco en píxeles (su anchura más o menos).
    centro:  (fila, columna) alrededor de la que se forma. Por defecto, el centro de la imagen.
    semilla: número que fija el azar, para repetir el mismo hueco.
    """
    _comprobar_forma(forma)
    if tamano <= 0:
        raise ValueError("tamano debe ser positivo")
    fila_centro, columna_centro = _centro_por_defecto(forma, centro)

    generador = np.random.default_rng(semilla)
    mascara = np.zeros(forma, dtype=bool)

    # Seis círculos cuyo centro se desplaza un poco y cuyo radio varía.
    # Al solaparse dan un contorno redondeado pero no regular.
    for _ in range(6):
        desplazamiento_fila = generador.integers(-(tamano // 4), tamano // 4 + 1)
        desplazamiento_columna = generador.integers(-(tamano // 4), tamano // 4 + 1)
        radio = generador.integers(max(tamano // 4, 1), max(tamano // 2, 2))
        centro_circulo = (fila_centro + desplazamiento_fila, columna_centro + desplazamiento_columna)
        mascara = mascara | mascara_circular(forma, radio, centro_circulo)
    return mascara


def aplicar_mascara(imagen, mascara, valor=255):
    """
    Estropea una imagen: pone un valor fijo en los píxeles del hueco.

    imagen:  imagen en gris (alto, ancho) o en color (alto, ancho, 3).
    mascara: máscara con el mismo alto y ancho que la imagen.
    valor:   valor con el que se tapa el hueco. Por defecto, 255 (blanco).

    Devuelve una copia: la imagen original no se modifica.
    """
    if imagen.shape[:2] != mascara.shape:
        raise ValueError("la imagen y la máscara deben tener el mismo alto y ancho")
    imagen_danada = imagen.copy()
    imagen_danada[mascara] = valor
    return imagen_danada


def porcentaje_hueco(mascara):
    """Porcentaje de píxeles de la imagen que son hueco."""
    return 100 * mascara.sum() / mascara.size
