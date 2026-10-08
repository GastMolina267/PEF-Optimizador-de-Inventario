"""Pruebas unitarias para el ranking de productos más solicitados."""

from __future__ import annotations

from pathlib import Path

from src.inventario.catalogo_hash import CatalogoHash
from src.inventario.catalogo_lineal import CatalogoLineal
from src.ranking.top_productos import (
    calcular_top_solicitados,
    calcular_top_solicitados_heap,
    calcular_top_solicitados_lineal,
)

DATASETS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "datasets"


class TestRankingTopProductos:
    def test_top_3_mas_solicitados_lineal(
        self,
        dataset_pequeno: tuple,
    ):
        prods, peds = dataset_pequeno
        catalogo = CatalogoLineal(prods)
        top = calcular_top_solicitados_lineal(peds, catalogo, k=3)
        assert len(top) == 3
        # Orden descendente por demanda
        assert top[0][1] >= top[1][1] >= top[2][1]

    def test_top_n_con_k_mayor_que_productos_unicos(
        self,
        dataset_pequeno: tuple,
    ):
        prods, peds = dataset_pequeno
        catalogo = CatalogoLineal(prods)
        top = calcular_top_solicitados_lineal(peds, catalogo, k=5000)
        assert len(top) <= len(prods)

    def test_top_solicitados_heap_vs_lineal_equivalencia(self, dataset_pequeno: tuple):
        prods, peds = dataset_pequeno
        cat = CatalogoHash(prods)
        top_sort = calcular_top_solicitados_lineal(peds, cat, k=10)
        top_heap = calcular_top_solicitados_heap(peds, cat, k=10)

        assert len(top_sort) == len(top_heap)
        demandas_sort = [d for _, d in top_sort]
        demandas_heap = [d for _, d in top_heap]
        assert demandas_sort == demandas_heap

    def test_top_solicitados_casos_borde(
        self, pedidos_muestra: list, catalogo_hash_muestra: CatalogoHash
    ):
        assert calcular_top_solicitados_lineal(pedidos_muestra, catalogo_hash_muestra, k=0) == []
        assert calcular_top_solicitados_lineal([], catalogo_hash_muestra, k=5) == []
        assert calcular_top_solicitados_heap(pedidos_muestra, catalogo_hash_muestra, k=-1) == []
        assert calcular_top_solicitados_heap([], catalogo_hash_muestra, k=5) == []

        res = calcular_top_solicitados(pedidos_muestra, catalogo_hash_muestra, k=3, metodo="heap")
        assert len(res) <= 3
        res_lin = calcular_top_solicitados(
            pedidos_muestra, catalogo_hash_muestra, k=3, metodo="lineal"
        )
        assert len(res_lin) <= 3
