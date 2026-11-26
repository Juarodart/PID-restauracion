"""
Estudio de cada algoritmo por separado: cómo cambia su resultado al variar el
tamaño del hueco, la forma de la máscara y el contraste.

A diferencia del experimento principal (que compara los métodos entre sí), aquí
se mira un método cada vez y se cambia una sola cosa por estudio:

  tamaño     hueco cuadrado de lado 8, 16, 24, 32, 48 y 64 píxeles, en el centro de
             12 fotos reales (las 4 más representativas de cada tipo: lisa,
             estructura y textura).
  forma      la misma área (unos 1000 píxeles) con distinta forma: cuadrado,
             círculo, tira alargada, arañazo diagonal, motas e irregular, sobre
             las mismas 12 fotos.
  contraste  imágenes sintéticas con un borde (o una línea fina de 3 píxeles)
             que cruza el hueco, con diferencia de gris de 10 a 240. Se mide el
             MSE y el MSE relativo, que es el MSE dividido entre el contraste al
             cuadrado, para poder comparar contrastes distintos.

Además de esos tres estudios comunes, cada método tiene los suyos:

  media      iteraciones (de 10 a 1000, y hasta converger) y tolerancia de parada.
  Bertalmio  valor de partida del hueco (difusión simple, media plana o ruido),
             máximo de ciclos, paso temporal y pasos de difusión por ciclo.
  Estos estudios propios se hacen con un hueco cuadrado de 32 píxeles en el centro
  de las mismas 12 fotos. Los de ejemplares (tamaño del parche, por ejemplo) los
  añade quien lo programó, en ESPECIFICOS.

Para cada estudio se guarda una fila por caso (CSV), una tabla de medianas y una
gráfica. Por defecto se estudian la media y Bertalmio; los ejemplares se pueden
estudiar con el mismo script y la misma forma de medir:

    python src/estudio_algoritmos.py --metodos media Bertalmio
    python src/estudio_algoritmos.py --metodos ejemplares

Los resultados de cada método se guardan en su propio CSV
(resultados/estudio_algoritmos/<método>.csv), y el script se puede reanudar.
"""

import argparse
import csv
import functools
import os
import time

import cv2 as cv
import numpy as np

import bertalmio
import difusion
import escenarios
import experimento_principal
import experimentos
import mascaras
import metricas

LADOS = (8, 16, 24, 32, 48, 64)
CONTRASTES = (10, 20, 40, 80, 160, 240)
# Estudios propios de cada método: nombre del estudio -> [(valor, función)].
# Cada función se llama igual que los métodos: f(imagen_dañada, máscara) -> (restaurada, iteraciones).
ESPECIFICOS = {
    "media": {
        "iteraciones": [(n, functools.partial(difusion.difusion_simple, iteraciones=n, tolerancia=0)) for n in (10, 50, 100, 250, 500, 1000)]
                       + [("hasta converger", functools.partial(difusion.difusion_simple, tolerancia=0.001))],
        "tolerancia": [(t, functools.partial(difusion.difusion_simple, tolerancia=t)) for t in (1, 0.1, 0.01, 0.001)],
    },
    "Bertalmio": {
        "valor de partida": [("difusión simple", functools.partial(bertalmio.bertalmio, inicio="difusion")),
                             ("media plana", functools.partial(bertalmio.bertalmio, inicio="media")),
                             ("ruido", functools.partial(bertalmio.bertalmio, inicio="ruido"))],
        "máximo de ciclos": [(c, functools.partial(bertalmio.bertalmio, ciclos=c)) for c in (25, 50, 100, 200, 600)],
        "paso temporal": [(dt, functools.partial(bertalmio.bertalmio, dt=dt)) for dt in (0.05, 0.1, 0.2)],
        "pasos de difusión por ciclo": [(b, functools.partial(bertalmio.bertalmio, pasos_difusion=b)) for b in (0, 2, 4)],
    },
    # "ejemplares": {"tamaño del parche": [...]},   <- lo añade Alejandro
}

COLUMNAS = ["estudio", "metodo", "valor", "caso", "tipo_imagen", "pixeles_hueco", "tiempo_s", "iteraciones",
            "mse_hueco", "psnr_hueco", "mse_relativo"]


def mascaras_de_forma(forma):
    """Seis máscaras de unos 1000 píxeles y distinta forma, centradas en la imagen."""
    alto, ancho = forma
    cy, cx = alto // 2, ancho // 2
    tira = np.zeros(forma, dtype=bool)
    tira[cy - 4:cy + 4, cx - 64:cx + 64] = True                       # 8 × 128
    return [
        ("cuadrado", mascaras.mascara_cuadrada(forma, 32, (cy, cx))),
        ("círculo", mascaras.mascara_circular(forma, 18, (cy, cx))),
        ("tira 8×128", tira),
        ("arañazo", mascaras.mascara_aranazo(forma, (cy - 100, cx - 100), (cy + 100, cx + 100), 3)),
        ("motas", mascaras.mascara_motas(forma, 9, 6, semilla=7)),
        ("irregular", mascaras.mascara_irregular(forma, 36, (cy, cx), semilla=7)),
    ]


def escena_contraste(tipo, contraste, variante):
    """Borde o línea fina de un cierto contraste que cruza el centro. Imagen gris en 3 canales, 256×256."""
    n = escenarios.N
    angulo = (-0.5, -0.2, 0.2, 0.5)[variante]
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    d = (yy - n / 2) * np.cos(angulo) - (xx - n / 2) * np.sin(angulo)       # distancia con signo a la línea
    if tipo == "borde":
        img = 128 + contraste * np.clip(d / 2, -0.5, 0.5)                    # transición suave de ~2 píxeles
    else:
        img = 128 + contraste * np.clip(1.5 - np.abs(d), 0, 1)               # línea de 3 píxeles
    img = np.clip(img, 0, 255)
    return np.repeat(np.rint(img)[..., None], 3, axis=2).astype(np.uint8)


def casos(por_tipo=4, carpeta="images/originales", ancho=256):
    """Genera todos los casos: (estudio, valor, caso, tipo_imagen, foto, máscara, contraste o None)."""
    lista = []
    fotos = []
    for tipo_imagen, clase in experimento_principal.clasificar(carpeta, ancho, por_tipo).items():
        for nombre, _, _ in clase:
            fotos.append((tipo_imagen, nombre, experimentos.cargar_imagen(os.path.join(carpeta, nombre), ancho)))
    for tipo_imagen, nombre, foto in fotos:
        alto, anc = foto.shape[:2]
        for lado in LADOS:
            lista.append(("tamaño", lado, nombre, tipo_imagen, foto,
                          mascaras.mascara_cuadrada(foto.shape[:2], lado, (alto // 2, anc // 2)), None))
        for forma, mascara in mascaras_de_forma(foto.shape[:2]):
            lista.append(("forma", forma, nombre, tipo_imagen, foto, mascara, None))
    n = escenarios.N
    centro = mascaras.mascara_cuadrada((n, n), 32, (n // 2, n // 2))
    for tipo in ("borde", "línea fina"):
        for contraste in CONTRASTES:
            for variante in range(4):
                lista.append((f"contraste ({tipo})", contraste, f"{tipo}_{variante}", "sintética",
                              escena_contraste("borde" if tipo == "borde" else "linea", contraste, variante), centro, contraste))
    return lista, fotos


def ya_hechos(ruta):
    if not os.path.exists(ruta):
        return set()
    with open(ruta, newline="", encoding="utf-8") as f:
        return {(r["estudio"], r["valor"], r["caso"]) for r in csv.DictReader(f)}


def ejecutar(metodos, carpeta_salida, por_tipo=4):
    os.makedirs(carpeta_salida, exist_ok=True)
    comunes, fotos = casos(por_tipo)
    inicio = time.perf_counter()
    for metodo in metodos:
        # casos comunes (todos los métodos) y propios de este método, todos con la misma forma de ejecutar
        trabajo = [(estudio, valor, caso, tipo_imagen, foto, mascara, contraste, experimentos.obtener_metodo(metodo))
                   for estudio, valor, caso, tipo_imagen, foto, mascara, contraste in comunes]
        for estudio, variantes in ESPECIFICOS.get(metodo, {}).items():
            for valor, funcion in variantes:
                for tipo_imagen, nombre, foto in fotos:
                    centro = mascaras.mascara_cuadrada(foto.shape[:2], 32, (foto.shape[0] // 2, foto.shape[1] // 2))
                    trabajo.append((f"propio: {estudio}", valor, nombre, tipo_imagen, foto, centro, None, funcion))
        ruta = os.path.join(carpeta_salida, f"{metodo}.csv")
        hechos = ya_hechos(ruta)
        nuevo = not os.path.exists(ruta)
        with open(ruta, "a", newline="", encoding="utf-8") as f:
            escritor = csv.DictWriter(f, fieldnames=COLUMNAS)
            if nuevo:
                escritor.writeheader()
            for n, (estudio, valor, caso, tipo_imagen, foto, mascara, contraste, funcion) in enumerate(trabajo, start=1):
                if (estudio, str(valor), caso) in hechos:
                    continue
                danada = mascaras.aplicar_mascara(foto, mascara)
                (restaurada, iteraciones), tiempo, _ = metricas.cronometrar(funcion, danada, mascara, repeticiones=1)
                med = metricas.evaluar(foto, restaurada, mascara)
                relativo = f"{med['mse_hueco'] / contraste ** 2:.5f}" if contraste else ""
                escritor.writerow({"estudio": estudio, "metodo": metodo, "valor": valor, "caso": caso,
                                   "tipo_imagen": tipo_imagen, "pixeles_hueco": int(mascara.sum()), "tiempo_s": f"{tiempo:.4f}",
                                   "iteraciones": iteraciones, "mse_hueco": f"{med['mse_hueco']:.2f}",
                                   "psnr_hueco": f"{med['psnr_hueco']:.2f}", "mse_relativo": relativo})
                f.flush()
                print(f"[{metodo}] {n}/{len(trabajo)} {estudio:32s} {str(valor):15s} {caso[:20]:20s} "
                      f"MSE {med['mse_hueco']:9.1f}  {tiempo:6.2f} s  it {iteraciones}", flush=True)
    print(f"Terminado en {time.perf_counter() - inicio:.0f} s")


def resumen(carpeta_salida, metodos):
    """Tabla en Markdown con las medianas por estudio y valor, y gráficas."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    datos = {}
    for metodo in metodos:
        ruta = os.path.join(carpeta_salida, f"{metodo}.csv")
        if os.path.exists(ruta):
            with open(ruta, newline="", encoding="utf-8") as f:
                datos[metodo] = list(csv.DictReader(f))
    lineas = ["# Estudio de cada algoritmo", "", "Medianas sobre los casos de cada fila. MSE sobre el hueco (menor es mejor).", ""]
    estudios = []
    for filas in datos.values():
        for r in filas:
            if r["estudio"] not in estudios:
                estudios.append(r["estudio"])
    for estudio in estudios:
        lineas += [f"## {estudio}", "", "| valor | " + " | ".join(f"{m}: MSE | {m}: tiempo (s) | {m}: iteraciones" for m in datos) + " |",
                   "|---|" + "---:|---:|---:|" * len(datos)]
        valores = []
        for filas in datos.values():
            for r in filas:
                if r["estudio"] == estudio and r["valor"] not in valores:
                    valores.append(r["valor"])
        for v in valores:
            celdas = []
            for m, filas in datos.items():
                sel = [r for r in filas if r["estudio"] == estudio and r["valor"] == v]
                if sel:
                    celdas += [f"{np.median([float(r['mse_hueco']) for r in sel]):.1f}",
                               f"{np.median([float(r['tiempo_s']) for r in sel]):.2f}",
                               f"{np.median([float(r['iteraciones']) for r in sel]):.0f}"]
                else:
                    celdas += ["-", "-", "-"]
            lineas.append(f"| {v} | " + " | ".join(celdas) + " |")
        lineas.append("")
    with open(os.path.join(carpeta_salida, "estudio.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lineas))

    # gráficas: una por estudio, una línea por método
    for estudio in estudios:
        figura, eje = plt.subplots(figsize=(6.5, 3.6))
        for m, filas in datos.items():
            sel = [r for r in filas if r["estudio"] == estudio]
            if not sel:
                continue                # este método no tiene este estudio
            valores = list(dict.fromkeys(r["valor"] for r in sel))
            y = [np.median([float(r["mse_relativo" if "contraste" in estudio else "mse_hueco"]) for r in sel if r["valor"] == v]) for v in valores]
            eje.plot(range(len(valores)), y, marker="o", label=m)
        eje.set_xticks(range(len(valores)))
        eje.set_xticklabels(valores, fontsize=8)
        eje.set_xlabel({"tamaño": "lado del hueco (px)", "forma": "forma de la máscara"}.get(
            estudio, estudio.replace("propio: ", "") if estudio.startswith("propio") else "contraste (niveles de gris)"))
        eje.set_ylabel("MSE relativo (MSE / contraste²)" if "contraste" in estudio else "MSE del hueco (mediana)")
        eje.set_title(estudio, fontsize=10)
        eje.grid(alpha=0.3)
        eje.legend(fontsize=8)
        figura.tight_layout()
        nombre = estudio.replace(" ", "_").replace("(", "").replace(")", "").replace(":", "").replace("í", "i").replace("ñ", "n").replace("á", "a").replace("é", "e").replace("ó", "o")
        nombre = f"{m_sel}_{nombre}" if False else nombre
        figura.savefig(os.path.join(carpeta_salida, f"{nombre}.png"), dpi=110)
        plt.close(figura)


if __name__ == "__main__":
    a = argparse.ArgumentParser(description="Estudio de cada algoritmo: tamaño, forma y contraste")
    a.add_argument("--metodos", nargs="+", default=["media", "Bertalmio"], choices=list(escenarios.METODOS))
    a.add_argument("--salida", default="resultados/estudio_algoritmos")
    a.add_argument("--por-tipo", type=int, default=4, help="fotos de cada tipo (lisa, estructura, textura)")
    a.add_argument("--solo-resumen", action="store_true", help="no ejecuta nada: rehace tabla y gráficas con los CSV que haya")
    args = a.parse_args()
    if not args.solo_resumen:
        ejecutar(args.metodos, args.salida, args.por_tipo)
    resumen(args.salida, [m for m in escenarios.METODOS if os.path.exists(os.path.join(args.salida, f"{m}.csv"))])
