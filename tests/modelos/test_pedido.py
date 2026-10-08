"""Pruebas unitarias para los modelos Pedido, LineaPedido y resultados."""

from __future__ import annotations

import pytest

from src.modelos.pedido import (
    EstadoPedido,
    LineaPedido,
    Pedido,
    ResultadoLinea,
    ResultadoPedido,
    ResumenProcesamiento,
)


class TestModelosPedido:
    def test_creacion_pedido_valido(self):
        lineas = [LineaPedido(id_producto=1, cantidad=5), LineaPedido(id_producto=2, cantidad=3)]
        p = Pedido(id=10, lineas=lineas)
        assert p.id == 10
        assert len(p.lineas) == 2
        assert p.lineas[0].cantidad == 5

    def test_validaciones_pedido_invalido(self):
        with pytest.raises(ValueError, match="entero positivo"):
            Pedido(id=0, lineas=[LineaPedido(id_producto=1, cantidad=1)])
        with pytest.raises(ValueError, match="línea"):
            Pedido(id=1, lineas=[])
        with pytest.raises(ValueError, match="cantidad"):
            LineaPedido(id_producto=1, cantidad=0)

    def test_linea_pedido_serializacion_y_validaciones(self):
        lp = LineaPedido(id_producto=10, cantidad=3)
        d = lp.a_diccionario()
        assert d == {"id_producto": 10, "cantidad": 3}
        lp2 = LineaPedido.desde_diccionario(d)
        assert lp2 == lp

        with pytest.raises(ValueError, match="entero positivo"):
            LineaPedido(id_producto=0, cantidad=3)
        with pytest.raises(ValueError, match="mayor a 0"):
            LineaPedido(id_producto=10, cantidad=0)

    def test_pedido_serializacion_y_validaciones(self):
        ped = Pedido(id=5, lineas=[LineaPedido(1, 2), LineaPedido(2, 4)])
        d = ped.a_diccionario()
        assert d["id"] == 5
        assert len(d["lineas"]) == 2
        ped2 = Pedido.desde_diccionario(d)
        assert ped2 == ped

        with pytest.raises(ValueError, match="entero positivo"):
            Pedido(id=0, lineas=[LineaPedido(1, 1)])
        with pytest.raises(ValueError, match="al menos una línea"):
            Pedido(id=1, lineas=[])

    def test_resumen_procesamiento_metricas_borde(self):
        resumen_vacio = ResumenProcesamiento(
            pedidos_procesados=0,
            pedidos_cubiertos=0,
            pedidos_parciales=0,
            pedidos_imposibles=0,
            tiempo_ejecucion_ms=0.0,
        )
        assert resumen_vacio.porcentaje_cobertura == 0.0

        rl = ResultadoLinea(id_producto=1, cantidad_solicitada=5, cantidad_asignada=5, faltante=0)
        assert rl.satisfecha_completamente is True
        rp = ResultadoPedido(id_pedido=1, estado=EstadoPedido.CUBIERTO, lineas_cubiertas=[rl])
        assert rp.es_exitoso is True
