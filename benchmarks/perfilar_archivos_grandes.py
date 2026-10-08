"""Benchmark de archivos grandes (.jsonl): streaming, buffering y paralelismo.

Experimentos:

1. Lectura de pedidos: carga completa en memoria vs streaming línea por línea.
2. Procesamiento de un archivo por lotes: secuencial vs paralelo, barriendo tamaños
   de lote para encontrar el punto de equilibrio.
3. Pedidos ya cargados en memoria (``grande.json``): secuencial vs pool de procesos.
   Justifica que el motor use el procesador secuencial por defecto.
4. Exportación del picking a CSV: buffer por defecto vs buffer explícito de 1 MB.

Metodología:

- **Tiempo y memoria se miden en corridas separadas.** ``tracemalloc`` hace mucho más
  lento al proceso que lo activa, pero no a los workers del pool. Medir el tiempo con
  ``tracemalloc`` activo favorece artificialmente a la versión paralela.
- Cada tiempo es la **mediana** de varias repeticiones, con el pool ya creado.
- La memoria es el pico del **proceso principal** según ``tracemalloc``. No incluye la
  memoria de los workers.

Uso::

    python -m benchmarks.perfilar_archivos_grandes
    python -m benchmarks.perfilar_archivos_grandes --pedidos 500000 --repeticiones 7

Genera ``docs/mediciones/archivos_grandes.md``.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import sys
import time
import tracemalloc
from collections.abc import Callable
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.datos.cargador import cargar_dataset_json  # noqa: E402
from src.datos.generador_archivos import generar_archivos_grandes_jsonl  # noqa: E402
from src.datos.procesador_lotes_paralelo import (  # noqa: E402
    procesar_pedidos_jsonl_paralelo,
    procesar_pedidos_jsonl_secuencial,
)
from src.datos.streaming import (  # noqa: E402
    exportar_picking_csv_con_buffer,
    leer_pedidos_streaming_jsonl,
    leer_productos_streaming_jsonl,
)
from src.inventario.catalogo_hash import CatalogoHash  # noqa: E402
from src.pedidos.agrupador import agrupar_pedidos_batch  # noqa: E402
from src.pedidos.gestor_pool import pool_archivos, pool_pedidos  # noqa: E402
from src.pedidos.procesador_concurrente import procesar_pedidos_concurrente  # noqa: E402
from src.pedidos.procesador_secuencial import procesar_pedidos_secuencial  # noqa: E402

GENERADOS_DIR = BASE_DIR / "data" / "generados"
DATASETS_DIR = BASE_DIR / "data" / "datasets"
RUTA_INFORME = BASE_DIR / "docs" / "mediciones" / "archivos_grandes.md"

BYTES_POR_MB = 1024.0 * 1024.0
BUFFER_EXPLICITO = 1024 * 1024
BUFFER_POR_DEFECTO = -1  # el buffer que elige Python (io.DEFAULT_BUFFER_SIZE)


def medir_tiempo_ms(funcion: Callable[[], Any], repeticiones: int) -> float:
    """Mediana del tiempo de ``funcion`` en milisegundos, sin ``tracemalloc``."""
    tiempos = []
    for _ in range(repeticiones):
        inicio = time.perf_counter()
        funcion()
        tiempos.append((time.perf_counter() - inicio) * 1000.0)
    return statistics.median(tiempos)


def medir_pico_mb(funcion: Callable[[], Any]) -> float:
    """Pico de memoria del proceso principal (MB) durante una ejecución."""
    tracemalloc.start()
    try:
        funcion()
        _, pico = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return pico / BYTES_POR_MB


def experimento_lectura(ruta_pedidos: Path, repeticiones: int) -> dict[str, float]:
    """Carga completa en memoria vs recorrido en streaming."""

    def carga_completa():
        with open(ruta_pedidos, encoding="utf-8") as archivo:
            return [json.loads(linea) for linea in archivo]

    def streaming():
        return sum(1 for _ in leer_pedidos_streaming_jsonl(ruta_pedidos))

    return {
        "completa_ms": medir_tiempo_ms(carga_completa, repeticiones),
        "completa_mb": medir_pico_mb(carga_completa),
        "streaming_ms": medir_tiempo_ms(streaming, repeticiones),
        "streaming_mb": medir_pico_mb(streaming),
    }


def experimento_lotes(
    ruta_pedidos: Path,
    mapa_stock: dict[int, int],
    lotes: list[int],
    workers: int,
    repeticiones: int,
) -> list[dict[str, float]]:
    """Barrido de tamaños de lote: secuencial vs paralelo sobre el mismo archivo."""
    # Crear el pool antes de medir: su arranque no forma parte del procesamiento.
    procesar_pedidos_jsonl_paralelo(ruta_pedidos, mapa_stock, max_workers=workers)

    filas = []
    for lote in lotes:

        def secuencial(lote=lote):
            return procesar_pedidos_jsonl_secuencial(ruta_pedidos, mapa_stock, tamano_lote=lote)

        def paralelo(lote=lote):
            return procesar_pedidos_jsonl_paralelo(
                ruta_pedidos, mapa_stock, tamano_lote=lote, max_workers=workers
            )

        t_sec = medir_tiempo_ms(secuencial, repeticiones)
        t_par = medir_tiempo_ms(paralelo, repeticiones)
        filas.append(
            {
                "lote": lote,
                "secuencial_ms": t_sec,
                "paralelo_ms": t_par,
                "speedup": t_sec / t_par if t_par > 0 else 0.0,
                "secuencial_mb": medir_pico_mb(secuencial),
                "paralelo_mb": medir_pico_mb(paralelo),
            }
        )
        print(
            f"  lote {lote:>7,}: secuencial {t_sec:8.1f} ms | paralelo {t_par:8.1f} ms "
            f"| speedup {filas[-1]['speedup']:.2f}x"
        )
    return filas


def experimento_memoria_en_ram(workers: int, repeticiones: int) -> dict[str, float]:
    """Pedidos ya cargados (grande.json): secuencial vs pool de procesos."""
    productos, pedidos = cargar_dataset_json(DATASETS_DIR / "grande.json")
    catalogo = CatalogoHash(productos)
    procesar_pedidos_concurrente(catalogo, pedidos, max_workers=workers)  # crear el pool
    t_sec = medir_tiempo_ms(lambda: procesar_pedidos_secuencial(catalogo, pedidos), repeticiones)
    t_par = medir_tiempo_ms(
        lambda: procesar_pedidos_concurrente(catalogo, pedidos, max_workers=workers),
        repeticiones,
    )
    return {
        "pedidos": len(pedidos),
        "secuencial_ms": t_sec,
        "paralelo_ms": t_par,
        "speedup": t_sec / t_par if t_par > 0 else 0.0,
    }


def experimento_csv(ruta_pedidos: Path, catalogo: CatalogoHash, repeticiones: int) -> dict:
    """Exportación del picking consolidado: buffer por defecto vs 1 MB."""
    pedidos = list(leer_pedidos_streaming_jsonl(ruta_pedidos))
    items = agrupar_pedidos_batch(pedidos, catalogo).items
    ruta_csv = GENERADOS_DIR / "picking_reporte.csv"

    def exportar(buffer: int):
        return exportar_picking_csv_con_buffer(ruta_csv, items, tamano_buffer=buffer)

    t_defecto = medir_tiempo_ms(lambda: exportar(BUFFER_POR_DEFECTO), repeticiones)
    t_explicito = medir_tiempo_ms(lambda: exportar(BUFFER_EXPLICITO), repeticiones)
    filas = exportar(BUFFER_EXPLICITO)
    return {
        "filas": filas,
        "kb": os.path.getsize(ruta_csv) / 1024.0,
        "defecto_ms": t_defecto,
        "explicito_ms": t_explicito,
    }


def _conclusion_lectura(lectura: dict[str, float]) -> str:
    ahorro = 100.0 * (1 - lectura["streaming_mb"] / lectura["completa_mb"])
    texto = (
        f"El streaming usa un **{ahorro:.1f} % menos de memoria pico**: la memoria depende "
        "del tamaño de una línea, no del tamaño del archivo."
    )
    if lectura["streaming_ms"] <= lectura["completa_ms"]:
        return (
            texto + " Además fue más rápido, porque no tiene que hacer crecer una lista gigante."
        )
    return texto + (
        " A cambio fue más lento, porque construye y valida un `Pedido` por línea en lugar "
        "de dejar diccionarios crudos."
    )


def _conclusion_lotes(filas: list[dict[str, float]], workers: int) -> str:
    mejor = max(filas, key=lambda f: f["speedup"])
    ganadores = [f"{f['lote']:,}" for f in filas if f["speedup"] > 1.0]
    techo = f"Con {workers} workers el máximo teórico es {workers}×."
    memoria = (
        " La memoria del proceso principal crece con el tamaño de lote (hay hasta dos lotes "
        "por worker en vuelo), no con el tamaño del archivo."
    )
    if not ganadores:
        return (
            f"En este equipo el paralelo **no superó** al secuencial con ningún tamaño de "
            f"lote (mejor caso: {mejor['speedup']:.2f}× con lotes de {mejor['lote']:,}). "
            f"{techo}" + memoria
        )
    return (
        f"El paralelo superó al secuencial con lotes de {', '.join(ganadores)} líneas. "
        f"El mejor resultado fue **{mejor['speedup']:.2f}×** con lotes de "
        f"{mejor['lote']:,}. {techo}" + memoria
    )


def _conclusion_csv(csv: dict[str, float]) -> str:
    base = f"Se exportaron {csv['filas']:,} filas ({csv['kb']:.1f} KB)."
    diferencia = 100.0 * (csv["defecto_ms"] - csv["explicito_ms"]) / csv["defecto_ms"]
    if diferencia > 5:
        return base + (
            f" El buffer de 1 MB fue un {diferencia:.0f} % más rápido: agrupa las escrituras "
            "en menos llamadas al sistema operativo."
        )
    return base + (
        " Con este tamaño de archivo la diferencia no es significativa: el buffer por "
        "defecto de Python ya agrupa las escrituras y el archivo se escribe en pocas "
        "llamadas. El buffer explícito pesa más con archivos grandes o discos lentos."
    )


def fila_markdown(*celdas: object) -> str:
    """Arma una fila de tabla Markdown: ``| a | b | c |``."""
    return "| " + " | ".join(str(celda) for celda in celdas) + " |"


def generar_informe(datos: dict[str, Any]) -> None:
    """Escribe ``docs/mediciones/archivos_grandes.md`` con los resultados."""
    lectura = datos["lectura"]
    ram = datos["memoria_ram"]
    csv = datos["csv"]
    entorno = (
        f"{datos['sistema']} · Python {datos['python']} · "
        f"{datos['nucleos']} núcleos lógicos · {datos['workers']} workers"
    )
    fila_carga_completa = fila_markdown(
        "Carga completa (`json.loads` de todas las líneas a una lista)",
        f"{lectura['completa_ms']:.1f}",
        f"{lectura['completa_mb']:.2f}",
    )
    fila_streaming = fila_markdown(
        "Streaming (`leer_pedidos_streaming_jsonl`)",
        f"{lectura['streaming_ms']:.1f}",
        f"{lectura['streaming_mb']:.2f}",
    )
    encabezado_lotes = fila_markdown(
        "Lote (líneas)",
        "Secuencial (ms)",
        "Paralelo (ms)",
        "Speedup",
        "Pico secuencial (MB)",
        "Pico paralelo (MB)",
    )
    filas_lotes = "\n".join(
        fila_markdown(
            f"{fila['lote']:,}",
            f"{fila['secuencial_ms']:.1f}",
            f"{fila['paralelo_ms']:.1f}",
            f"**{fila['speedup']:.2f}×**",
            f"{fila['secuencial_mb']:.2f}",
            f"{fila['paralelo_mb']:.2f}",
        )
        for fila in datos["lotes"]
    )
    fila_ram = fila_markdown(
        f"{ram['pedidos']:,}",
        f"{ram['secuencial_ms']:.1f}",
        f"{ram['paralelo_ms']:.1f}",
        f"**{ram['speedup']:.2f}×**",
    )

    contenido = f"""# Archivos grandes: streaming, buffering y paralelismo

Generado por `python -m benchmarks.perfilar_archivos_grandes`. No editar a mano: volver
a correr el script para actualizar los números.

## Entorno y datos

- **Sistema:** {entorno}.
- **Archivos generados** (semilla {datos["semilla"]}, en `data/generados/`, fuera de git):
  `productos.jsonl` con {datos["n_productos"]:,} productos ({datos["mb_productos"]:.2f} MB) y
  `pedidos.jsonl` con {datos["n_pedidos"]:,} pedidos ({datos["mb_pedidos"]:.2f} MB).
- **Metodología:** cada tiempo es la mediana de {datos["repeticiones"]} corridas con el pool ya
  creado. Tiempo y memoria se miden en corridas separadas, porque `tracemalloc` frena al
  proceso principal pero no a los workers y eso inflaba el speedup del paralelo. La memoria
  es el pico del proceso principal (no incluye los workers).

## 1. Lectura: carga completa vs streaming

| Estrategia | Tiempo (ms) | Pico de memoria (MB) |
|---|---:|---:|
{fila_carga_completa}
{fila_streaming}

{_conclusion_lectura(lectura)}

## 2. Procesamiento por lotes: secuencial vs paralelo

Cada lote se parsea, valida y evalúa con la misma función en ambas versiones. La versión
paralela manda el stock una sola vez por worker (initializer) y mantiene como máximo dos
lotes en vuelo por worker, así que su memoria no crece con el archivo.

{encabezado_lotes}
|---:|---:|---:|---:|---:|---:|
{filas_lotes}

{_conclusion_lotes(datos["lotes"], datos["workers"])}

## 3. Pedidos ya cargados en memoria (`grande.json`)

| Pedidos | Secuencial (ms) | Pool de procesos (ms) | Speedup |
|---:|---:|---:|---:|
{fila_ram}

Evaluar un pedido en memoria es un lookup O(1) por línea, más barato que serializarlo hacia
un worker. Por eso `MotorInventario.procesar_pedidos` es secuencial por defecto y el pool
queda como opción explícita. Con archivos (sección 2) el balance cambia porque cada worker
además parsea y valida JSON.

## 4. Exportación a CSV con buffer

| Buffer | Tiempo (ms) |
|---|---:|
| Por defecto de Python | {csv["defecto_ms"]:.1f} |
| Explícito de 1 MB | {csv["explicito_ms"]:.1f} |

{_conclusion_csv(csv)}
"""
    RUTA_INFORME.write_text(contenido, encoding="utf-8")
    print(f"\nInforme generado en {RUTA_INFORME.relative_to(BASE_DIR)}")


def ejecutar_benchmark_archivos_grandes(
    n_productos: int = 5000,
    n_pedidos: int = 200_000,
    lotes: list[int] | None = None,
    repeticiones: int = 5,
    workers: int | None = None,
    semilla: int = 42,
) -> dict[str, Any]:
    """Corre los cuatro experimentos y genera el informe."""
    lotes = lotes or [1_000, 5_000, 20_000, 50_000]
    workers = workers or min(os.cpu_count() or 4, 8)
    GENERADOS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Generando {n_productos:,} productos y {n_pedidos:,} pedidos (semilla {semilla})...")
    ruta_productos, ruta_pedidos = generar_archivos_grandes_jsonl(
        directorio_destino=GENERADOS_DIR,
        n_productos=n_productos,
        n_pedidos=n_pedidos,
        seed=semilla,
    )
    productos = list(leer_productos_streaming_jsonl(ruta_productos))
    catalogo = CatalogoHash(productos)
    mapa_stock = {p.id: p.stock for p in productos}

    try:
        print("\n[1] Lectura: carga completa vs streaming")
        lectura = experimento_lectura(ruta_pedidos, repeticiones)
        print(f"\n[2] Lotes: secuencial vs paralelo ({workers} workers)")
        filas_lotes = experimento_lotes(ruta_pedidos, mapa_stock, lotes, workers, repeticiones)
        print("\n[3] Pedidos en memoria: secuencial vs pool")
        memoria_ram = experimento_memoria_en_ram(workers, repeticiones)
        print("\n[4] Exportación CSV con buffer")
        csv = experimento_csv(ruta_pedidos, catalogo, repeticiones)
    finally:
        pool_archivos.cerrar()
        pool_pedidos.cerrar()

    datos = {
        "sistema": f"{platform.system()} {platform.release()}",
        "python": platform.python_version(),
        "nucleos": os.cpu_count(),
        "workers": workers,
        "semilla": semilla,
        "repeticiones": repeticiones,
        "n_productos": n_productos,
        "n_pedidos": n_pedidos,
        "mb_productos": os.path.getsize(ruta_productos) / BYTES_POR_MB,
        "mb_pedidos": os.path.getsize(ruta_pedidos) / BYTES_POR_MB,
        "lectura": lectura,
        "lotes": filas_lotes,
        "memoria_ram": memoria_ram,
        "csv": csv,
    }
    generar_informe(datos)
    return datos


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--productos", type=int, default=5000)
    parser.add_argument("--pedidos", type=int, default=200_000)
    parser.add_argument("--lotes", type=int, nargs="+", default=None)
    parser.add_argument("--repeticiones", type=int, default=5)
    parser.add_argument("--workers", type=int, default=None)
    args = parser.parse_args(argv)
    limites = {
        "productos": (1, 1_000_000),
        "pedidos": (1, 10_000_000),
        "repeticiones": (1, 50),
        "workers": (1, 64),
    }
    for nombre, (minimo, maximo) in limites.items():
        valor = getattr(args, nombre)
        if valor is not None and not minimo <= valor <= maximo:
            parser.error(f"--{nombre} debe estar entre {minimo} y {maximo}")
    if args.lotes and not all(1 <= lote <= 1_000_000 for lote in args.lotes):
        parser.error("--lotes debe tener valores entre 1 y 1000000")
    ejecutar_benchmark_archivos_grandes(
        n_productos=args.productos,
        n_pedidos=args.pedidos,
        lotes=args.lotes,
        repeticiones=args.repeticiones,
        workers=args.workers,
    )


if __name__ == "__main__":
    main()
