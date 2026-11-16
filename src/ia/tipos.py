"""Modelos de datos y estructuras de tipado para el subsistema de Inteligencia Artificial."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any

import numpy as np

NOMBRES_FEATURES: tuple[str, ...] = (
    "rotacion_historica",
    "frecuencia_pedidos",
    "tamano_medio_lote",
    "varianza_lote",
    "stock_actual",
    "precio_unitario",
    "ratio_stock_rotacion",
    "tasa_quiebre_reciente",
    "tendencia_demanda",
    "dias_cobertura_estimados",
)


class EstrategiaPrediccion(str, Enum):
    """Estrategia de cálculo utilizada para predecir demanda y quiebres de stock."""

    CONVENCIONAL = "convencional"  # Regla analítica O(1) de punto de reorden
    IA = "ia"  # Pipeline scikit-learn con vector multidimensional
    HIBRIDA = "hibrida"  # Cascada rápida O(1) con inferencia IA en zona incierta


class NivelRiesgo(str, Enum):
    """Nivel cualitativo de riesgo de quiebre de stock."""

    BAJO = "bajo"  # Stock abundante y seguro
    MEDIO = "medio"  # Zona de incertidumbre o aproximación a punto crítico
    CRITICO = "critico"  # Quiebre inminente de stock proyectado


@dataclass(slots=True, frozen=True)
class FeatureVector:
    """Vector de características estructuradas para un producto en el catálogo.

    Representa las dimensiones cuantitativas requeridas por los modelos
    de aprendizaje automático supervisado.
    """

    id_producto: int
    rotacion_historica: float
    frecuencia_pedidos: float
    tamano_medio_lote: float
    varianza_lote: float
    stock_actual: int
    precio_unitario: float
    ratio_stock_rotacion: float
    tasa_quiebre_reciente: float
    tendencia_demanda: float
    dias_cobertura_estimados: float

    def a_array(self) -> np.ndarray:
        """Convierte las características numéricas en un array 1D de NumPy."""
        return np.array(
            [
                self.rotacion_historica,
                self.frecuencia_pedidos,
                self.tamano_medio_lote,
                self.varianza_lote,
                float(self.stock_actual),
                self.precio_unitario,
                self.ratio_stock_rotacion,
                self.tasa_quiebre_reciente,
                self.tendencia_demanda,
                self.dias_cobertura_estimados,
            ],
            dtype=np.float64,
        )

    def a_diccionario(self) -> dict[str, Any]:
        """Serializa el vector a un diccionario plano."""
        return asdict(self)


@dataclass(slots=True)
class RegistroHistoricoDemanda:
    """Registro temporal de demanda observada para un producto en un período dado."""

    id_producto: int
    periodo: int
    demanda_unidades: int
    stock_al_inicio: int
    quiebre_stock: bool

    def a_diccionario(self) -> dict[str, Any]:
        """Serializa el registro histórico a un diccionario plano."""
        return asdict(self)


@dataclass(slots=True)
class DatasetHistorico:
    """Conjunto estructurado de datos para entrenamiento y validación de modelos IA."""

    registros: list[RegistroHistoricoDemanda]
    features: list[FeatureVector]
    X: np.ndarray
    y_demanda: np.ndarray
    y_quiebre: np.ndarray

    def __post_init__(self) -> None:
        """Valida concordancia dimensional de las matrices y vectores."""
        n_muestras = len(self.features)
        if self.X.shape[0] != n_muestras:
            raise ValueError(
                f"Discrepancia dimensional: features ({n_muestras}) vs X filas ({self.X.shape[0]})"
            )
        if len(self.y_demanda) != n_muestras:
            raise ValueError(
                f"Discrepancia dimensional: features ({n_muestras}) "
                f"vs y_demanda ({len(self.y_demanda)})"
            )
        if len(self.y_quiebre) != n_muestras:
            raise ValueError(
                f"Discrepancia dimensional: features ({n_muestras}) "
                f"vs y_quiebre ({len(self.y_quiebre)})"
            )


@dataclass(slots=True)
class ResultadoPrediccion:
    """Resultado de la evaluación de stock para un producto individual."""

    id_producto: int
    nombre_producto: str
    categoria: str
    stock_actual: int
    demanda_proyectada: float
    probabilidad_quiebre: float
    riesgo: NivelRiesgo
    alerta_quiebre: bool
    estrategia: EstrategiaPrediccion
    tiempo_inferencia_us: float
    memoria_pico_bytes: int
    explicacion: str

    def a_diccionario(self) -> dict[str, Any]:
        """Serializa el resultado a diccionario plano para vistas o exportación."""
        datos = asdict(self)
        datos["riesgo"] = self.riesgo.value
        datos["estrategia"] = self.estrategia.value
        return datos


@dataclass(slots=True)
class MetricasModelo:
    """Métricas cuantitativas de desempeño predictivo y costo de inferencia."""

    r2_score: float
    mae: float
    precision: float
    recall: float
    f1_score: float
    latencia_promedio_us: float
    memoria_heap_kb: float
    total_muestras_test: int

    def a_diccionario(self) -> dict[str, Any]:
        """Serializa las métricas a un diccionario plano."""
        return asdict(self)
