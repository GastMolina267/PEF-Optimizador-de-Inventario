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
    PoliticaDescuento,
    ResultadoPedido,
    ResumenProcesamiento,
)
from src.pedidos.evaluador import debe_descontar, evaluar_pedido


def procesar_pedidos_secuencial(
    catalogo,
    pedidos: Sequence[Pedido],
    descontar_stock: bool = False,
    politica_descuento: PoliticaDescuento | str = PoliticaDescuento.SOLO_CUBIERTOS,
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
        resultado_pedido = evaluar_pedido(pedido, catalogo)
        resultados.append(resultado_pedido)

        if resultado_pedido.estado == EstadoPedido.CUBIERTO:
            cubiertos += 1
        elif resultado_pedido.estado == EstadoPedido.IMPOSIBLE:
            imposibles += 1
        else:
            parciales += 1

        # Aplicación de descuentos de stock si fue solicitado
        if descontar_stock and debe_descontar(resultado_pedido.estado, politica_descuento):
            todas_lineas = resultado_pedido.lineas_cubiertas + resultado_pedido.lineas_faltantes
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
