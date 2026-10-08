"""Pruebas unitarias para el núcleo de evaluación de pedidos."""

from __future__ import annotations

import pytest

from src.inventario.catalogo_hash import CatalogoHash
from src.modelos.pedido import EstadoPedido, LineaPedido, Pedido
from src.modelos.producto import Producto
from src.pedidos.evaluador import (
    ContadorEstados,
    crear_consulta_stock,
    evaluar_lineas,
    evaluar_pedido,
    evaluar_pedido_compacto,
    resultado_desde_compacto,
)


def _catalogo(stocks: dict[int, int]) -> CatalogoHash:
    return CatalogoHash(
        [
            Producto(id_, f"Producto {id_}", "Ferretería y Herramientas", stock, 100.0)
            for id_, stock in stocks.items()
        ]
    )


class TestNucleoEvaluacion:
    def test_cubierto(self):
        estado, lineas = evaluar_lineas([(1, 5), (2, 3)], lambda i: {1: 10, 2: 3}.get(i, 0))
        assert estado is EstadoPedido.CUBIERTO
        assert lineas == ((1, 5, 5, 0), (2, 3, 3, 0))

    def test_parcial_ordena_cubiertas_primero(self):
        estado, lineas = evaluar_lineas([(2, 5), (1, 4)], lambda i: {1: 10, 2: 3}.get(i, 0))
        assert estado is EstadoPedido.PARCIAL
        assert lineas == ((1, 4, 4, 0), (2, 5, 3, 2))

    def test_imposible(self):
        estado, lineas = evaluar_lineas([(3, 2), (9, 1)], lambda i: 0)
        assert estado is EstadoPedido.IMPOSIBLE
        assert lineas == ((3, 2, 0, 2), (9, 1, 0, 1))

    def test_roundtrip_compacto_igual_a_evaluar_pedido(self):
        pedido = Pedido(7, [LineaPedido(1, 4), LineaPedido(2, 5), LineaPedido(3, 1)])
        mapa = {1: 10, 2: 3, 3: 0}
        directo = evaluar_pedido(pedido, mapa)
        lineas = [(lin.id_producto, lin.cantidad) for lin in pedido.lineas]
        via_compacto = resultado_desde_compacto(
            evaluar_pedido_compacto(pedido.id, lineas, crear_consulta_stock(mapa))
        )
        assert directo == via_compacto

    def test_consulta_stock_desde_catalogo_y_mapeo(self):
        assert crear_consulta_stock(_catalogo({1: 4}))(1) == 4
        assert crear_consulta_stock(_catalogo({1: 4}))(99) == 0
        assert crear_consulta_stock({1: 4})(1) == 4

    def test_consulta_stock_rechaza_fuente_invalida(self):
        with pytest.raises(TypeError, match="no soportada"):
            crear_consulta_stock([1, 2, 3])

    def test_contador_acepta_enum_y_valor(self):
        contador = ContadorEstados()
        for estado in (EstadoPedido.CUBIERTO, "cubierto", "parcial", EstadoPedido.IMPOSIBLE):
            contador.registrar(estado)
        assert (contador.cubiertos, contador.parciales, contador.imposibles) == (2, 1, 1)
        assert contador.total == 4
