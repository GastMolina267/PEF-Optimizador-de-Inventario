"""Pruebas rigurosas de presupuesto de memoria heap (tracemalloc) y no regresión de latencia."""

from __future__ import annotations

import gc
import time
import tracemalloc

import pytest

from src.datos.cargador import cargar_dataset_json
from src.ia.modelos import ModeloPredictorIA
from src.ia.tipos import EstrategiaPrediccion
from src.motor.motor_inventario import EstrategiaMotor, MotorInventario

# Presupuestos estrictos de memoria heap acordados para el Proyecto Final
MAX_MEMORIA_MODELO_MB = 3.0  # El modelo en memoria no puede superar 3 MB
MAX_DELTA_INFERENCIA_CONVENCIONAL_MB = 0.5  # La heurística O(1) no debe alocar más de 0.5 MB
MAX_FUGA_MEMORIA_KB = 128.0  # 500 evaluaciones no deben retener más de 128 KB tras GC


@pytest.fixture
def motor_con_datos() -> MotorInventario:
    """Instancia de MotorInventario con dataset real para mediciones de memoria."""
    prods, peds = cargar_dataset_json("data/datasets/demo_oral.json")
    motor = MotorInventario(productos=prods, pedidos=peds, estrategia=EstrategiaMotor.OPTIMIZADO)
    if not motor.predictor_ia.modelo_ia.esta_entrenado:
        motor.entrenar_modelo_ia(seed=42, periodos=10, pedidos_por_periodo=15)
    return motor


class TestPresupuestoMemoriaIA:
    """Verificación de límites presupuestarios de memoria heap con tracemalloc."""

    def test_presupuesto_memoria_modelo_ia(self) -> None:
        """Verifica que el modelo de scikit-learn consuma menos de 3 MB de memoria heap."""
        gc.collect()
        tracemalloc.start()
        inicio_bytes, _ = tracemalloc.get_traced_memory()

        modelo = ModeloPredictorIA.cargar("data/modelos/predictor_ia.joblib")
        assert modelo.esta_entrenado is True

        _, pico_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        consumo_mb = (pico_bytes - inicio_bytes) / (1024.0 * 1024.0)
        assert consumo_mb < MAX_MEMORIA_MODELO_MB, (
            f"El modelo de IA excedió el presupuesto de memoria: "
            f"{consumo_mb:.2f} MB > {MAX_MEMORIA_MODELO_MB} MB"
        )

    def test_presupuesto_memoria_inferencia_convencional(
        self, motor_con_datos: MotorInventario
    ) -> None:
        """Verifica que la regla convencional O(1) no genere picos excesivos de heap."""
        gc.collect()
        tracemalloc.start()
        inicio_bytes, _ = tracemalloc.get_traced_memory()

        resultados = motor_con_datos.predecir_quiebres_stock(
            estrategia=EstrategiaPrediccion.CONVENCIONAL
        )
        assert len(resultados) > 0

        _, pico_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        delta_mb = (pico_bytes - inicio_bytes) / (1024.0 * 1024.0)
        assert delta_mb < MAX_DELTA_INFERENCIA_CONVENCIONAL_MB, (
            f"La inferencia convencional excedió el presupuesto de heap: "
            f"{delta_mb:.3f} MB > {MAX_DELTA_INFERENCIA_CONVENCIONAL_MB} MB"
        )

    def test_ausencia_fugas_memoria_en_bucle(self, motor_con_datos: MotorInventario) -> None:
        """Verifica que 200 llamadas sucesivas de inferencia no presenten fugas de memoria."""
        gc.collect()
        tracemalloc.start()

        # Ronda de calentamiento
        motor_con_datos.predecir_quiebres_stock(estrategia=EstrategiaPrediccion.HIBRIDA)
        gc.collect()
        inicio_bytes, _ = tracemalloc.get_traced_memory()

        for _ in range(200):
            motor_con_datos.predecir_quiebres_stock(estrategia=EstrategiaPrediccion.HIBRIDA)

        gc.collect()
        final_bytes, _ = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        delta_remanente_kb = max(0.0, (final_bytes - inicio_bytes) / 1024.0)
        assert delta_remanente_kb < MAX_FUGA_MEMORIA_KB, (
            f"Detectada potencial fuga de memoria tras 200 evaluaciones: "
            f"{delta_remanente_kb:.2f} KB retenidos > {MAX_FUGA_MEMORIA_KB} KB permitidos"
        )

    def test_speedup_convencional_vs_ia(self, motor_con_datos: MotorInventario) -> None:
        """Aserción: la heurística O(1) debe ser al menos 3x más veloz que la IA."""
        # Medir tiempo convencional
        t0 = time.perf_counter_ns()
        for _ in range(5):
            motor_con_datos.predecir_quiebres_stock(estrategia=EstrategiaPrediccion.CONVENCIONAL)
        t_conv = time.perf_counter_ns() - t0

        # Medir tiempo IA
        t1 = time.perf_counter_ns()
        for _ in range(5):
            motor_con_datos.predecir_quiebres_stock(estrategia=EstrategiaPrediccion.IA)
        t_ia = time.perf_counter_ns() - t1

        assert t_conv > 0
        speedup = t_ia / t_conv
        assert speedup >= 3.0, (
            f"El speedup de la heurística convencional ({speedup:.2f}x) "
            f"fue menor al umbral mínimo esperado de 3.0x"
        )
