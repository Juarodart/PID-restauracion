"""
Script de experimentos de la Fase 3.

Recorre un conjunto de imágenes, un conjunto de máscaras y los tres métodos
(la media de los cuatro vecinos, Bertalmio y ejemplares) y guarda, para cada
combinación, el tiempo y el error en un archivo CSV.

Todos los métodos se llaman igual: metodo(imagen_dañada, mascara) devuelve
(restaurada, iteraciones). Para cada imagen se generan las mismas máscaras con
una semilla fija, de modo que los tres métodos ven exactamente el mismo problema
y los experimentos se pueden repetir.

Uso desde la carpeta del repositorio:

    python src/experimentos.py --imagenes 20 --ancho 256 --salida resultados/experimentos.csv

El script puede interrumpirse y volver a lanzarse: las combinaciones que ya
están en el CSV se saltan.

Se usa NumPy, OpenCV (solo para leer y reducir las imágenes) y la biblioteca
estándar de Python.
"""

import argparse
import csv
import functools
import os
import random
import sys
import time

import cv2 as cv
import numpy as np

import bertalmio
import difusion
import ejemplares
import mascaras
import metricas

METODOS = {
    "media": difusion.difusion_simple,
    "Bertalmio": bertalmio.bertalmio,
    "ejemplares": ejemplares.inpainting_ejemplares,
}

def obtener_metodo(nombre):
    """
    Devuelve la función de un método a partir de su nombre. Además de los tres
    métodos, acepta «Bertalmio_cN» (por ejemplo «Bertalmio_c100»): Bertalmio
    con un máximo de N ciclos, y «media_itN»: la media con exactamente N
    iteraciones, para estudiar cuántas hacen falta.
    """
    if nombre in METODOS:
        return METODOS[nombre]
    if nombre.startswith("media_it") and nombre[len("media_it"):].isdigit():
        # la media con exactamente N iteraciones (tolerancia 0, para que no pare antes)
        return functools.partial(difusion.difusion_simple, iteraciones=int(nombre[len("media_it"):]), tolerancia=0)
    if nombre.startswith("Bertalmio_c") and nombre[len("Bertalmio_c"):].isdigit():
        return functools.partial(bertalmio.bertalmio, ciclos=int(nombre[len("Bertalmio_c"):]))
    raise ValueError(f"método desconocido: {nombre}")


COLUMNAS = ["imagen", "ancho", "alto", "mascara", "tipo", "pixeles_hueco", "porcentaje_hueco",
            "metodo", "tiempo_s", "iteraciones", "mse_hueco", "psnr_hueco", "mse_imagen", "psnr_imagen", "error"]


def lista_imagenes(carpeta, cantidad, semilla=42):
    """
    Elige `cantidad` imágenes de la carpeta, al azar pero siempre las mismas
    (la semilla fija la elección). Si cantidad es None, devuelve todas.
    """
    todas = sorted(f for f in os.listdir(carpeta) if f.lower().endswith((".jpg", ".jpeg", ".png")))
    if cantidad is None or cantidad >= len(todas):
        return todas
    return sorted(random.Random(semilla).sample(todas, cantidad))


def cargar_imagen(ruta, ancho):
    """Lee una imagen en RGB y la reduce al ancho indicado (mantiene la proporción)."""
    imagen = cv.cvtColor(cv.imread(ruta), cv.COLOR_BGR2RGB)
    escala = ancho / imagen.shape[1]
    return cv.resize(imagen, (ancho, round(imagen.shape[0] * escala)), interpolation=cv.INTER_AREA)


def definir_mascaras(forma, semilla):
    """
    Máscaras de una imagen: devuelve una lista de (nombre, tipo, máscara).

    Los tamaños son relativos al ancho de la imagen, para que el experimento
    sea comparable si se cambia el tamaño al que se reducen las fotos. Los
    centros de las formas se eligen al azar con la semilla, dentro de la imagen
    y alejados del borde, para que los huecos caigan sobre contenido distinto.
    """
    alto, ancho = forma
    azar = random.Random(semilla)

    def centro(margen):
        return (azar.randint(margen, alto - margen), azar.randint(margen, ancho - margen))

    lista = []
    for fraccion in (1 / 16, 1 / 8, 1 / 4):
        lado = round(ancho * fraccion)
        lista.append((f"cuadrado_{lado}", "cuadrado", mascaras.mascara_cuadrada(forma, lado, centro(lado))))
    for fraccion in (1 / 16, 1 / 8):
        radio = round(ancho * fraccion)
        lista.append((f"circulo_{radio}", "circulo", mascaras.mascara_circular(forma, radio, centro(radio + 1))))
    # arañazo: un segmento entre dos puntos al azar, fino
    inicio, fin = (azar.randint(0, alto - 1), azar.randint(0, ancho // 3)), (azar.randint(0, alto - 1), azar.randint(2 * ancho // 3, ancho - 1))
    lista.append(("aranazo_3", "aranazo", mascaras.mascara_aranazo(forma, inicio, fin, 3)))
    lista.append(("motas", "motas", mascaras.mascara_motas(forma, 10, max(2, ancho // 85), semilla=semilla)))
    tamano = round(ancho / 5)
    lista.append((f"irregular_{tamano}", "irregular", mascaras.mascara_irregular(forma, tamano, centro(tamano), semilla=semilla)))
    return lista


def quitar_metodos(ruta_csv, metodos):
    """
    Borra del CSV las filas de los métodos indicados, para poder repetirlos
    (por ejemplo, si cambia el código de un método). Devuelve cuántas filas quita.
    """
    if not os.path.exists(ruta_csv):
        return 0
    with open(ruta_csv, newline="", encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
        campos = list(filas[0]) if filas else COLUMNAS
    quedan = [fila for fila in filas if fila["metodo"] not in metodos]
    with open(ruta_csv, "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(quedan)
    return len(filas) - len(quedan)


def ya_hechos(ruta_csv):
    """Combinaciones (imagen, mascara, metodo) que ya están en el CSV."""
    hechos = set()
    if os.path.exists(ruta_csv):
        with open(ruta_csv, newline="", encoding="utf-8") as f:
            for fila in csv.DictReader(f):
                hechos.add((fila["imagen"], fila["mascara"], fila["metodo"]))
    return hechos


def ejecutar(carpeta_imagenes, cantidad, ancho, ruta_csv, repeticiones=1, semilla=42, metodos=None, guardar_en=None, rehacer=None):
    """
    Lanza el experimento completo y escribe una fila en el CSV por cada
    combinación de imagen, máscara y método.

    repeticiones: veces que se ejecuta cada método para medir el tiempo (se
                  guarda la media). El error se calcula con la última ejecución.
    guardar_en:   carpeta donde guardar la imagen restaurada de cada caso (PNG).
                  Si es None, no se guarda ninguna.
    """
    metodos = metodos or list(METODOS)
    if rehacer:
        print(f"Se borran {quitar_metodos(ruta_csv, rehacer)} filas de {', '.join(rehacer)} para repetirlas.")
    os.makedirs(os.path.dirname(ruta_csv) or ".", exist_ok=True)
    if guardar_en:
        os.makedirs(guardar_en, exist_ok=True)
    hechos = ya_hechos(ruta_csv)
    nuevo = not os.path.exists(ruta_csv)
    imagenes = lista_imagenes(carpeta_imagenes, cantidad, semilla)
    inicio_total = time.perf_counter()

    with open(ruta_csv, "a", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUMNAS)
        if nuevo:
            escritor.writeheader()
        for numero, nombre_imagen in enumerate(imagenes, start=1):
            foto = cargar_imagen(os.path.join(carpeta_imagenes, nombre_imagen), ancho)
            for nombre_mascara, tipo, mascara in definir_mascaras(foto.shape[:2], semilla):
                danada = mascaras.aplicar_mascara(foto, mascara)
                for metodo in metodos:
                    if (nombre_imagen, nombre_mascara, metodo) in hechos:
                        continue
                    fila = {"imagen": nombre_imagen, "ancho": foto.shape[1], "alto": foto.shape[0],
                            "mascara": nombre_mascara, "tipo": tipo, "pixeles_hueco": int(mascara.sum()),
                            "porcentaje_hueco": f"{mascaras.porcentaje_hueco(mascara):.2f}", "metodo": metodo,
                            "tiempo_s": "", "iteraciones": "", "mse_hueco": "", "psnr_hueco": "",
                            "mse_imagen": "", "psnr_imagen": "", "error": ""}
                    try:
                        (restaurada, iteraciones), media, _ = metricas.cronometrar(
                            obtener_metodo(metodo), danada, mascara, repeticiones=repeticiones)
                        medidas = metricas.evaluar(foto, restaurada, mascara)
                        fila.update({"tiempo_s": f"{media:.4f}", "iteraciones": iteraciones,
                                     "mse_hueco": f"{medidas['mse_hueco']:.2f}", "psnr_hueco": f"{medidas['psnr_hueco']:.2f}",
                                     "mse_imagen": f"{medidas['mse_imagen']:.3f}", "psnr_imagen": f"{medidas['psnr_imagen']:.2f}"})
                        if guardar_en:
                            nombre_png = f"{os.path.splitext(nombre_imagen)[0]}__{nombre_mascara}__{metodo}.png"
                            cv.imwrite(os.path.join(guardar_en, nombre_png), cv.cvtColor(restaurada, cv.COLOR_RGB2BGR))
                    except Exception as fallo:      # un fallo no debe parar todo el experimento
                        fila["error"] = f"{type(fallo).__name__}: {fallo}"
                    escritor.writerow(fila)
                    f.flush()
                    print(f"[{numero}/{len(imagenes)}] {nombre_imagen[:24]:24s} {nombre_mascara:14s} {metodo:10s} "
                          f"{fila['tiempo_s'] or '-':>8s} s  MSE hueco {fila['mse_hueco'] or '-':>8s} {fila['error']}", flush=True)
    print(f"Terminado en {time.perf_counter() - inicio_total:.1f} s. Resultados en {ruta_csv}")


if __name__ == "__main__":
    analizador = argparse.ArgumentParser(description="Experimentos de inpainting: media, Bertalmio y ejemplares")
    analizador.add_argument("--carpeta", default="images/originales", help="carpeta con las imágenes originales")
    analizador.add_argument("--imagenes", type=int, default=20, help="cuántas imágenes usar (se eligen al azar con la semilla)")
    analizador.add_argument("--ancho", type=int, default=256, help="ancho al que se reducen las imágenes")
    analizador.add_argument("--salida", default="resultados/experimentos.csv", help="archivo CSV de resultados")
    analizador.add_argument("--repeticiones", type=int, default=1, help="repeticiones para medir el tiempo")
    analizador.add_argument("--semilla", type=int, default=42)
    analizador.add_argument("--metodos", nargs="+", choices=list(METODOS), help="métodos a ejecutar (por defecto, los tres)")
    analizador.add_argument("--rehacer", nargs="+", choices=list(METODOS), help="borra del CSV las filas de estos métodos y las vuelve a calcular")
    analizador.add_argument("--ciclos", type=int, nargs="+", help="en vez de los métodos, Bertalmio con estos máximos de ciclos")
    analizador.add_argument("--iteraciones", type=int, nargs="+", help="en vez de los métodos, la media con exactamente estas iteraciones")
    analizador.add_argument("--guardar", default=None, help="carpeta donde guardar las imágenes restauradas")
    argumentos = analizador.parse_args()
    if argumentos.iteraciones:
        metodos = [f"media_it{n}" for n in argumentos.iteraciones]
    else:
        metodos = [f"Bertalmio_c{n}" for n in argumentos.ciclos] if argumentos.ciclos else argumentos.metodos
    ejecutar(argumentos.carpeta, argumentos.imagenes, argumentos.ancho, argumentos.salida,
             argumentos.repeticiones, argumentos.semilla, metodos, argumentos.guardar, argumentos.rehacer)
