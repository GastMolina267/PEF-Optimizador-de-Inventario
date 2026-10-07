"""Módulo para la carga, validación y persistencia de datasets en formato JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.modelos.pedido import Pedido
from src.modelos.producto import Producto


def validar_dataset(datos: dict[str, Any]) -> tuple[list[Producto], list[Pedido]]:
    """Valida exhaustivamente la estructura e integridad referencial de un dataset.

    Reglas de validación:
    1. Debe contener las claves 'productos' y 'pedidos' como listas.
    2. Cada producto debe tener id único (> 0), nombre, categoría, stock (>= 0) y precio (>= 0).
    3. Cada pedido debe tener id único (> 0) y al menos una línea.
    4. Cada línea de pedido debe referenciar un id_producto existente en el catálogo.
    5. Cada cantidad de línea debe ser estrictamente mayor a 0.

    Retorna:
        Tupla (lista_productos, lista_pedidos).

    Lanza:
        ValueError: Ante cualquier incumplimiento de formato o integridad.
    """
    if not isinstance(datos, dict):
        raise ValueError("El contenido raíz del dataset debe ser un objeto JSON (diccionario).")

    if "productos" not in datos or not isinstance(datos["productos"], list):
        raise ValueError(
            "El dataset debe incluir una clave 'productos' con una lista de elementos."
        )

    if "pedidos" not in datos or not isinstance(datos["pedidos"], list):
        raise ValueError("El dataset debe incluir una clave 'pedidos' con una lista de elementos.")

    # 1. Validar productos y verificar unicidad de IDs
    productos: list[Producto] = []
    ids_productos: set[int] = set()

    for idx, item in enumerate(datos["productos"]):
        if not isinstance(item, dict):
            raise ValueError(f"El producto en la posición {idx} no es un objeto JSON válido.")
        try:
            prod = Producto.desde_diccionario(item)
        except Exception as e:
            raise ValueError(
                f"Error en datos de producto #{idx} (id={item.get('id')}): {e}"
            ) from e

        if prod.id in ids_productos:
            raise ValueError(f"Identificador de producto duplicado en dataset: #{prod.id}")
        ids_productos.add(prod.id)
        productos.append(prod)

    # 2. Validar pedidos, unicidad de IDs y referencia a productos existentes
    pedidos: list[Pedido] = []
    ids_pedidos: set[int] = set()

    for idx, item in enumerate(datos["pedidos"]):
        if not isinstance(item, dict):
            raise ValueError(f"El pedido en la posición {idx} no es un objeto JSON válido.")
        try:
            ped = Pedido.desde_diccionario(item)
        except Exception as e:
            raise ValueError(f"Error en datos de pedido #{idx} (id={item.get('id')}): {e}") from e

        if ped.id in ids_pedidos:
            raise ValueError(f"Identificador de pedido duplicado en dataset: #{ped.id}")
        ids_pedidos.add(ped.id)

        # Validar integridad referencial de las líneas
        for linea in ped.lineas:
            if linea.id_producto not in ids_productos:
                raise ValueError(
                    f"Integridad rota en pedido #{ped.id}: el producto con id #{linea.id_producto} "
                    "no existe en el catálogo."
                )

        pedidos.append(ped)

    return productos, pedidos


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


# Alias de conveniencia
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
        metadatos: Diccionario opcional con información adicional (semilla, descripción, fecha, etc.).
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
