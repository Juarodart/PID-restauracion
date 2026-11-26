"""
Verificación de los experimentos: vuelve a ejecutarlos delante de quien lo lance
y deja un registro real de lo que ha pasado.

Para cada imagen elegida genera sus máscaras (cuadrados, círculos, arañazo,
motas e irregular, con la misma semilla que el experimento principal), aplica
los tres métodos, mide el tiempo y el error en el momento, y guarda:

  resultados/verificacion/<fecha>/registro.csv   una fila por imagen, máscara y método
  resultados/verificacion/<fecha>/registro.md    la misma tabla en Markdown, con el equipo y las versiones
  resultados/verificacion/<fecha>/figuras/*.png  original, máscara, dañada y resultados de cada método

Además compara cada fila con la del experimento principal (resultados/experimentos.csv):
el error debe coincidir (los métodos son deterministas) y el tiempo, parecerse.

Uso desde la carpeta del repositorio:

    python src/verificar.py --imagenes 3            # unos minutos
    python src/verificar.py --imagenes 20           # repite todo el experimento principal
"""

import argparse
import csv
import datetime
import os
import platform
import sys
import time

import cv2 as cv
import numpy as np

import experimentos
import mascaras
import metricas


def leer_experimento(ruta_csv):
    """Filas del experimento principal, por (imagen, máscara, método)."""
    if not os.path.exists(ruta_csv):
        return {}
    with open(ruta_csv, newline="", encoding="utf-8") as f:
        return {(fila["imagen"], fila["mascara"], fila["metodo"]): fila for fila in csv.DictReader(f)}


def guardar_figura(ruta, foto, mascara, danada, resultados, nombre):
    """Una fila de imágenes: original, máscara, dañada y la restauración de cada método."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    paneles = [("original", foto), ("máscara", mascara), ("dañada", danada)] + resultados
    figura, ejes = plt.subplots(1, len(paneles), figsize=(3 * len(paneles), 3.3))
    for eje, (titulo, imagen) in zip(ejes, paneles):
        eje.imshow(imagen, cmap="gray" if imagen.ndim == 2 else None)
        eje.set_title(titulo, fontsize=8)
        eje.axis("off")
    figura.suptitle(nombre, fontsize=9)
    figura.tight_layout()
    figura.savefig(ruta, dpi=90)
    plt.close(figura)


def verificar(carpeta_imagenes, cantidad, ancho, carpeta_salida, semilla=42, metodos=None, referencia="resultados/experimentos.csv"):
    metodos = metodos or list(experimentos.METODOS)
    sello = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
    destino = os.path.join(carpeta_salida, sello)
    os.makedirs(os.path.join(destino, "figuras"), exist_ok=True)
    antes = leer_experimento(referencia)
    # las 20 del experimento principal (misma semilla) y de ahí, las primeras `cantidad`
    imagenes = experimentos.lista_imagenes(carpeta_imagenes, 20, semilla)[:cantidad]
    columnas = ["imagen", "mascara", "tipo", "pixeles_hueco", "metodo", "tiempo_s", "iteraciones",
                "mse_hueco", "psnr_hueco", "mse_imagen", "psnr_imagen",
                "mse_hueco_experimento", "mismo_error", "tiempo_experimento_s"]
    filas = []
    inicio = time.perf_counter()

    for n, nombre in enumerate(imagenes, start=1):
        foto = experimentos.cargar_imagen(os.path.join(carpeta_imagenes, nombre), ancho)
        for nombre_mascara, tipo, mascara in experimentos.definir_mascaras(foto.shape[:2], semilla):
            danada = mascaras.aplicar_mascara(foto, mascara)
            restauradas = []
            for metodo in metodos:
                (restaurada, iteraciones), tiempo, _ = metricas.cronometrar(
                    experimentos.obtener_metodo(metodo), danada, mascara, repeticiones=1)
                medidas = metricas.evaluar(foto, restaurada, mascara)
                previo = antes.get((nombre, nombre_mascara, metodo))
                mse_previo = float(previo["mse_hueco"]) if previo and previo["mse_hueco"] else None
                filas.append({
                    "imagen": nombre, "mascara": nombre_mascara, "tipo": tipo, "pixeles_hueco": int(mascara.sum()),
                    "metodo": metodo, "tiempo_s": f"{tiempo:.4f}", "iteraciones": iteraciones,
                    "mse_hueco": f"{medidas['mse_hueco']:.2f}", "psnr_hueco": f"{medidas['psnr_hueco']:.2f}",
                    "mse_imagen": f"{medidas['mse_imagen']:.3f}", "psnr_imagen": f"{medidas['psnr_imagen']:.2f}",
                    "mse_hueco_experimento": "" if mse_previo is None else f"{mse_previo:.2f}",
                    "mismo_error": "" if mse_previo is None else ("sí" if abs(mse_previo - medidas["mse_hueco"]) < 0.01 else "NO"),
                    "tiempo_experimento_s": "" if not previo else previo["tiempo_s"]})
                restauradas.append((f"{metodo}\nMSE {medidas['mse_hueco']:.0f}  {tiempo:.2f} s", restaurada))
                print(f"[{n}/{len(imagenes)}] {nombre[:24]:24s} {nombre_mascara:14s} {metodo:10s} "
                      f"{tiempo:7.3f} s  MSE hueco {medidas['mse_hueco']:8.2f}  {filas[-1]['mismo_error']}", flush=True)
            guardar_figura(os.path.join(destino, "figuras", f"{os.path.splitext(nombre)[0][:20]}__{nombre_mascara}.png"),
                           foto, mascara, danada, restauradas, f"{nombre} · {nombre_mascara}")

    total = time.perf_counter() - inicio
    with open(os.path.join(destino, "registro.csv"), "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=columnas)
        escritor.writeheader()
        escritor.writerows(filas)
    escribir_markdown(os.path.join(destino, "registro.md"), filas, sello, total, ancho, semilla, imagenes)
    print(f"\nVerificación terminada en {total:.1f} s. Registro en {destino}")
    return destino, filas


def escribir_markdown(ruta, filas, sello, total, ancho, semilla, imagenes):
    comparables = [f for f in filas if f["mismo_error"]]
    iguales = sum(f["mismo_error"] == "sí" for f in comparables)
    lineas = [f"# Registro de verificación de los experimentos ({sello})", "",
              "Generado automáticamente por `src/verificar.py`: cada fila es una ejecución real hecha en el momento.", "",
              f"- Equipo: {platform.platform()} · {platform.machine()} · Python {platform.python_version()}",
              f"- Bibliotecas: NumPy {np.__version__}, OpenCV {cv.__version__}",
              f"- Imágenes: {len(imagenes)} (ancho {ancho} px, semilla {semilla}); {len(filas)} ejecuciones en {total:.0f} s",
              f"- Coincidencia del error con el experimento principal: {iguales} de {len(comparables)} filas", "",
              "| Imagen | Máscara | Hueco (px) | Método | Tiempo (s) | Iter. | MSE hueco | PSNR hueco | MSE imagen | ¿Mismo error que el experimento? |",
              "|---|---|---:|---|---:|---:|---:|---:|---:|:---:|"]
    for f in filas:
        lineas.append(f"| {f['imagen'][:22]} | {f['mascara']} | {f['pixeles_hueco']} | {f['metodo']} | {f['tiempo_s']} | "
                      f"{f['iteraciones']} | {f['mse_hueco']} | {f['psnr_hueco']} | {f['mse_imagen']} | {f['mismo_error'] or '-'} |")
    lineas += ["", "Las figuras de cada caso (original, máscara, dañada y los tres resultados) están en `figuras/`."]
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas) + "\n")


if __name__ == "__main__":
    a = argparse.ArgumentParser(description="Repite los experimentos y deja un registro real")
    a.add_argument("--carpeta", default="images/originales")
    a.add_argument("--imagenes", type=int, default=3, help="cuántas imágenes (las mismas del experimento principal)")
    a.add_argument("--ancho", type=int, default=256)
    a.add_argument("--salida", default="resultados/verificacion")
    a.add_argument("--semilla", type=int, default=42)
    a.add_argument("--metodos", nargs="+", choices=list(experimentos.METODOS))
    verificar_args = a.parse_args()
    verificar(verificar_args.carpeta, verificar_args.imagenes, verificar_args.ancho, verificar_args.salida,
              verificar_args.semilla, verificar_args.metodos)
