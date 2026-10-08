"""Pruebas unitarias para el procesador concurrente de pedidos."""

from __future__ import annotations

from pathlib import Path

from src.datos.cargador import cargar_dataset_json
from src.inventario.catalogo_hash import CatalogoHash
from src.inventario.catalogo_lineal import CatalogoLineal
from src.modelos.pedido import LineaPedido, Pedido
from src.modelos.producto import Producto
from src.pedidos.procesador_concurrente import (
    _armar_fragmentos,
    _cerrar_executor,
    procesar_pedidos_concurrente,
)
from src.pedidos.procesador_secuencial import procesar_pedidos_secuencial

DATASETS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "datasets"


def _catalogo(stocks: dict[int, int]) -> CatalogoHash:
    return CatalogoHash(
        [
            Producto(id_, f"Producto {id_}", "Ferretería y Herramientas", stock, 100.0)
            for id_, stock in stocks.items()
        ]
    )


class TestProcesadorConcurrente:
    def test_equivalencia_secuencial_vs_concurrente_demo_oral(self):
        prods, peds = cargar_dataset_json(DATASETS_DIR / "demo_oral.json")
        cat = CatalogoHash(prods)

        res_sec = procesar_pedidos_secuencial(cat, peds, descontar_stock=False)
        res_conc = procesar_pedidos_concurrente(cat, peds, max_workers=2, descontar_stock=False)

        assert res_sec.pedidos_procesados == res_conc.pedidos_procesados == 8
        assert res_sec.pedidos_cubiertos == res_conc.pedidos_cubiertos
        assert res_sec.pedidos_parciales == res_conc.pedidos_parciales
        assert res_sec.pedidos_imposibles == res_conc.pedidos_imposibles

        estados_sec = [r.estado for r in res_sec.resultados]
        estados_conc = [r.estado for r in res_conc.resultados]
        assert estados_sec == estados_conc

    def test_equivalencia_secuencial_vs_concurrente_pequeno(self):
        prods, peds = cargar_dataset_json(DATASETS_DIR / "pequeno.json")
        cat = CatalogoHash(prods)

        res_sec = procesar_pedidos_secuencial(cat, peds, descontar_stock=False)
        res_conc = procesar_pedidos_concurrente(cat, peds, max_workers=4, descontar_stock=False)

        assert res_sec.pedidos_procesados == res_conc.pedidos_procesados == 20
        assert res_sec.pedidos_cubiertos == res_conc.pedidos_cubiertos
        assert res_sec.pedidos_parciales == res_conc.pedidos_parciales
        assert res_sec.pedidos_imposibles == res_conc.pedidos_imposibles

    def test_fragmentos_llevan_solo_el_stock_referenciado(self):
        catalogo = _catalogo({i: i for i in range(1, 101)})
        pedidos = [Pedido(1, [LineaPedido(5, 1)]), Pedido(2, [LineaPedido(7, 1)])]
        fragmentos = _armar_fragmentos(catalogo, pedidos, workers=2)
        assert [stock for _, stock in fragmentos] == [{5: 5}, {7: 7}]
        assert [compactos for compactos, _ in fragmentos] == [[(1, ((5, 1),))], [(2, ((7, 1),))]]

    def test_descuento_delegado_al_secuencial(self):
        pedidos = [Pedido(i, [LineaPedido(1, 5)]) for i in (1, 2, 3)]
        cat_sec, cat_conc = _catalogo({1: 10}), _catalogo({1: 10})
        sec = procesar_pedidos_secuencial(cat_sec, pedidos, descontar_stock=True)
        conc = procesar_pedidos_concurrente(cat_conc, pedidos, descontar_stock=True)
        assert [r.estado for r in conc.resultados] == [r.estado for r in sec.resultados]
        assert cat_conc.buscar_por_id(1).stock == cat_sec.buscar_por_id(1).stock == 0
        assert conc.estrategia == "optimizado_concurrente_descuento_secuencial"

    def test_resultados_en_orden_original(self, dataset_pequeno):
        productos, pedidos = dataset_pequeno
        catalogo = CatalogoHash(productos)
        conc = procesar_pedidos_concurrente(catalogo, pedidos, max_workers=2)
        sec = procesar_pedidos_secuencial(catalogo, pedidos)
        assert [r.id_pedido for r in conc.resultados] == [p.id for p in pedidos]
        assert conc.resultados == sec.resultados

    def test_concurrencia_respeta_descuento_de_stock(self):
        prods_sec = [
            Producto(
                id=1, nombre="Taladro Percutor", categoria="Herramientas", stock=5, precio=500.0
            )
        ]
        prods_conc = [
            Producto(
                id=1, nombre="Taladro Percutor", categoria="Herramientas", stock=5, precio=500.0
            )
        ]

        pedidos = [
            Pedido(id=1, lineas=[LineaPedido(id_producto=1, cantidad=5)]),
            Pedido(id=2, lineas=[LineaPedido(id_producto=1, cantidad=5)]),
        ]

        cat_sec = CatalogoLineal(prods_sec)
        cat_conc = CatalogoHash(prods_conc)

        res_sec = procesar_pedidos_secuencial(
            cat_sec, pedidos, descontar_stock=True, politica_descuento="solo_cubiertos"
        )
        res_conc = procesar_pedidos_concurrente(
            cat_conc, pedidos, descontar_stock=True, politica_descuento="solo_cubiertos"
        )

        assert cat_sec.buscar_por_id(1).stock == 0
        assert cat_conc.buscar_por_id(1).stock == 0
        assert res_conc.pedidos_cubiertos == res_sec.pedidos_cubiertos == 1
        assert res_conc.pedidos_imposibles == res_sec.pedidos_imposibles == 1

    def test_procesador_concurrente_lista_vacia_y_cierre(self, catalogo_hash_muestra):
        res = procesar_pedidos_concurrente(catalogo_hash_muestra, [])
        assert res.pedidos_procesados == 0
        assert res.tiempo_ejecucion_ms == 0.0
        _cerrar_executor()
