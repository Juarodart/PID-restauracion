"""
Resumen del experimento principal (resultados/principal/principal.csv):
tablas por tipo de foto y por tipo de máscara, y una gráfica.

    python src/resumen_principal.py
"""

import csv
import os
import sys

import numpy as np

METODOS = ("media", "Bertalmio", "ejemplares")


def leer(ruta):
    with open(ruta, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def agrupar(filas, clave):
    """{grupo: {caso: {método: fila}}} con caso = (imagen, máscara)."""
    grupos = {}
    for r in filas:
        grupos.setdefault(clave(r), {}).setdefault((r["imagen"], r["mascara"]), {})[r["metodo"]] = r
    return grupos


def tabla(titulo, filas, clave, nombre_clave):
    lineas = [f"### {titulo}", "", f"| {nombre_clave} | casos | " + " | ".join(f"MSE mediano {m}" for m in METODOS) + " | " +
              " | ".join(f"tiempo mediano {m} (s)" for m in METODOS) + " | gana (media / Bertalmio / ejemplares) |",
              "|---|---:|" + "---:|" * 6 + "---|"]
    for grupo, casos in agrupar(filas, clave).items():
        casos = {k: v for k, v in casos.items() if all(m in v for m in METODOS)}
        mse = {m: np.median([float(c[m]["mse_hueco"]) for c in casos.values()]) for m in METODOS}
        tiempo = {m: np.median([float(c[m]["tiempo_s"]) for c in casos.values()]) for m in METODOS}
        gana = {m: 0 for m in METODOS}
        for c in casos.values():
            gana[min(METODOS, key=lambda m: float(c[m]["mse_hueco"]))] += 1
        lineas.append(f"| {grupo} | {len(casos)} | " + " | ".join(f"{mse[m]:.1f}" for m in METODOS) + " | " +
                      " | ".join(f"{tiempo[m]:.2f}" for m in METODOS) + " | " + " / ".join(str(gana[m]) for m in METODOS) + " |")
    return "\n".join(lineas) + "\n"


def grafica(filas, ruta):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    tipos = list(dict.fromkeys(r["tipo_imagen"] for r in filas))
    figura, ejes = plt.subplots(1, 2, figsize=(11, 3.8))
    ancho = 0.27
    for k, m in enumerate(METODOS):
        for eje, campo, etiqueta in ((ejes[0], "mse_hueco", "MSE del hueco (mediana)"), (ejes[1], "tiempo_s", "tiempo (s, mediana)")):
            valores = [np.median([float(r[campo]) for r in filas if r["tipo_imagen"] == t and r["metodo"] == m]) for t in tipos]
            eje.bar(np.arange(len(tipos)) + (k - 1) * ancho, valores, ancho, label=m)
            eje.set_xticks(range(len(tipos)))
            eje.set_xticklabels(tipos)
            eje.set_ylabel(etiqueta)
            eje.grid(axis="y", alpha=0.3)
    ejes[0].legend(fontsize=8)
    ejes[1].set_yscale("log")
    figura.tight_layout()
    figura.savefig(ruta, dpi=110)
    plt.close(figura)


if __name__ == "__main__":
    carpeta = sys.argv[1] if len(sys.argv) > 1 else "resultados/principal"
    filas = [r for r in leer(os.path.join(carpeta, "principal.csv")) if r["mse_hueco"]]
    fotos = len({r["imagen"] for r in filas})
    texto = ["# Experimento principal: los tres métodos sobre fotos clasificadas por tipo", "",
             f"{fotos} fotos ({len(filas)} ejecuciones), 8 máscaras por foto. MSE sobre el hueco: menor es mejor.", "",
             tabla("Por tipo de foto", filas, lambda r: r["tipo_imagen"], "tipo de foto"),
             tabla("Por tipo de máscara", filas, lambda r: r["tipo"], "máscara"),
             tabla("Por tipo de foto y de máscara", filas, lambda r: f"{r['tipo_imagen']} · {r['tipo']}", "foto · máscara")]
    with open(os.path.join(carpeta, "principal.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(texto))
    grafica(filas, os.path.join(carpeta, "principal_por_tipo.png"))
    print("\n".join(texto[:8]))
