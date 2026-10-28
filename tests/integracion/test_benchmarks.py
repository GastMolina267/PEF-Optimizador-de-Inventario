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


def test_speedup_hash_vs_lineal_asercion() -> None:
    """Valida formalmente que la búsqueda por ID en tabla Hash supere a la lista lineal."""
    import time

    prods, _ = cargar_dataset_json(DATASETS_DIR / "pequeno.json")
    cat_lineal = CatalogoLineal(prods)
    cat_hash = CatalogoHash(prods)

    # Warmup
    for i in range(1, 50):
        cat_lineal.buscar_por_id(i)
        cat_hash.buscar_por_id(i)

    t0 = time.perf_counter()
    for _ in range(100):
        for i in range(1, 100):
            cat_lineal.buscar_por_id(i)
    t_lineal = time.perf_counter() - t0

    t0 = time.perf_counter()
    for _ in range(100):
        for i in range(1, 100):
            cat_hash.buscar_por_id(i)
    t_hash = time.perf_counter() - t0

    speedup = t_lineal / max(t_hash, 1e-9)
    # Exigir un speedup mínimo de 3.0x para prevenir regresiones algorítmicas hacia O(n)
    assert speedup > 3.0, (
        f"Alerta de regresión algorítmica: el speedup del catálogo hash ({speedup:.2f}x) "
        "no alcanzó el umbral mínimo aceptable de 3.0x frente a la lista lineal."
    )
