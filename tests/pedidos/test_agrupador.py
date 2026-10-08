"""Pruebas unitarias para agrupación de pedidos (Batch Picking consolidado)."""

from __future__ import annotations

from pathlib import Path

from src.datos.cargador import cargar_dataset_json
from src.inventario.catalogo_hash import CatalogoHash
from src.pedidos.agrupador import (
    DetalleDemandaPedido,
    ItemPickingConsolidado,
    LotePickingConsolidado,
    agrupar_pedidos_batch,
)

DATASETS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "datasets"


class TestAgrupadorPedidos:
    def test_agrupacion_batch_picking_demo_oral(self):
        prods, peds = cargar_dataset_json(DATASETS_DIR / "demo_oral.json")
        cat = CatalogoHash(prods)

        lote_consolidado = agrupar_pedidos_batch(peds, cat)
        assert lote_consolidado.total_pedidos == 8
        assert lote_consolidado.total_unidades > 0

        # En demo_oral, el producto 22 (Tornillos autoperforantes) es pedido en Pedido 2 y Pedido 4
        item_22 = lote_consolidado.obtener_por_producto(22)
        assert item_22 is not None
        assert item_22.cantidad_total == 15  # 5 en pedido 2 + 10 en pedido 4
        pedidos_demandantes = [d.id_pedido for d in item_22.demandas_por_pedido]
        assert 2 in pedidos_demandantes
        assert 4 in pedidos_demandantes

    def test_lote_picking_metodos_auxiliares(self, productos_muestra):
        det = DetalleDemandaPedido(id_pedido=1, cantidad=5)
        item = ItemPickingConsolidado(
            id_producto=1,
            producto=productos_muestra[0],
            cantidad_total=5,
            demandas_por_pedido=[det],
        )
        assert item.total_pedidos_solicitantes == 1
        d = item.a_diccionario()
        assert d["id_producto"] == 1
        assert d["cantidad_total"] == 5

        lote = LotePickingConsolidado(total_pedidos=1, total_unidades=5, items=[item])
        assert lote.total_productos_distintos == 1
        assert lote.obtener_por_producto(1) is item
        assert lote.obtener_por_producto(999) is None

        # Lista vacía
        lote_vacio = agrupar_pedidos_batch([])
        assert lote_vacio.total_pedidos == 0
