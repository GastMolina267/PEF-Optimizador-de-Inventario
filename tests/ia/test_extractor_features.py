"""Tests unitarios, de integración y de propiedades para ExtractorFeatures y tipos de IA."""

from __future__ import annotations

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

from src.ia.extractor_features import ExtractorFeatures, GeneradorHistorialSintetico
from src.ia.tipos import (
    NOMBRES_FEATURES,
    DatasetHistorico,
    EstrategiaPrediccion,
    FeatureVector,
    NivelRiesgo,
    RegistroHistoricoDemanda,
    ResultadoPrediccion,
)
from src.modelos.pedido import LineaPedido, Pedido
from src.modelos.producto import Producto


@pytest.fixture
def producto_ejemplo() -> Producto:
    """Fixture de producto representativo con stock intermedio."""
    return Producto(
        id=101,
        nombre="Taladro Percutor 750W",
        categoria="Herramientas",
        stock=15,
        precio=12500.0,
    )


@pytest.fixture
def catalogo_basico() -> list[Producto]:
    """Fixture de catálogo de prueba con 5 productos variados."""
    return [
        Producto(
            id=1, nombre="Tornillo 2 Pulgadas", categoria="Fijaciones", stock=500, precio=10.0
        ),
        Producto(id=2, nombre="Arandela Plana", categoria="Fijaciones", stock=300, precio=5.0),
        Producto(
            id=3, nombre="Martillo Galponero", categoria="Herramientas", stock=12, precio=4500.0
        ),
        Producto(id=4, nombre="Cinta Métrica 5m", categoria="Medición", stock=25, precio=2200.0),
        Producto(
            id=5,
            nombre="Destornillador Phillips",
            categoria="Herramientas",
            stock=40,
            precio=1800.0,
        ),
    ]


class TestTiposIA:
    """Pruebas de modelos de datos, inmutabilidad y serialización del subsistema IA."""

    def test_nombres_features_concordancia_dimensional(self) -> None:
        """Verifica que NOMBRES_FEATURES tenga exactamente 10 dimensiones canónicas."""
        assert len(NOMBRES_FEATURES) == 10
        assert "rotacion_historica" in NOMBRES_FEATURES
        assert "dias_cobertura_estimados" in NOMBRES_FEATURES

    def test_feature_vector_a_array_y_diccionario(self, producto_ejemplo: Producto) -> None:
        """Verifica la conversión de FeatureVector a numpy array y diccionario."""
        fv = FeatureVector(
            id_producto=producto_ejemplo.id,
            rotacion_historica=50.0,
            frecuencia_pedidos=5.0,
            tamano_medio_lote=10.0,
            varianza_lote=4.0,
            stock_actual=producto_ejemplo.stock,
            precio_unitario=producto_ejemplo.precio,
            ratio_stock_rotacion=0.294,
            tasa_quiebre_reciente=0.2,
            tendencia_demanda=1.25,
            dias_cobertura_estimados=1.5,
        )

        arr = fv.a_array()
        assert isinstance(arr, np.ndarray)
        assert arr.shape == (10,)
        assert arr.dtype == np.float64
        assert not np.isnan(arr).any()

        dicc = fv.a_diccionario()
        assert dicc["id_producto"] == 101
        assert dicc["rotacion_historica"] == 50.0

    def test_dataset_historico_valida_dimensiones(self) -> None:
        """Verifica que DatasetHistorico rechace matrices con discrepancia de filas."""
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
        reg = RegistroHistoricoDemanda(
            id_producto=1,
            periodo=1,
            demanda_unidades=10,
            stock_al_inicio=10,
            quiebre_stock=False,
        )

        # X con 2 filas mientras features tiene 1 -> debe lanzar ValueError
        with pytest.raises(ValueError, match="Discrepancia dimensional"):
            DatasetHistorico(
                registros=[reg],
                features=[fv],
                X=np.zeros((2, 10)),
                y_demanda=np.zeros(1),
                y_quiebre=np.zeros(1),
            )

    def test_resultado_prediccion_serializacion(self) -> None:
        """Verifica que ResultadoPrediccion se serialice con valores legibles de enums."""
        res = ResultadoPrediccion(
            id_producto=1,
            nombre_producto="Martillo",
            categoria="Herramientas",
            stock_actual=5,
            demanda_proyectada=8.5,
            probabilidad_quiebre=0.88,
            riesgo=NivelRiesgo.CRITICO,
            alerta_quiebre=True,
            estrategia=EstrategiaPrediccion.IA,
            tiempo_inferencia_us=185.4,
            memoria_pico_bytes=4096,
            explicacion="Demanda estimada (8.5) supera stock disponible (5).",
        )
        dicc = res.a_diccionario()
        assert dicc["riesgo"] == "critico"
        assert dicc["estrategia"] == "ia"
        assert dicc["alerta_quiebre"] is True


class TestExtractorFeatures:
    """Pruebas funcionales del extractor de características."""

    def test_extraer_vector_sin_historial(self, producto_ejemplo: Producto) -> None:
        """Verifica que un producto sin historial devuelva un vector por defecto sin errores."""
        fv = ExtractorFeatures.extraer_vector(producto_ejemplo, pedidos=[])
        assert fv.id_producto == producto_ejemplo.id
        assert fv.rotacion_historica == 0.0
        assert fv.frecuencia_pedidos == 0.0
        assert fv.tamano_medio_lote == 0.0
        assert fv.varianza_lote == 0.0
        assert fv.stock_actual == 15
        assert fv.dias_cobertura_estimados == 999.0

    def test_extraer_vector_con_pedidos(self, producto_ejemplo: Producto) -> None:
        """Verifica la extracción precisa de métricas con historial de pedidos."""
        pedidos = [
            Pedido(id=1, lineas=[LineaPedido(id_producto=producto_ejemplo.id, cantidad=4)]),
            Pedido(id=2, lineas=[LineaPedido(id_producto=producto_ejemplo.id, cantidad=6)]),
            # Pedido 3 supera el stock (20 > 15) generando un evento de quiebre
            Pedido(id=3, lineas=[LineaPedido(id_producto=producto_ejemplo.id, cantidad=20)]),
        ]

        fv = ExtractorFeatures.extraer_vector(producto_ejemplo, pedidos)
        assert fv.id_producto == producto_ejemplo.id
        assert fv.rotacion_historica == 30.0  # 4 + 6 + 20
        assert fv.frecuencia_pedidos == 3.0
        assert fv.tamano_medio_lote == 10.0  # 30 / 3
        assert fv.varianza_lote > 0.0
        assert fv.stock_actual == 15
        assert pytest.approx(fv.tasa_quiebre_reciente, rel=1e-2) == 1.0 / 3.0
        assert fv.dias_cobertura_estimados == 1.5  # 15 / 10

    def test_extraer_matriz_catalogo(self, catalogo_basico: list[Producto]) -> None:
        """Verifica la extracción de matriz de diseño completa sobre un catálogo."""
        pedidos = [
            Pedido(
                id=1,
                lineas=[
                    LineaPedido(id_producto=1, cantidad=10),
                    LineaPedido(id_producto=3, cantidad=2),
                ],
            )
        ]

        matriz_x, vectores = ExtractorFeatures.extraer_matriz(catalogo_basico, pedidos)
        assert matriz_x.shape == (5, 10)
        assert len(vectores) == 5
        assert not np.isnan(matriz_x).any()

    def test_extraer_matriz_catalogo_vacio(self) -> None:
        """Verifica que un catálogo vacío retorne una matriz vacía sin fallar."""
        matriz_x, vectores = ExtractorFeatures.extraer_matriz([], pedidos=[])
        assert matriz_x.shape == (0, 10)
        assert vectores == []


class TestGeneradorHistorialSintetico:
    """Pruebas del generador determinista de datos sintéticos para IA."""

    def test_reproducibilidad_con_semilla(self, catalogo_basico: list[Producto]) -> None:
        """Verifica que dos generadores con la misma semilla produzcan idéntico resultado."""
        gen1 = GeneradorHistorialSintetico(seed=1234)
        gen2 = GeneradorHistorialSintetico(seed=1234)

        pedidos1 = gen1.generar_pedidos_sinteticos(catalogo_basico, cantidad_pedidos=50)
        pedidos2 = gen2.generar_pedidos_sinteticos(catalogo_basico, cantidad_pedidos=50)

        assert len(pedidos1) == len(pedidos2) == 50
        for p1, p2 in zip(pedidos1, pedidos2, strict=True):
            assert p1.id == p2.id
            assert len(p1.lineas) == len(p2.lineas)
            for l1, l2 in zip(p1.lineas, p2.lineas, strict=True):
                assert l1.id_producto == l2.id_producto
                assert l1.cantidad == l2.cantidad

    def test_generar_dataset_supervisado(self, catalogo_basico: list[Producto]) -> None:
        """Verifica la construcción del DatasetHistorico supervisado."""
        gen = GeneradorHistorialSintetico(seed=42)
        dataset = gen.generar_dataset_supervisado(
            catalogo_basico, periodos=5, pedidos_por_periodo=10
        )

        n_esperado = len(catalogo_basico) * 5  # 5 prods * 5 períodos = 25 muestras
        assert len(dataset.registros) == n_esperado
        assert len(dataset.features) == n_esperado
        assert dataset.X.shape == (n_esperado, 10)
        assert dataset.y_demanda.shape == (n_esperado,)
        assert dataset.y_quiebre.shape == (n_esperado,)
        assert not np.isnan(dataset.X).any()
        assert (dataset.y_demanda >= 0).all()
        assert set(np.unique(dataset.y_quiebre)).issubset({0.0, 1.0})


class TestPropiedadesConHypothesis:
    """Enfoque 1: IA Aplicada al Desarrollo - Pruebas de propiedades invariantes."""

    @given(
        stock=st.integers(min_value=0, max_value=10_000),
        precio=st.floats(
            min_value=0.01, max_value=500_000.0, allow_nan=False, allow_infinity=False
        ),
        cantidades=st.lists(st.integers(min_value=1, max_value=100), min_size=0, max_size=50),
    )
    def test_invariantes_feature_vector(
        self, stock: int, precio: float, cantidades: list[int]
    ) -> None:
        """Verifica invariantes de calidad matemática y robustez numérica."""
        prod = Producto(id=1, nombre="Item Test", categoria="General", stock=stock, precio=precio)
        pedidos = [
            Pedido(id=idx + 1, lineas=[LineaPedido(id_producto=1, cantidad=c)])
            for idx, c in enumerate(cantidades)
        ]

        fv = ExtractorFeatures.extraer_vector(prod, pedidos)
        arr = fv.a_array()

        assert fv.rotacion_historica >= 0.0
        assert fv.frecuencia_pedidos >= 0.0
        assert 0.0 <= fv.tasa_quiebre_reciente <= 1.0
        assert fv.ratio_stock_rotacion >= 0.0
        assert fv.dias_cobertura_estimados >= 0.0
        assert not np.isnan(arr).any()
        assert not np.isinf(arr).any()
