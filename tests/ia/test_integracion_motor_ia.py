"""Pruebas de integración del subsistema de Inteligencia Artificial con MotorInventario."""

from __future__ import annotations

import pytest

from src.datos.cargador import cargar_dataset_json
from src.ia.tipos import EstrategiaPrediccion, MetricasModelo, NivelRiesgo
from src.modelos.pedido import LineaPedido, Pedido
from src.modelos.producto import Producto
from src.motor.motor_inventario import EstrategiaMotor, MotorInventario


@pytest.fixture
def productos_prueba() -> list[Producto]:
    """Catálogo mínimo para pruebas del motor."""
    return [
        Producto(id=1, nombre="Clavos 1 pulgada", categoria="Fijaciones", stock=200, precio=5.0),
        Producto(
            id=2, nombre="Sierra Circular", categoria="Herramientas", stock=3, precio=45000.0
        ),
        Producto(
            id=3, nombre="Guantes de Seguridad", categoria="Seguridad", stock=0, precio=1200.0
        ),
    ]


@pytest.fixture
def pedidos_prueba() -> list[Pedido]:
    """Pedidos de prueba asociados."""
    return [
        Pedido(id=1, lineas=[LineaPedido(id_producto=1, cantidad=10)]),
        Pedido(id=2, lineas=[LineaPedido(id_producto=2, cantidad=5)]),
        Pedido(id=3, lineas=[LineaPedido(id_producto=3, cantidad=2)]),
    ]


class TestIntegracionMotorIA:
    """Verifica la orquestación de la IA dentro de la fachada MotorInventario."""

    def test_motor_inicializa_predictor_ia(self, productos_prueba: list[Producto]) -> None:
        """Verifica que MotorInventario exponga el predictor de IA adecuadamente."""
        motor = MotorInventario(productos=productos_prueba, estrategia=EstrategiaMotor.OPTIMIZADO)
        assert motor.predictor_ia is not None
        stats = motor.obtener_estadisticas()
        assert "modelo_ia_entrenado" in stats

    def test_predecir_quiebres_convencional(
        self, productos_prueba: list[Producto], pedidos_prueba: list[Pedido]
    ) -> None:
        """Verifica la ejecución de la regla analítica convencional O(1) desde el motor."""
        motor = MotorInventario(productos=productos_prueba, pedidos=pedidos_prueba)
        resultados = motor.predecir_quiebres_stock(estrategia=EstrategiaPrediccion.CONVENCIONAL)

        assert len(resultados) == len(productos_prueba)
        # Producto 3 tiene stock 0 -> debe ser clasificado en riesgo crítico
        item_critico = next(r for r in resultados if r.id_producto == 3)
        assert item_critico.riesgo == NivelRiesgo.CRITICO
        assert item_critico.alerta_quiebre is True
        assert item_critico.estrategia == EstrategiaPrediccion.CONVENCIONAL

    def test_entrenar_modelo_ia_desde_motor(self, productos_prueba: list[Producto]) -> None:
        """Verifica que entrenar_modelo_ia ajuste el modelo y retorne métricas válidas."""
        motor = MotorInventario(productos=productos_prueba)
        metricas = motor.entrenar_modelo_ia(seed=42, periodos=5, pedidos_por_periodo=10)

        assert isinstance(metricas, MetricasModelo)
        assert motor.predictor_ia.modelo_ia.esta_entrenado is True
        assert motor.obtener_estadisticas()["modelo_ia_entrenado"] is True

    def test_predecir_quiebres_estrategias_conmutables(
        self, productos_prueba: list[Producto], pedidos_prueba: list[Pedido]
    ) -> None:
        """Verifica que predecir_quiebres_stock funcione con las 3 estrategias."""
        motor = MotorInventario(productos=productos_prueba, pedidos=pedidos_prueba)
        motor.entrenar_modelo_ia(seed=42, periodos=6, pedidos_por_periodo=10)

        res_conv = motor.predecir_quiebres_stock(estrategia=EstrategiaPrediccion.CONVENCIONAL)
        res_ia = motor.predecir_quiebres_stock(estrategia=EstrategiaPrediccion.IA)
        res_hib = motor.predecir_quiebres_stock(estrategia=EstrategiaPrediccion.HIBRIDA)

        assert len(res_conv) == len(res_ia) == len(res_hib) == len(productos_prueba)
        for r_c, r_i, r_h in zip(res_conv, res_ia, res_hib, strict=False):
            assert r_c.estrategia == EstrategiaPrediccion.CONVENCIONAL
            assert r_i.estrategia == EstrategiaPrediccion.IA
            assert r_h.estrategia == EstrategiaPrediccion.HIBRIDA

    def test_integracion_dataset_demo_oral(self) -> None:
        """Verifica la inferencia predictiva sobre el dataset canónico demo_oral.json."""
        prods, pedidos = cargar_dataset_json("data/datasets/demo_oral.json")
        motor = MotorInventario(
            productos=prods, pedidos=pedidos, estrategia=EstrategiaMotor.OPTIMIZADO
        )

        resultados = motor.predecir_quiebres_stock(estrategia=EstrategiaPrediccion.HIBRIDA)
        assert len(resultados) == len(prods)
        # Todos los productos deben tener latencia positiva y probabilidad acotada
        for r in resultados:
            assert r.tiempo_inferencia_us >= 0.0
            assert 0.0 <= r.probabilidad_quiebre <= 1.0
            assert r.nombre_producto
