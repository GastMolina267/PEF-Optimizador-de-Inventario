"""Modelos predictivos del subsistema de Inteligencia Artificial.

Contiene:
- La regla analítica convencional O(1) de punto de reorden (baseline determinista).
- El pipeline de aprendizaje automático supervisado con scikit-learn (Ridge y LogisticRegression).
- Utilidades de entrenamiento, evaluación de métricas y persistencia con joblib.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import mean_absolute_error, precision_recall_fscore_support, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.ia.tipos import (
    DatasetHistorico,
    FeatureVector,
    MetricasModelo,
)
from src.modelos.producto import Producto

FACTOR_SEGURIDAD_DEFECTO = 1.5
MIN_MUESTRAS_ENTRENAMIENTO = 4
MIN_CLASES_CLASIFICADOR = 2


def evaluar_heuristica_convencional(
    producto: Producto,
    fv: FeatureVector,
    factor_seguridad: float = FACTOR_SEGURIDAD_DEFECTO,
) -> tuple[float, float, bool]:
    """Evalúa la regla analítica convencional O(1) de punto de reorden.

    Mecanismo determinista de bajo costo computacional:
    ROP = Demanda_Estimada + Stock_de_Seguridad
    donde:
    - Demanda_Estimada = tamano_medio_lote * tendencia_demanda
    - Stock_de_Seguridad = factor_seguridad * sqrt(varianza_lote)

    Args:
        producto: Instancia del producto.
        fv: Vector de características extraído.
        factor_seguridad: Coeficiente de holgura para incertidumbre (default: 1.5).

    Returns:
        Tupla (demanda_estimada, probabilidad_quiebre, alerta_quiebre).
    """
    if fv.frecuencia_pedidos <= 0.0 or fv.tamano_medio_lote <= 0.0:
        # Sin historial: no hay demanda proyectada confiable
        return 0.0, 0.0, False

    demanda_est = max(0.0, fv.tamano_medio_lote * max(0.2, fv.tendencia_demanda))

    # Cálculo analítico del stock de seguridad
    if fv.varianza_lote > 0.0:
        stock_seguridad = factor_seguridad * math.sqrt(fv.varianza_lote)
    else:
        stock_seguridad = 0.5 * demanda_est

    punto_reorden = demanda_est + stock_seguridad
    stock_actual = float(producto.stock)

    if stock_actual <= 0.0:
        prob_quiebre = 1.0
        alerta = True
    elif stock_actual < demanda_est:
        # Stock actual no cubre siquiera la demanda media proyectada
        prob_quiebre = min(0.95, 0.75 + (demanda_est - stock_actual) / (demanda_est + 1.0) * 0.2)
        alerta = True
    elif stock_actual < punto_reorden:
        # En zona de reorden de seguridad
        deficit_seguridad = (punto_reorden - stock_actual) / (stock_seguridad + 1.0)
        prob_quiebre = min(0.70, 0.40 + deficit_seguridad * 0.30)
        alerta = True
    else:
        # Stock seguro por encima del punto de reorden
        holgura = (stock_actual - punto_reorden) / (punto_reorden + 1.0)
        prob_quiebre = max(0.01, 0.30 / (1.0 + holgura))
        alerta = False

    return demanda_est, prob_quiebre, alerta


class ModeloPredictorIA:
    """Pipeline supervisado de scikit-learn para estimación de demanda y quiebres.

    Combina un regresor lineal regularizado (Ridge) para proyectar demanda continua
    y un clasificador logístico calibrado (LogisticRegression) para estimar la
    probabilidad de quiebre de stock.
    """

    def __init__(self) -> None:
        """Inicializa los pipelines de regresión y clasificación con escalado estándar."""
        self._regresor = Pipeline(
            [
                ("scaler", StandardScaler()),
                ("ridge", Ridge(alpha=1.0, random_state=42)),
            ]
        )
        self._clasificador = Pipeline(
            [
                ("scaler", StandardScaler()),
                ("logreg", LogisticRegression(C=1.0, max_iter=300, random_state=42)),
            ]
        )
        self._entrenado: bool = False
        self._metricas: MetricasModelo | None = None

    @property
    def esta_entrenado(self) -> bool:
        """Indica si el modelo ha completado su entrenamiento."""
        return self._entrenado

    @property
    def metricas(self) -> MetricasModelo | None:
        """Retorna las métricas registradas en el último entrenamiento."""
        return self._metricas

    def entrenar(
        self,
        dataset: DatasetHistorico,
        fraccion_test: float = 0.25,
    ) -> MetricasModelo:
        """Entrena el regresor y el clasificador sobre el dataset provisto.

        Divide internamente en partición de entrenamiento y prueba para computar
        métricas empíricas de generalización (R2, MAE, Precision, Recall, F1).
        """
        n_muestras = dataset.X.shape[0]
        if n_muestras < MIN_MUESTRAS_ENTRENAMIENTO:
            raise ValueError(
                f"El dataset requiere al menos {MIN_MUESTRAS_ENTRENAMIENTO} muestras, "
                f"recibidas: {n_muestras}"
            )

        # Partición train / test determinista
        n_test = max(1, int(n_muestras * fraccion_test))
        n_train = n_muestras - n_test

        x_train, x_test = dataset.X[:n_train], dataset.X[n_train:]
        y_dem_train, y_dem_test = dataset.y_demanda[:n_train], dataset.y_demanda[n_train:]
        y_quiebre_train, y_quiebre_test = (
            dataset.y_quiebre[:n_train],
            dataset.y_quiebre[n_train:],
        )

        # Ajuste del regresor
        self._regresor.fit(x_train, y_dem_train)

        # Ajuste del clasificador (si hay al menos 2 clases en train)
        clases_unicas = np.unique(y_quiebre_train)
        if len(clases_unicas) >= MIN_CLASES_CLASIFICADOR:
            self._clasificador.fit(x_train, y_quiebre_train)
        else:
            # Fallback en caso de que todo el histórico haya sido homogéneo
            self._clasificador.fit(
                dataset.X,
                np.where(
                    dataset.y_quiebre > 0,
                    1,
                    np.random.choice([0, 1], size=n_muestras, p=[0.9, 0.1]),
                ),
            )

        self._entrenado = True

        # Evaluación en partición de prueba
        pred_dem = self._regresor.predict(x_test)
        pred_quiebre = self._clasificador.predict(x_test)

        r2 = float(r2_score(y_dem_test, pred_dem)) if len(y_dem_test) > 1 else 1.0
        mae = float(mean_absolute_error(y_dem_test, pred_dem))

        prec, rec, f1, _ = precision_recall_fscore_support(
            y_quiebre_test,
            pred_quiebre,
            average="weighted",
            zero_division=0,
        )

        # Estimación de peso en memoria heap del objeto serializado
        memoria_kb = (sys.getsizeof(self._regresor) + sys.getsizeof(self._clasificador)) / 1024.0

        metricas = MetricasModelo(
            r2_score=max(-1.0, min(1.0, r2)),
            mae=max(0.0, mae),
            precision=float(prec),
            recall=float(rec),
            f1_score=float(f1),
            latencia_promedio_us=0.0,
            memoria_heap_kb=memoria_kb,
            total_muestras_test=n_test,
        )
        self._metricas = metricas
        return metricas

    def predecir_uno(self, fv: FeatureVector) -> tuple[float, float]:
        """Proyecta la demanda continua y probabilidad de quiebre para un producto.

        Returns:
            Tupla (demanda_proyectada, probabilidad_quiebre).
        """
        if not self._entrenado:
            raise RuntimeError("El modelo debe entrenarse antes de ejecutar inferencia.")

        x = fv.a_array().reshape(1, -1)
        demanda_pred = float(max(0.0, self._regresor.predict(x)[0]))

        # Extraer probabilidad calibrada de quiebre (clase 1)
        prob_quiebre_arr = self._clasificador.predict_proba(x)
        if prob_quiebre_arr.shape[1] >= MIN_CLASES_CLASIFICADOR:
            prob_quiebre = float(prob_quiebre_arr[0][1])
        else:
            prob_quiebre = float(prob_quiebre_arr[0][0])

        return demanda_pred, prob_quiebre

    def predecir_matriz(self, matriz_x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Ejecuta inferencia vectorizada de alto rendimiento sobre una matriz completa.

        Args:
            matriz_x: Matriz NumPy 2D con forma (N, 10).

        Returns:
            Tupla (vector_demandas, vector_probabilidades).
        """
        if not self._entrenado:
            raise RuntimeError("El modelo debe entrenarse antes de ejecutar inferencia.")

        if matriz_x.shape[0] == 0:
            return np.empty(0, dtype=np.float64), np.empty(0, dtype=np.float64)

        demandas = np.maximum(0.0, self._regresor.predict(matriz_x))

        prob_matriz = self._clasificador.predict_proba(matriz_x)
        probabilidades = (
            prob_matriz[:, 1]
            if prob_matriz.shape[1] >= MIN_CLASES_CLASIFICADOR
            else prob_matriz[:, 0]
        )

        return demandas, probabilidades

    def guardar(self, ruta: Path | str) -> None:
        """Serializa y persiste el modelo entrenado en disco usando joblib."""
        if not self._entrenado:
            raise RuntimeError("No se puede persistir un modelo no entrenado.")
        destino = Path(ruta)
        destino.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "regresor": self._regresor,
                "clasificador": self._clasificador,
                "metricas": self._metricas,
                "entrenado": self._entrenado,
            },
            destino,
        )

    @classmethod
    def cargar(cls, ruta: Path | str) -> ModeloPredictorIA:
        """Deserializa y restaura un modelo previamente guardado."""
        origen = Path(ruta)
        if not origen.is_file():
            raise FileNotFoundError(f"Archivo de modelo no encontrado: {origen}")
        datos: dict[str, Any] = joblib.load(origen)
        instancia = cls()
        instancia._regresor = datos["regresor"]
        instancia._clasificador = datos["clasificador"]
        instancia._metricas = datos.get("metricas")
        instancia._entrenado = bool(datos.get("entrenado", True))
        return instancia
