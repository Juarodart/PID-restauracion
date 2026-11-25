"""
Comparación visual de la media y de Bertalmio en casos variados.

Se eligen fotos distintas (de más lisas a más con textura) y, en cada una, tres
huecos de forma distinta colocados a propósito:

  - un CUADRADO sobre un borde nítido,
  - un CÍRCULO sobre una zona con textura,
  - un RAYÓN fino que cruza un borde.

Para cada caso se restaura con la media (difusion.py) y con Bertalmio
(bertalmio.py), se mide el MSE y el PSNR sobre el hueco y sobre la imagen entera,
y se guarda todo en un CSV y en un PDF en el que cada hoja muestra, para una foto,
el original (con el hueco marcado), el resultado de la media y el de Bertalmio.

Dónde poner cada hueco: se calcula, con el gradiente de la imagen, cuánta energía
(cuánto cambia la imagen) y cuánta coherencia (si los bordes van todos en la
misma dirección) hay en una banda alrededor de cada posible hueco. Un borde nítido
tiene mucha energía y mucha coherencia; una textura, mucha energía y poca coherencia.

Uso desde la carpeta del repositorio:

    python src/comparacion_variada.py --fotos 16 --ancho 256

Se usa NumPy, OpenCV (para leer imágenes, filtros de gradiente y escribir imágenes)
y Matplotlib (para el PDF).
"""

import argparse
import csv
import os
import random
import time

import cv2 as cv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np

import bertalmio
import difusion
import ejemplares
import experimentos
import mascaras
import metricas

LADO = 32            # lado del cuadrado
RADIO = 20           # radio del círculo
GROSOR = 3           # grosor del rayón
LARGO_RAYON = 120    # largo del rayón, en píxeles
BANDA = 8            # anchura de la banda alrededor del hueco para medir el contexto


METODOS_VAR = {
    "media": difusion.difusion_simple,
    "Bertalmio": bertalmio.bertalmio,
    "ejemplares": ejemplares.inpainting_ejemplares,
}


def mapas_gradiente(foto):
    """Productos del gradiente (Jxx, Jyy, Jxy) de la imagen en gris, suavizada un poco."""
    gris = cv.cvtColor(foto, cv.COLOR_RGB2GRAY).astype(np.float32)
    gris = cv.GaussianBlur(gris, (0, 0), 1.0)
    ix = cv.Sobel(gris, cv.CV_32F, 1, 0, ksize=3) / 8
    iy = cv.Sobel(gris, cv.CV_32F, 0, 1, ksize=3) / 8
    return ix * ix, iy * iy, ix * iy


def caracteristicas_global(foto):
    """Energía y coherencia de toda la imagen (para ordenar las fotos de lisas a con textura)."""
    jxx, jyy, jxy = mapas_gradiente(foto)
    return _energia_coherencia(jxx.mean(), jyy.mean(), jxy.mean())[:2]


def _energia_coherencia(sxx, syy, sxy):
    """De los promedios del tensor de estructura, saca energía, coherencia y ángulo del gradiente dominante."""
    energia = sxx + syy
    disc = np.sqrt(max((sxx - syy) ** 2 + 4 * sxy ** 2, 0))
    l1, l2 = (energia + disc) / 2, (energia - disc) / 2
    coherencia = (l1 - l2) / max(l1 + l2, 1e-9)
    angulo = 0.5 * np.arctan2(2 * sxy, sxx - syy)       # dirección del gradiente dominante (x, y)
    return energia, coherencia, angulo


def mejores_posiciones(foto, lado=LADO, banda=BANDA, margen=24, paso=4):
    """
    Busca dos posiciones para un hueco de tamaño `lado`:
      - «borde»:   la de más energía × coherencia en la banda que lo rodea,
      - «textura»: la de más energía × (1 − coherencia).
    Devuelve ((fila, columna, ángulo), (fila, columna, ángulo)) de borde y textura.
    """
    jxx, jyy, jxy = mapas_gradiente(foto)
    externo, interno = lado + 2 * banda, lado
    area = externo ** 2 - interno ** 2
    suma = lambda m, k: cv.boxFilter(m, -1, (k, k), normalize=False, borderType=cv.BORDER_REFLECT)
    sxx = (suma(jxx, externo) - suma(jxx, interno)) / area
    syy = (suma(jyy, externo) - suma(jyy, interno)) / area
    sxy = (suma(jxy, externo) - suma(jxy, interno)) / area
    alto, ancho = foto.shape[:2]
    mejor_borde, mejor_textura = (-1, None), (-1, None)
    for fila in range(margen + externo // 2, alto - margen - externo // 2, paso):
        for col in range(margen + externo // 2, ancho - margen - externo // 2, paso):
            e, c, a = _energia_coherencia(sxx[fila, col], syy[fila, col], sxy[fila, col])
            if e * c > mejor_borde[0]:
                mejor_borde = (e * c, (fila, col, a))
            if e * (1 - c) > mejor_textura[0]:
                mejor_textura = (e * (1 - c), (fila, col, a))
    return mejor_borde[1], mejor_textura[1]


def casos_al_azar(foto, azar):
    """
    Los mismos tres huecos (mismas formas y tamaños) pero en posiciones al azar,
    como control: sirve para ver si la ventaja de Bertalmio depende de dónde se pone el hueco.
    """
    alto, ancho = foto.shape[:2]
    forma = (alto, ancho)
    centro = lambda margen: (azar.randint(margen, alto - margen), azar.randint(margen, ancho - margen))
    fila, col = centro(10)
    angulo = azar.uniform(0, np.pi)
    dy, dx = np.sin(angulo) * LARGO_RAYON / 2, np.cos(angulo) * LARGO_RAYON / 2
    inicio = (int(np.clip(fila - dy, 0, alto - 1)), int(np.clip(col - dx, 0, ancho - 1)))
    fin = (int(np.clip(fila + dy, 0, alto - 1)), int(np.clip(col + dx, 0, ancho - 1)))
    return [
        (f"cuadrado_{LADO}", "cuadrado", "al azar", mascaras.mascara_cuadrada(forma, LADO, centro(LADO))),
        (f"circulo_{RADIO}", "circulo", "al azar", mascaras.mascara_circular(forma, RADIO, centro(RADIO + 1))),
        (f"rayon_{GROSOR}", "rayon", "al azar", mascaras.mascara_aranazo(forma, inicio, fin, GROSOR)),
    ]


def casos_de_una_foto(foto):
    """Los tres huecos de una foto: lista de (nombre, tipo, colocación, máscara)."""
    forma = foto.shape[:2]
    borde, textura = mejores_posiciones(foto)
    f_b, c_b, ang = borde
    f_t, c_t, _ = textura
    # el rayón va en la dirección del gradiente, es decir, cruza el borde
    dy, dx = np.sin(ang) * LARGO_RAYON / 2, np.cos(ang) * LARGO_RAYON / 2
    inicio = (int(np.clip(f_b - dy, 0, forma[0] - 1)), int(np.clip(c_b - dx, 0, forma[1] - 1)))
    fin = (int(np.clip(f_b + dy, 0, forma[0] - 1)), int(np.clip(c_b + dx, 0, forma[1] - 1)))
    return [
        (f"cuadrado_{LADO}", "cuadrado", "sobre un borde", mascaras.mascara_cuadrada(forma, LADO, (f_b, c_b))),
        (f"circulo_{RADIO}", "circulo", "sobre textura", mascaras.mascara_circular(forma, RADIO, (f_t, c_t))),
        (f"rayon_{GROSOR}", "rayon", "cruzando un borde", mascaras.mascara_aranazo(forma, inicio, fin, GROSOR)),
    ]


def elegir_fotos(carpeta, cantidad, ancho, excluir, solo=None):
    """
    Elige `cantidad` fotos que no estén en `excluir`, repartidas de menos a más
    energía del gradiente (de fotos lisas a fotos con mucho detalle).
    """
    nombres = sorted(f for f in os.listdir(carpeta) if f.lower().endswith((".jpg", ".jpeg", ".png")) and f not in excluir
                     and (solo is None or f in solo))
    medidas = []
    for nombre in nombres:
        foto = experimentos.cargar_imagen(os.path.join(carpeta, nombre), ancho)
        medidas.append((caracteristicas_global(foto)[0], nombre))
    medidas.sort()
    indices = np.linspace(0, len(medidas) - 1, cantidad).round().astype(int)
    return [(medidas[i][1], medidas[i][0]) for i in indices]


def recorte(imagen, mascara, tam=144):
    """Ventana de tam×tam centrada en el hueco (acotada a la imagen)."""
    ys, xs = np.nonzero(mascara)
    cy, cx = int(ys.mean()), int(xs.mean())
    y0 = min(max(cy - tam // 2, 0), max(imagen.shape[0] - tam, 0))
    x0 = min(max(cx - tam // 2, 0), max(imagen.shape[1] - tam, 0))
    return (slice(y0, y0 + tam), slice(x0, x0 + tam))


def ejecutar(carpeta, cantidad, ancho, ruta_csv, ruta_pdf, semilla=42, grupo="nuevas", colocacion="dirigida", con_pdf=True,
             metodos=("media", "Bertalmio"), anadir=False):
    """
    grupo:      «nuevas» = fotos distintas de las 20 del experimento principal;
                «anteriores» = esas 20 fotos.
    colocacion: «dirigida» = huecos sobre un borde, sobre textura y cruzando un borde;
                «azar» = mismas formas y tamaños en posiciones al azar (control).
    metodos:    métodos a ejecutar (media, Bertalmio y/o ejemplares).
    anadir:     si es True, las filas nuevas se añaden al CSV existente en vez de reescribirlo
                (sirve para añadir un método a un experimento ya hecho, con los mismos casos).
    """
    previas = set(experimentos.lista_imagenes(carpeta, 20, semilla))
    if grupo == "nuevas":
        fotos = elegir_fotos(carpeta, cantidad, ancho, previas)
    else:
        fotos = elegir_fotos(carpeta, cantidad, ancho, set(), solo=previas)
    filas, hojas = [], []
    inicio = time.perf_counter()
    for numero, (nombre, energia) in enumerate(fotos, start=1):
        foto = experimentos.cargar_imagen(os.path.join(carpeta, nombre), ancho)
        casos = []
        azar = random.Random(semilla * 1000 + numero)
        casos_foto = casos_de_una_foto(foto) if colocacion == "dirigida" else casos_al_azar(foto, azar)
        for nombre_caso, tipo, colocacion_hueco, mascara in casos_foto:
            danada = mascaras.aplicar_mascara(foto, mascara)
            resultados = {}
            for metodo in metodos:
                funcion = METODOS_VAR[metodo]
                (restaurada, iteraciones), t, _ = metricas.cronometrar(funcion, danada, mascara, repeticiones=1)
                medidas = metricas.evaluar(foto, restaurada, mascara)
                resultados[metodo] = {"imagen": restaurada, "tiempo": t, "iteraciones": iteraciones, **medidas}
                filas.append({"foto": nombre, "energia_foto": f"{energia:.1f}", "caso": nombre_caso, "tipo": tipo, "colocacion": colocacion_hueco, "grupo": grupo,
                              "pixeles_hueco": int(mascara.sum()), "metodo": metodo, "tiempo_s": f"{t:.3f}", "iteraciones": iteraciones,
                              "mse_hueco": f"{medidas['mse_hueco']:.2f}", "psnr_hueco": f"{medidas['psnr_hueco']:.2f}",
                              "mse_imagen": f"{medidas['mse_imagen']:.3f}", "psnr_imagen": f"{medidas['psnr_imagen']:.2f}"})
            casos.append((nombre_caso, colocacion_hueco, mascara, resultados))
            resumen = "  ".join(f"{m} MSE {resultados[m]['mse_hueco']:8.1f} ({resultados[m]['tiempo']:.1f} s)" for m in metodos)
            print(f"[{numero}/{len(fotos)}] {nombre[:26]:26s} {nombre_caso:12s} {resumen}", flush=True)
        hojas.append((nombre, energia, foto, casos))

    os.makedirs(os.path.dirname(ruta_csv) or ".", exist_ok=True)
    if anadir and os.path.exists(ruta_csv):
        with open(ruta_csv, newline="", encoding="utf-8") as f:
            campos = next(csv.reader(f))                 # se respetan las columnas del archivo existente
        with open(ruta_csv, "a", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=campos, extrasaction="ignore").writerows(filas)
    else:
        with open(ruta_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(filas[0]))
            w.writeheader()
            w.writerows(filas)
    if con_pdf:
        escribir_pdf(ruta_pdf, hojas, filas, ancho, metodos)
    print(f"Terminado en {time.perf_counter() - inicio:.0f} s. CSV: {ruta_csv}" + (f". PDF: {ruta_pdf}" if con_pdf else ""))


def escribir_pdf(ruta, hojas, filas, ancho, metodos=("media", "Bertalmio")):
    """Una hoja por foto: foto entera con los huecos, y una fila por hueco con el original y el resultado de cada método."""
    columnas = 1 + len(metodos)
    titulo = " , ".join(metodos).replace(" , ", ", ")
    with PdfPages(ruta) as pdf:
        # portada
        fig = plt.figure(figsize=(8.27, 11.69))
        fig.text(0.08, 0.92, "Comparación de métodos en casos variados", fontsize=18, weight="bold")
        fig.text(0.08, 0.885, f"{titulo}: comparación visual con MSE y PSNR sobre el hueco", fontsize=11, color="0.3")
        texto = (
            f"Fotos: {len(hojas)} fotos distintas de las 20 usadas en el experimento principal, reducidas a {ancho} píxeles de ancho\n"
            "y repartidas de menos a más detalle (energía del gradiente).\n\n"
            "Huecos de cada foto, colocados a propósito:\n"
            f"  A. Cuadrado de lado {LADO} sobre un borde nítido (mucha energía y mucha coherencia alrededor).\n"
            f"  B. Círculo de radio {RADIO} sobre una zona con textura (mucha energía y poca coherencia).\n"
            f"  C. Rayón de {GROSOR} píxeles que cruza un borde.\n\n"
            "Cada fila de una hoja es un hueco y enseña, de izquierda a derecha:\n"
            "  - la foto original, con el hueco marcado en rojo,\n"
            + "".join({"media": "  - el resultado de la media de los cuatro vecinos,\n",
                      "Bertalmio": "  - el resultado de Bertalmio (valores por defecto: hasta 600 ciclos),\n",
                      "ejemplares": "  - el resultado de ejemplares (Criminisi, parches de 9×9),\n"}[m] for m in metodos) +
            "\n"
            "Medidas, siempre sobre los píxeles del hueco:\n"
            "  MSE  = error cuadrático medio entre la foto original y la restaurada (cuanto menor, mejor).\n"
            "  PSNR = relación señal-ruido de pico, 10·log10(255² / MSE), en decibelios (cuanto mayor, mejor).\n\n"
            f"Cuidado al interpretarlo: son pocos casos ({len(hojas)} fotos × 3 huecos), un solo valor de partida de Bertalmio y\n"
            "el MSE y el PSNR favorecen el borrón frente a un borde nítido mal colocado. Hay que mirar también la imagen."
        )
        fig.text(0.08, 0.80, texto, fontsize=9.5, va="top", linespacing=1.5)
        pdf.savefig(fig); plt.close(fig)

        for nombre, energia, foto, casos in hojas:
            fig = plt.figure(figsize=(8.27, 11.69))
            gs = fig.add_gridspec(4, columnas, height_ratios=[1.25, 1, 1, 1], hspace=0.38, wspace=0.05, left=0.05, right=0.95, top=0.93, bottom=0.03)
            ax = fig.add_subplot(gs[0, :])
            panel = foto.copy()
            colores = [(255, 0, 0), (0, 160, 255), (255, 200, 0)]
            for (nombre_caso, colocacion, mascara, _), color in zip(casos, colores):
                borde = mascara & ~cv.erode(mascara.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
                panel[cv.dilate(borde.astype(np.uint8), np.ones((2, 2), np.uint8)).astype(bool)] = color
            ax.imshow(panel); ax.axis("off")
            ax.set_title(f"{nombre}   (energía del gradiente {energia:.0f})\nrojo: A, cuadrado sobre borde · azul: B, círculo sobre textura · amarillo: C, rayón", fontsize=9)
            for fila, (nombre_caso, colocacion, mascara, res) in enumerate(casos, start=1):
                v = recorte(foto, mascara)
                a0 = fig.add_subplot(gs[fila, 0])
                a0.imshow(foto[v])
                a0.contour(mascara[v].astype(float), levels=[0.5], colors="red", linewidths=1.0)
                a0.set_title(f"{'ABC'[fila - 1]}. {nombre_caso}, {colocacion}\noriginal", fontsize=8)
                for col, metodo in enumerate(metodos, start=1):
                    r = res[metodo]
                    a = fig.add_subplot(gs[fila, col])
                    a.imshow(r["imagen"][v])
                    a.set_title(f"{metodo}\nMSE {r['mse_hueco']:.0f} · PSNR {r['psnr_hueco']:.1f} dB · {r['tiempo']:.1f} s", fontsize=8)
                for a in [a0] + fig.axes[-len(metodos):]:
                    a.axis("off")
            pdf.savefig(fig); plt.close(fig)

        # hoja final con el resumen
        por = {}
        for f in filas:
            por.setdefault((f["foto"], f["caso"]), {})[f["metodo"]] = f
        tipos = [("cuadrado", "A. cuadrado sobre un borde"), ("circulo", "B. círculo sobre textura"), ("rayon", "C. rayón cruzando un borde")]
        lineas = ["Resumen (sobre los casos de este PDF)", ""]
        for tipo, etiqueta in tipos:
            ks = [k for k, v in por.items() if v[metodos[0]]["tipo"] == tipo]
            lineas.append(f"{etiqueta}  ({len(ks)} casos)")
            for m in metodos:
                em = np.mean([float(por[k][m]["mse_hueco"]) for k in ks]); pm = np.mean([float(por[k][m]["psnr_hueco"]) for k in ks])
                lineas.append(f"     {m:<11s}MSE medio {em:7.0f}, PSNR medio {pm:5.1f} dB")
            lineas.append("")
        mejor = {m: 0 for m in metodos}
        for v in por.values():
            mejor[min(metodos, key=lambda m: float(v[m]["mse_hueco"]))] += 1
        lineas.append(f"Método con menos MSE en cada caso ({len(por)} casos):")
        for m in metodos:
            lineas.append(f"     {m:<11s}{mejor[m]} casos")
        if "media" in metodos and "Bertalmio" in metodos:
            gana = sum(1 for v in por.values() if float(v["Bertalmio"]["mse_hueco"]) < float(v["media"]["mse_hueco"]))
            lineas.append("")
            lineas.append(f"Bertalmio tiene menos MSE que la media en {gana} de {len(por)} casos.")
        lineas.append("Los valores de cada caso están en el CSV.")
        fig = plt.figure(figsize=(8.27, 11.69))
        fig.text(0.08, 0.92, "\n".join(lineas), fontsize=10, va="top", family="monospace", linespacing=1.5)
        pdf.savefig(fig); plt.close(fig)


if __name__ == "__main__":
    a = argparse.ArgumentParser(description="Media y Bertalmio en casos variados, con CSV y PDF")
    a.add_argument("--carpeta", default="images/originales")
    a.add_argument("--fotos", type=int, default=16)
    a.add_argument("--ancho", type=int, default=256)
    a.add_argument("--csv", default="resultados/comparacion_variada.csv")
    a.add_argument("--pdf", default="resultados/comparacion_variada.pdf")
    a.add_argument("--grupo", choices=["nuevas", "anteriores"], default="nuevas", help="fotos distintas de las del experimento principal, o esas mismas")
    a.add_argument("--colocacion", choices=["dirigida", "azar"], default="dirigida", help="huecos dirigidos a bordes y texturas, o al azar")
    a.add_argument("--sin-pdf", action="store_true", help="no generar el PDF, solo el CSV")
    a.add_argument("--metodos", nargs="+", choices=list(METODOS_VAR), default=["media", "Bertalmio"], help="métodos a ejecutar")
    a.add_argument("--anadir", action="store_true", help="añadir las filas al CSV existente en vez de reescribirlo")
    args = a.parse_args()
    ejecutar(args.carpeta, args.fotos, args.ancho, args.csv, args.pdf, grupo=args.grupo, colocacion=args.colocacion, con_pdf=not args.sin_pdf,
             metodos=tuple(args.metodos), anadir=args.anadir)
