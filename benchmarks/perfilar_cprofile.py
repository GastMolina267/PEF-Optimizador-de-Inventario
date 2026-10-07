"""Script de perfilado por funciones utilizando cProfile y pstats.

Analiza el tiempo acumulado (cumulative) y el tiempo propio (tottime) de las
funciones del sistema durante la ejecución del pipeline completo de inventario.

Genera:
- docs/mediciones/cprofile_resumen.txt (Informe legible en texto plano)
- docs/mediciones/escenario_mediano.prof (Dump binario para SnakeViz / Tuna)
- docs/mediciones/escenario_grande.prof (Dump binario para SnakeViz / Tuna)
"""

from __future__ import annotations

import cProfile
import io
import pstats
from pathlib import Path

from src.motor.motor_inventario import MotorInventario

BASE_DIR = Path(__file__).resolve().parent.parent
DATASETS_DIR = BASE_DIR / "data" / "datasets"
MEDICIONES_DIR = BASE_DIR / "docs" / "mediciones"


def ejecutar_flujo_completo(ruta_dataset: Path, estrategia: str = "optimizado") -> None:
    """Ejecuta un ciclo representativo completo de operaciones de negocio."""
    motor = MotorInventario(estrategia=estrategia)
    motor.cargar_dataset(ruta_dataset)

    prods = motor.catalogo.obtener_todos()

    # 1. Búsquedas repetitivas de catálogo
    for i in range(min(50, len(prods))):
        _ = motor.buscar_por_id(prods[i].id)
        termino = prods[i].nombre.split()[0]
        _ = motor.buscar_por_nombre(termino, usar_cache=True)

    # 2. Batch picking
    _ = motor.agrupar_pedidos()

    # 3. Top-N
    _ = motor.calcular_top_productos(k=10)

    # 4. Alternativas con memoización
    if prods:
        _ = motor.buscar_alternativas(
            prods[0].categoria, 35000.0, max_combinaciones=10, max_candidatos=15
        )

    # 5. Procesamiento de pedidos sin mutar stock
    _ = motor.procesar_pedidos(descontar_stock=False)


def perfilar_dataset(nombre_dataset: str) -> tuple[str, Path]:
    """Ejecuta cProfile sobre el dataset y devuelve (texto_resumen, ruta_prof)."""
    ruta = DATASETS_DIR / nombre_dataset
    if not ruta.is_file():
        raise FileNotFoundError(f"Dataset no encontrado: {ruta}")

    prof = cProfile.Profile()
    prof.enable()
    ejecutar_flujo_completo(ruta, estrategia="optimizado")
    prof.disable()

    # Guardar dump binario .prof
    stem = Path(nombre_dataset).stem
    ruta_prof = MEDICIONES_DIR / f"escenario_{stem}.prof"
    prof.dump_stats(str(ruta_prof))

    # Formatear estadísticas legibles
    stream_cum = io.StringIO()
    ps_cum = pstats.Stats(prof, stream=stream_cum).sort_stats(pstats.SortKey.CUMULATIVE)
    ps_cum.print_stats(30)

    stream_tot = io.StringIO()
    ps_tot = pstats.Stats(prof, stream=stream_tot).sort_stats(pstats.SortKey.TIME)
    ps_tot.print_stats(30)

    resumen = (
        f"===============================================================================\n"
        f" PERFILADO CPROFILE: {nombre_dataset.upper()} (Estrategia Optimizada)\n"
        f"===============================================================================\n\n"
        f"--- TOP 30 FUNCIONES POR TIEMPO ACUMULADO (CUMULATIVE TIME) ---\n"
        f"{stream_cum.getvalue()}\n\n"
        f"--- TOP 30 FUNCIONES POR TIEMPO PROPIO (SELF / TOTTIME) ---\n"
        f"{stream_tot.getvalue()}\n\n"
    )

    return resumen, ruta_prof


def main():
    MEDICIONES_DIR.mkdir(parents=True, exist_ok=True)
    ruta_informe = MEDICIONES_DIR / "cprofile_resumen.txt"

    print("=" * 80)
    print(" EJECUTANDO PERFILADO CON CPROFILE")
    print("=" * 80)

    informes = []
    for ds in ["mediano.json", "grande.json"]:
        print(f"\n---> Perfilando {ds}...")
        resumen, ruta_prof = perfilar_dataset(ds)
        informes.append(resumen)
        print(f"     Dump binario guardado en: {ruta_prof}")

    with open(ruta_informe, "w", encoding="utf-8") as f:
        f.write("\n".join(informes))

    print("\n" + "=" * 80)
    print(f" [OK] Informe de cProfile generado exitosamente en:\n - {ruta_informe}")
    print("=" * 80)


if __name__ == "__main__":
    main()
