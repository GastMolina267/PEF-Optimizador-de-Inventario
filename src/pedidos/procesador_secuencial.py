"""Procesador de pedidos secuencial (Baseline).

Procesa un lote de pedidos uno a uno de forma estrictamente secuencial,
resolviendo la disponibilidad de cada línea contra el catálogo de inventario.
"""

from __future__ import annotations

import time
from collections.abc import Sequence

from src.modelos.pedido import (
    EstadoPedido,
    Pedido,
    ResultadoLinea,
    ResultadoPedido,
    ResumenProcesamiento,
)


def procesar_pedidos_secuencial(
    catalogo,
    pedidos: Sequence[Pedido],
    descontar_stock: bool = False,
    politica_descuento: str = "solo_cubiertos",
) -> ResumenProcesamiento:
    """Procesa una secuencia de pedidos de manera secuencial (mono-hilo).

    Para cada pedido:
    1. Examina cada línea buscando el producto en el catálogo.
    2. Determina el stock disponible frente a la demanda.
    3. Clasifica el pedido como CUBIERTO, PARCIAL o IMPOSIBLE.
    4. Si descontar_stock=True y cumple la política, descuenta el stock del catálogo.

    Complejidad temporal con CatalogoLineal:
    O(P * M * N), donde P es la cantidad de pedidos, M la cantidad promedio de líneas
    por pedido, y N el tamaño del catálogo (debido a la búsqueda lineal O(N) por línea).
    """
    inicio = time.perf_counter()

    resultados: list[ResultadoPedido] = []
    cubiertos = 0
    parciales = 0
    imposibles = 0

    for pedido in pedidos:
        lineas_cubiertas: list[ResultadoLinea] = []
        lineas_faltantes: list[ResultadoLinea] = []
        total_lineas = len(pedido.lineas)
        lineas_satisfechas_count = 0
        lineas_con_algo_asignado_count = 0

        for linea in pedido.lineas:
            producto = catalogo.buscar_por_id(linea.id_producto)
            stock_disp = producto.stock if producto is not None else 0

            if stock_disp >= linea.cantidad:
                asignada = linea.cantidad
                faltante = 0
                lineas_satisfechas_count += 1
                lineas_con_algo_asignado_count += 1
            elif stock_disp > 0:
                asignada = stock_disp
                faltante = linea.cantidad - stock_disp
                lineas_con_algo_asignado_count += 1
            else:
                asignada = 0
                faltante = linea.cantidad

            res_linea = ResultadoLinea(
                id_producto=linea.id_producto,
                cantidad_solicitada=linea.cantidad,
                cantidad_asignada=asignada,
                faltante=faltante,
            )

            if res_linea.satisfecha_completamente:
                lineas_cubiertas.append(res_linea)
            else:
                lineas_faltantes.append(res_linea)

        # Determinar estado del pedido
        if lineas_satisfechas_count == total_lineas:
            estado = EstadoPedido.CUBIERTO
            cubiertos += 1
        elif lineas_con_algo_asignado_count == 0:
            estado = EstadoPedido.IMPOSIBLE
            imposibles += 1
        else:
            estado = EstadoPedido.PARCIAL
            parciales += 1

        resultado_pedido = ResultadoPedido(
            id_pedido=pedido.id,
            estado=estado,
            lineas_cubiertas=lineas_cubiertas,
            lineas_faltantes=lineas_faltantes,
        )
        resultados.append(resultado_pedido)

        # Aplicación de descuentos de stock si fue solicitado
        if descontar_stock:
            debe_descontar = (
                politica_descuento == "solo_cubiertos" and estado == EstadoPedido.CUBIERTO
            ) or (
                politica_descuento == "todo_lo_posible"
                and estado in (EstadoPedido.CUBIERTO, EstadoPedido.PARCIAL)
            )
            if debe_descontar:
                todas_lineas = lineas_cubiertas + lineas_faltantes
                for rl in todas_lineas:
                    if rl.cantidad_asignada > 0:
                        catalogo.descontar_stock(rl.id_producto, rl.cantidad_asignada)

    tiempo_total_ms = (time.perf_counter() - inicio) * 1000.0

    return ResumenProcesamiento(
        pedidos_procesados=len(pedidos),
        pedidos_cubiertos=cubiertos,
        pedidos_parciales=parciales,
        pedidos_imposibles=imposibles,
        tiempo_ejecucion_ms=tiempo_total_ms,
        resultados=resultados,
        estrategia="baseline_secuencial",
    )
