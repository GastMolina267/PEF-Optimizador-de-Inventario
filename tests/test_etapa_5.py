"""Pruebas unitarias y de integración para la Etapa 5: Medición, análisis y tests.

Verifica:
1. Equivalencia funcional estricta baseline vs. optimizado en datasets medianos y grandes.
2. Integridad de los scripts de benchmark y perfilado.
3. Existencia y validez de los artefactos de medición generados en docs/mediciones/.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.datos.cargador import cargar_dataset
from src.inventario.catalogo_hash import CatalogoHash
from src.inventario.catalogo_lineal import CatalogoLineal
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
MEDICIONES_DIR = BASE_DIR / "docs" / "mediciones"
DOCS_DIR = BASE_DIR / "docs"


class TestEquivalenciaEscalaMediana:
    """Verifica equivalencia matemática y de negocio sobre mediano.json."""

    @pytest.fixture(scope="class")
    @classmethod
    def datos_mediano(cls):
        ruta = DATASETS_DIR / "mediano.json"
        return cargar_dataset(ruta)

    def test_equivalencia_busquedas_id_y_nombre(self, datos_mediano):
        productos, _ = datos_mediano
        cat_lin = CatalogoLineal(productos)
        cat_hash = CatalogoHash(productos)

        # Muestreo de 50 productos
        for p in productos[::20]:
            assert cat_lin.buscar_por_id(p.id) == cat_hash.buscar_por_id(p.id)

            termino = p.nombre.split()[0].lower()
            res_lin = {prod.id for prod in cat_lin.buscar_por_nombre(termino)}
            res_hash = {prod.id for prod in cat_hash.buscar_por_nombre(termino)}
            assert res_lin == res_hash

    def test_equivalencia_top_n_sort_vs_heap(self, datos_mediano):
        productos, pedidos = datos_mediano
        cat_lin = CatalogoLineal(productos)
        cat_hash = CatalogoHash(productos)

        for k in (3, 5, 10):
            top_sort = calcular_top_solicitados_lineal(pedidos, cat_lin, k=k)
            top_heap = calcular_top_solicitados_heap(pedidos, cat_hash, k=k)

            assert len(top_sort) == len(top_heap)
            for (p_sort, cant_sort), (p_heap, cant_heap) in zip(top_sort, top_heap, strict=True):
                assert cant_sort == cant_heap
                assert p_sort.id == p_heap.id

    def test_equivalencia_procesamiento_pedidos_sec_vs_conc(self, datos_mediano):
        productos, pedidos = datos_mediano
        cat_lin = CatalogoLineal(productos)
        cat_hash = CatalogoHash(productos)

        res_sec = procesar_pedidos_secuencial(cat_lin, pedidos, descontar_stock=False)
        res_conc = procesar_pedidos_concurrente(cat_hash, pedidos, descontar_stock=False)

        assert res_sec.pedidos_procesados == res_conc.pedidos_procesados
        assert res_sec.pedidos_cubiertos == res_conc.pedidos_cubiertos
        assert res_sec.pedidos_parciales == res_conc.pedidos_parciales
        assert res_sec.pedidos_imposibles == res_conc.pedidos_imposibles

        # Muestreo de resultados individuales
        for p_sec, p_conc in zip(res_sec.resultados[:20], res_conc.resultados[:20], strict=True):
            assert p_sec.id_pedido == p_conc.id_pedido
            assert p_sec.estado == p_conc.estado
            assert p_sec.lineas_cubiertas == p_conc.lineas_cubiertas

    def test_equivalencia_alternativas_dp_vs_recursivo(self, datos_mediano):
        productos, _ = datos_mediano
        buscador = BuscadorAlternativas(productos)
        cat = productos[0].categoria

        # Comparar con candidatos limitados a 12 para evitar tiempo excesivo en recursión pura
        res_puro = buscador.buscar_alternativas(
            cat, 25000.0, usar_memoizacion=False, max_combinaciones=5, max_candidatos=12
        )
        res_memo = buscador.buscar_alternativas(
            cat, 25000.0, usar_memoizacion=True, max_combinaciones=5, max_candidatos=12
        )

        assert len(res_puro.combinaciones) == len(res_memo.combinaciones)
        for c_puro, c_memo in zip(res_puro.combinaciones, res_memo.combinaciones, strict=True):
            assert abs(c_puro.costo_total - c_memo.costo_total) < 1e-2


class TestEquivalenciaEscalaGrande:
    """Verifica operaciones a gran escala en grande.json (10.000 productos, 2.000 pedidos)."""

    @pytest.fixture(scope="class")
    @classmethod
    def datos_grande(cls):
        ruta = DATASETS_DIR / "grande.json"
        return cargar_dataset(ruta)

    def test_top_n_en_dataset_grande(self, datos_grande):
        productos, pedidos = datos_grande
        cat_hash = CatalogoHash(productos)
        top = calcular_top_solicitados_heap(pedidos, cat_hash, k=10)

        assert len(top) == 10
        # Verificar orden descendente estricto por demanda
        cantidades = [cant for _, cant in top]
        assert cantidades == sorted(cantidades, reverse=True)

    def test_agrupacion_batch_picking_en_dataset_grande(self, datos_grande):
        productos, pedidos = datos_grande
        cat_hash = CatalogoHash(productos)
        lote = agrupar_pedidos_batch(pedidos, cat_hash)

        assert lote.total_pedidos == len(pedidos)
        assert lote.total_productos_distintos > 0
        assert lote.total_unidades > 0


class TestArtefactosMedicionesGenerados:
    """Verifica que todos los informes exigidos por la Etapa 5 existan y contengan datos válidos."""

    def test_tabla_comparativa_existe(self):
        ruta_md = MEDICIONES_DIR / "tabla_comparativa.md"
        ruta_txt = MEDICIONES_DIR / "tabla_comparativa.txt"
        assert ruta_md.is_file()
        assert ruta_txt.is_file()
        contenido = ruta_md.read_text(encoding="utf-8")
        assert "Tabla Comparativa Oficial" in contenido
        assert "Speedup" in contenido
        assert "grande.json" in contenido

    def test_preparacion_pedidos_aisla_concurrencia(self):
        """La fila de preparación no debe mezclar catálogo lineal con el pool de procesos."""
        fuente = (BASE_DIR / "benchmarks" / "comparar.py").read_text(encoding="utf-8")
        bloque = fuente.split("# 6. Preparación", 1)[1].split("return filas_resultados", 1)[0]
        assert "procesar_pedidos_secuencial, cat_hash" in bloque
        assert "procesar_pedidos_concurrente, cat_hash" in bloque
        assert "cat_lineal" not in bloque
        assert "aísla" in bloque.lower() or "aisla" in bloque.lower()

    def test_informe_cprofile_existe(self):
        ruta_cprofile = MEDICIONES_DIR / "cprofile_resumen.txt"
        assert ruta_cprofile.is_file()
        contenido = ruta_cprofile.read_text(encoding="utf-8")
        assert "PERFILADO CPROFILE" in contenido
        assert "CUMULATIVE TIME" in contenido

    def test_informe_line_profiler_existe(self):
        ruta_lp = MEDICIONES_DIR / "line_profiler_resumen.txt"
        assert ruta_lp.is_file()
        contenido = ruta_lp.read_text(encoding="utf-8")
        assert "LINE_PROFILER" in contenido
        assert "CatalogoLineal.buscar_por_id" in contenido

    def test_informe_memoria_existe(self):
        ruta_mem = MEDICIONES_DIR / "memoria_resumen.txt"
        assert ruta_mem.is_file()
        contenido = ruta_mem.read_text(encoding="utf-8")
        assert "INFORME DE PERFILADO DE MEMORIA" in contenido
        assert "Catálogo Hash" in contenido
        assert "Min-Heap Acotado" in contenido

    def test_documento_analisis_completo(self):
        ruta_analisis = DOCS_DIR / "analisis.md"
        assert ruta_analisis.is_file()
        contenido = ruta_analisis.read_text(encoding="utf-8")
        assert "Análisis de Complejidad, Perfilado y Optimización" in contenido
        assert "O(N log k)" in contenido
        assert "O(2^N)" in contenido
        assert "Memoización vs. Caching" in contenido
        assert "ProcessPoolExecutor" in contenido
        assert "Defensa Oral" in contenido
