"""
Huecos grandes: ¿qué pasa cuando el hueco ocupa buena parte de la foto?

La hipótesis H1 del trabajo dice que la difusión funciona bien con huecos
pequeños y emborrona al crecer el hueco, y que los ejemplares mantienen mejor el
resultado en huecos grandes. Los experimentos anteriores llegan a 64 píxeles de
lado (un cuarto del ancho de la foto); aquí se sube a 96 y 128 (la mitad del
ancho), con un hueco cuadrado en el centro de cada foto.

Se usan las fotos más representativas de cada tipo (lisa, con estructura y con
textura; ver experimento_principal.py), los tres métodos y los lados 64, 96 y 128.
Se guarda una fila por foto, tamaño y método, un resumen y una gráfica.

    python src/huecos_grandes.py --por-tipo 8
"""

import argparse
import csv
import os
import time

import numpy as np

import escenarios
import experimento_principal
import experimentos
import mascaras

LADOS = (64, 96, 128)
COLUMNAS = ["tipo_imagen", "imagen", "lado", "porcentaje_hueco", "metodo", "tiempo_s", "iteraciones",
            "mse_hueco", "psnr_hueco"]


def ya_hechos(ruta):
    if not os.path.exists(ruta):
        return set()
    with open(ruta, newline="", encoding="utf-8") as f:
        return {(r["imagen"], r["lado"], r["metodo"]) for r in csv.DictReader(f)}


def ejecutar(carpeta, ancho, por_tipo, ruta_csv, carpeta_figuras):
    os.makedirs(os.path.dirname(ruta_csv), exist_ok=True)
    os.makedirs(carpeta_figuras, exist_ok=True)
    clases = experimento_principal.clasificar(carpeta, ancho, por_tipo)
    hechos = ya_hechos(ruta_csv)
    nuevo = not os.path.exists(ruta_csv)
    total = sum(len(v) for v in clases.values()) * len(LADOS)
    n = 0
    inicio = time.perf_counter()
    with open(ruta_csv, "a", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUMNAS)
        if nuevo:
            escritor.writeheader()
        for tipo_imagen, lista in clases.items():
            for nombre, _, _ in lista:
                foto = experimentos.cargar_imagen(os.path.join(carpeta, nombre), ancho)
                alto, anc = foto.shape[:2]
                for lado in LADOS:
                    n += 1
                    if all((nombre, str(lado), m) in hechos for m in escenarios.METODOS):
                        continue
                    mascara = mascaras.mascara_cuadrada(foto.shape[:2], lado, (alto // 2, anc // 2))
                    danada, salida = escenarios.ejecutar_caso(foto, mascara)
                    for metodo, (_, t, it, med) in salida.items():
                        escritor.writerow({"tipo_imagen": tipo_imagen, "imagen": nombre, "lado": lado,
                                           "porcentaje_hueco": f"{mascaras.porcentaje_hueco(mascara):.1f}", "metodo": metodo,
                                           "tiempo_s": f"{t:.4f}", "iteraciones": it, "mse_hueco": f"{med['mse_hueco']:.2f}",
                                           "psnr_hueco": f"{med['psnr_hueco']:.2f}"})
                    f.flush()
                    print(f"[{n}/{total}] {tipo_imagen:10s} {nombre[:22]:22s} lado {lado:3d}  " +
                          "  ".join(f"{m} {s[3]['mse_hueco']:8.1f} ({s[1]:.1f}s)" for m, s in salida.items()), flush=True)
                    if lado == 128:
                        escenarios.figura(os.path.join(carpeta_figuras, f"{tipo_imagen}_{os.path.splitext(nombre)[0][:22]}_{lado}.png"),
                                          f"{tipo_imagen} · {nombre[:24]} · hueco {lado}×{lado}", foto, mascara, danada, salida)
    print(f"Terminado en {time.perf_counter() - inicio:.0f} s")


def resumen(carpeta_salida):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    with open(os.path.join(carpeta_salida, "huecos_grandes.csv"), newline="", encoding="utf-8") as f:
        filas = [r for r in csv.DictReader(f)]
    metodos = list(escenarios.METODOS)
    tipos = ["todas"] + list(dict.fromkeys(r["tipo_imagen"] for r in filas))

    def sel(tipo, lado, metodo):
        return [r for r in filas if r["metodo"] == metodo and r["lado"] == str(lado) and (tipo == "todas" or r["tipo_imagen"] == tipo)]

    lineas = ["# Huecos grandes", "", f"{len({r['imagen'] for r in filas})} fotos, hueco cuadrado centrado de 64, 96 y 128 píxeles. MSE del hueco (mediana); menor es mejor.", ""]
    for tipo in tipos:
        lineas += [f"### {tipo}", "", "| lado | % de la foto | " + " | ".join(f"MSE {m}" for m in metodos) + " | " + " | ".join(f"tiempo {m} (s)" for m in metodos) + " | gana (m / B / e) |",
                   "|---:|---:|" + "---:|" * 6 + "---|"]
        for lado in LADOS:
            casos = {}
            for r in filas:
                if r["lado"] == str(lado) and (tipo == "todas" or r["tipo_imagen"] == tipo):
                    casos.setdefault(r["imagen"], {})[r["metodo"]] = float(r["mse_hueco"])
            gana = [0, 0, 0]
            for c in casos.values():
                if len(c) == 3:
                    gana[min(range(3), key=lambda i: c[metodos[i]])] += 1
            pct = np.median([float(r["porcentaje_hueco"]) for r in sel(tipo, lado, "media")])
            lineas.append(f"| {lado} | {pct:.0f} | " + " | ".join(f"{np.median([float(r['mse_hueco']) for r in sel(tipo, lado, m)]):.0f}" for m in metodos) + " | " +
                          " | ".join(f"{np.median([float(r['tiempo_s']) for r in sel(tipo, lado, m)]):.1f}" for m in metodos) + " | " + " / ".join(map(str, gana)) + " |")
        lineas.append("")
    with open(os.path.join(carpeta_salida, "huecos_grandes.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lineas))

    figura, ejes = plt.subplots(1, 3, figsize=(13, 3.8))
    for eje, tipo in zip(ejes, tipos[1:]):
        for m in metodos:
            eje.plot(range(len(LADOS)), [np.median([float(r["mse_hueco"]) for r in sel(tipo, lado, m)]) for lado in LADOS], marker="o", label=m)
        eje.set_xticks(range(len(LADOS)))
        eje.set_xticklabels(LADOS)
        eje.set_xlabel("lado del hueco (px)")
        eje.set_title(tipo)
        eje.grid(alpha=0.3)
    ejes[0].set_ylabel("MSE del hueco (mediana)")
    ejes[0].legend(fontsize=8)
    figura.tight_layout()
    figura.savefig(os.path.join(carpeta_salida, "huecos_grandes.png"), dpi=110)
    plt.close(figura)


if __name__ == "__main__":
    a = argparse.ArgumentParser(description="Huecos grandes: 64, 96 y 128 píxeles")
    a.add_argument("--carpeta", default="images/originales")
    a.add_argument("--ancho", type=int, default=256)
    a.add_argument("--por-tipo", type=int, default=8)
    a.add_argument("--salida", default="resultados/huecos_grandes")
    a.add_argument("--solo-resumen", action="store_true")
    args = a.parse_args()
    if not args.solo_resumen:
        ejecutar(args.carpeta, args.ancho, args.por_tipo, os.path.join(args.salida, "huecos_grandes.csv"), os.path.join(args.salida, "figuras"))
    resumen(args.salida)
