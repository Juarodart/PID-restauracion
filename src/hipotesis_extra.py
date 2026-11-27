"""
Experimentos que faltaban para contrastar las hipótesis H3 y H4.

H3  «La difusión reconstruye mal los bordes curvos que cruzan el hueco.»
    Hasta ahora solo se había probado una cresta suave. Aquí un borde con forma
    de arco de circunferencia cruza el centro del hueco (de 32 píxeles), con radios
    de curvatura de 2000 (casi recto) a 12 píxeles (más cerrado que el hueco).

H4  «Los ejemplares reconstruyen estructura y textura; la difusión, sobre todo
    estructura.»
    Los ejemplares solo ganaban con repetición exacta (error 0). Aquí se parte de
    una repetición exacta (rayas o bloques) y se le añade ruido gaussiano cada vez
    mayor (desviación típica de 0 a 80 niveles de gris): así se ve hasta dónde
    sigue ganando copiar y cuándo pasa a ganar el promedio.

Los tres métodos reciben el mismo problema. Se guarda un CSV por experimento, una
tabla en Markdown, una gráfica y una figura de ejemplo.

    python src/hipotesis_extra.py
"""

import argparse
import csv
import os
import time

import numpy as np

import escenarios
import mascaras

N = escenarios.N
RADIOS = (2000, 200, 100, 50, 32, 20, 12)
RUIDOS = (0, 5, 10, 20, 40, 80)
VARIANTES = 4
COLUMNAS = ["experimento", "subtipo", "valor", "variante", "metodo", "tiempo_s", "iteraciones", "mse_hueco", "psnr_hueco"]


def escena_curva(radio, variante):
    """Disco oscuro sobre fondo claro; su borde (arco de radio `radio`) pasa por el centro de la imagen."""
    angulo = (0.3, 1.2, 2.4, 4.0)[variante]
    cy, cx = N / 2 + radio * np.sin(angulo), N / 2 + radio * np.cos(angulo)
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    d = radio - np.hypot(yy - cy, xx - cx)               # >0 dentro del disco
    img = 190 - 130 * np.clip(d / 2 + 0.5, 0, 1)         # transición de ~2 píxeles
    return np.repeat(np.rint(img)[..., None], 3, axis=2).astype(np.uint8)


def escena_ruido(patron, sigma, variante):
    """Repetición exacta (rayas o bloques) más ruido gaussiano de desviación `sigma`."""
    azar = np.random.RandomState(500 + variante)
    verdes = np.array([[40, 110, 30], [70, 150, 50], [30, 90, 25], [95, 165, 60], [55, 125, 40]], np.float32)
    if patron == "bloques":
        baldosa = verdes[azar.randint(0, len(verdes), (14, 14))]
        img = np.tile(baldosa, (N // 14 + 2, N // 14 + 2, 1))[:N, :N]
    else:
        periodo = 8 + (variante % 2) * 2
        x = (np.arange(N) // (periodo // 2)) % 2
        fila = np.where(x[:, None] == 0, np.array([40, 100, 30]), np.array([110, 175, 70])).astype(np.float32)
        img = np.repeat(fila[None], N, axis=0)
    img = img + azar.normal(0, sigma, img.shape) if sigma else img
    return np.clip(np.rint(img), 0, 255).astype(np.uint8)


def ejecutar(carpeta):
    os.makedirs(os.path.join(carpeta, "figuras"), exist_ok=True)
    mascara = mascaras.mascara_cuadrada((N, N), 32, (N // 2, N // 2))
    filas = []
    inicio = time.perf_counter()
    casos = [("curvatura", "arco", r, v, escena_curva(r, v)) for r in RADIOS for v in range(VARIANTES)]
    casos += [("repeticion_ruido", p, s, v, escena_ruido(p, s, v)) for p in ("rayas", "bloques") for s in RUIDOS for v in range(VARIANTES)]
    for n, (exper, subtipo, valor, v, foto) in enumerate(casos, start=1):
        danada, salida = escenarios.ejecutar_caso(foto, mascara)
        for metodo, (_, t, it, med) in salida.items():
            filas.append({"experimento": exper, "subtipo": subtipo, "valor": valor, "variante": v, "metodo": metodo,
                          "tiempo_s": f"{t:.4f}", "iteraciones": it, "mse_hueco": f"{med['mse_hueco']:.2f}",
                          "psnr_hueco": f"{med['psnr_hueco']:.2f}"})
        print(f"[{n}/{len(casos)}] {exper:17s} {subtipo:8s} {str(valor):5s} v{v}  " +
              "  ".join(f"{m} {s[3]['mse_hueco']:9.1f}" for m, s in salida.items()), flush=True)
        if v == 0 and ((exper == "curvatura" and valor in (2000, 32, 12)) or (exper == "repeticion_ruido" and valor in (0, 20, 80))):
            escenarios.figura(os.path.join(carpeta, "figuras", f"{exper}_{subtipo}_{valor}.png"),
                              f"{exper} · {subtipo} · {valor}", foto, mascara, danada, salida)
    for exper in ("curvatura", "repeticion_ruido"):
        sub = [f for f in filas if f["experimento"] == exper]
        with open(os.path.join(carpeta, f"{exper}.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=COLUMNAS)
            w.writeheader()
            w.writerows(sub)
    print(f"Terminado en {time.perf_counter() - inicio:.0f} s")
    return filas


def resumen(carpeta):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    metodos = list(escenarios.METODOS)
    lineas = ["# Experimentos extra para las hipótesis H3 y H4", "", "MSE mediano del hueco (menor es mejor), 4 variantes por fila.", ""]
    datos = {}
    for exper in ("curvatura", "repeticion_ruido"):
        with open(os.path.join(carpeta, f"{exper}.csv"), newline="", encoding="utf-8") as f:
            datos[exper] = list(csv.DictReader(f))

    def med(exper, subtipo, valor, metodo):
        return float(np.median([float(r["mse_hueco"]) for r in datos[exper]
                                if r["subtipo"] == subtipo and r["valor"] == str(valor) and r["metodo"] == metodo]))

    lineas += ["## H3: borde curvo (arco de radio R que cruza el hueco de 32 px)", "", "| radio R (px) | " + " | ".join(metodos) + " |", "|---:|" + "---:|" * 3]
    for r in RADIOS:
        lineas.append(f"| {r} | " + " | ".join(f"{med('curvatura', 'arco', r, m):.0f}" for m in metodos) + " |")
    for patron in ("rayas", "bloques"):
        lineas += ["", f"## H4: repetición exacta ({patron}) más ruido gaussiano", "", "| ruido (σ) | " + " | ".join(metodos) + " |", "|---:|" + "---:|" * 3]
        for s in RUIDOS:
            lineas.append(f"| {s} | " + " | ".join(f"{med('repeticion_ruido', patron, s, m):.0f}" for m in metodos) + " |")
    with open(os.path.join(carpeta, "hipotesis_extra.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lineas) + "\n")

    figura, ejes = plt.subplots(1, 3, figsize=(13, 3.8))
    for m in metodos:
        ejes[0].plot(range(len(RADIOS)), [med("curvatura", "arco", r, m) for r in RADIOS], marker="o", label=m)
    ejes[0].set_xticks(range(len(RADIOS)))
    ejes[0].set_xticklabels([str(r) for r in RADIOS])
    ejes[0].set_xlabel("radio de curvatura (px)")
    ejes[0].set_ylabel("MSE del hueco (mediana)")
    ejes[0].set_title("Borde curvo (H3)")
    for eje, patron in zip(ejes[1:], ("rayas", "bloques")):
        for m in metodos:
            eje.plot(range(len(RUIDOS)), [med("repeticion_ruido", patron, s, m) for s in RUIDOS], marker="o", label=m)
        eje.set_xticks(range(len(RUIDOS)))
        eje.set_xticklabels([str(s) for s in RUIDOS])
        eje.set_xlabel("ruido añadido (σ)")
        eje.set_title(f"Repetición con ruido: {patron} (H4)")
        eje.set_yscale("symlog", linthresh=10)
    for eje in ejes:
        eje.grid(alpha=0.3)
    ejes[0].legend(fontsize=8)
    figura.tight_layout()
    figura.savefig(os.path.join(carpeta, "hipotesis_extra.png"), dpi=110)
    plt.close(figura)


if __name__ == "__main__":
    a = argparse.ArgumentParser(description="Experimentos extra para H3 y H4")
    a.add_argument("--salida", default="resultados/hipotesis")
    a.add_argument("--solo-resumen", action="store_true")
    args = a.parse_args()
    if not args.solo_resumen:
        ejecutar(args.salida)
    resumen(args.salida)
