"""Pruebas unitarias y de integración para la Etapa 3 (Motor Optimizado).

Valida los criterios de cierre de las 5 subetapas:
3.1 Catálogo hash vs. Catálogo lineal: equivalencia de respuestas en pequeno y mediano.
3.2 Agrupación (batch picking) y Top-N: equivalencia entre sort total y heapq.
3.3 Combinaciones y memoización: equivalencia entre recursión pura y DP memoizada;
    aislamiento de universo de candidatos.
3.4 Caché inteligente con invalidación: hits en repetición y misses tras invalidación reactiva.
3.5 Concurrencia con ProcessPoolExecutor: equivalencia estricta contra el procesador secuencial.
Cierre general de la Etapa 3: alternancia dinámica de estrategias sobre los mismos datasets.
"""

from __future__ import annotations

from pathlib import Path

from src.cache.cache_consultas import GestorCacheConsultas
from src.datos.cargador import cargar_dataset_json
from src.inventario.catalogo_hash import CatalogoHash
from src.inventario.catalogo_lineal import CatalogoLineal
from src.modelos.producto import Producto
from src.motor.motor_inventario import MotorInventario
from src.pedidos.agrupador import agrupar_pedidos_batch
from src.pedidos.combinaciones import BuscadorAlternativas
from src.pedidos.procesador_concurrente import procesar_pedidos_concurrente
from src.pedidos.procesador_secuencial import procesar_pedidos_secuencial
from src.ranking.top_productos import (
    calcular_top_solicitados_heap,
    calcular_top_solicitados_lineal,
)

BASE_DIR = Path(__file__).resolve().parent.parent
DATASETS_DIR = BASE_DIR / "data" / "datasets"


class TestSubetapa31CatalogoHash:
    """3.1 Catálogo hash: dict por id + índices. Misma respuesta que el baseline."""

    def test_equivalencia_busquedas_en_pequeno(self):
        prods, _ = cargar_dataset_json(DATASETS_DIR / "pequeno.json")
        cat_lineal = CatalogoLineal(prods)
        cat_hash = CatalogoHash(prods)

        assert len(cat_lineal) == len(cat_hash) == 100

        # Equivalencia en búsqueda por ID existente
        for id_prod in [1, 25, 50, 75, 100]:
            p_lin = cat_lineal.buscar_por_id(id_prod)
            p_hash = cat_hash.buscar_por_id(id_prod)
            assert p_lin is not None and p_hash is not None
            assert p_lin == p_hash

        # Equivalencia en ID inexistente
        assert cat_lineal.buscar_por_id(9999) is None
        assert cat_hash.buscar_por_id(9999) is None

        # Equivalencia en búsqueda por categoría
        cats = ["Ferretería y Herramientas", "Electricidad e Iluminación", "Pinturas y Adhesivos"]
        for c in cats:
            res_lin = sorted([p.id for p in cat_lineal.buscar_por_categoria(c)])
            res_hash = sorted([p.id for p in cat_hash.buscar_por_categoria(c)])
            assert res_lin == res_hash

    def test_equivalencia_busquedas_en_mediano(self):
        prods, _ = cargar_dataset_json(DATASETS_DIR / "mediano.json")
        cat_lineal = CatalogoLineal(prods)
        cat_hash = CatalogoHash(prods)

        assert len(cat_lineal) == len(cat_hash) == 1000

        # Muestreo de IDs en mediano
        for id_prod in [1, 100, 250, 500, 750, 999]:
            assert cat_lineal.buscar_por_id(id_prod) == cat_hash.buscar_por_id(id_prod)

        # Búsqueda por texto coincidente
        res_lin = sorted([p.id for p in cat_lineal.buscar_por_nombre("Premium")])
        res_hash = sorted([p.id for p in cat_hash.buscar_por_nombre("Premium")])
        assert res_lin == res_hash


class TestSubetapa32AgrupacionYTopN:
    """3.2 Agrupación y Top-N: Picking consolidado y heapq vs. sort."""

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
        assert 2 in pedidos_demandantes and 4 in pedidos_demandantes

    def test_equivalencia_top_n_sort_vs_heap(self):
        prods, peds = cargar_dataset_json(DATASETS_DIR / "mediano.json")
        cat = CatalogoHash(prods)

        top_sort = calcular_top_solicitados_lineal(peds, cat, k=10)
        top_heap = calcular_top_solicitados_heap(peds, cat, k=10)

        assert len(top_sort) == len(top_heap) == 10

        # Comprobar que las cantidades demandadas son idénticas y ordenadas de mayor a menor
        cantidades_sort = [cant for _, cant in top_sort]
        cantidades_heap = [cant for _, cant in top_heap]
        assert cantidades_sort == cantidades_heap
        assert cantidades_heap == sorted(cantidades_heap, reverse=True)


class TestSubetapa33CombinacionesYMemoizacion:
    """3.3 Combinaciones y memoización: equivalencia y preservación de universo."""

    def test_equivalencia_recursivo_vs_memoizado(self):
        prods, _ = cargar_dataset_json(DATASETS_DIR / "demo_oral.json")
        buscador = BuscadorAlternativas(prods)

        # Buscamos alternativas en 'Ferretería y Herramientas' con presupuesto 50.000
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

        # Costos idénticos
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

        assert ids_res1.issubset({1, 2})
        assert ids_res2.issubset({3, 4})
        assert len(ids_res1.intersection(ids_res2)) == 0


class TestSubetapa34CacheConInvalidacion:
    """3.4 Caché LRU con invalidación reactiva."""

    def test_hit_en_repeticion_y_miss_tras_invalidar(self):
        gestor = GestorCacheConsultas(capacidad_busquedas=10, capacidad_ranking=5)

        # 1. Primera consulta: Miss
        assert gestor.obtener_busqueda_nombre("taladro") is None
        stats_1 = gestor.obtener_estadisticas()
        assert stats_1["busquedas"]["misses"] == 1
        assert stats_1["busquedas"]["hits"] == 0

        # 2. Guardar en caché y reconsultar: Hit
        prods_mock = [Producto(1, "Taladro 750W", "Ferretería", 10, 5000.0)]
        gestor.guardar_busqueda_nombre("taladro", prods_mock)

        recuperado = gestor.obtener_busqueda_nombre("taladro")
        assert recuperado == prods_mock
        stats_2 = gestor.obtener_estadisticas()
        assert stats_2["busquedas"]["hits"] == 1

        # 3. Invalidación reactiva por mutación de stock: Miss
        gestor.invalidar_por_mutacion_stock()
        assert gestor.obtener_busqueda_nombre("taladro") is None
        stats_3 = gestor.obtener_estadisticas()
        assert stats_3["busquedas"]["misses"] == 2


class TestSubetapa35Concurrencia:
    """3.5 Concurrencia con ProcessPoolExecutor: equivalencia estricta frente a secuencial."""

    def test_equivalencia_secuencial_vs_concurrente_demo_oral(self):
        prods, peds = cargar_dataset_json(DATASETS_DIR / "demo_oral.json")
        cat = CatalogoHash(prods)

        res_sec = procesar_pedidos_secuencial(cat, peds, descontar_stock=False)
        res_conc = procesar_pedidos_concurrente(cat, peds, max_workers=2, descontar_stock=False)

        assert res_sec.pedidos_procesados == res_conc.pedidos_procesados == 8
        assert res_sec.pedidos_cubiertos == res_conc.pedidos_cubiertos
        assert res_sec.pedidos_parciales == res_conc.pedidos_parciales
        assert res_sec.pedidos_imposibles == res_conc.pedidos_imposibles

        # Mismo estado para cada pedido individual
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


class TestCierreEtapa3MotorInventario:
    """Cierre de la Etapa 3: El motor permite alternar dinámicamente estrategias."""

    def test_alternancia_estrategia_baseline_y_optimizada(self):
        motor = MotorInventario(estrategia="baseline")
        motor.cargar_dataset(DATASETS_DIR / "pequeno.json")

        assert motor.estrategia == "baseline"
        assert isinstance(motor.catalogo, CatalogoLineal)

        # Conmutar dinámicamente a optimizado
        motor.cambiar_estrategia("optimizado")
        assert motor.estrategia == "optimizado"
        assert isinstance(motor.catalogo, CatalogoHash)

        # Operar en modo optimizado: Batch picking, Top-N Heap, Alternativas
        picking = motor.agrupar_pedidos()
        assert picking.total_pedidos == 20

        top = motor.obtener_top_solicitados(k=5)
        assert len(top) == 5

        # Búsqueda con caché
        p1 = motor.buscar_por_nombre("Premium", usar_cache=True)
        stats_c1 = motor.cache.obtener_estadisticas()
        assert stats_c1["busquedas"]["misses"] >= 1

        p2 = motor.buscar_por_nombre("Premium", usar_cache=True)
        assert p1 == p2
        stats_c2 = motor.cache.obtener_estadisticas()
        assert stats_c2["busquedas"]["hits"] >= 1

        # Procesar pedidos con concurrencia
        res_lote = motor.procesar_pedidos(concurrente=True)
        assert res_lote.pedidos_procesados == 20
