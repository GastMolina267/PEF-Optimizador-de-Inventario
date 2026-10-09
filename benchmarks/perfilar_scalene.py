"""Escenario de perfilado para Scalene: CPU (Python / nativo / sistema) y memoria.

Ejecuta, sobre los datasets oficiales:

1. Búsquedas intensivas en catálogo (ID y texto).
2. Consolidación de pedidos para batch picking.
3. Ranking Top-N de productos más solicitados.
4. Búsqueda combinatoria de alternativas de sustitución.
5. Procesamiento de pedidos, secuencial vs pool de procesos, **repetido** varias veces
   con el pool ya creado. Así Scalene mide el costo de cada llamada (serialización e
   IPC) y no solo el arranque de los procesos, que se paga una vez.

Uso (desde la raíz del repo, para que Scalene perfile también ``src/``)::

    scalene run --memory --program-path . -o docs/mediciones/scalene/scalene_despues.json \
        benchmarks/perfilar_scalene.py
    scalene run ... benchmarks/perfilar_scalene.py --- --iteraciones 50

El resumen comparativo se genera con ``python -m benchmarks.resumir_scalene``.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.datos.cargador import cargar_dataset_json
from src.motor.motor_inventario import MotorInventario
from src.pedidos.procesador_concurrente import procesar_pedidos_concurrente
from src.pedidos.procesador_secuencial import procesar_pedidos_secuencial

DATASETS_DIR = BASE_DIR / "data" / "datasets"
SCALENE_DIR = BASE_DIR / "docs" / "mediciones" / "scalene"


def ejecutar_escenario_scalene(nombre_dataset: str = "grande.json", iteraciones: int = 30) -> None:
    """Ejecuta una corrida representativa de operaciones sobre el dataset indicado."""
    ruta_dataset = DATASETS_DIR / nombre_dataset
    if not ruta_dataset.is_file():
        raise FileNotFoundError(f"Dataset no encontrado: {ruta_dataset}")

    motor = MotorInventario(estrategia="optimizado")
    motor.cargar_dataset(ruta_dataset)
    prods, peds = cargar_dataset_json(ruta_dataset)

    print(f"[Scalene] Dataset {nombre_dataset}: {len(prods)} productos, {len(peds)} pedidos")

    # 1. Búsquedas repetitivas de catálogo (Python CPU & Memoria)
    for _ in range(5):
        for prod in prods[:100]:
            _ = motor.buscar_por_id(prod.id)
            palabra = prod.nombre.split()[0]
            _ = motor.buscar_por_nombre(palabra, usar_cache=True)

    # 2. Agrupación Batch Picking
    for _ in range(5):
        _ = motor.agrupar_pedidos()

    # 3. Top-N
    for _ in range(5):
        _ = motor.calcular_top_productos(k=10)

    # 4. Alternativas con memoización
    if prods:
        categoria = prods[0].categoria
        for _ in range(3):
            _ = motor.buscar_alternativas(
                categoria=categoria,
                presupuesto_maximo=30000.0,
                max_combinaciones=10,
                max_candidatos=14,
            )

    # 5. Procesamiento repetido: secuencial vs pool (el pool se crea en la primera vuelta).
    print(f"[Scalene] Procesamiento secuencial x{iteraciones}...")
    for _ in range(iteraciones):
        procesar_pedidos_secuencial(catalogo=motor.catalogo, pedidos=peds, descontar_stock=False)

    print(f"[Scalene] Procesamiento con pool de procesos x{iteraciones}...")
    for _ in range(iteraciones):
        procesar_pedidos_concurrente(catalogo=motor.catalogo, pedidos=peds, descontar_stock=False)


def main(argv: list[str] | None = None) -> None:
    """Lee los argumentos y corre el escenario que perfila Scalene."""
    parser = argparse.ArgumentParser(description="Escenario de perfilado para Scalene.")
    parser.add_argument("--dataset", default="grande.json")
    parser.add_argument("--iteraciones", type=int, default=30)
    args = parser.parse_args(argv)

    SCALENE_DIR.mkdir(parents=True, exist_ok=True)
    inicio = time.perf_counter()
    ejecutar_escenario_scalene(args.dataset, args.iteraciones)
    print(f"[Scalene] Ejecución completa en {time.perf_counter() - inicio:.2f} s")


if __name__ == "__main__":
    main()
