"""Script de perfilado línea a línea (Line Profiler).

Analiza en detalle las líneas de código de las funciones críticas del sistema:
- Cantidad de ejecuciones (Hits).
- Tiempo total por línea (Time).
- Tiempo medio por ejecución (Per Hit).
- Porcentaje del tiempo total consumido por cada línea (% Time).

Compara:
- Búsquedas lineales en catálogo vs. Búsquedas hash.
- Top-N lineal con sorted vs. Top-N acotado con heapq.
- Batch picking consolidado en un solo paso.
- Recursión pura vs. Programación dinámica con memoización.

Genera:
- docs/mediciones/line_profiler_resumen.txt
"""

from __future__ import annotations

import io
from pathlib import Path

from line_profiler import LineProfiler

from src.datos.cargador import cargar_dataset
from src.inventario.catalogo_hash import CatalogoHash
from src.inventario.catalogo_lineal import CatalogoLineal
from src.pedidos.agrupador import agrupar_pedidos_batch
from src.pedidos.combinaciones import BuscadorAlternativas
from src.pedidos.procesador_secuencial import procesar_pedidos_secuencial
from src.ranking.top_productos import (
    calcular_top_solicitados_heap,
    calcular_top_solicitados_lineal,
)

BASE_DIR = Path(__file__).resolve().parent.parent
DATASETS_DIR = BASE_DIR / "data" / "datasets"
MEDICIONES_DIR = BASE_DIR / "docs" / "mediciones"


def main():
    MEDICIONES_DIR.mkdir(parents=True, exist_ok=True)
    ruta_dataset = DATASETS_DIR / "mediano.json"
    productos, pedidos = cargar_dataset(ruta_dataset)

    cat_lineal = CatalogoLineal(productos)
    cat_hash = CatalogoHash(productos)
    buscador_alt = BuscadorAlternativas(productos)

    lp = LineProfiler()

    # Registrar funciones objetivo para análisis línea por línea
    lp.add_function(CatalogoLineal.buscar_por_id)
    lp.add_function(CatalogoLineal.buscar_por_nombre)
    lp.add_function(CatalogoHash.buscar_por_id)
    lp.add_function(CatalogoHash.buscar_por_nombre)
    lp.add_function(calcular_top_solicitados_lineal)
    lp.add_function(calcular_top_solicitados_heap)
    lp.add_function(agrupar_pedidos_batch)
    lp.add_function(BuscadorAlternativas._resolver_recursivo_puro)
    lp.add_function(BuscadorAlternativas._resolver_dp_memo)
    lp.add_function(procesar_pedidos_secuencial)

    print("=" * 80)
    print(" INICIANDO PERFILADO LÍNEA A LÍNEA (LINE_PROFILER)")
    print(f" Dataset: {ruta_dataset.name} ({len(productos)} productos, {len(pedidos)} pedidos)")
    print("=" * 80)

    # 1. Ejecutar búsquedas en catálogo bajo perfilado
    id_muestra = productos[-1].id
    termino = productos[len(productos) // 2].nombre.split()[0].lower()

    print("-> Perfilando búsquedas en catálogo...")
    for _ in range(50):
        lp.runcall(cat_lineal.buscar_por_id, id_muestra)
        lp.runcall(cat_hash.buscar_por_id, id_muestra)

    for _ in range(20):
        lp.runcall(cat_lineal.buscar_por_nombre, termino)
        lp.runcall(cat_hash.buscar_por_nombre, termino)

    # 2. Ejecutar Top-N
    print("-> Perfilando ranking Top-N (Sort vs. Heap)...")
    for _ in range(10):
        lp.runcall(calcular_top_solicitados_lineal, pedidos, cat_lineal, 5)
        lp.runcall(calcular_top_solicitados_heap, pedidos, cat_hash, 5)

    # 3. Ejecutar Batch Picking
    print("-> Perfilando Batch Picking consolidado...")
    for _ in range(5):
        lp.runcall(agrupar_pedidos_batch, pedidos, cat_hash)

    # 4. Ejecutar Alternativas (Recursivo vs DP Memo)
    print("-> Perfilando alternativas sustitutas (Recursión pura vs. DP Memo)...")
    cat_ejemplo = productos[0].categoria
    presupuesto = 35000.0
    for _ in range(3):
        lp.runcall(
            buscador_alt.buscar_alternativas,
            cat_ejemplo,
            presupuesto,
            usar_memoizacion=False,
            max_combinaciones=10,
            max_candidatos=14,
        )
        lp.runcall(
            buscador_alt.buscar_alternativas,
            cat_ejemplo,
            presupuesto,
            usar_memoizacion=True,
            max_combinaciones=10,
            max_candidatos=14,
        )

    # 5. Ejecutar procesamiento secuencial
    print("-> Perfilando procesamiento secuencial de pedidos...")
    lp.runcall(procesar_pedidos_secuencial, cat_lineal, pedidos, descontar_stock=False)
    lp.runcall(procesar_pedidos_secuencial, cat_hash, pedidos, descontar_stock=False)

    # Generar salida
    stream = io.StringIO()
    lp.print_stats(stream=stream)
    contenido = stream.getvalue()

    ruta_salida = MEDICIONES_DIR / "line_profiler_resumen.txt"
    with open(ruta_salida, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write(" REPORTE DE PERFILADO LÍNEA A LÍNEA (LINE_PROFILER)\n")
        f.write(f" Dataset base: {ruta_dataset.name}\n")
        f.write("=" * 80 + "\n\n")
        f.write(contenido)

    print("\n" + "=" * 80)
    print(f" [OK] Reporte de line_profiler guardado en:\n - {ruta_salida}")
    print("=" * 80)


if __name__ == "__main__":
    main()
