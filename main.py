"""Punto de entrada principal para el Optimizador de Inventario y Pedidos.

Permite la ejecución directa:
    python main.py

Y sirve como punto de anclaje canónico para compiladores y empaquetadores como PyInstaller.
"""

from __future__ import annotations

import multiprocessing
import sys
from pathlib import Path

# Asegurar que el directorio raíz del proyecto esté en sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import flet as ft  # noqa: E402

from src.ui.app import main as app_main  # noqa: E402


def run() -> None:
    """Inicia la aplicación de escritorio Flet."""
    if len(sys.argv) > 1 and sys.argv[1] in ("--version", "-v"):
        print("Optimizador de Inventario y Pedidos v1.0.0 (UBP - PEF 2026)")
        sys.exit(0)

    if hasattr(ft, "run") and callable(ft.run):
        ft.run(app_main)
    elif hasattr(ft, "app") and callable(ft.app):
        ft.app(target=app_main)
    else:
        ft.run(app_main)


if __name__ == "__main__":
    # Obligatorio en el .exe: sin esto, ProcessPoolExecutor relanza el GUI
    # (Windows spawn + PyInstaller). Comparativa y Pedidos abrían N ventanas.
    multiprocessing.freeze_support()
    run()
