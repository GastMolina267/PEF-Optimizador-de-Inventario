"""Pruebas de benchmark con pytest-benchmark para detectar regresiones de rendimiento."""

from __future__ import annotations

from pathlib import Path

from src.datos.cargador import cargar_dataset_json
from src.inventario.catalogo_hash import CatalogoHash
from src.inventario.catalogo_lineal import CatalogoLineal
from src.pedidos.agrupador import agrupar_pedidos_batch
from src.pedidos.combinaciones import BuscadorAlternativas
from src.pedidos.procesador_secuencial import procesar_pedidos_secuencial
from src.ranking.top_productos import calcular_top_solicitados_heap

DATASETS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "datasets"


def test_benchmark_busqueda_hash_id(benchmark):
    prods, _ = cargar_dataset_json(DATASETS_DIR / "pequeno.json")
    cat = CatalogoHash(prods)
    resultado = benchmark(cat.buscar_por_id, 50)
    assert resultado is not None


def test_benchmark_busqueda_lineal_id(benchmark):
    prods, _ = cargar_dataset_json(DATASETS_DIR / "pequeno.json")
    cat = CatalogoLineal(prods)
    resultado = benchmark(cat.buscar_por_id, 50)
    assert resultado is not None


def test_benchmark_top_n_heap(benchmark):
    prods, peds = cargar_dataset_json(DATASETS_DIR / "pequeno.json")
    cat = CatalogoHash(prods)
    resultado = benchmark(calcular_top_solicitados_heap, peds, cat, k=5)
    assert len(resultado) == 5


def test_benchmark_batch_picking(benchmark):
    prods, peds = cargar_dataset_json(DATASETS_DIR / "pequeno.json")
    cat = CatalogoHash(prods)
    lote = benchmark(agrupar_pedidos_batch, peds, cat)
    assert lote.total_pedidos == 20


def test_benchmark_combinaciones_dp(benchmark):
    prods, _ = cargar_dataset_json(DATASETS_DIR / "demo_oral.json")
    buscador = BuscadorAlternativas(prods)
    resultado = benchmark(
        buscador.buscar_alternativas,
        "Ferretería y Herramientas",
        30000.0,
        usar_memoizacion=True,
    )
    assert resultado.total_combinaciones >= 1


def test_benchmark_procesamiento_pedidos(benchmark):
    prods, peds = cargar_dataset_json(DATASETS_DIR / "pequeno.json")
    cat = CatalogoHash(prods)
    resumen = benchmark(procesar_pedidos_secuencial, cat, peds, descontar_stock=False)
    assert resumen.pedidos_procesados == 20
