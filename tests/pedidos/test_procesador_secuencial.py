"""Pruebas unitarias para el procesador secuencial de pedidos."""

from __future__ import annotations

from pathlib import Path

from src.datos.cargador import cargar_dataset_json
from src.inventario.catalogo_lineal import CatalogoLineal
from src.modelos.pedido import EstadoPedido
from src.pedidos.procesador_secuencial import procesar_pedidos_secuencial

DATASETS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "datasets"


class TestProcesadorSecuencial:
    def test_procesamiento_demo_oral(self):
        prods, peds = cargar_dataset_json(DATASETS_DIR / "demo_oral.json")
        catalogo = CatalogoLineal(prods)
        resumen = procesar_pedidos_secuencial(catalogo, peds, descontar_stock=False)

        assert resumen.pedidos_procesados == 8
        assert resumen.pedidos_cubiertos >= 1
        assert resumen.pedidos_parciales >= 1
        assert resumen.pedidos_imposibles >= 1
        assert resumen.tiempo_ejecucion_ms >= 0.0

        # Pedido 1 debe estar cubierto
        res_p1 = next(r for r in resumen.resultados if r.id_pedido == 1)
        assert res_p1.estado == EstadoPedido.CUBIERTO
        assert res_p1.es_exitoso is True

        # Pedido 3 debe ser parcial (Producto 5 tiene stock 0)
        res_p3 = next(r for r in resumen.resultados if r.id_pedido == 3)
        assert res_p3.estado == EstadoPedido.PARCIAL

        # Pedido 5 debe ser imposible (ambos productos tienen stock 0)
        res_p5 = next(r for r in resumen.resultados if r.id_pedido == 5)
        assert res_p5.estado == EstadoPedido.IMPOSIBLE

    def test_procesador_secuencial_politica_todo_lo_posible(
        self, catalogo_lineal_muestra, pedidos_muestra
    ):
        res = procesar_pedidos_secuencial(
            catalogo_lineal_muestra,
            pedidos_muestra,
            descontar_stock=True,
            politica_descuento="todo_lo_posible",
        )
        assert res.pedidos_procesados == len(pedidos_muestra)
