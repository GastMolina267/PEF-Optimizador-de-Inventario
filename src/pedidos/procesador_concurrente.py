"""Procesador concurrente de pedidos con multiprocessing (ProcessPoolExecutor).

Justificación técnica académica y Propuesta Origin 1:
1. Separar evaluación de asignación:
   Los workers ejecutan la evaluación de factibilidad en paralelo sobre la instantánea
   de stock. La asignación/descuento de inventario se ejecuta de forma atómica en el proceso
   principal respetando el orden de los pedidos, garantizando consistencia absoluta
   con el procesamiento secuencial y evitando condiciones de carrera.
2. Reducir overhead de IPC:
   El envío y retorno de datos utiliza tuplas compactas primitivas (id, cantidad, asignada, faltante)
   en lugar de dataclasses pesadas, reduciendo drásticamente el tamaño del payload en el canal IPC.
3. Eliminar trabajo redundante:
   Los futuros se despachan y consumen en orden contiguo, eliminando ordenamientos innecesarios.
4. Gestión del ciclo de vida:
   El pool es encapsulado por `GestorPool` para controlar inicio, reutilización, reinicio
   y cierre ordenado sin fugas de descriptores en Windows.
"""

from __future__ import annotations

import os
import time
from collections.abc import Sequence
from concurrent.futures.process import BrokenProcessPool

from src.modelos.pedido import (
    EstadoPedido,
    Pedido,
    PoliticaDescuento,
    ResultadoLinea,
    ResultadoPedido,
    ResumenProcesamiento,
)
from src.pedidos.evaluador import debe_descontar, evaluar_pedido
from src.pedidos.gestor_pool import pool_pedidos

# Alias de retrocompatibilidad
_cerrar_executor = pool_pedidos.cerrar


def _evaluar_fragmento_compacto(
    fragmento_pedidos: list[tuple[int, tuple[tuple[int, int], ...]]],
    mapa_stock: dict[int, int],
) -> list[tuple[int, int, tuple[tuple[int, int, int, int], ...]]]:
    """Evalúa un fragmento de pedidos contra el mapa de stock provisto.

    Tanto la entrada como la salida son tuplas compactas con tipos primitivos,
    minimizando el tamaño del buffer y el tiempo de serialización (pickle) en IPC.
    """
    resultados: list[tuple[int, int, tuple[tuple[int, int, int, int], ...]]] = []
    for id_pedido, lineas in fragmento_pedidos:
        lineas_cubiertas: list[tuple[int, int, int, int]] = []
        lineas_faltantes: list[tuple[int, int, int, int]] = []
        total_lineas = len(lineas)
        satisfechas_count = 0
        con_algo_count = 0

        for id_prod, cant in lineas:
            stock_disp = mapa_stock.get(id_prod, 0)
            if stock_disp >= cant:
                asig = cant
                falt = 0
                satisfechas_count += 1
                con_algo_count += 1
            elif stock_disp > 0:
                asig = stock_disp
                falt = cant - stock_disp
                con_algo_count += 1
            else:
                asig = 0
                falt = cant

            tupla_linea = (id_prod, cant, asig, falt)
            if asig == cant:
                lineas_cubiertas.append(tupla_linea)
            else:
                lineas_faltantes.append(tupla_linea)

        if satisfechas_count == total_lineas:
            estado_val = EstadoPedido.CUBIERTO.value
        elif con_algo_count == 0:
            estado_val = EstadoPedido.IMPOSIBLE.value
        else:
            estado_val = EstadoPedido.PARCIAL.value

        resultados.append((id_pedido, estado_val, tuple(lineas_cubiertas + lineas_faltantes)))
    return resultados


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
        max_workers: Cantidad de procesos trabajadores en paralelo.
        descontar_stock: Si True, muta el stock en el catálogo en orden secuencial atómico.
        politica_descuento: 'solo_cubiertos' o 'todo_lo_posible'.
    """
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

    # 1. Snapshot de stock para evaluación pura
    mapa_stock = {p.id: p.stock for p in catalogo.obtener_todos()}

    # 2. Conversión compacta para transmisión IPC ligera
    pedidos_compactos = [
        (p.id, tuple((lin.id_producto, lin.cantidad) for lin in p.lineas)) for p in pedidos
    ]

    workers = max_workers or min(os.cpu_count() or 4, len(pedidos))
    tamano_chunk = max(1, (len(pedidos_compactos) + workers - 1) // workers)
    fragmentos = [
        pedidos_compactos[i : i + tamano_chunk]
        for i in range(0, len(pedidos_compactos), tamano_chunk)
    ]

    # 3. Obtener executor administrado por GestorPool
    executor = pool_pedidos.obtener_executor(max_workers=workers)

    tuplas_compactas: list[tuple[int, int, tuple[tuple[int, int, int, int], ...]]] = []
    try:
        futuros = [
            executor.submit(_evaluar_fragmento_compacto, frag, mapa_stock) for frag in fragmentos
        ]
        for f in futuros:
            tuplas_compactas.extend(f.result())
    except (BrokenProcessPool, RuntimeError):
        executor = pool_pedidos.reiniciar(max_workers=workers)
        futuros = [
            executor.submit(_evaluar_fragmento_compacto, frag, mapa_stock) for frag in fragmentos
        ]
        for f in futuros:
            tuplas_compactas.extend(f.result())

    # 4. Consolidación de resultados y descuento de stock (Separación de evaluación y asignación)
    todos_resultados: list[ResultadoPedido] = []
    cubiertos = 0
    parciales = 0
    imposibles = 0

    if descontar_stock:
        # Asignación atómica secuencial en el proceso principal sobre el inventario real
        stock_actual = {p.id: p.stock for p in catalogo.obtener_todos()}
        for pedido in pedidos:
            res = evaluar_pedido(pedido, stock_actual)
            if debe_descontar(res.estado, politica_descuento):
                for rl in res.lineas_cubiertas + res.lineas_faltantes:
                    if rl.cantidad_asignada > 0:
                        stock_actual[rl.id_producto] -= rl.cantidad_asignada
                        catalogo.descontar_stock(rl.id_producto, rl.cantidad_asignada)

            if res.estado == EstadoPedido.CUBIERTO:
                cubiertos += 1
            elif res.estado == EstadoPedido.PARCIAL:
                parciales += 1
            else:
                imposibles += 1
            todos_resultados.append(res)
    else:
        # Reconstruir ResultadoPedido desde las tuplas compactas devueltas por los workers
        for id_ped, estado_val, lineas_tupla in tuplas_compactas:
            lineas_cub = []
            lineas_fal = []
            for id_prod, cant_sol, cant_asig, falt in lineas_tupla:
                rl = ResultadoLinea(
                    id_producto=id_prod,
                    cantidad_solicitada=cant_sol,
                    cantidad_asignada=cant_asig,
                    faltante=falt,
                )
                if rl.satisfecha_completamente:
                    lineas_cub.append(rl)
                else:
                    lineas_fal.append(rl)

            estado = EstadoPedido(estado_val)
            if estado == EstadoPedido.CUBIERTO:
                cubiertos += 1
            elif estado == EstadoPedido.PARCIAL:
                parciales += 1
            else:
                imposibles += 1

            todos_resultados.append(
                ResultadoPedido(
                    id_pedido=id_ped,
                    estado=estado,
                    lineas_cubiertas=lineas_cub,
                    lineas_faltantes=lineas_fal,
                )
            )

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
