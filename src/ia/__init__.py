"""Subsistema de Inteligencia Artificial para Inventario y Pedidos.

Proporciona capacidades predictivas y de aprendizaje automático:
- Extracción vectorial de características operativas del catálogo.
- Modelos predictivos supervisados (Ridge, RandomForest) para demanda y quiebres.
- Comparador algorítmico estricto: Regla convencional O(1) vs. Modelo IA vs. Cascada Híbrida.
- Telemetría de costos computacionales (latencia en µs, memoria heap tracemalloc).
"""

from src.ia.tipos import (
    NOMBRES_FEATURES,
    DatasetHistorico,
    EstrategiaPrediccion,
    FeatureVector,
    MetricasModelo,
    NivelRiesgo,
    RegistroHistoricoDemanda,
    ResultadoPrediccion,
)

__all__ = [
    "NOMBRES_FEATURES",
    "DatasetHistorico",
    "EstrategiaPrediccion",
    "FeatureVector",
    "MetricasModelo",
    "NivelRiesgo",
    "RegistroHistoricoDemanda",
    "ResultadoPrediccion",
]
