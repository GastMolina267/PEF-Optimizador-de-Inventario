"""Pruebas unitarias para combinaciones de alternativas y DP memoizada."""

from __future__ import annotations

from pathlib import Path

from src.datos.cargador import cargar_dataset_json
from src.modelos.producto import Producto
from src.pedidos.combinaciones import (
    BuscadorAlternativas,
    CombinacionAlternativa,
    _agregar_hasta_limite,
)

DATASETS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "datasets"


class TestCombinacionesDP:
    def test_equivalencia_recursivo_vs_memoizado(self):
        prods, _ = cargar_dataset_json(DATASETS_DIR / "demo_oral.json")
        buscador = BuscadorAlternativas(prods)

        res_memo = buscador.buscar_alternativas(
            categoria="Ferretería y Herramientas",
            presupuesto_maximo=50000.0,
            usar_memoizacion=True,
        )
        res_puro = buscador.buscar_alternativas(
            categoria="Ferretería y Herramientas",
            presupuesto_maximo=50000.0,
            usar_memoizacion=False,
        )

        assert res_memo.total_combinaciones == res_puro.total_combinaciones
        assert res_memo.total_combinaciones > 0

        costos_memo = [c.costo_total for c in res_memo.combinaciones]
        costos_puro = [c.costo_total for c in res_puro.combinaciones]
        assert costos_memo == costos_puro

    def test_memo_no_mezcla_universos_diferentes(self):
        prods1 = [
            Producto(1, "A", "CatX", 10, 100.0),
            Producto(2, "B", "CatX", 10, 200.0),
        ]
        prods2 = [
            Producto(3, "C", "CatX", 10, 150.0),
            Producto(4, "D", "CatX", 10, 250.0),
        ]

        buscador1 = BuscadorAlternativas(prods1)
        res1 = buscador1.buscar_alternativas("CatX", 300.0, usar_memoizacion=True)

        buscador2 = BuscadorAlternativas(prods2)
        res2 = buscador2.buscar_alternativas("CatX", 300.0, usar_memoizacion=True)

        ids_res1 = {p.id for c in res1.combinaciones for p in c.productos}
        ids_res2 = {p.id for c in res2.combinaciones for p in c.productos}
        assert ids_res1.isdisjoint(ids_res2)

    def test_buscador_alternativas_metodos_auxiliares(self, productos_muestra):
        buscador = BuscadorAlternativas(productos_muestra)
        comb = CombinacionAlternativa(productos=[productos_muestra[0]], costo_total=12500.0)
        assert comb.cantidad_items == 1

        res = buscador.buscar_alternativas("Herramientas", 15000.0)
        assert res.total_combinaciones > 0
        buscador.limpiar_cache()
        assert len(buscador._memo_cache) == 0

    def test_agregar_hasta_limite_conserva_el_comportamiento_original(self):
        resultados = [[0]]
        _agregar_hasta_limite(resultados, iter([[1], [2], [3]]), limite=1)
        # Agrega y después compara: con un elemento previo, queda uno por encima del límite.
        assert resultados == [[0], [1]]
        vacio: list[list[int]] = []
        _agregar_hasta_limite(vacio, iter([[1], [2], [3]]), limite=2)
        assert vacio == [[1], [2]]
