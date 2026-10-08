"""Módulo de evaluación y reglas de resolución de pedidos."""

from __future__ import annotations

from typing import Any

from src.modelos.pedido import (
    EstadoPedido,
    Pedido,
    PoliticaDescuento,
    ResultadoLinea,
    ResultadoPedido,
)


def _consultar_stock(fuente_stock: Any, id_producto: int) -> int:
    """Obtiene el stock disponible desde un objeto catálogo o un mapeo directo."""
    if hasattr(fuente_stock, "buscar_por_id"):
        prod = fuente_stock.buscar_por_id(id_producto)
        return prod.stock if prod is not None else 0
    if hasattr(fuente_stock, "get"):
        return fuente_stock.get(id_producto, 0)
    return 0


def evaluar_pedido(pedido: Pedido, fuente_stock: Any) -> ResultadoPedido:
    """Evalúa la factibilidad de un pedido frente al stock disponible.

    Calcula la asignación y faltantes de cada línea y determina si el
    pedido resulta CUBIERTO, PARCIAL o IMPOSIBLE.

    Argumentos:
        pedido: Instancia del Pedido a evaluar.
        fuente_stock: Instancia de CatalogoLineal/CatalogoHash o mapeo {id_producto: stock}.

    Retorna:
        ResultadoPedido con el detalle línea por línea y el estado general.
    """
    lineas_cubiertas: list[ResultadoLinea] = []
    lineas_faltantes: list[ResultadoLinea] = []
    total_lineas = len(pedido.lineas)
    lineas_satisfechas_count = 0
    lineas_con_algo_asignado_count = 0

    for linea in pedido.lineas:
        stock_disp = _consultar_stock(fuente_stock, linea.id_producto)

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

    if lineas_satisfechas_count == total_lineas:
        estado = EstadoPedido.CUBIERTO
    elif lineas_con_algo_asignado_count == 0:
        estado = EstadoPedido.IMPOSIBLE
    else:
        estado = EstadoPedido.PARCIAL

    return ResultadoPedido(
        id_pedido=pedido.id,
        estado=estado,
        lineas_cubiertas=lineas_cubiertas,
        lineas_faltantes=lineas_faltantes,
    )


def debe_descontar(
    estado: EstadoPedido,
    politica: PoliticaDescuento | str = PoliticaDescuento.SOLO_CUBIERTOS,
) -> bool:
    """Determina si un pedido califica para descontar stock según la política elegida."""
    politica_norm = (
        politica.value if isinstance(politica, PoliticaDescuento) else str(politica).lower()
    )
    if politica_norm == PoliticaDescuento.SOLO_CUBIERTOS:
        return estado == EstadoPedido.CUBIERTO
    if politica_norm == PoliticaDescuento.TODO_LO_POSIBLE:
        return estado in (EstadoPedido.CUBIERTO, EstadoPedido.PARCIAL)
    return False
