"""
Contraste de las hipótesis H1 a H4 con los datos de todos los experimentos.

Para cada hipótesis se calculan, a partir de los CSV de resultados, las cifras
que la confirman o la desmienten, con un contraste de signos exacto cuando se
comparan dos métodos sobre los mismos casos (se cuenta en cuántos casos uno tiene
menos error que otro, sin contar empates, y se da el valor p bilateral de una
binomial con p = 0,5).

    python src/hipotesis.py

Escribe resultados/hipotesis/hipotesis.md.
"""

import csv
import math
import os

import numpy as np

R = "resultados"


def leer(ruta):
    with open(ruta, newline="", encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if r.get("mse_hueco", "x") != ""]


def p_signos(a, b):
    """Contraste de signos exacto sobre pares (a_i, b_i): (veces a<b, veces a>b, p bilateral)."""
    menos = sum(x < y for x, y in zip(a, b))
    mas = sum(x > y for x, y in zip(a, b))
    n = menos + mas
    if n == 0:
        return 0, 0, 1.0
    k = min(menos, mas)
    p = min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)
    return menos, mas, p


def pares(filas, clave, m1, m2, campo="mse_hueco"):
    d = {}
    for r in filas:
        d.setdefault(clave(r), {})[r["metodo"]] = float(r[campo])
    d = {k: v for k, v in d.items() if m1 in v and m2 in v}
    return [v[m1] for v in d.values()], [v[m2] for v in d.values()]


def fmt_p(p):
    return "< 0,001" if p < 0.001 else f"{p:.3f}".replace(".", ",")


def pendiente(xs, ys):
    """Pendiente de log(y) frente a log(x): exponente k de y ∝ x^k."""
    return float(np.polyfit(np.log(xs), np.log(ys), 1)[0])


def main():
    L = ["# Contraste de las hipótesis H1 a H4", "",
         "Contraste de signos exacto (bilateral): «A < B» es en cuántos casos A tiene menos error que B. p < 0,05 se considera diferencia clara.", ""]

    # ------------------------------------------------------------------ H1
    g = leer(f"{R}/huecos_grandes/huecos_grandes.csv")
    L += ["## H1: los ejemplares mantienen mejor el resultado en huecos grandes", "",
          f"{len({r['imagen'] for r in g})} fotos, hueco cuadrado centrado.", "",
          "| lado | MSE mediano media | MSE mediano ejemplares | cociente ejemplares/media (mediana) | ejemplares < media | ejemplares > media | p |", "|---:|---:|---:|---:|---:|---:|---:|"]
    cocientes = []
    for lado in ("64", "96", "128"):
        sel = [r for r in g if r["lado"] == lado]
        e, m = pares(sel, lambda r: r["imagen"], "ejemplares", "media")
        menos, mas, p = p_signos(e, m)
        c = float(np.median(np.array(e) / np.array(m)))
        cocientes.append(c)
        L.append(f"| {lado} | {np.median(m):.0f} | {np.median(e):.0f} | {c:.2f} | {menos} | {mas} | {fmt_p(p)} |")
    L += ["", f"El cociente ejemplares/media va de {cocientes[0]:.2f} a {cocientes[-1]:.2f} al pasar de 64 a 128 píxeles: "
          + ("crece, es decir, los ejemplares empeoran respecto a la media cuando el hueco crece." if cocientes[-1] > cocientes[0]
             else "baja, es decir, los ejemplares mejoran respecto a la media cuando el hueco crece."), ""]
    # por tipo de foto en el hueco de 128
    L += ["| tipo de foto (hueco 128) | fotos | ejemplares < media | ejemplares > media | p |", "|---|---:|---:|---:|---:|"]
    for t in ("lisa", "estructura", "textura"):
        sel = [r for r in g if r["lado"] == "128" and r["tipo_imagen"] == t]
        e, m = pares(sel, lambda r: r["imagen"], "ejemplares", "media")
        menos, mas, p = p_signos(e, m)
        L.append(f"| {t} | {len(e)} | {menos} | {mas} | {fmt_p(p)} |")
    L.append("")

    # ------------------------------------------------------------------ H2
    L += ["## H2: tiempo de cálculo (difusión lenta, ejemplares rápidos)", "",
          "Exponente k de t ∝ (área del hueco)^k, ajustado con las medianas por tamaño de hueco (estudio de tamaño, 8 a 64 px, y huecos grandes, 64 a 128 px):", "",
          "| método | t con 64 px (s) | t con 128 px (s) | exponente k (8 a 128 px) |", "|---|---:|---:|---:|"]
    est = {m: leer(f"{R}/estudio_algoritmos/{m}.csv") for m in ("media", "Bertalmio", "ejemplares")}
    for m in ("media", "Bertalmio", "ejemplares"):
        pts = {}
        for r in est[m]:
            if r["estudio"] == "tamaño":
                pts.setdefault(int(r["valor"]), []).append(float(r["tiempo_s"]))
        for r in g:
            if r["metodo"] == m and int(r["lado"]) > 64:
                pts.setdefault(int(r["lado"]), []).append(float(r["tiempo_s"]))
        lados = sorted(pts)
        t = [float(np.median(pts[l])) for l in lados]
        k = pendiente([l * l for l in lados], t)
        t64 = float(np.median([float(r["tiempo_s"]) for r in g if r["metodo"] == m and r["lado"] == "64"]))
        t128 = float(np.median([float(r["tiempo_s"]) for r in g if r["metodo"] == m and r["lado"] == "128"]))
        L.append(f"| {m} | {t64:.1f} | {t128:.1f} | {k:.2f} |")
    cr = leer(f"{R}/cronometraje.csv") if os.path.exists(f"{R}/cronometraje.csv") else []
    L += ["", "Tiempo según el tamaño de la imagen (cronometraje B), si el archivo lo contiene:", ""]
    if cr and "ancho_imagen" in cr[0]:
        L += ["| método | tamaños de imagen (px de ancho) | tiempos (s) | exponente k (t ∝ ancho^k) |", "|---|---|---|---:|"]
        for m in ("media", "Bertalmio", "ejemplares"):
            pts = {}
            for r in cr:
                if r["experimento"] == "B" and r["metodo"] == m:
                    pts.setdefault(int(r["ancho_imagen"]), []).append(float(r["tiempo_medio_s"]))
            if len(pts) >= 2:
                a = sorted(pts)
                t = [float(np.median(pts[x])) for x in a]
                L.append(f"| {m} | {', '.join(map(str, a))} | {', '.join(f'{x:.2f}' for x in t)} | {pendiente(a, t):.2f} |")
    L.append("")

    # ------------------------------------------------------------------ H3
    ruta = f"{R}/hipotesis/curvatura.csv"
    if os.path.exists(ruta):
        c = leer(ruta)
        L += ["## H3: la difusión reconstruye mal los bordes curvos que cruzan el hueco", "",
              "Arco de radio R que cruza el hueco de 32 px (4 variantes por radio). MSE mediano y comparación por casos:", "",
              "| radio R | media | Bertalmio | ejemplares | Bertalmio < media (de 4) | p |", "|---:|---:|---:|---:|---:|---:|"]
        for r in ("2000", "200", "100", "50", "32", "20", "12"):
            sel = [x for x in c if x["valor"] == r]
            med = {m: np.median([float(x["mse_hueco"]) for x in sel if x["metodo"] == m]) for m in ("media", "Bertalmio", "ejemplares")}
            b, m_ = pares(sel, lambda x: x["variante"], "Bertalmio", "media")
            menos, mas, p = p_signos(b, m_)
            L.append(f"| {r} | {med['media']:.0f} | {med['Bertalmio']:.0f} | {med['ejemplares']:.0f} | {menos} | {fmt_p(p)} |")
        b, m_ = pares(c, lambda x: (x["valor"], x["variante"]), "Bertalmio", "media")
        menos, mas, p = p_signos(b, m_)
        L += ["", f"En conjunto (28 casos): Bertalmio < media en {menos}, Bertalmio > media en {mas}, p = {fmt_p(p)}.", ""]

    # ------------------------------------------------------------------ H4
    pr = leer(f"{R}/principal/principal.csv")
    L += ["## H4: ejemplares reconstruyen estructura y textura; la difusión, sobre todo estructura", "",
          "Fotos reales (experimento principal), contraste de signos sobre los casos foto × máscara:", "",
          "| tipo de foto | comparación | casos | A < B | A > B | p |", "|---|---|---:|---:|---:|---:|"]
    for t in ("lisa", "estructura", "textura"):
        sel = [r for r in pr if r["tipo_imagen"] == t]
        for a, b in (("Bertalmio", "media"), ("ejemplares", "media"), ("ejemplares", "Bertalmio")):
            x, y = pares(sel, lambda r: (r["imagen"], r["mascara"]), a, b)
            menos, mas, p = p_signos(x, y)
            L.append(f"| {t} | {a} (A) frente a {b} (B) | {len(x)} | {menos} | {mas} | {fmt_p(p)} |")
    rr = f"{R}/hipotesis/repeticion_ruido.csv"
    if os.path.exists(rr):
        d = leer(rr)
        L += ["", "Repetición exacta más ruido (MSE mediano; el cruce es el ruido a partir del cual la media supera a ejemplares):", "",
              "| patrón | ruido σ | media | Bertalmio | ejemplares |", "|---|---:|---:|---:|---:|"]
        for patron in ("rayas", "bloques"):
            for s in ("0", "5", "10", "20", "40", "80"):
                sel = [x for x in d if x["subtipo"] == patron and x["valor"] == s]
                med = {m: np.median([float(x["mse_hueco"]) for x in sel if x["metodo"] == m]) for m in ("media", "Bertalmio", "ejemplares")}
                L.append(f"| {patron} | {s} | {med['media']:.0f} | {med['Bertalmio']:.0f} | {med['ejemplares']:.0f} |")
    os.makedirs(f"{R}/hipotesis", exist_ok=True)
    with open(f"{R}/hipotesis/hipotesis.md", "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
