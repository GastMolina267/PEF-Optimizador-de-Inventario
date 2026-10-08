"""Procesador concurrente de pedidos con multiprocessing (ProcessPoolExecutor).

Justificación técnica académica:
1. Qué tareas se ejecutan simultáneamente:
   La evaluación de factibilidad y cálculo de disponibilidad de lotes de pedidos independientes.
2. Por qué son independientes:
   Cada pedido analiza su propia canasta de ítems frente a una instantánea del inventario.
3. Qué mecanismo utiliza el lenguaje:
   `concurrent.futures.ProcessPoolExecutor` (procesos separados). Dado que la validación
   y cálculo de líneas es una tarea CPU-bound, los hilos de `threading` colisionarían con
   el Global Interpreter Lock (GIL) de Python, impidiendo el paralelismo multinúcleo real.
4. Riesgos y Trade-offs:
   - Costo de IPC (Inter-Process Communication) y serialización (pickle) de datos entre procesos.
   - Con lotes pequeños (p. ej. N < 50), el overhead de inicialización de los procesos hace que
     la ejecución secuencial sea más rápida (el paralelismo no paga).
   - Con lotes medianos/grandes, el paralelismo escala eficientemente aprovechando todos los núcleos.
   - Para evitar condiciones de carrera sin bloqueos lentos, la evaluación de disponibilidad se
     realiza en paralelo y la consolidación de descuento de stock se aplica de forma atómica
     en el proceso principal.
"""

from __future__ import annotations

import atexit
import os
import time
from collections.abc import Sequence
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool

from src.modelos.pedido import (
    EstadoPedido,
    Pedido,
    PoliticaDescuento,
    ResultadoPedido,
    ResumenProcesamiento,
)
from src.pedidos.evaluador import debe_descontar, evaluar_pedido

_executor: ProcessPoolExecutor | None = None
_executor_workers: int | None = None


def _cerrar_executor() -> None:
    """Cierra el pool persistente sin bloquear la salida del proceso."""
    global _executor, _executor_workers
    if _executor is None:
        return
    _executor.shutdown(wait=False, cancel_futures=True)
    _executor = None
    _executor_workers = None


atexit.register(_cerrar_executor)


def _evaluar_fragmento_pedidos(
    fragmento: list[Pedido],
    mapa_stock: dict[int, int],
) -> list[ResultadoPedido]:
    """Función de nivel de módulo para ser serializable (pickleable) por ProcessPoolExecutor en Windows.

    Evalúa un subconjunto de pedidos contra un mapa estático de stock {id_producto: stock}.
    """
    return [evaluar_pedido(pedido, mapa_stock) for pedido in fragmento]


def procesar_pedidos_concurrente(
    catalogo,
    pedidos: Sequence[Pedido],
    max_workers: int | None = None,
    descontar_stock: bool = False,
    politica_descuento: PoliticaDescuento | str = PoliticaDescuento.SOLO_CUBIERTOS,
) -> ResumenProcesamiento:
    """Procesa un lote de pedidos en paralelo utilizando un pool de procesos independientes.

    Argumentos:
        catalogo: Catálogo de productos (CatalogoHash o CatalogoLineal).
        pedidos: Secuencia de pedidos a procesar.
        max_workers: Cantidad de procesos trabajadores en paralelo (por defecto: CPU cores disponibles).
        descontar_stock: Si True, muta el stock en el catálogo una vez finalizado el cálculo paralelo.
        politica_descuento: 'solo_cubiertos' o 'todo_lo_posible'.
    """
    global _executor, _executor_workers
    inicio = time.perf_counter()

    if not pedidos:
        return ResumenProcesamiento(
            pedidos_procesados=0,
            pedidos_cubiertos=0,
            pedidos_parciales=0,
            pedidos_imposibles=0,
            tiempo_ejecucion_ms=0.0,
            resultados=[],
            estrategia="optimizado_concurrente",
        )

    # 1. Crear snapshot ligero de stock {id_producto: stock} para transmisión IPC eficiente
    mapa_stock = {p.id: p.stock for p in catalogo.obtener_todos()}

    # 2. Determinar cantidad de procesos y tamaño de fragmento (chunk size)
    workers = max_workers or min(os.cpu_count() or 4, len(pedidos))
    tamano_chunk = max(1, (len(pedidos) + workers - 1) // workers)
    fragmentos = [
        list(pedidos[i : i + tamano_chunk]) for i in range(0, len(pedidos), tamano_chunk)
    ]

    # 3. Reutilizar ProcessPoolExecutor. En Windows, CreateProcess por clic cuesta cientos de ms.
    if _executor is None or _executor_workers != workers:
        if _executor is not None:
            _executor.shutdown(wait=False, cancel_futures=True)
        _executor = ProcessPoolExecutor(max_workers=workers)
        _executor_workers = workers

    todos_resultados: list[ResultadoPedido] = []
    try:
        futuros = [
            _executor.submit(_evaluar_fragmento_pedidos, frag, mapa_stock) for frag in fragmentos
        ]
        for f in futuros:
            todos_resultados.extend(f.result())
    except (BrokenProcessPool, RuntimeError):
        _cerrar_executor()
        _executor = ProcessPoolExecutor(max_workers=workers)
        _executor_workers = workers
        futuros = [
            _executor.submit(_evaluar_fragmento_pedidos, frag, mapa_stock) for frag in fragmentos
        ]
        for f in futuros:
            todos_resultados.extend(f.result())

    # Asegurar el orden original de los pedidos
    mapa_posicion_original = {p.id: idx for idx, p in enumerate(pedidos)}
    todos_resultados.sort(key=lambda r: mapa_posicion_original.get(r.id_pedido, 0))

    # 4. Totalizar métricas de resolución
    cubiertos = sum(1 for r in todos_resultados if r.estado == EstadoPedido.CUBIERTO)
    parciales = sum(1 for r in todos_resultados if r.estado == EstadoPedido.PARCIAL)
    imposibles = sum(1 for r in todos_resultados if r.estado == EstadoPedido.IMPOSIBLE)

    # 5. Aplicar descuentos atómicos en el proceso principal si fue solicitado
    if descontar_stock:
        for res_pedido in todos_resultados:
            if debe_descontar(res_pedido.estado, politica_descuento):
                for rl in res_pedido.lineas_cubiertas + res_pedido.lineas_faltantes:
                    if rl.cantidad_asignada > 0:
                        catalogo.descontar_stock(rl.id_producto, rl.cantidad_asignada)

    tiempo_total_ms = (time.perf_counter() - inicio) * 1000.0

    return ResumenProcesamiento(
        pedidos_procesados=len(pedidos),
        pedidos_cubiertos=cubiertos,
        pedidos_parciales=parciales,
        pedidos_imposibles=imposibles,
        tiempo_ejecucion_ms=tiempo_total_ms,
        resultados=todos_resultados,
        estrategia="optimizado_concurrente",
    )
