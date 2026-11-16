"""Módulo de entrenamiento de modelos de Machine Learning para Inventario.

Permite entrenar y persistir el modelo de scikit-learn ejecutándolo como módulo:
    python -m src.ia.entrenador
"""

from __future__ import annotations

import argparse
from pathlib import Path

from src.datos.cargador import cargar_dataset_json
from src.ia.modelos import ModeloPredictorIA
from src.ia.predictor_demanda import PredictorDemanda

RUTA_MODELO_DEFECTO = Path("data/modelos/predictor_ia.joblib")
RUTA_DATASET_DEFECTO = Path("data/datasets/demo_oral.json")


def entrenar_y_guardar(
    ruta_dataset: Path = RUTA_DATASET_DEFECTO,
    ruta_salida: Path = RUTA_MODELO_DEFECTO,
    seed: int = 42,
    periodos: int = 30,
) -> ModeloPredictorIA:
    """Carga un dataset, genera histórico determinista, entrena y guarda el modelo."""
    print(f"[*] Cargando catálogo base desde: {ruta_dataset}")
    productos, _pedidos = cargar_dataset_json(ruta_dataset)

    print(
        f"[*] Generando dataset histórico sintético "
        f"({len(productos)} productos, {periodos} períodos)..."
    )
    predictor = PredictorDemanda()
    metricas = predictor.entrenar_con_catalogo(productos, seed=seed, periodos=periodos)

    print("\n" + "=" * 50)
    print("MÉTRICAS DE EVALUACIÓN DEL MODELO DE IA (scikit-learn)")
    print("=" * 50)
    print(f"  - R² Score (Demanda):     {metricas.r2_score:.4f}")
    print(f"  - MAE (Error Absoluto):   {metricas.mae:.2f} unidades")
    print(f"  - Precisión (Quiebre):    {metricas.precision:.4f}")
    print(f"  - Recall (Sensibilidad):  {metricas.recall:.4f}")
    print(f"  - F1-Score Ponderado:     {metricas.f1_score:.4f}")
    print(f"  - Muestras de Test:       {metricas.total_muestras_test}")
    print(f"  - Memoria Heap Estimada:  {metricas.memoria_heap_kb:.2f} KB")
    print("=" * 50 + "\n")

    print(f"[*] Guardando modelo entrenado en: {ruta_salida}")
    predictor.guardar_modelo(ruta_salida)
    print("[+] Modelo guardado y listo para inferencia en producción.")
    return predictor.modelo_ia


def main() -> None:
    """Punto de entrada de línea de comandos."""
    parser = argparse.ArgumentParser(description="Entrenador de Modelos de IA para Inventario")
    parser.add_argument(
        "--dataset", type=Path, default=RUTA_DATASET_DEFECTO, help="Ruta al dataset JSON"
    )
    parser.add_argument(
        "--salida", type=Path, default=RUTA_MODELO_DEFECTO, help="Ruta de guardado .joblib"
    )
    parser.add_argument("--seed", type=int, default=42, help="Semilla determinista")
    parser.add_argument("--periodos", type=int, default=30, help="Períodos de simulación")
    args = parser.parse_args()

    entrenar_y_guardar(
        ruta_dataset=args.dataset,
        ruta_salida=args.salida,
        seed=args.seed,
        periodos=args.periodos,
    )


if __name__ == "__main__":
    main()
