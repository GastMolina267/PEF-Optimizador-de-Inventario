"""Generador sintético determinista de archivos JSON Lines masivos (.jsonl).

Utiliza buffering explícito (1 MB) y escritura por lotes sin indentación
para lograr alta tasa de transferencia en disco y consumo de memoria mínimo.
"""

from __future__ import annotations

import json
import random
from collections.abc import Iterator
from pathlib import Path

from src.datos.streaming import (
    TAMANO_BUFFER_DEFECTO,
    TAMANO_LOTE_DEFECTO,
    escribir_lineas_con_buffer,
)

CATEGORIAS_DISPONIBLES: tuple[str, ...] = (
    "Ferretería y Herramientas",
    "Pinturas y Acabados",
    "Materiales de Construcción",
    "Electricidad e Iluminación",
    "Plomería y Grifería",
    "Fijaciones y Tornillería",
    "Jardín y Exteriores",
    "Seguridad Industrial",
)

SUFIJOS_PRODUCTOS: tuple[str, ...] = (
    "Pro",
    "Industrial",
    "Estándar",
    "Económico",
    "Reforzado",
    "Compacto",
    "Max",
    "Plus",
)


def generar_lineas_productos(n_productos: int, seed: int = 42) -> Iterator[str]:
    """Genera strings JSONL para productos de forma lazy con semilla determinista."""
    rnd = random.Random(seed)
    for i in range(1, n_productos + 1):
        cat = rnd.choice(CATEGORIAS_DISPONIBLES)
        suf = rnd.choice(SUFIJOS_PRODUCTOS)
        nombre = f"Producto-{i} {suf} ({cat})"
        stock = rnd.randint(5, 500)
        precio = round(rnd.uniform(50.0, 15000.0), 2)
        doc = {
            "id": i,
            "nombre": nombre,
            "categoria": cat,
            "stock": stock,
            "precio": precio,
        }
        yield json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n"


def generar_lineas_pedidos(
    n_pedidos: int,
    n_productos: int,
    lineas_por_pedido: int = 4,
    seed: int = 42,
) -> Iterator[str]:
    """Genera strings JSONL para pedidos de forma lazy referenciando IDs válidos de productos."""
    rnd = random.Random(seed + 100)
    for id_ped in range(1, n_pedidos + 1):
        cant_lineas = rnd.randint(1, max(1, lineas_por_pedido))
        ids_elegidos = rnd.sample(range(1, n_productos + 1), k=cant_lineas)
        lineas_doc = [
            {"id_producto": id_p, "cantidad": rnd.randint(1, 15)} for id_p in ids_elegidos
        ]
        doc = {"id": id_ped, "lineas": lineas_doc}
        yield json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n"


def generar_archivos_grandes_jsonl(
    directorio_destino: str | Path,
    n_productos: int = 10000,
    n_pedidos: int = 50000,
    seed: int = 42,
    tamano_buffer: int = TAMANO_BUFFER_DEFECTO,
    tamano_lote: int = TAMANO_LOTE_DEFECTO,
) -> tuple[Path, Path]:
    """Genera productos.jsonl y pedidos.jsonl de gran escala con buffer explícito y memoria O(1).

    Retorna:
        (ruta_productos_jsonl, ruta_pedidos_jsonl)
    """
    dir_path = Path(directorio_destino)
    dir_path.mkdir(parents=True, exist_ok=True)

    ruta_prods = dir_path / "productos.jsonl"
    ruta_peds = dir_path / "pedidos.jsonl"

    # 1. Escribir productos en streaming con buffer
    escribir_lineas_con_buffer(
        ruta_prods,
        generar_lineas_productos(n_productos, seed=seed),
        tamano_buffer=tamano_buffer,
        tamano_lote=tamano_lote,
    )

    # 2. Escribir pedidos en streaming con buffer
    escribir_lineas_con_buffer(
        ruta_peds,
        generar_lineas_pedidos(n_pedidos, n_productos, seed=seed),
        tamano_buffer=tamano_buffer,
        tamano_lote=tamano_lote,
    )

    return ruta_prods, ruta_peds
