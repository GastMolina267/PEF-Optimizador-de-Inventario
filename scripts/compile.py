"""Script multiplataforma de compilación y empaquetado para el Optimizador de Inventario.

Uso:
    python scripts/compile.py
    python scripts/compile.py --mode onefile
    python scripts/compile.py --clean
    python scripts/compile.py --dry-run
"""

from __future__ import annotations

import argparse
import contextlib
import shutil
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"
DATA_DIR = BASE_DIR / "data"
DOCS_DIR = BASE_DIR / "docs"
ENTRY_POINT = BASE_DIR / "main.py"
APP_NAME = "OptimizadorInventario"


def verificar_pyinstaller() -> bool:
    """Comprueba si PyInstaller está disponible en el entorno."""
    try:
        import PyInstaller  # noqa: F401

        return True
    except ImportError:
        return False


def limpiar_directorios() -> None:
    """Elimina artefactos previos de compilación."""
    for carpeta in [BASE_DIR / "build", BASE_DIR / "dist"]:
        if carpeta.exists():
            print(f"Limpiando {carpeta.name}/...")
            shutil.rmtree(carpeta, ignore_errors=True)

    for spec_file in BASE_DIR.glob("*.spec"):
        with contextlib.suppress(OSError):
            spec_file.unlink()


def construir_comando(mode: str, debug: bool) -> list[str]:
    """Genera la lista de argumentos para ejecutar PyInstaller."""
    sep = ";" if sys.platform.startswith("win") else ":"

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--name",
        APP_NAME,
        f"--{mode}",
    ]

    # Modo sin consola en producción a menos que se active debug
    if not debug:
        cmd.append("--windowed")

    # Inclusión de datos y assets
    if DATA_DIR.exists():
        cmd.extend(["--add-data", f"{DATA_DIR}{sep}data"])

    pres_dir = DOCS_DIR / "presentation"
    if pres_dir.exists():
        cmd.extend(["--add-data", f"{pres_dir}{sep}docs/presentation"])

    # Colección completa de assets, datos (icons.json), metadatos y módulos de Flet
    cmd.extend(["--collect-all", "flet"])
    cmd.extend(["--copy-metadata", "flet"])
    cmd.extend(["--collect-all", "flet_desktop"])
    # Agente de Elastic APM: importa transportes y métricas de forma dinámica.
    cmd.extend(["--collect-submodules", "elasticapm"])
    cmd.extend(["--copy-metadata", "elastic-apm"])

    # Hidden imports requeridos por Flet y multiproceso
    hidden_imports = [
        "flet",
        "flet_desktop",
        "concurrent.futures",
        "multiprocessing",
        "multiprocessing.spawn",
        "multiprocessing.popen_spawn_win32",
        "multiprocessing.popen_spawn_posix",
        "src.motor.motor_inventario",
        "src.inventario.catalogo_hash",
        "src.inventario.catalogo_lineal",
        "src.pedidos.procesador_concurrente",
        "src.pedidos.procesador_secuencial",
        "src.pedidos.evaluador",
        "src.pedidos.agrupador",
        "src.pedidos.combinaciones",
        "src.ranking.top_productos",
        "src.cache.cache_consultas",
        "src.datos.cargador",
        "src.datos.validador",
        "src.observabilidad.apm",
    ]
    for imp in hidden_imports:
        cmd.extend(["--hidden-import", imp])

    cmd.append(str(ENTRY_POINT))
    return cmd


def main() -> int:
    """Arma y ejecuta el comando de PyInstaller; devuelve su código de salida."""
    parser = argparse.ArgumentParser(
        description="Compila y empaqueta el Optimizador de Inventario usando PyInstaller."
    )
    parser.add_argument(
        "--mode",
        choices=["onedir", "onefile"],
        default="onedir",
        help="Modo de empaquetado: 'onedir' (recomendado) o 'onefile'.",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Limpia build/ y dist/ antes de compilar.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Mantiene la ventana de consola abierta para ver logs.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Solo muestra el comando generado sin ejecutarlo.",
    )

    args = parser.parse_args()

    if args.clean:
        limpiar_directorios()

    cmd = construir_comando(args.mode, args.debug)
    cmd_str = " ".join(f'"{c}"' if " " in c else c for c in cmd)

    print("=" * 70)
    print("OPTMIZADOR DE INVENTARIO — COMPILACIÓN Y EMPAQUETADO")
    print("=" * 70)
    print(f"Sistema Operativo: {sys.platform}")
    print(f"Modo:              {args.mode}")
    print(f"Punto de Entrada:  {ENTRY_POINT.name}")
    print(f"Comando PyInstaller:\n  {cmd_str}\n")

    if args.dry_run:
        print("[DRY-RUN] Comando validado con éxito. No se realizaron cambios.")
        return 0

    if not verificar_pyinstaller():
        print("ERROR: PyInstaller no está instalado en este entorno de Python.")
        print("Para instalarlo, ejecute:")
        print("    pip install pyinstaller")
        print("O instale todas las dependencias de desarrollo:")
        print("    pip install -r requirements-dev.txt")
        return 1

    print("Iniciando compilación con PyInstaller...")
    resultado = subprocess.run(cmd, cwd=BASE_DIR)

    if resultado.returncode == 0:
        salida = BASE_DIR / "dist" / APP_NAME
        print("\n" + "=" * 70)
        print("¡COMPILACIÓN EXITOSA!")
        print(f"Artefacto generado en: {salida}")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print(f"ERROR: La compilación falló con código de salida {resultado.returncode}.")
        print("=" * 70)

    return resultado.returncode


if __name__ == "__main__":
    sys.exit(main())
