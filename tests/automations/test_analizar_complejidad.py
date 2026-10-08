"""Pruebas unitarias para el análisis de complejidad y derivación AST."""

from __future__ import annotations

from pathlib import Path

from automations.analizar_complejidad import (
    EvidenciaAST,
    _rastros_evidencia,
    analizar_repositorio,
)
from automations.inventario_funciones import (
    FUNCIONES_FUNDAMENTALES,
    MODULOS_FUNDAMENTALES,
    resolver_raiz,
)

BASE_DIR = resolver_raiz(Path(__file__))


def _informe_por_nombre(nombre: str):
    for inf in analizar_repositorio(BASE_DIR):
        if inf.funcion.nombre_calificado == nombre:
            return inf
    raise AssertionError(f"No se analizó {nombre}")


class TestInventarioFundamental:
    def test_modulos_existen_y_no_son_ui(self):
        for ruta in MODULOS_FUNDAMENTALES:
            assert (BASE_DIR / ruta).is_file()
            assert not ruta.startswith("src/ui/")
            assert not ruta.startswith("tests/")

    def test_cubre_operaciones_del_enunciado(self):
        nombres = {f.nombre_calificado for f in FUNCIONES_FUNDAMENTALES}
        assert "CatalogoLineal.buscar_por_id" in nombres
        assert "CatalogoHash.buscar_por_id" in nombres
        assert "agrupar_pedidos_batch" in nombres
        assert "calcular_top_solicitados_heap" in nombres
        assert "BuscadorAlternativas._resolver_dp_memo" in nombres
        assert "procesar_pedidos_concurrente" in nombres
        assert "CacheLRU.obtener" in nombres


class TestDerivacionAST:
    def test_busqueda_lineal_es_o_n(self):
        inf = _informe_por_nombre("CatalogoLineal.buscar_por_id")
        assert inf.evidencia.recorre_lista_productos
        assert inf.evidencia.profundidad_bucles == 1
        promedio = inf.promedio.replace(" ", "").lower()
        peor = inf.peor.replace(" ", "").lower()
        assert "θ(n)" in promedio or "theta(n)" in promedio
        assert "o(n)" in peor
        assert "θ(1)" not in promedio
        assert "o(1)" not in promedio

    def test_busqueda_hash_es_o_1(self):
        inf = _informe_por_nombre("CatalogoHash.buscar_por_id")
        assert inf.evidencia.accesos_hash
        assert inf.evidencia.profundidad_bucles == 0
        assert "1" in inf.promedio

    def test_top_n_sort_vs_heap(self):
        sort = _informe_por_nombre("calcular_top_solicitados_lineal")
        heap = _informe_por_nombre("calcular_top_solicitados_heap")
        assert sort.evidencia.llamadas_sorted
        assert heap.evidencia.llamadas_heapq
        assert "log" in sort.peor.lower()
        assert "log k" in heap.peor.lower() or "log k" in heap.promedio.lower()

    def test_combinaciones_recursion_vs_memo(self):
        puro = _informe_por_nombre("BuscadorAlternativas._resolver_recursivo_puro")
        memo = _informe_por_nombre("BuscadorAlternativas._resolver_dp_memo")
        assert puro.evidencia.es_recursiva
        assert not puro.evidencia.usa_memo
        assert "2" in puro.peor
        assert memo.evidencia.es_recursiva
        assert memo.evidencia.usa_memo
        assert "N" in memo.peor or "n" in memo.peor.lower()

    def test_concurrencia_detecta_process_pool(self):
        inf = _informe_por_nombre("procesar_pedidos_concurrente")
        assert inf.evidencia.usa_process_pool
        assert "IPC" in inf.promedio or "IPC" in inf.peor

    def test_justificacion_cita_el_cuerpo(self):
        inf = _informe_por_nombre("CatalogoHash.buscar_por_id")
        assert inf.justificacion
        assert any(
            token in inf.justificacion.lower() for token in ("hash", "dict", "get", "bucle")
        )

    def test_rastros_de_evidencia_en_orden(self):
        evidencia = EvidenciaAST(profundidad_bucles=2, llamadas_heapq=True, usa_memo=True)
        evidencia.accesos_hash.append("dict.get")
        assert _rastros_evidencia(evidencia) == ["bucles×2", "hash", "heapq", "memo"]
