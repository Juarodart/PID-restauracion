"""
Experimento por escenarios: ¿en qué casos va mejor cada método?

Se prueban tres hipótesis, cada una con imágenes construidas a propósito, en las
que se sabe exactamente qué hay debajo del hueco:

  H-liso      Zona lisa (cielo con degradado): la media debería bastar.
  H-borde     Un borde o una línea cruza el hueco (la línea de una montaña, un hilo
              marrón sobre el cielo): Bertalmio debería continuarlo mejor que la media.
  H-repeticion  El hueco está en algo que se repite en la imagen (césped, rayas):
              ejemplares debería copiarlo de otra zona y ganar.

Cada escenario tiene 3 subtipos × 4 variantes (ángulo, desplazamiento, semilla) y
3 tamaños de hueco cuadrado, centrado en lo que se quiere probar. Los tres métodos
reciben exactamente el mismo problema. El script no decide el resultado: guarda lo
que miden el tiempo y el MSE, y escribe la tabla.

Una segunda parte repite la idea con fotos reales: las 20 del experimento principal,
con el hueco puesto en la zona más lisa, en el borde más marcado o en la textura más
densa de cada foto (--reales).

Uso desde la carpeta del repositorio:

    python src/escenarios.py              # escenarios sintéticos
    python src/escenarios.py --reales     # además, fotos reales (unos 10 minutos más)

Salida en resultados/escenarios/: escenarios.csv, escenarios.md, reales.csv y figuras/.
"""

import argparse
import csv
import datetime
import os
import platform
import time

import cv2 as cv
import numpy as np

import comparacion_variada as cvar
import experimentos
import mascaras
import metricas

N = 256
TAMANOS = (16, 32, 48)
VARIANTES = 4
METODOS = ("media", "Bertalmio", "ejemplares")


# ---------------------------------------------------------------- imágenes sintéticas

def _cielo(azar, angulo):
    """Degradado de azul claro a azul intenso en una dirección."""
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    t = (np.cos(angulo) * (xx - N / 2) + np.sin(angulo) * (yy - N / 2)) / N + 0.5
    t = np.clip(t, 0, 1)[..., None]
    a, b = np.array([70, 130, 220], np.float32), np.array([200, 225, 250], np.float32)
    return a * (1 - t) + b * t


def _a_uint8(img):
    return np.clip(np.rint(img), 0, 255).astype(np.uint8)


def escena_liso(subtipo, v):
    azar = np.random.RandomState(100 + v)
    img = _cielo(azar, azar.uniform(0, np.pi))
    if subtipo == "cielo con grano":
        img += azar.normal(0, 3, img.shape)
    return _a_uint8(img)


def escena_borde(subtipo, v):
    azar = np.random.RandomState(200 + v)
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    cielo = _cielo(azar, np.pi / 2 + azar.uniform(-0.3, 0.3))
    marron = np.array([105, 78, 52], np.float32) + azar.uniform(-10, 10, 3)
    angulo = azar.uniform(-0.6, 0.6)
    # distancia con signo a la línea que pasa por el centro
    d = (yy - N / 2) * np.cos(angulo) - (xx - N / 2) * np.sin(angulo)
    if subtipo == "montaña recta":
        dentro = d > 0
    elif subtipo == "cresta ondulada":
        dentro = d > 6 * np.sin(2 * np.pi * (xx / 90 + azar.uniform()))
    elif subtipo == "hilo fino":
        dentro = np.abs(d) < 2
    else:
        raise ValueError(subtipo)
    img = np.where(dentro[..., None], marron * (0.85 + 0.15 * yy[..., None] / N), cielo)
    return _a_uint8(img)


def escena_repeticion(subtipo, v):
    azar = np.random.RandomState(300 + v)
    verdes = np.array([[40, 110, 30], [70, 150, 50], [30, 90, 25], [95, 165, 60], [55, 125, 40]], np.float32)
    if subtipo == "césped en bloques":      # una baldosa de 14×14 repetida: repetición exacta
        baldosa = verdes[azar.randint(0, len(verdes), (14, 14))]
        img = np.tile(baldosa, (N // 14 + 2, N // 14 + 2, 1))[:N, :N]
    elif subtipo == "césped aleatorio":     # misma estadística, sin repetición exacta
        ruido = azar.randint(0, len(verdes), (N, N))
        img = cv.GaussianBlur(verdes[ruido], (0, 0), 0.8)
    elif subtipo == "rayas":
        periodo = 8 + (v % 2) * 2
        x = (np.arange(N) // (periodo // 2)) % 2
        fila = np.where(x[:, None] == 0, np.array([40, 100, 30]), np.array([110, 175, 70])).astype(np.float32)
        img = np.repeat(fila[None], N, axis=0)
    else:
        raise ValueError(subtipo)
    return _a_uint8(img)


FAMILIAS = {
    "liso": (escena_liso, ("degradado", "cielo con grano")),
    "borde": (escena_borde, ("montaña recta", "cresta ondulada", "hilo fino")),
    "repetición": (escena_repeticion, ("césped en bloques", "césped aleatorio", "rayas")),
}


# ---------------------------------------------------------------- ejecución

def ejecutar_caso(foto, mascara, metodos=METODOS):
    """Aplica los métodos y devuelve {método: (restaurada, tiempo, iteraciones, medidas)}."""
    danada = mascaras.aplicar_mascara(foto, mascara)
    salida = {}
    for metodo in metodos:
        (restaurada, iteraciones), tiempo, _ = metricas.cronometrar(
            experimentos.obtener_metodo(metodo), danada, mascara, repeticiones=1)
        salida[metodo] = (restaurada, tiempo, iteraciones, metricas.evaluar(foto, restaurada, mascara))
    return danada, salida


def figura(ruta, titulo, foto, mascara, danada, salida):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ventana = cvar.recorte(foto, mascara, 96)
    paneles = [("original", foto), ("dañada", danada)] + [
        (f"{m}\nMSE {s[3]['mse_hueco']:.0f}", s[0]) for m, s in salida.items()]
    fig, ejes = plt.subplots(1, len(paneles), figsize=(2.6 * len(paneles), 3.0))
    for eje, (t, im) in zip(ejes, paneles):
        eje.imshow(im[ventana], interpolation="nearest")
        eje.set_title(t, fontsize=8)
        eje.axis("off")
    fig.suptitle(titulo, fontsize=9)
    fig.tight_layout()
    fig.savefig(ruta, dpi=100)
    plt.close(fig)


def sinteticos(destino):
    filas, total = [], sum(len(s) for _, s in FAMILIAS.values()) * VARIANTES * len(TAMANOS)
    hecho = 0
    for familia, (generar, subtipos) in FAMILIAS.items():
        for subtipo in subtipos:
            for v in range(VARIANTES):
                foto = generar(subtipo, v)
                for lado in TAMANOS:
                    mascara = mascaras.mascara_cuadrada((N, N), lado, (N // 2, N // 2))
                    danada, salida = ejecutar_caso(foto, mascara)
                    hecho += 1
                    for metodo, (_, t, it, med) in salida.items():
                        filas.append({"familia": familia, "subtipo": subtipo, "variante": v, "lado": lado,
                                      "metodo": metodo, "tiempo_s": f"{t:.4f}", "iteraciones": it,
                                      "mse_hueco": f"{med['mse_hueco']:.2f}", "psnr_hueco": f"{med['psnr_hueco']:.2f}"})
                    print(f"[{hecho}/{total}] {familia:10s} {subtipo:18s} v{v} lado {lado:2d}  " +
                          "  ".join(f"{m} {s[3]['mse_hueco']:8.1f}" for m, s in salida.items()), flush=True)
                    if v == 0 and lado == 32:
                        figura(os.path.join(destino, "figuras", f"{familia}_{subtipo.replace(' ', '_')}.png"),
                               f"{familia} · {subtipo} · hueco {lado}×{lado}", foto, mascara, danada, salida)
    return filas


def reales(destino, carpeta="images/originales", cantidad=20, ancho=256, lado=32):
    """Fotos reales: hueco en la zona más lisa, en el borde más marcado y en la textura más densa."""
    filas = []
    imagenes = experimentos.lista_imagenes(carpeta, cantidad, 42)
    for n, nombre in enumerate(imagenes, start=1):
        foto = experimentos.cargar_imagen(os.path.join(carpeta, nombre), ancho)
        borde, textura = cvar.mejores_posiciones(foto, lado=lado)
        liso = zona_lisa(foto, lado)
        for caso, (fila, col) in (("liso", liso), ("borde", borde[:2]), ("repetición/textura", textura[:2])):
            mascara = mascaras.mascara_cuadrada(foto.shape[:2], lado, (int(fila), int(col)))
            danada, salida = ejecutar_caso(foto, mascara)
            for metodo, (_, t, it, med) in salida.items():
                filas.append({"foto": nombre, "caso": caso, "lado": lado, "metodo": metodo, "tiempo_s": f"{t:.4f}",
                              "iteraciones": it, "mse_hueco": f"{med['mse_hueco']:.2f}", "psnr_hueco": f"{med['psnr_hueco']:.2f}"})
            print(f"[{n}/{len(imagenes)}] {nombre[:22]:22s} {caso:19s} " +
                  "  ".join(f"{m} {s[3]['mse_hueco']:8.1f}" for m, s in salida.items()), flush=True)
            figura(os.path.join(destino, "figuras", f"real_{n:02d}_{caso.split('/')[0]}.png"),
                   f"{nombre[:24]} · {caso}", foto, mascara, danada, salida)
    return filas


def zona_lisa(foto, lado, margen=24, paso=4):
    """Centro de la ventana de `lado`+banda con menos energía de gradiente."""
    jxx, jyy, _ = cvar.mapas_gradiente(foto)
    k = lado + 2 * cvar.BANDA
    energia = cv.boxFilter(jxx + jyy, -1, (k, k), normalize=True, borderType=cv.BORDER_REFLECT)
    mejor = (np.inf, None)
    for f in range(margen + k // 2, foto.shape[0] - margen - k // 2, paso):
        for c in range(margen + k // 2, foto.shape[1] - margen - k // 2, paso):
            if energia[f, c] < mejor[0]:
                mejor = (energia[f, c], (f, c))
    return mejor[1]


# ---------------------------------------------------------------- informe

def guardar_csv(ruta, filas):
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=list(filas[0]))
        escritor.writeheader()
        escritor.writerows(filas)


def resumen(filas, claves):
    """Por grupo: mediana del MSE de cada método y cuántas veces gana cada uno."""
    grupos = {}
    for f in filas:
        grupos.setdefault(tuple(f[k] for k in claves), {}).setdefault(
            tuple(f[k] for k in f if k in ("subtipo", "variante", "lado", "foto")), {})[f["metodo"]] = float(f["mse_hueco"])
    texto = []
    for grupo, casos in grupos.items():
        medianas = {m: float(np.median([c[m] for c in casos.values()])) for m in METODOS}
        gana = {m: 0 for m in METODOS}
        for c in casos.values():
            gana[min(c, key=c.get)] += 1
        texto.append((grupo, len(casos), medianas, gana))
    return texto


def tabla_md(titulo, filas, claves):
    lineas = [f"### {titulo}", "", "| " + " | ".join(claves) + " | casos | " +
              " | ".join(f"MSE mediano {m}" for m in METODOS) + " | gana (media / Bertalmio / ejemplares) |",
              "|" + "---|" * (len(claves) + 5)]
    for grupo, n, med, gana in resumen(filas, claves):
        lineas.append("| " + " | ".join(str(g) for g in grupo) + f" | {n} | " +
                      " | ".join(f"{med[m]:.1f}" for m in METODOS) + " | " +
                      " / ".join(str(gana[m]) for m in METODOS) + " |")
    return "\n".join(lineas) + "\n"


def escribir_md(ruta, sint, real, total):
    partes = ["# Experimento por escenarios: ¿cuándo va mejor cada método?", "",
              f"Generado por `src/escenarios.py` el {datetime.datetime.now():%Y-%m-%d %H:%M} en {platform.platform()} ({platform.machine()}), "
              f"{len(sint)} ejecuciones sintéticas" + (f" y {len(real)} con fotos reales" if real else "") + f" en {total:.0f} s.", "",
              "MSE sobre el hueco: cuanto **menor**, mejor. «Gana» cuenta en cuántos casos cada método tuvo el MSE más bajo.", "",
              tabla_md("Imágenes sintéticas, por familia", sint, ["familia"]),
              tabla_md("Imágenes sintéticas, por familia y subtipo", sint, ["familia", "subtipo"]),
              tabla_md("Imágenes sintéticas, por familia y tamaño del hueco (px de lado)", sint, ["familia", "lado"])]
    if real:
        partes.append(tabla_md("Fotos reales, por tipo de zona (hueco de 32 px)", real, ["caso"]))
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("\n".join(partes))


if __name__ == "__main__":
    a = argparse.ArgumentParser(description="¿En qué casos va mejor cada método?")
    a.add_argument("--salida", default="resultados/escenarios")
    a.add_argument("--reales", action="store_true", help="añade la parte con fotos reales")
    argumentos = a.parse_args()
    os.makedirs(os.path.join(argumentos.salida, "figuras"), exist_ok=True)
    inicio = time.perf_counter()
    sint = sinteticos(argumentos.salida)
    guardar_csv(os.path.join(argumentos.salida, "escenarios.csv"), sint)
    real = []
    if argumentos.reales:
        real = reales(argumentos.salida)
        guardar_csv(os.path.join(argumentos.salida, "reales.csv"), real)
    escribir_md(os.path.join(argumentos.salida, "escenarios.md"), sint, real, time.perf_counter() - inicio)
    print(f"\nTerminado en {time.perf_counter() - inicio:.0f} s. Resultados en {argumentos.salida}")
