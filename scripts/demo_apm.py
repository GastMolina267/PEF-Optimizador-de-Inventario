"""Genera actividad de ejemplo para ver en Kibana (Elastic APM).

Corre las operaciones principales del motor con las dos estrategias sobre los datasets
del repo, procesa pedidos en secuencial y con pool, y provoca a propósito un error de
carga para que aparezca en la vista de errores.

Uso (con ELASTIC_APM_SERVER_URL y ELASTIC_APM_API_KEY en el entorno o en .env)::

    python -m scripts.demo_apm
    python -m scripts.demo_apm --vueltas 5
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.motor.motor_inventario import MotorInventario  # noqa: E402
from src.observabilidad import cerrar_apm, configurar_apm, transaccion  # noqa: E402
from src.pedidos.gestor_pool import pool_pedidos  # noqa: E402

DATASETS = BASE_DIR / "data" / "datasets"


def correr_escenario(estrategia: str, dataset: str) -> None:
    """Una vuelta de operaciones de negocio, agrupada en una transacción."""
    with transaccion(f"escenario.{estrategia}", "escenario", {"dataset": dataset}):
        motor = MotorInventario(estrategia=estrategia)
        motor.cargar_dataset(DATASETS / dataset)
        for producto in motor.catalogo.obtener_todos()[:20]:
            motor.buscar_por_nombre(producto.nombre.split()[0])
        motor.obtener_top_solicitados(k=10)
        motor.agrupar_pedidos()
        motor.procesar_pedidos()
        motor.procesar_pedidos(concurrente=True)


def provocar_error_de_carga() -> None:
    """Carga un dataset inválido: el error queda registrado en Elastic APM."""
    with tempfile.TemporaryDirectory() as carpeta:
        ruta = Path(carpeta) / "dataset_invalido.json"
        ruta.write_text(json.dumps({"productos": [], "pedidos": "no es una lista"}), "utf-8")
        try:
            MotorInventario(estrategia="optimizado").cargar_dataset(ruta)
        except ValueError as error:
            print(f"Error de carga provocado y enviado a APM: {error}")


def main(argv: list[str] | None = None) -> int:
    """Envía las vueltas de actividad y el error de prueba; devuelve el código de salida."""
    parser = argparse.ArgumentParser(description="Actividad de ejemplo para Elastic APM.")
    parser.add_argument("--vueltas", type=int, default=3, choices=range(1, 21))
    args = parser.parse_args(argv)

    if configurar_apm() is None:
        print("Falta ELASTIC_APM_SERVER_URL (entorno o .env). Ver .env.example.")
        return 1

    try:
        for vuelta in range(1, args.vueltas + 1):
            for estrategia in ("baseline", "optimizado"):
                for dataset in ("pequeno.json", "mediano.json", "grande.json"):
                    correr_escenario(estrategia, dataset)
            print(f"Vuelta {vuelta}/{args.vueltas} enviada")
        provocar_error_de_carga()
    finally:
        pool_pedidos.cerrar()
        cerrar_apm()
    print("Listo. Ver Kibana: Observability > Applications > optimizador-inventario")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
