"""
Inpainting basado en ejemplares: Criminisi, Pérez y Toyama (2004).

Referencia principal:
    A. Criminisi, P. Pérez y K. Toyama, «Region Filling and Object Removal
    by Exemplar-Based Image Inpainting», IEEE TIP 13(9), 2004, sec. III,
    ecuaciones (1)-(2) y tabla I (pp. 1203-1204; pp. 4-5 en el PDF de MSR).

Idea: en cada iteración se identifica la frontera del hueco, se asigna a
cada parche de esa frontera la prioridad P(p) = C(p) * D(p), se busca en la
región conocida ORIGINAL el parche fuente con SSD mínima sobre los píxeles
conocidos del objetivo, y se copian solo los píxeles desconocidos.

Convenciones comunes con el repositorio de Juanlu:
  - Imagen: array NumPy gris (H,W) o RGB (H,W,3), normalmente uint8.
  - Máscara booleana (H,W): True significa hueco.
  - Coordenadas (fila, columna), con (0,0) arriba a la izquierda.
  - La función pública devuelve (restaurada, iteraciones); si se solicita
    historial, devuelve (restaurada, iteraciones, historial).
  - La imagen de entrada y los píxeles originales conocidos no se modifican.

Decisiones discretas de esta implementación (NO fijadas exactamente por
las ecuaciones continuas del artículo):
  - Frontera: píxeles desconocidos con algún vecino conocido de N4.
  - Normal al contorno: gradiente de la máscara suavizada con filtro 3x3.
  - Gradientes: diferencias centradas si hay dos vecinos conocidos;
    unilaterales si solo hay uno. Se usa el de mayor módulo en el parche.
  - Las ventanas objetivo se RECORTAN en los bordes físicos de la foto;
    las fuentes son siempre ventanas completas del tamaño indicado.
  - Cuando todas las prioridades son 0 (p. ej., imagen plana), se usa C
    para desempatar; no se suma un epsilon a la fórmula original.
  - La SSD en color se calcula en CIE Lab con cv2 (como el artículo).
    En gris se usa directamente la intensidad.
  - Búsqueda exhaustiva, por lotes para limitar memoria. No se usa
    cv2.inpaint ni un algoritmo de inpainting preimplementado.

Dependencias: NumPy y OpenCV (conversión de RGB a Lab).
"""

import numpy as np
import cv2 as cv
from numpy.lib.stride_tricks import sliding_window_view


def _comprobar_entradas(imagen, mascara, tam_parche):
    """Valida dimensiones, tipo de máscara y tamaño del parche."""
    if not isinstance(imagen, np.ndarray) or imagen.ndim not in (2, 3):
        raise ValueError("imagen debe ser un ndarray de 2 o 3 dimensiones")
    if imagen.ndim == 3 and imagen.shape[2] != 3:
        raise ValueError("solo se admiten imágenes en gris o RGB de 3 canales")
    if not isinstance(mascara, np.ndarray) or mascara.dtype != np.bool_:
        raise ValueError("mascara debe ser un ndarray booleano (True = hueco)")
    if imagen.shape[:2] != mascara.shape:
        raise ValueError("la máscara y la imagen deben tener el mismo alto y ancho")
    if not isinstance(tam_parche, (int, np.integer)) or tam_parche < 3 or tam_parche % 2 == 0:
        raise ValueError("tam_parche debe ser un entero impar >= 3")
    if tam_parche > min(mascara.shape):
        raise ValueError("tam_parche no cabe en la imagen")
    if not np.issubdtype(imagen.dtype, np.number) or not np.isfinite(imagen).all():
        raise ValueError("la imagen debe contener números finitos")
    if np.any(imagen < 0):
        raise ValueError("la imagen no debe contener intensidades negativas")
    if imagen.dtype.kind == "f" and np.any(imagen > 255):
        raise ValueError("las imágenes flotantes deben estar en [0,1] o [0,255]")


def _ventana(centro, forma, tam_parche):
    """Devuelve corte recortado y sus offsets dentro de un parche completo.

    Los offsets permiten alinear un parche OBJETIVO pegado al borde con
    una ventana FUENTE completa de tam_parche x tam_parche.
    """
    fila, columna = (int(centro[0]), int(centro[1]))
    alto, ancho = forma
    radio = tam_parche // 2
    fila_desde = max(0, fila - radio)
    fila_hasta = min(alto, fila + radio + 1)
    columna_desde = max(0, columna - radio)
    columna_hasta = min(ancho, columna + radio + 1)
    desfila = fila_desde - (fila - radio)
    descol = columna_desde - (columna - radio)
    return (
        (slice(fila_desde, fila_hasta), slice(columna_desde, columna_hasta)),
        (slice(desfila, desfila + fila_hasta - fila_desde),
         slice(descol, descol + columna_hasta - columna_desde)),
    )


def obtener_borde(mascara):
    """Frontera interna: píxeles del hueco con al menos un vecino N4 conocido.

    Es una convención discreta para representar delta(Omega) de Criminisi.
    """
    if mascara.ndim != 2 or mascara.dtype != np.bool_:
        raise ValueError("la máscara debe ser booleana y bidimensional")
    conocidos = ~mascara
    # Fuera de la imagen NO se cuenta como píxel conocido.
    k = np.pad(conocidos, ((1, 1), (1, 1)), constant_values=False)
    adyacente_a_conocido = (
        k[:-2, 1:-1] | k[2:, 1:-1] |
        k[1:-1, :-2] | k[1:-1, 2:]
    )
    return mascara & adyacente_a_conocido


def confianza_inicial(mascara):
    """C(q)=1 en conocidos, C(q)=0 en desconocidos [1, sec. III]."""
    return (~mascara).astype(np.float64)


def calcular_confianza(centro, confianza, mascara, tam_parche=9):
    """C(p) = sum(C(q), q conocido del parche) / área del parche.

    En bordes físicos la ventana se recorta y el denominador es el área
    efectiva; en el interior coincide con el área tam_parche**2.
    """
    corte, _ = _ventana(centro, mascara.shape, tam_parche)
    conocidos = ~mascara[corte]
    return float(confianza[corte][conocidos].sum() / conocidos.size)


def _suavizar_mascara(mascara):
    """Filtro binomial 3x3 de la máscara, para estimar normales estables."""
    a = np.pad(mascara.astype(np.float64), 1, mode="edge")
    return (
        a[:-2, :-2] + 2*a[:-2, 1:-1] + a[:-2, 2:] +
        2*a[1:-1, :-2] + 4*a[1:-1, 1:-1] + 2*a[1:-1, 2:] +
        a[2:, :-2] + 2*a[2:, 1:-1] + a[2:, 2:]
    ) / 16.0


def normales_borde(mascara):
    """Normal unitaria aproximada al borde del hueco (componentes fila,col)."""
    suavizada = _suavizar_mascara(mascara)
    d_fila, d_columna = np.gradient(suavizada)
    norma = np.hypot(d_fila, d_columna)
    norma_segura = np.where(norma == 0, 1, norma)
    return d_fila / norma_segura, d_columna / norma_segura


def _intensidad(imagen):
    """Intensidad en escala 0..255 para el cálculo de gradientes e isófotas."""
    f = imagen.astype(np.float64)
    if imagen.dtype.kind == "f" and f.max() <= 1:
        f *= 255.0
    if imagen.ndim == 2:
        return f
    # Los arrays de Juanlu están en RGB (no en BGR).
    return .299 * f[..., 0] + .587 * f[..., 1] + .114 * f[..., 2]


def _gradientes_validos(intensidad, mascara_actual):
    """Gradientes (fila,columna) evitando utilizar píxeles aún vacíos.

    Se usan diferencias centrales si ambos vecinos son conocidos y,
    cuando solo hay uno, una diferencia unilateral.
    """
    a = np.pad(intensidad, 1, mode="edge")
    k = np.pad(~mascara_actual, 1, mode="edge")
    centro = a[1:-1, 1:-1]
    arriba, abajo = a[:-2, 1:-1], a[2:, 1:-1]
    izquierda, derecha = a[1:-1, :-2], a[1:-1, 2:]
    ka, kb = k[:-2, 1:-1], k[2:, 1:-1]
    ki, kd = k[1:-1, :-2], k[1:-1, 2:]
    d_fila = np.where(ka & kb, (abajo-arriba)/2,
               np.where(kb, abajo-centro, np.where(ka, centro-arriba, 0.0)))
    d_col = np.where(ki & kd, (derecha-izquierda)/2,
               np.where(kd, derecha-centro, np.where(ki, centro-izquierda, 0.0)))
    d_fila[mascara_actual] = 0
    d_col[mascara_actual] = 0
    return d_fila, d_col


def calcular_datos(centro, mascara, grad_fila, grad_col, normal_fila, normal_col,
                    tam_parche=9, alfa=255.0):
    """D(p) = abs(isófota(p) · normal(p)) / alfa [1, sec. III].

    Se toma el gradiente de mayor módulo entre píxeles CONOCIDOS del
    parche, como indica la implementación descrita en [1, sec. III].
    Las componentes son (fila,columna), consistentes con los arrays.
    """
    if alfa <= 0:
        raise ValueError("alfa debe ser positivo")
    corte, _ = _ventana(centro, mascara.shape, tam_parche)
    conocidos = ~mascara[corte]
    if not conocidos.any():
        return 0.0
    gx = grad_fila[corte]
    gy = grad_col[corte]
    modulo_2 = np.where(conocidos, gx*gx + gy*gy, -np.inf)
    pos = np.unravel_index(np.argmax(modulo_2), modulo_2.shape)
    # Isófota = gradiente rotado 90 grados.
    iso_fila, iso_col = -gy[pos], gx[pos]
    f, c = int(centro[0]), int(centro[1])
    return float(abs(iso_fila * normal_fila[f,c] +
                     iso_col * normal_col[f,c]) / alfa)


def calcular_prioridades(imagen, mascara_actual, confianza, tam_parche=9):
    """Mapas de C, D y P=C*D en los píxeles de la frontera actual.

    Devuelve (borde, C_mapa, D_mapa, P_mapa) para explicar cada
    componente en el notebook. Fuera de la frontera los mapas valen 0.
    """
    if imagen.shape[:2] != mascara_actual.shape or confianza.shape != mascara_actual.shape:
        raise ValueError("dimensiones incompatibles en calcular_prioridades")
    borde = obtener_borde(mascara_actual)
    C_mapa = np.zeros(mascara_actual.shape, dtype=np.float64)
    D_mapa = np.zeros(mascara_actual.shape, dtype=np.float64)
    P_mapa = np.zeros(mascara_actual.shape, dtype=np.float64)
    if not borde.any():
        return borde, C_mapa, D_mapa, P_mapa
    grad_f, grad_c = _gradientes_validos(_intensidad(imagen), mascara_actual)
    normal_f, normal_c = normales_borde(mascara_actual)
    for f, c in np.argwhere(borde):
        centro = (int(f), int(c))
        C_mapa[f,c] = calcular_confianza(centro, confianza, mascara_actual, tam_parche)
        D_mapa[f,c] = calcular_datos(centro, mascara_actual, grad_f, grad_c,
                                   normal_f, normal_c, tam_parche)
        P_mapa[f,c] = C_mapa[f,c] * D_mapa[f,c]
    return borde, C_mapa, D_mapa, P_mapa


def _preparar_fuentes(imagen_comparacion, mascara_original, tam_parche):
    """Parches FUENTE totalmente dentro de Phi = I menos Omega original.

    El artículo define la región fuente Phi como FIJA; nunca se permite
    emplear un parche que invada el hueco original, aunque ya se rellene.
    """
    ventanas_hueco = sliding_window_view(mascara_original, (tam_parche, tam_parche))
    posiciones_validas = ~ventanas_hueco.any(axis=(-2, -1))
    filas, columnas = np.nonzero(posiciones_validas)
    if len(filas) == 0:
        raise ValueError("no existe ningún parche fuente totalmente conocido; "
                         "reduce tam_parche o usa otra máscara")
    if imagen_comparacion.ndim == 2:
        vista = sliding_window_view(imagen_comparacion, (tam_parche,tam_parche))
        vista = vista[..., np.newaxis]  # (H', W', k, k, 1)
    else:
        vista = sliding_window_view(imagen_comparacion, (tam_parche,tam_parche), axis=(0,1))
        vista = np.moveaxis(vista, 2, -1)  # (H', W', k, k, canales)
    return vista, filas, columnas


def _imagen_comparacion(imagen):
    """Imagen de comparación para SSD: Lab en RGB, intensidad en gris."""
    if imagen.ndim == 2:
        return _intensidad(imagen)
    f = imagen.astype(np.float32)
    if imagen.dtype.kind != 'f' or f.max() > 1.0:
        f /= 255.0
    # Para RGB flotante en [0,1], OpenCV devuelve L* en [0,100], a*, b*.
    return cv.cvtColor(np.ascontiguousarray(f), cv.COLOR_RGB2LAB).astype(np.float64)


def buscar_parche_fuente(comparacion, mascara_original, mascara_actual,
                         centro_objetivo, tam_parche=9, tam_lote=256,
                         fuentes_preparadas=None):
    """Busca el parche fuente de SSD mínima sobre SOLO los píxeles conocidos.

    Devuelve (centro_fuente, ssd). El candidato se elige en la región
    fuente original, nunca entre los píxeles reconstruidos.

    Para la eficiencia se procesan los candidatos por lotes; el resultado
    es el mismo que una búsqueda exhaustiva sin dividir en lotes.
    """
    if tam_lote <= 0:
        raise ValueError("tam_lote debe ser positivo")
    if fuentes_preparadas is None:
        fuentes_preparadas = _preparar_fuentes(comparacion, mascara_original, tam_parche)
    vista, filas, columnas = fuentes_preparadas
    corte, offsets = _ventana(centro_objetivo, mascara_actual.shape, tam_parche)
    conocidas = ~mascara_actual[corte]
    if not conocidas.any():
        raise ValueError("el parche objetivo no tiene píxeles conocidos")
    objetivo = comparacion[corte]
    if objetivo.ndim == 2:
        objetivo = objetivo[..., None]
    a, b = offsets
    mejor_ssd = np.inf
    mejor_indice = -1
    for inicio in range(0, len(filas), tam_lote):
        final = min(inicio + tam_lote, len(filas))
        candidatos = vista[filas[inicio:final], columnas[inicio:final], a, b, :]
        # Indexación booleana sobre las dos dimensiones espaciales.
        diferencias = candidatos[:, conocidas, :] - objetivo[conocidas, :][None,:,:]
        distancias = np.sum(diferencias**2, axis=(1,2))
        indice_lote = int(np.argmin(distancias))
        if distancias[indice_lote] < mejor_ssd:
            mejor_ssd = float(distancias[indice_lote])
            mejor_indice = inicio + indice_lote
    radio = tam_parche // 2
    return (int(filas[mejor_indice] + radio),
            int(columnas[mejor_indice] + radio)), mejor_ssd


def rellenar_parche(imagen, comparacion, mascara_actual, confianza,
                    centro_objetivo, centro_fuente, confianza_parche, tam_parche=9):
    """Copia SOLO los píxeles desconocidos y actualiza máscara y confianza.

    Los valores de confianza asignados no vuelven a modificarse; esto
    reproduce el paso 3 y la regla de actualización de [1, sec. III].
    """
    corte, (a,b) = _ventana(centro_objetivo, mascara_actual.shape, tam_parche)
    radio = tam_parche // 2
    fs, cs = int(centro_fuente[0])-radio, int(centro_fuente[1])-radio
    fuente = imagen[fs:fs+tam_parche, cs:cs+tam_parche]
    fuente_comp = comparacion[fs:fs+tam_parche, cs:cs+tam_parche]
    nuevos = mascara_actual[corte].copy()
    cuantos = int(nuevos.sum())
    if cuantos == 0:
        raise ValueError("el parche elegido no tiene píxeles por rellenar")
    if fuente.ndim == 2:
        imagen[corte][nuevos] = fuente[a,b][nuevos]
        comparacion[corte][nuevos] = fuente_comp[a,b][nuevos]
    else:
        imagen[corte][nuevos] = fuente[a,b][nuevos]
        comparacion[corte][nuevos] = fuente_comp[a,b][nuevos]
    confianza[corte][nuevos] = confianza_parche
    mascara_actual[corte][nuevos] = False
    return cuantos


def inpainting_ejemplares(imagen, mascara, tam_parche=9, max_iteraciones=None,
                          devolver_historial=False, guardar_primeras=8,
                          tam_lote=256):
    """Restaura un hueco con el algoritmo clásico de Criminisi [1, sec. III].

    Parameters
    ----------
    imagen : ndarray
        Imagen dañada en gris o RGB. El valor que tengan sus huecos no importa.
    mascara : ndarray booleano
        True en la región a restaurar. No se modifica.
    tam_parche : int impar
        Tamaño de los parches objetivo y fuente (9 en el artículo).
    max_iteraciones : int o None
        Si se proporciona, limita las iteraciones. Puede devolver un relleno
        PARCIAL; con None se ejecuta hasta que el hueco desaparece.
    devolver_historial : bool
        Si True, añade una lista de estados didácticos a la tupla devuelta.
    guardar_primeras : int
        Máximo de primeras iteraciones para las que se guardan imágenes y mapas.
    tam_lote : int
        Número de parches fuente examinados simultáneamente para la SSD.

    Returns
    -------
    (restaurada, iteraciones), o (restaurada, iteraciones, historial).
    El número de iteraciones significa *parches objetivo rellenados*.
    """
    _comprobar_entradas(imagen, mascara, tam_parche)
    if max_iteraciones is not None and (not isinstance(max_iteraciones, int) or max_iteraciones <= 0):
        raise ValueError("max_iteraciones debe ser None o un entero positivo")
    if guardar_primeras < 0:
        raise ValueError("guardar_primeras debe ser >= 0")
    restaurada = imagen.copy()
    historial = []
    if not mascara.any():
        return (restaurada, 0, historial) if devolver_historial else (restaurada, 0)
    if mascara.all():
        raise ValueError("la máscara cubre toda la imagen: no existe región fuente")
    original = mascara.copy()                 # Phi permanece FIJA
    faltantes = mascara.copy()                # Omega evoluciona en cada iteración
    confianza = confianza_inicial(original)   # Los valores copiados se congelan
    comparacion = _imagen_comparacion(restaurada)
    fuentes = _preparar_fuentes(comparacion, original, tam_parche)
    usadas = 0

    while faltantes.any() and (max_iteraciones is None or usadas < max_iteraciones):
        borde, mapa_C, mapa_D, prioridades = calcular_prioridades(
            restaurada, faltantes, confianza, tam_parche
        )
        if not borde.any():
            raise RuntimeError("no se pudo identificar una frontera de relleno")
        candidatas = [(prioridades[f,c], mapa_C[f,c], (int(f),int(c)), mapa_D[f,c])
                      for f,c in np.argwhere(borde)]
        # La ecuación original puede dar empates (todos P=0 en zonas planas).
        # Se desempata por C y luego por orden de lectura: no altera la fórmula.
        P,C,centro,D = max(candidatas, key=lambda x: (x[0],x[1],-x[2][0],-x[2][1]))
        centro_fuente, ssd = buscar_parche_fuente(
            comparacion, original, faltantes, centro, tam_parche,
            tam_lote=tam_lote, fuentes_preparadas=fuentes
        )
        guardar = devolver_historial and usadas < guardar_primeras
        if guardar:
            antes = restaurada.copy()
            mascara_antes = faltantes.copy()
        nuevos = rellenar_parche(restaurada, comparacion, faltantes, confianza,
                                centro, centro_fuente, C, tam_parche)
        usadas += 1
        if guardar:
            historial.append({
                "iteracion": usadas,
                "centro_objetivo": centro,
                "centro_fuente": centro_fuente,
                "C": C, "D": D, "P": P, "ssd": ssd,
                "nuevos": nuevos, "restantes": int(faltantes.sum()),
                "borde": borde.copy(), "prioridades": prioridades,
                "mascara_antes": mascara_antes,
                "imagen_antes": antes, "imagen_despues": restaurada.copy(),
                "confianza_despues": confianza.copy(),
            })
    if devolver_historial:
        return restaurada, usadas, historial
    return restaurada, usadas
