"""
Inpainting por propagación a lo largo de las isófotas, siguiendo a
Bertalmio, Sapiro, Caselles y Ballester, «Image inpainting», SIGGRAPH 2000
(en los comentarios se cita como [1], con la página impresa, pp. 417-424).

Idea [1, sec. 3.1, p. 418]: se prolongan hacia dentro del hueco las isófotas
(líneas de igual valor de gris) que llegan a su borde. Se repite, dentro del hueco,

    I^{n+1} = I^n + dt * I_t^n                         ec. (1) y (4), pp. 418-419

donde la actualización propaga una medida de suavidad L en la dirección N de
las isófotas [1, sec. 3.2, p. 419]. Cada cierto número de pasos se intercala
difusión anisotrópica, ec. (3), p. 419 [1, sec. 3.3, pp. 419-420].

Simplificaciones nuestras respecto al artículo (se indican en cada función):
  - El modelo de color (Fig. 3, p. 420) es nuestra lectura de la figura.
  - La difusión anisotrópica se aplica solo dentro del hueco (g = 1 dentro y 0 fuera).
  - No se usa multirresolución [1, nota 10, p. 420].
  - Se trabaja con valores entre 0 y 1 (ver la función bertalmio).
  - Por defecto, el hueco parte del resultado de la difusión simple (ver el parámetro inicio).

Convención de ejes: se llama «x» al primer índice de la matriz (las filas) e «y»
al segundo (las columnas). Basta con que sea la misma en todas las fórmulas,
porque lo que importa es que N sea el gradiente girado 90 grados.

Se usa NumPy.
"""

import numpy as np

import difusion


def _x(A, k):
    """A en la posición desplazada k píxeles en x: devuelve A[i + k, j]."""
    return np.roll(A, -k, axis=0)


def _y(A, k):
    """A en la posición desplazada k píxeles en y: devuelve A[i, j + k]."""
    return np.roll(A, -k, axis=1)


def laplaciano(A):
    """
    Medida de suavidad L = I_xx + I_yy  [1, sec. 3.2, p. 419; ec. (7), p. 420].
    Es la suma de los cuatro vecinos menos cuatro veces el píxel.
    """
    return _x(A, 1) + _x(A, -1) + _y(A, 1) + _y(A, -1) - 4 * A


def direccion_isofotas(A):
    """
    Dirección de las isófotas en cada píxel, normalizada: N / |N| = (-I_y, I_x) / |grad I|
    [1, sec. 3.2, p. 419; ec. (8), p. 420]. Es el gradiente girado 90 grados.

    Devuelve (N_x, N_y). Donde el gradiente es 0 no hay dirección y se devuelve 0.
    """
    Ix = (_x(A, 1) - _x(A, -1)) / 2
    Iy = (_y(A, 1) - _y(A, -1)) / 2
    norma = np.sqrt(Ix ** 2 + Iy ** 2)
    sin_gradiente = norma == 0
    norma_segura = np.where(sin_gradiente, 1, norma)
    N_x = np.where(sin_gradiente, 0, -Iy / norma_segura)
    N_y = np.where(sin_gradiente, 0, Ix / norma_segura)
    return N_x, N_y


def paso_inpainting(A, hueco, dt):
    """
    Un paso de propagación a lo largo de las isófotas, solo dentro del hueco.
    Sigue las ecuaciones (4) a (10) de [1, pp. 419-420].

    A:     matriz de decimales con valores entre 0 y 1, en gris (alto, ancho)
           o en color (alto, ancho, 3). Cada canal se trata por separado.
    hueco: matriz de True y False con True en el hueco.
    dt:    paso temporal, Delta t.
    """
    # ec. (7): medida de suavidad L, y ec. (6): su cambio entre vecinos.
    L = laplaciano(A)
    cambio_L_x = _x(L, 1) - _x(L, -1)
    cambio_L_y = _y(L, 1) - _y(L, -1)

    # ec. (8): dirección de las isófotas.
    N_x, N_y = direccion_isofotas(A)

    # ec. (9): beta es el cambio de L a lo largo de la isófota.
    beta = cambio_L_x * N_x + cambio_L_y * N_y

    # ec. (10): módulo del gradiente con limitadores de pendiente. Se usan
    # diferencias hacia atrás (b) y hacia delante (f), quedándose con el
    # mínimo (m) o el máximo (M) entre la diferencia y 0. Con diferencias
    # centrales el esquema sería inestable [1, p. 420].
    Ix_atras = A - _x(A, -1)
    Ix_delante = _x(A, 1) - A
    Iy_atras = A - _y(A, -1)
    Iy_delante = _y(A, 1) - A

    gradiente_si_beta_positivo = np.sqrt(
        np.minimum(Ix_atras, 0) ** 2 + np.maximum(Ix_delante, 0) ** 2
        + np.minimum(Iy_atras, 0) ** 2 + np.maximum(Iy_delante, 0) ** 2)
    gradiente_si_beta_negativo = np.sqrt(
        np.maximum(Ix_atras, 0) ** 2 + np.minimum(Ix_delante, 0) ** 2
        + np.maximum(Iy_atras, 0) ** 2 + np.minimum(Iy_delante, 0) ** 2)
    gradiente = np.where(beta > 0, gradiente_si_beta_positivo, gradiente_si_beta_negativo)

    # ec. (5): actualización, y ec. (4): se suma solo dentro del hueco.
    It = beta * gradiente
    nueva = A.copy()
    nueva[hueco] = A[hueco] + dt * It[hueco]
    return nueva


def paso_difusion(A, region, dt):
    """
    Un paso de difusión anisotrópica por curvatura: dI/dt = kappa * |grad I|,
    ec. (3) de [1, p. 419], con diferencias centrales [1, sec. 3.3, p. 419].

    kappa es la curvatura de las isófotas. Desarrollada, la ecuación queda:

        dI/dt = (I_xx I_y^2 - 2 I_x I_y I_xy + I_yy I_x^2) / (I_x^2 + I_y^2)

    A:      matriz de decimales, como en paso_inpainting.
    region: dónde se aplica. Simplificación nuestra: g = 1 en esa región y 0 fuera.
    dt:     paso temporal.
    """
    Ix = (_x(A, 1) - _x(A, -1)) / 2
    Iy = (_y(A, 1) - _y(A, -1)) / 2
    Ixx = _x(A, 1) - 2 * A + _x(A, -1)
    Iyy = _y(A, 1) - 2 * A + _y(A, -1)
    Ixy = (_x(_y(A, 1), 1) - _x(_y(A, 1), -1) - _x(_y(A, -1), 1) + _x(_y(A, -1), -1)) / 4

    numerador = Ixx * Iy ** 2 - 2 * Ix * Iy * Ixy + Iyy * Ix ** 2
    denominador = Ix ** 2 + Iy ** 2
    sin_gradiente = denominador < 1e-12
    cambio = np.where(sin_gradiente, 0, numerador / np.where(sin_gradiente, 1, denominador))

    nueva = A.copy()
    nueva[region] = A[region] + dt * cambio[region]
    return nueva


def rgb_a_modelo(rgb):
    """
    Pasa una imagen en color (valores entre 0 y 1) al modelo de color que usa
    el artículo para evitar colores falsos: un brillo y dos coordenadas de color
    [1, sec. 3.3, p. 420; Fig. 3]. Se escribe (rho, sin phi, sin psi), con
    rho el módulo del vector (R, G, B), psi el ángulo de ese vector con el plano
    R-B y phi el ángulo del vector, proyectado en ese plano, con el eje B.

    Es nuestra lectura de la Fig. 3. El artículo dice que su modelo «es muy
    parecido al LUV, con una luminancia y dos crominancias».

    Devuelve una matriz con tres planos: rho, sin phi y sin psi.
    """
    R, G, B = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    rho = np.sqrt(R ** 2 + G ** 2 + B ** 2)
    plano = np.sqrt(R ** 2 + B ** 2)
    rho_seguro = np.where(rho == 0, 1, rho)
    plano_seguro = np.where(plano == 0, 1, plano)
    sin_psi = np.where(rho == 0, 0, G / rho_seguro)
    sin_phi = np.where(plano == 0, 0, R / plano_seguro)
    return np.stack([rho, sin_phi, sin_psi], axis=-1)


def modelo_a_rgb(modelo):
    """Operación inversa de rgb_a_modelo: de (rho, sin phi, sin psi) a (R, G, B)."""
    rho = np.maximum(modelo[..., 0], 0)
    sin_phi = np.clip(modelo[..., 1], 0, 1)
    sin_psi = np.clip(modelo[..., 2], 0, 1)
    G = rho * sin_psi
    plano = rho * np.sqrt(1 - sin_psi ** 2)
    R = plano * sin_phi
    B = plano * np.sqrt(1 - sin_phi ** 2)
    return np.stack([R, G, B], axis=-1)


def bertalmio(imagen, mascara, ciclos=600, pasos_inpainting=15, pasos_difusion=2,
              dt=0.1, tolerancia=0.01, pasos_previos=5, modelo_color=True, inicio="difusion", semilla=0):
    """
    Rellena el hueco propagando las isófotas, con difusión anisotrópica intercalada.

    imagen:           imagen dañada, en gris o en color. Los valores del hueco no importan.
    mascara:          matriz de True y False, con True en el hueco.
    ciclos:           número máximo de ciclos. Un ciclo son «pasos_inpainting» pasos de
                      inpainting seguidos de «pasos_difusion» de difusión [1, sec. 3.3, p. 420].
    pasos_inpainting: A en el artículo, 15 [1, p. 420].
    pasos_difusion:   B en el artículo, 2 [1, p. 420].
    dt:               paso temporal, 0,1 en el artículo [1, p. 420].
    tolerancia:       se para antes si, en un ciclo, ningún píxel del hueco cambia más que esto
                      (en niveles de gris, de 0 a 255).
    pasos_previos:    pasos de difusión anisotrópica sobre toda la zona de trabajo antes de
                      empezar, para reducir el efecto del ruido en las isófotas [1, sec. 3.3,
                      p. 419]. El artículo no dice cuántos; este valor es una elección nuestra.

    modelo_color:     si es True y la imagen es en color, se trabaja en el modelo de
                      color del artículo (rho, sin phi, sin psi) en vez de en R, G y B,
                      para evitar colores falsos [1, sec. 3.3, p. 420; Fig. 3].

    inicio:           valor de partida del hueco. El artículo no lo fija y dice que el
                      resultado es robusto a él [1, sec. 4, p. 420], pero en nuestras pruebas
                      no lo es (cuaderno 04):
                      - «difusion» (por defecto): el resultado de la difusión simple. Sus
                        isófotas ya cruzan el hueco y el transporte puede seguirlas. Es una
                        elección nuestra.
                      - «media»: un valor plano, la media de los píxeles conocidos. Sus isófotas
                        son paralelas al borde del hueco y la información apenas entra
                        (el «problema de arranque» de [1, sec. 3.2, p. 419]).
                      - «ruido»: valores al azar, como en la implementación de referencia de
                        Parisotto y Schönlieb (repositorio MATLAB-Python-inpainting-codes).
    semilla:          semilla del azar para «ruido».

    Los píxeles conocidos de la imagen devuelta son los originales; el suavizado
    previo solo se usa para calcular.

    Se trabaja con valores entre 0 y 1: con imágenes de 8 bits, la imagen se divide
    entre 255. El artículo no dice la escala de los valores. Con dt = 0,1 hace falta
    esta, porque con valores de 0 a 255 el paso es demasiado grande y el esquema se
    dispara (se comprueba en el cuaderno 04).

    Devuelve (restaurada, ciclos_usados).
    """
    if imagen.shape[:2] != mascara.shape:
        raise ValueError("la imagen y la máscara deben tener el mismo alto y ancho")
    if ciclos <= 0:
        raise ValueError("ciclos debe ser positivo")
    if not mascara.any():
        return imagen.copy(), 0
    if mascara.all():
        raise ValueError("la máscara cubre toda la imagen: no hay píxeles conocidos")

    es_entera = np.issubdtype(imagen.dtype, np.integer)
    rango = np.iinfo(imagen.dtype).max if es_entera else 1.0

    # Rectángulo de trabajo: el hueco más un margen. Los cálculos de cada píxel
    # usan vecinos hasta a dos píxeles de distancia, así que el margen es de 3.
    margen = 3
    filas, columnas = np.nonzero(mascara)
    fila_desde = max(filas.min() - margen, 0)
    fila_hasta = min(filas.max() + margen + 1, mascara.shape[0])
    columna_desde = max(columnas.min() - margen, 0)
    columna_hasta = min(columnas.max() + margen + 1, mascara.shape[1])
    zona = (slice(fila_desde, fila_hasta), slice(columna_desde, columna_hasta))

    if inicio not in ("media", "difusion", "ruido"):
        raise ValueError("inicio debe ser 'media', 'difusion' o 'ruido'")

    base = imagen
    if inicio == "difusion":
        base, _ = difusion.difusion_simple(imagen, mascara)

    trabajo = base[zona].astype(np.float64) / rango
    hueco = mascara[zona]

    # Si hay color, se pasa al modelo del artículo. Cada plano se trata por separado.
    usar_modelo = modelo_color and imagen.ndim == 3 and imagen.shape[2] == 3
    if usar_modelo:
        trabajo = rgb_a_modelo(trabajo)

    # Se repite el valor del borde de la imagen para que los cálculos de la orilla
    # tengan vecinos. El hueco no se extiende a ese borde añadido.
    relleno = [(margen, margen), (margen, margen)] + [(0, 0)] * (imagen.ndim - 2)
    trabajo = np.pad(trabajo, relleno, mode="edge")
    hueco = np.pad(hueco, margen, mode="constant", constant_values=False)
    todo = np.ones_like(hueco)

    # Valor de partida del hueco. Con «media», la media de los píxeles conocidos de
    # la zona. Con «difusion», se deja el resultado de la difusión simple.
    if inicio == "media":
        trabajo[hueco] = trabajo[~hueco].mean(axis=0)
    elif inicio == "ruido":
        generador = np.random.default_rng(semilla)
        trabajo[hueco] = generador.random(trabajo[hueco].shape)

    # Preproceso: difusión anisotrópica de toda la zona [1, sec. 3.3, p. 419].
    for _ in range(pasos_previos):
        trabajo = paso_difusion(trabajo, todo, dt)

    usados = 0
    for _ in range(ciclos):
        antes = trabajo.copy()
        for _ in range(pasos_inpainting):
            trabajo = paso_inpainting(trabajo, hueco, dt)
        for _ in range(pasos_difusion):
            trabajo = paso_difusion(trabajo, hueco, dt)
        usados += 1
        cambio = np.abs(trabajo[hueco] - antes[hueco]).max() * rango
        if cambio < tolerancia:
            break

    # Se recorta el borde añadido y se devuelve la imagen entera, con el mismo tipo
    # que la entrada, tocando solo los píxeles del hueco.
    trabajo = trabajo[margen:-margen, margen:-margen]
    if usar_modelo:
        trabajo = modelo_a_rgb(trabajo)
    trabajo = trabajo * rango
    hueco = hueco[margen:-margen, margen:-margen]
    if es_entera:
        trabajo = np.clip(np.rint(trabajo), np.iinfo(imagen.dtype).min, np.iinfo(imagen.dtype).max)
    restaurada = imagen.copy()
    restaurada[zona][hueco] = trabajo[hueco].astype(imagen.dtype)
    return restaurada, usados
