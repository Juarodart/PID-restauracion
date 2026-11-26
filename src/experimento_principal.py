"""
Experimento principal: los tres métodos sobre fotos clasificadas por tipo.

En vez de elegir fotos al azar (que podrían favorecer sin querer a un método),
se clasifican las 100 fotos originales según lo que contienen y se eligen las
más representativas de cada tipo:

  lisa        poco detalle: energía del gradiente baja (cielos, paredes, agua).
  estructura  líneas y bordes largos en una dirección dominante: energía media o
              alta y coherencia alta (horizontes, montañas, edificios).
  textura     mucho detalle en todas direcciones: energía alta y coherencia baja
              (hojas, césped, rocas, multitudes).

La energía y la coherencia salen del tensor de estructura de la foto en gris
(comparacion_variada.caracteristicas_global). Los umbrales son percentiles de las
100 fotos, de modo que cada tipo tiene fotos suficientes: lisa, energía por debajo
del percentil 33; estructura, energía desde el percentil 33 y coherencia desde el
percentil 67; textura, energía desde el percentil 67 y coherencia hasta el
percentil 33. De cada tipo se toman las N más extremas.

A cada foto se le aplican las 8 máscaras del experimento principal (cuadrados de
16, 32 y 64 píxeles, círculos, arañazo, motas y una forma irregular) y los tres
métodos. Se guarda una fila por foto, máscara y método, y una figura de algunos
casos. El script se puede interrumpir y reanudar.

Uso desde la carpeta del repositorio:

    python src/experimento_principal.py --por-tipo 10
"""

import argparse
import csv
import os
import time

import numpy as np

import comparacion_variada as cvar
import escenarios
import experimentos
import mascaras
import metricas

COLUMNAS = ["tipo_imagen", "imagen", "energia", "coherencia", "mascara", "tipo", "pixeles_hueco", "metodo",
            "tiempo_s", "iteraciones", "mse_hueco", "psnr_hueco", "mse_imagen", "psnr_imagen"]


def clasificar(carpeta, ancho, por_tipo):
    """Devuelve {tipo: [(imagen, energía, coherencia), ...]} con las más representativas de cada tipo."""
    medidas = []
    for nombre in experimentos.lista_imagenes(carpeta, None):
        foto = experimentos.cargar_imagen(os.path.join(carpeta, nombre), ancho)
        e, c = cvar.caracteristicas_global(foto)
        medidas.append((nombre, float(e), float(c)))
    e = np.array([m[1] for m in medidas])
    c = np.array([m[2] for m in medidas])
    e33, e67 = np.percentile(e, [33, 67])
    c33, c67 = np.percentile(c, [33, 67])
    tipos = {
        "lisa": ([m for m in medidas if m[1] < e33], lambda m: m[1]),
        "estructura": ([m for m in medidas if m[1] >= e33 and m[2] >= c67], lambda m: -m[2]),
        "textura": ([m for m in medidas if m[1] >= e67 and m[2] <= c33], lambda m: -m[1] * (1 - m[2])),
    }
    return {t: sorted(lista, key=orden)[:por_tipo] for t, (lista, orden) in tipos.items()}


def ya_hechos(ruta):
    if not os.path.exists(ruta):
        return set()
    with open(ruta, newline="", encoding="utf-8") as f:
        return {(r["imagen"], r["mascara"], r["metodo"]) for r in csv.DictReader(f)}


def ejecutar(carpeta, ancho, por_tipo, ruta_csv, carpeta_figuras, figuras_mascaras=("cuadrado_32", "aranazo_3")):
    os.makedirs(os.path.dirname(ruta_csv), exist_ok=True)
    os.makedirs(carpeta_figuras, exist_ok=True)
    clases = clasificar(carpeta, ancho, por_tipo)
    for t, lista in clases.items():
        print(f"{t}: {len(lista)} fotos")
    hechos = ya_hechos(ruta_csv)
    nuevo = not os.path.exists(ruta_csv)
    total = sum(len(v) for v in clases.values())
    n = 0
    inicio = time.perf_counter()
    with open(ruta_csv, "a", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUMNAS)
        if nuevo:
            escritor.writeheader()
        for tipo_imagen, lista in clases.items():
            for nombre, energia, coherencia in lista:
                n += 1
                foto = experimentos.cargar_imagen(os.path.join(carpeta, nombre), ancho)
                for nombre_mascara, tipo, mascara in experimentos.definir_mascaras(foto.shape[:2], 42):
                    if all((nombre, nombre_mascara, m) in hechos for m in escenarios.METODOS):
                        continue
                    danada, salida = escenarios.ejecutar_caso(foto, mascara)
                    for metodo, (_, t, it, med) in salida.items():
                        escritor.writerow({
                            "tipo_imagen": tipo_imagen, "imagen": nombre, "energia": f"{energia:.1f}", "coherencia": f"{coherencia:.3f}",
                            "mascara": nombre_mascara, "tipo": tipo, "pixeles_hueco": int(mascara.sum()), "metodo": metodo,
                            "tiempo_s": f"{t:.4f}", "iteraciones": it, "mse_hueco": f"{med['mse_hueco']:.2f}",
                            "psnr_hueco": f"{med['psnr_hueco']:.2f}", "mse_imagen": f"{med['mse_imagen']:.3f}",
                            "psnr_imagen": f"{med['psnr_imagen']:.2f}"})
                    f.flush()
                    print(f"[{n}/{total}] {tipo_imagen:10s} {nombre[:22]:22s} {nombre_mascara:13s} " +
                          "  ".join(f"{m} {s[3]['mse_hueco']:8.1f}" for m, s in salida.items()), flush=True)
                    if nombre_mascara in figuras_mascaras:
                        escenarios.figura(os.path.join(carpeta_figuras, f"{tipo_imagen}_{os.path.splitext(nombre)[0][:22]}_{nombre_mascara}.png"),
                                          f"{tipo_imagen} · {nombre[:24]} · {nombre_mascara}", foto, mascara, danada, salida)
    print(f"Terminado en {time.perf_counter() - inicio:.0f} s. Resultados en {ruta_csv}")


if __name__ == "__main__":
    a = argparse.ArgumentParser(description="Experimento principal: tres métodos sobre fotos clasificadas por tipo")
    a.add_argument("--carpeta", default="images/originales")
    a.add_argument("--ancho", type=int, default=256)
    a.add_argument("--por-tipo", type=int, default=10)
    a.add_argument("--csv", default="resultados/principal/principal.csv")
    a.add_argument("--figuras", default="resultados/principal/figuras")
    args = a.parse_args()
    ejecutar(args.carpeta, args.ancho, args.por_tipo, args.csv, args.figuras)
