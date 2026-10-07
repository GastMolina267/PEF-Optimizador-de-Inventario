"""Punto de entrada local de las automatizaciones Origin (Etapa 6).

Uso:
    python -m automations.ejecutar
    python -m automations.ejecutar --complejidad
    python -m automations.ejecutar --propuestas

Los agentes Origin invocan este módulo en cada push. Solo escribe Markdown
en ``docs/``; jamás altera el motor de inventario.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from automations.analizar_complejidad import ejecutar as ejecutar_complejidad
from automations.inventario_funciones import resolver_raiz
from automations.proponer_mejoras import ejecutar as ejecutar_propuestas


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Regenera el análisis de complejidad y/o las propuestas de mejora."
    )
    parser.add_argument(
        "--complejidad",
        action="store_true",
        help="Solo automatización 1: sección marcada de docs/analisis.md",
    )
    parser.add_argument(
        "--propuestas",
        action="store_true",
        help="Solo automatización 2: docs/propuestas-mejora.md",
    )
    parser.add_argument(
        "--raiz",
        type=Path,
        default=None,
        help="Raíz del repositorio (por defecto se detecta sola).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    args = construir_parser().parse_args(argv)
    raiz = resolver_raiz(args.raiz)
    correr_todo = not args.complejidad and not args.propuestas

    if args.complejidad or correr_todo:
        informes = ejecutar_complejidad(raiz)
        print(f"[complejidad] {len(informes)} funciones fundamentales -> docs/analisis.md")
        for inf in informes:
            print(f"  - {inf.funcion.nombre_calificado}: {inf.promedio} (peor {inf.peor})")

    if args.propuestas or correr_todo:
        ruta = ejecutar_propuestas(raiz)
        print(f"[propuestas] informe escrito en {ruta.relative_to(raiz).as_posix()}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
