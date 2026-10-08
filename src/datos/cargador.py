"""Módulo para la carga, validación y persistencia de datasets en formato JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.datos.validador import ValidadorDataset
from src.modelos.pedido import Pedido
from src.modelos.producto import Producto


def validar_dataset(datos: dict[str, Any]) -> tuple[list[Producto], list[Pedido]]:
    """Valida exhaustivamente la estructura e integridad referencial de un dataset.

    Delega al ValidadorDataset unificado.
    """
    return ValidadorDataset.validar_diccionario(datos)


def cargar_dataset_json(ruta: str | Path) -> tuple[list[Producto], list[Pedido]]:
    """Carga un archivo JSON desde el sistema de archivos y valida su integridad.

    Argumentos:
        ruta: Ruta al archivo JSON en disco.

    Retorna:
        Tupla con las listas de Producto y Pedido validadas.
    """
    path_archivo = Path(ruta)
    if not path_archivo.is_file():
        raise FileNotFoundError(
            f"No se encontró el archivo de dataset en la ruta: {path_archivo.resolve()}"
        )

    with open(path_archivo, encoding="utf-8") as f:
        try:
            contenido = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Error de sintaxis JSON en el archivo {path_archivo.name}: {e}"
            ) from e

    return validar_dataset(contenido)


# Alias para retrocompatibilidad (estandarizado en cargar_dataset_json)
cargar_dataset = cargar_dataset_json


def guardar_dataset_json(
    ruta: str | Path,
    productos: list[Producto],
    pedidos: list[Pedido],
    metadatos: dict[str, Any] | None = None,
) -> None:
    """Serializa y almacena un conjunto de productos y pedidos en un archivo JSON estructurado.

    Argumentos:
        ruta: Ruta de destino para el archivo.
        productos: Lista de instancias Producto.
        pedidos: Lista de instancias Pedido.
        metadatos: Información adicional opcional (semilla, descripción, fecha, etc.).
    """
    path_archivo = Path(ruta)
    path_archivo.parent.mkdir(parents=True, exist_ok=True)

    payload: dict[str, Any] = {
        "metadatos": metadatos
        or {
            "total_productos": len(productos),
            "total_pedidos": len(pedidos),
        },
        "productos": [p.a_diccionario() for p in productos],
        "pedidos": [ped.a_diccionario() for ped in pedidos],
    }

    with open(path_archivo, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
