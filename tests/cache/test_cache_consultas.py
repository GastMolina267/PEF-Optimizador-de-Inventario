"""Pruebas unitarias para el gestor de caché LRU con invalidación."""

from __future__ import annotations

import pytest

from src.cache.cache_consultas import CacheLRU, GestorCacheConsultas, MetricasCache


class TestCacheConsultas:
    def test_cache_lru_capacidad_y_eviccion(self):
        with pytest.raises(ValueError, match="mayor a 0"):
            CacheLRU(capacidad_maxima=0)

        cache = CacheLRU[str](capacidad_maxima=2)
        assert cache.capacidad == 2

        cache.guardar("a", "1")
        cache.guardar("b", "2")
        assert len(cache) == 2

        # Actualizar clave existente
        cache.guardar("a", "1_actualizado")
        assert cache.obtener("a") == "1_actualizado"

        # Provocar evicción de 'b'
        cache.guardar("c", "3")
        assert cache.metricas.evicciones == 1
        assert cache.obtener("b") is None
        assert cache.obtener("c") == "3"

        # Invalidar clave
        assert cache.invalidar_clave("a") is True
        assert cache.invalidar_clave("inexistente") is False

        # Limpiar
        cache.limpiar()
        assert len(cache) == 0

    def test_metricas_cache_consultas(self):
        m = MetricasCache()
        assert m.total_consultas == 0
        assert m.tasa_aciertos == 0.0

    def test_gestor_cache_consultas_operaciones(self, productos_muestra):
        gestor = GestorCacheConsultas(capacidad_busquedas=4, capacidad_ranking=4)
        p = productos_muestra[:2]

        # Búsqueda por categoría
        assert gestor.obtener_busqueda_categoria("Herramientas") is None
        gestor.guardar_busqueda_categoria("Herramientas", p)
        assert gestor.obtener_busqueda_categoria("Herramientas") == p

        # Invalidación por nuevos pedidos
        gestor.guardar_top_solicitados(5, [(p[0], 10)])
        assert gestor.obtener_top_solicitados(5) is not None
        gestor.invalidar_por_nuevos_pedidos()
        assert gestor.obtener_top_solicitados(5) is None

        # Invalidación por mutación de stock
        assert gestor.obtener_busqueda_categoria("Herramientas") == p
        gestor.invalidar_por_mutacion_stock()
        assert gestor.obtener_busqueda_categoria("Herramientas") is None

        # Estadísticas consolidadas
        stats = gestor.obtener_estadisticas()
        assert "tasa_aciertos_global_pct" in stats
        assert "total_entradas_activas" in stats
