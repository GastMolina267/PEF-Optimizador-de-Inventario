"""Fachada unificada y comparador de estrategias predictivas (Convencional vs IA vs Híbrida)."""

from __future__ import annotations

import time
import tracemalloc
from collections.abc import Iterable
from typing import TYPE_CHECKING

from src.ia.extractor_features import ExtractorFeatures, GeneradorHistorialSintetico
from src.ia.modelos import (
    FACTOR_SEGURIDAD_DEFECTO,
    ModeloPredictorIA,
    evaluar_heuristica_convencional,
)
from src.ia.tipos import (
    EstrategiaPrediccion,
    FeatureVector,
    MetricasModelo,
    NivelRiesgo,
    ResultadoPrediccion,
)
from src.modelos.pedido import Pedido
from src.modelos.producto import Producto

if TYPE_CHECKING:
    from pathlib import Path

UMBRAL_PROBABILIDAD_QUIEBRE_DEFECTO = 0.50
FACTOR_HOLGURA_HIBRIDA_DEFECTO = 3.0
PROB_RIESGO_CRITICO = 0.70
PROB_RIESGO_MEDIO = 0.40


class PredictorDemanda:
    """Orquestador de inferencia predictiva y evaluación comparativa de costo computacional.

    Permite conmutar dinámicamente entre:
    1. CONVENCIONAL: Heurística analítica O(1) basada en el punto de reorden clásico.
    2. IA: Pipeline supervisado de scikit-learn con vector multidimensional.
    3. HIBRIDA: Cascada reactiva (filtro rápido O(1) y fallback a IA en zona de incertidumbre).
    """

    def __init__(
        self,
        modelo_ia: ModeloPredictorIA | None = None,
        umbral_quiebre: float = UMBRAL_PROBABILIDAD_QUIEBRE_DEFECTO,
        factor_holgura_hibrida: float = FACTOR_HOLGURA_HIBRIDA_DEFECTO,
    ) -> None:
        """Inicializa el predictor configurando el modelo y umbrales operativos."""
        self._modelo_ia = modelo_ia if modelo_ia is not None else ModeloPredictorIA()
        self._umbral_quiebre = umbral_quiebre
        self._factor_holgura_hibrida = factor_holgura_hibrida

    @property
    def modelo_ia(self) -> ModeloPredictorIA:
        """Acceso al modelo subyacente de scikit-learn."""
        return self._modelo_ia

    @property
    def umbral_quiebre(self) -> float:
        """Umbral probabilístico para activar alerta de quiebre."""
        return self._umbral_quiebre

    def entrenar_con_catalogo(
        self,
        catalogo: list[Producto],
        seed: int = 42,
        periodos: int = 25,
        pedidos_por_periodo: int = 30,
    ) -> MetricasModelo:
        """Genera un historial determinista y entrena el modelo de IA."""
        gen = GeneradorHistorialSintetico(seed=seed)
        dataset = gen.generar_dataset_supervisado(
            catalogo, periodos=periodos, pedidos_por_periodo=pedidos_por_periodo
        )
        return self._modelo_ia.entrenar(dataset)

    def _resolver_estrategia(
        self,
        producto: Producto,
        fv: FeatureVector,
        estrategia: EstrategiaPrediccion,
    ) -> tuple[float, float, bool, str]:
        """Calcula demanda, probabilidad, alerta y explicación según la estrategia."""
        if estrategia == EstrategiaPrediccion.CONVENCIONAL:
            demanda_est, prob_quiebre, alerta = evaluar_heuristica_convencional(
                producto, fv, factor_seguridad=FACTOR_SEGURIDAD_DEFECTO
            )
            explicacion = (
                f"Heurística O(1): Demanda proyectada={demanda_est:.1f}, "
                f"Prob. Quiebre={prob_quiebre * 100:.1f}% (Stock actual: {producto.stock})"
            )
            return demanda_est, prob_quiebre, alerta, explicacion

        if estrategia == EstrategiaPrediccion.IA:
            if not self._modelo_ia.esta_entrenado:
                demanda_est, prob_quiebre, alerta = evaluar_heuristica_convencional(producto, fv)
                explicacion = "Modelo IA no entrenado: Fallback a heurística convencional O(1)."
                return demanda_est, prob_quiebre, alerta, explicacion

            demanda_est, prob_quiebre = self._modelo_ia.predecir_uno(fv)
            alerta = prob_quiebre >= self._umbral_quiebre
            explicacion = (
                f"Modelo supervisado scikit-learn: Demanda esperada={demanda_est:.1f}, "
                f"Prob. Quiebre={prob_quiebre * 100:.1f}%"
            )
            return demanda_est, prob_quiebre, alerta, explicacion

        # Estrategia HIBRIDA
        dem_conv, prob_conv, alerta_conv = evaluar_heuristica_convencional(producto, fv)
        umbral_seguro = dem_conv * self._factor_holgura_hibrida

        if float(producto.stock) >= max(10.0, umbral_seguro):
            explicacion = (
                f"Cascada Híbrida (Filtro O(1)): Stock abundante ({producto.stock} uds) "
                f"descarta riesgo sin evaluar IA."
            )
            return dem_conv, prob_conv, False, explicacion

        if self._modelo_ia.esta_entrenado:
            demanda_est, prob_quiebre = self._modelo_ia.predecir_uno(fv)
            alerta = prob_quiebre >= self._umbral_quiebre
            explicacion = (
                f"Cascada Híbrida (Inferencia IA): Zona de incertidumbre evaluada "
                f"(Demanda={demanda_est:.1f}, Quiebre={prob_quiebre * 100:.1f}%)"
            )
            return demanda_est, prob_quiebre, alerta, explicacion

        explicacion = (
            f"Cascada Híbrida (Fallback O(1)): {producto.stock} uds, "
            f"Quiebre={prob_conv * 100:.1f}%"
        )
        return dem_conv, prob_conv, alerta_conv, explicacion

    def evaluar_producto(
        self,
        producto: Producto,
        fv: FeatureVector,
        estrategia: EstrategiaPrediccion = EstrategiaPrediccion.HIBRIDA,
    ) -> ResultadoPrediccion:
        """Evalúa el estado proyectado de un producto bajo la estrategia solicitada.

        Mide la latencia en microsegundos (µs) con alta resolución y el consumo
        de memoria heap mediante tracemalloc.
        """
        tracemalloc_iniciado_aqui = False
        if not tracemalloc.is_tracing():
            tracemalloc.start()
            tracemalloc_iniciado_aqui = True

        inicio_bytes, _ = tracemalloc.get_traced_memory()
        t_inicio = time.perf_counter_ns()

        demanda_est, prob_quiebre, alerta, explicacion = self._resolver_estrategia(
            producto, fv, estrategia
        )

        t_fin = time.perf_counter_ns()
        _, fin_pico = tracemalloc.get_traced_memory()
        if tracemalloc_iniciado_aqui:
            tracemalloc.stop()

        latencia_us = (t_fin - t_inicio) / 1000.0
        memoria_bytes = max(0, fin_pico - inicio_bytes)

        # Determinar nivel cualitativo de riesgo
        if prob_quiebre >= PROB_RIESGO_CRITICO or producto.stock <= 0:
            riesgo = NivelRiesgo.CRITICO
        elif prob_quiebre >= PROB_RIESGO_MEDIO:
            riesgo = NivelRiesgo.MEDIO
        else:
            riesgo = NivelRiesgo.BAJO

        return ResultadoPrediccion(
            id_producto=producto.id,
            nombre_producto=producto.nombre,
            categoria=producto.categoria,
            stock_actual=producto.stock,
            demanda_proyectada=round(demanda_est, 2),
            probabilidad_quiebre=round(prob_quiebre, 4),
            riesgo=riesgo,
            alerta_quiebre=alerta,
            estrategia=estrategia,
            tiempo_inferencia_us=round(latencia_us, 2),
            memoria_pico_bytes=memoria_bytes,
            explicacion=explicacion,
        )

    def evaluar_catalogo(
        self,
        productos: Iterable[Producto],
        pedidos: list[Pedido],
        estrategia: EstrategiaPrediccion = EstrategiaPrediccion.HIBRIDA,
    ) -> list[ResultadoPrediccion]:
        """Evalúa un catálogo completo de productos bajo la estrategia seleccionada.

        Retorna la lista ordenada con los productos más críticos primero.
        """
        lista_prods = list(productos)
        if not lista_prods:
            return []

        resultados: list[ResultadoPrediccion] = []
        for prod in lista_prods:
            fv = ExtractorFeatures.extraer_vector(prod, pedidos)
            res = self.evaluar_producto(prod, fv, estrategia=estrategia)
            resultados.append(res)

        # Ordenar por probabilidad de quiebre descendente
        resultados.sort(key=lambda r: r.probabilidad_quiebre, reverse=True)
        return resultados

    def guardar_modelo(self, ruta: Path | str) -> None:
        """Persiste el modelo de IA en disco."""
        self._modelo_ia.guardar(ruta)

    def cargar_modelo(self, ruta: Path | str) -> None:
        """Carga y restaura el modelo de IA desde disco."""
        self._modelo_ia = ModeloPredictorIA.cargar(ruta)
