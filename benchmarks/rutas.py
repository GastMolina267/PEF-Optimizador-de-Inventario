"""Validación de rutas recibidas por línea de comandos en los scripts de benchmarks."""

from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def ruta_en_proyecto(ruta: str | Path) -> Path:
    """Resuelve ``ruta`` y exige que quede dentro del repositorio.

    Los argumentos de línea de comandos no deben poder leer ni escribir archivos fuera
    del proyecto (por ejemplo, con ``../../``).

    Argumentos:
        ruta: Ruta absoluta o relativa a la raíz del repositorio.

    Retorna:
        La ruta absoluta, ya resuelta.

    Lanza:
        ValueError: Si la ruta resuelta queda fuera del repositorio.
    """
    ruta = Path(ruta)
    absoluta = (ruta if ruta.is_absolute() else BASE_DIR / ruta).resolve()
    if not absoluta.is_relative_to(BASE_DIR.resolve()):
        raise ValueError(f"La ruta {ruta} queda fuera del proyecto")
    return absoluta
