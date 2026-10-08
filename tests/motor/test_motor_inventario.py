"""Pruebas unitarias y de integración para la fachada MotorInventario."""

from __future__ import annotations

from pathlib import Path

import pytest

from benchmarks.generar_datos import generar_dataset_sintetico
from src.inventario.catalogo_hash import CatalogoHash
from src.inventario.catalogo_lineal import CatalogoLineal
from src.modelos.pedido import ResumenProcesamiento
from src.modelos.producto import Producto
from src.motor.motor_inventario import MotorInventario

DATASETS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "datasets"


class TestMotorInventarioAPI:
    def test_cierre_etapa_2_con_pequeno_json(self):
        motor = MotorInventario(estrategia="baseline")
        ruta_pequeno = DATASETS_DIR / "pequeno.json"
        motor.cargar_dataset(ruta_pequeno)

        stats = motor.obtener_estadisticas()
        assert stats["total_productos"] == 100
        assert stats["total_pedidos"] == 20
        assert stats["estrategia"] == "baseline"

        prod_1 = motor.buscar_por_id(1)
        assert prod_1 is not None
        assert prod_1.id == 1

        res_nombre = motor.buscar_por_nombre("Premium")
        assert isinstance(res_nombre, list)

        resumen = motor.procesar_pedidos(descontar_stock=False)
        assert isinstance(resumen, ResumenProcesamiento)
        assert resumen.pedidos_procesados == 20
        assert (
            resumen.pedidos_cubiertos + resumen.pedidos_parciales + resumen.pedidos_imposibles
        ) == 20

        top_5 = motor.obtener_top_solicitados(k=5)
        assert len(top_5) == 5
        for prod, cant in top_5:
            assert isinstance(prod, Producto)
            assert cant > 0

    def test_alternancia_estrategia_baseline_y_optimizada(self):
        motor = MotorInventario(estrategia="baseline")
        motor.cargar_dataset(DATASETS_DIR / "pequeno.json")

        assert motor.estrategia == "baseline"
        assert isinstance(motor.catalogo, CatalogoLineal)

        motor.cambiar_estrategia("optimizado")
        assert motor.estrategia == "optimizado"
        assert isinstance(motor.catalogo, CatalogoHash)

        picking = motor.agrupar_pedidos()
        assert picking.total_pedidos == 20

        top = motor.obtener_top_solicitados(k=5)
        assert len(top) == 5

        p1 = motor.buscar_por_nombre("Premium", usar_cache=True)
        stats_c1 = motor.cache.obtener_estadisticas()
        assert stats_c1["busquedas"]["misses"] >= 1

        p2 = motor.buscar_por_nombre("Premium", usar_cache=True)
        assert p1 == p2
        stats_c2 = motor.cache.obtener_estadisticas()
        assert stats_c2["busquedas"]["hits"] >= 1

        res_lote = motor.procesar_pedidos(concurrente=True)
        assert res_lote.pedidos_procesados == 20

    def test_motor_inicializacion_optimizada(self, productos_muestra):
        motor = MotorInventario(productos=productos_muestra, estrategia="optimizado")
        assert motor.es_optimizado is True
        assert isinstance(motor.catalogo, CatalogoHash)

    def test_motor_cambio_estrategia_y_errores(self, motor_baseline):
        with pytest.raises(ValueError, match="Estrategia inválida"):
            motor_baseline.cambiar_estrategia("estrategia_falsa")

        motor_baseline.cambiar_estrategia("baseline")
        assert motor_baseline.es_optimizado is False

        motor_baseline.cambiar_estrategia("optimizado")
        assert motor_baseline.es_optimizado is True
        assert isinstance(motor_baseline.catalogo, CatalogoHash)

        motor_baseline.cambiar_estrategia("baseline")
        assert motor_baseline.es_optimizado is False
        assert isinstance(motor_baseline.catalogo, CatalogoLineal)

    def test_motor_busqueda_categoria_con_cache(self, motor_optimizado):
        prods1 = motor_optimizado.buscar_por_categoria("Herramientas", usar_cache=True)
        prods2 = motor_optimizado.buscar_por_categoria("Herramientas", usar_cache=True)
        assert prods1 == prods2
        assert len(prods1) > 0

    def test_motor_top_productos_con_cache(self, motor_optimizado):
        top1 = motor_optimizado.obtener_top_solicitados(k=5, usar_cache=True)
        top2 = motor_optimizado.calcular_top_productos(k=5, usar_cache=True)
        assert top1 == top2

    def test_motor_descuento_invalida_cache(self, motor_optimizado):
        motor_optimizado.buscar_por_nombre("taladro", usar_cache=True)
        assert len(motor_optimizado.cache._cache_busquedas) > 0
        motor_optimizado.procesar_pedidos(descontar_stock=True)
        assert len(motor_optimizado.cache._cache_busquedas) == 0

    def test_motor_estadisticas_completas(self, motor_optimizado):
        stats = motor_optimizado.obtener_estadisticas()
        assert stats["estrategia"] == "optimizado"
        assert stats["total_productos"] > 0
        assert "metricas_cache" in stats

    def test_motor_procesa_en_secuencial_por_defecto(self):
        motor = MotorInventario(estrategia="optimizado")
        motor.cargar_dataset(DATASETS_DIR / "grande.json")
        assert motor.procesar_pedidos().estrategia == "baseline_secuencial"

    def test_semilla_fija_produce_resultados_identicos(self):
        prods1, peds1 = generar_dataset_sintetico(50, 10, semilla=99)
        prods2, peds2 = generar_dataset_sintetico(50, 10, semilla=99)
        assert len(prods1) == len(prods2)
        assert len(peds1) == len(peds2)
        for p1, p2 in zip(prods1, prods2, strict=True):
            assert p1 == p2
        for ped1, ped2 in zip(peds1, peds2, strict=True):
            assert ped1 == ped2
