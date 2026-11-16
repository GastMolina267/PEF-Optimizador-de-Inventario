"""Tests exhaustivos para la heurística O(1), modelos scikit-learn y PredictorDemanda."""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

from src.ia.extractor_features import ExtractorFeatures, GeneradorHistorialSintetico
from src.ia.modelos import (
    ModeloPredictorIA,
    evaluar_heuristica_convencional,
)
from src.ia.predictor_demanda import PredictorDemanda
from src.ia.tipos import (
    DatasetHistorico,
    EstrategiaPrediccion,
    FeatureVector,
    NivelRiesgo,
)
from src.modelos.pedido import LineaPedido, Pedido
from src.modelos.producto import Producto


@pytest.fixture
def catalogo_prueba() -> list[Producto]:
    """Catálogo pequeño y variado para pruebas de predicción."""
    return [
        Producto(
            id=1, nombre="Tornillo Zincado", categoria="Fijaciones", stock=100, precio=15.0
        ),
        Producto(
            id=2, nombre="Taladro Percutor", categoria="Herramientas", stock=5, precio=25000.0
        ),
        Producto(
            id=3, nombre="Disco de Corte", categoria="Abrasivos", stock=0, precio=850.0
        ),
        Producto(
            id=4, nombre="Amoladora Angular", categoria="Herramientas", stock=2, precio=32000.0
        ),
    ]


@pytest.fixture
def dataset_entrenado(catalogo_prueba: list[Producto]) -> DatasetHistorico:
    """Dataset sintético generado para entrenar el modelo de prueba."""
    gen = GeneradorHistorialSintetico(seed=42)
    return gen.generar_dataset_supervisado(catalogo_prueba, periodos=10, pedidos_por_periodo=15)


class TestHeuristicaConvencional:
    """Pruebas de la regla analítica O(1) de punto de reorden."""

    def test_producto_sin_historial_no_alerta(self) -> None:
        """Verifica que un producto sin historial no dispare alertas espurias."""
        prod = Producto(id=1, nombre="Item", categoria="Cat", stock=50, precio=100.0)
        fv = ExtractorFeatures.extraer_vector(prod, pedidos=[])
        dem, prob, alerta = evaluar_heuristica_convencional(prod, fv)
        assert dem == 0.0
        assert prob == 0.0
        assert alerta is False

    def test_stock_cero_dispara_quiebre_maximo(self) -> None:
        """Verifica que stock 0 produzca probabilidad 1.0 y alerta crítica."""
        prod = Producto(id=1, nombre="Item", categoria="Cat", stock=0, precio=100.0)
        pedidos = [Pedido(id=1, lineas=[LineaPedido(id_producto=1, cantidad=10)])]
        fv = ExtractorFeatures.extraer_vector(prod, pedidos)
        dem, prob, alerta = evaluar_heuristica_convencional(prod, fv)
        assert dem > 0.0
        assert prob == 1.0
        assert alerta is True

    def test_stock_abundante_evita_alerta(self) -> None:
        """Verifica que stock muy holgado tenga probabilidad baja y sin alerta."""
        prod = Producto(id=1, nombre="Item", categoria="Cat", stock=1000, precio=100.0)
        pedidos = [Pedido(id=1, lineas=[LineaPedido(id_producto=1, cantidad=5)])]
        fv = ExtractorFeatures.extraer_vector(prod, pedidos)
        _dem, prob, alerta = evaluar_heuristica_convencional(prod, fv)
        assert prob < 0.35
        assert alerta is False


class TestModeloPredictorIA:
    """Pruebas del pipeline supervisado scikit-learn."""

    def test_prediccion_sin_entrenar_lanza_runtime_error(self) -> None:
        """Verifica que predecir sin entrenar falle explícitamente."""
        modelo = ModeloPredictorIA()
        fv = FeatureVector(
            id_producto=1,
            rotacion_historica=10.0,
            frecuencia_pedidos=1.0,
            tamano_medio_lote=10.0,
            varianza_lote=0.0,
            stock_actual=10,
            precio_unitario=100.0,
            ratio_stock_rotacion=0.9,
            tasa_quiebre_reciente=0.0,
            tendencia_demanda=1.0,
            dias_cobertura_estimados=1.0,
        )
        with pytest.raises(RuntimeError, match="debe entrenarse"):
            modelo.predecir_uno(fv)

    def test_guardar_sin_entrenar_lanza_runtime_error(self) -> None:
        """Verifica que guardar sin entrenar falle explícitamente."""
        modelo = ModeloPredictorIA()
        with pytest.raises(RuntimeError, match="no entrenado"):
            modelo.guardar("dummy.joblib")

    def test_entrenamiento_y_metricas(self, dataset_entrenado: DatasetHistorico) -> None:
        """Verifica el cálculo de métricas tras el entrenamiento."""
        modelo = ModeloPredictorIA()
        metricas = modelo.entrenar(dataset_entrenado)
        assert modelo.esta_entrenado is True
        assert metricas.mae >= 0.0
        assert 0.0 <= metricas.f1_score <= 1.0
        assert metricas.total_muestras_test > 0

    def test_roundtrip_guardar_y_cargar_joblib(
        self, dataset_entrenado: DatasetHistorico
    ) -> None:
        """Verifica la persistencia y restauración idéntica con joblib."""
        modelo = ModeloPredictorIA()
        modelo.entrenar(dataset_entrenado)

        fv = dataset_entrenado.features[0]
        dem1, prob1 = modelo.predecir_uno(fv)

        with tempfile.TemporaryDirectory() as tmpdir:
            ruta = Path(tmpdir) / "modelo_test.joblib"
            modelo.guardar(ruta)
            assert ruta.is_file()

            cargado = ModeloPredictorIA.cargar(ruta)
            assert cargado.esta_entrenado is True
            dem2, prob2 = cargado.predecir_uno(fv)

            assert dem1 == dem2
            assert prob1 == prob2


class TestPredictorDemanda:
    """Pruebas de conmutación de estrategias y telemetría de inferencia."""

    def test_conmutacion_estrategias(
        self,
        catalogo_prueba: list[Producto],
        dataset_entrenado: DatasetHistorico,
    ) -> None:
        """Verifica que las tres estrategias devuelvan resultados coherentes."""
        predictor = PredictorDemanda()
        predictor.modelo_ia.entrenar(dataset_entrenado)

        prod = catalogo_prueba[1]  # Taladro (stock 5)
        fv = dataset_entrenado.features[1]

        res_conv = predictor.evaluar_producto(
            prod, fv, estrategia=EstrategiaPrediccion.CONVENCIONAL
        )
        res_ia = predictor.evaluar_producto(prod, fv, estrategia=EstrategiaPrediccion.IA)
        res_hib = predictor.evaluar_producto(
            prod, fv, estrategia=EstrategiaPrediccion.HIBRIDA
        )

        assert res_conv.estrategia == EstrategiaPrediccion.CONVENCIONAL
        assert res_ia.estrategia == EstrategiaPrediccion.IA
        assert res_hib.estrategia == EstrategiaPrediccion.HIBRIDA

        # Latencias en microsegundos deben ser no negativas
        assert res_conv.tiempo_inferencia_us >= 0.0
        assert res_ia.tiempo_inferencia_us >= 0.0
        assert res_hib.tiempo_inferencia_us >= 0.0

        # Ambas probabilidades deben ser matemáticamente válidas
        assert 0.0 <= res_conv.probabilidad_quiebre <= 1.0
        assert 0.0 <= res_ia.probabilidad_quiebre <= 1.0
        assert 0.0 <= res_hib.probabilidad_quiebre <= 1.0

    def test_cascada_hibrida_filtro_rapido_vs_incertidumbre(
        self,
        catalogo_prueba: list[Producto],
        dataset_entrenado: DatasetHistorico,
    ) -> None:
        """Verifica que la cascada filtre en O(1) con stock masivo y recurra a IA en riesgo."""
        predictor = PredictorDemanda()
        predictor.modelo_ia.entrenar(dataset_entrenado)

        # Producto con stock masivo (100 unidades)
        prod_seguro = catalogo_prueba[0]
        fv_seguro = dataset_entrenado.features[0]
        res_seguro = predictor.evaluar_producto(
            prod_seguro, fv_seguro, estrategia=EstrategiaPrediccion.HIBRIDA
        )
        assert "Filtro O(1)" in res_seguro.explicacion
        assert res_seguro.alerta_quiebre is False
        assert res_seguro.riesgo == NivelRiesgo.BAJO

        # Producto con stock crítico (0 unidades)
        prod_critico = catalogo_prueba[2]
        fv_critico = dataset_entrenado.features[2]
        res_critico = predictor.evaluar_producto(
            prod_critico, fv_critico, estrategia=EstrategiaPrediccion.HIBRIDA
        )
        assert res_critico.riesgo == NivelRiesgo.CRITICO

    def test_evaluar_catalogo_ordenado_por_quiebre(
        self,
        catalogo_prueba: list[Producto],
        dataset_entrenado: DatasetHistorico,
    ) -> None:
        """Verifica que evaluar_catalogo ordene de mayor a menor probabilidad de quiebre."""
        predictor = PredictorDemanda()
        predictor.modelo_ia.entrenar(dataset_entrenado)

        pedidos = [
            Pedido(id=1, lineas=[LineaPedido(id_producto=1, cantidad=5)]),
            Pedido(id=2, lineas=[LineaPedido(id_producto=3, cantidad=20)]),
        ]

        resultados = predictor.evaluar_catalogo(
            catalogo_prueba, pedidos, estrategia=EstrategiaPrediccion.HIBRIDA
        )
        assert len(resultados) == len(catalogo_prueba)

        probs = [r.probabilidad_quiebre for r in resultados]
        assert probs == sorted(probs, reverse=True)


class TestPropiedadesInferencia:
    """Enfoque 1: Pruebas de propiedades con Hypothesis sobre la inferencia."""

    @given(
        stock=st.integers(min_value=0, max_value=5000),
        rotacion=st.floats(
            min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False
        ),
        frecuencia=st.floats(
            min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False
        ),
        tamano_medio=st.floats(
            min_value=0.0, max_value=50.0, allow_nan=False, allow_infinity=False
        ),
        tendencia=st.floats(
            min_value=0.1, max_value=5.0, allow_nan=False, allow_infinity=False
        ),
    )
    def test_invariantes_heuristica_probabilidades(
        self,
        stock: int,
        rotacion: float,
        frecuencia: float,
        tamano_medio: float,
        tendencia: float,
    ) -> None:
        """Verifica que la heurística nunca genere probabilidades fuera de [0, 1]."""
        prod = Producto(id=1, nombre="Item", categoria="General", stock=stock, precio=100.0)
        fv = FeatureVector(
            id_producto=1,
            rotacion_historica=rotacion,
            frecuencia_pedidos=frecuencia,
            tamano_medio_lote=tamano_medio,
            varianza_lote=5.0,
            stock_actual=stock,
            precio_unitario=100.0,
            ratio_stock_rotacion=0.5,
            tasa_quiebre_reciente=0.0,
            tendencia_demanda=tendencia,
            dias_cobertura_estimados=10.0,
        )

        dem, prob, _ = evaluar_heuristica_convencional(prod, fv)
        assert not np.isnan(dem)
        assert not np.isnan(prob)
        assert dem >= 0.0
        assert 0.0 <= prob <= 1.0
