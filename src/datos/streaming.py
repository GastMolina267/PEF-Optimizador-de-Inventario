"""Módulo de lectura, escritura y procesamiento en streaming con buffer para datasets masivos.

Implementa los requisitos de la Fase F5:
1. Buffering explícito (por defecto 1 MB) para minimizar syscalls de I/O en disco.
2. Formato JSON Lines (.jsonl) para serialización y deserialización línea por línea.
3. Generador en_lotes compatible con Python 3.10+ (memoria constante O(1)).
4. Exportación con buffer de resultados a CSV.
"""

from __future__ import annotations

import csv
import itertools
import json
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any, TypeVar

from src.modelos.pedido import LineaPedido, Pedido
from src.modelos.producto import Producto

T = TypeVar("T")

# Tamaño de buffer de 1 MB (1 << 20 bytes) para optimizar transferencias de disco
TAMANO_BUFFER_DEFECTO: int = 1024 * 1024
TAMANO_LOTE_DEFECTO: int = 5000


def en_lotes(iterable: Iterable[T], n: int) -> Iterator[tuple[T, ...]]:
    """Agrupa elementos de un iterable en lotes de tamaño n sin materializarlos en memoria.

    Compatible con Python 3.10 y 3.11 sin depender de itertools.batched (Python 3.12+).
    """
    if n < 1:
        raise ValueError("El tamaño de lote debe ser al menos 1")
    iterator = iter(iterable)
    while lote := tuple(itertools.islice(iterator, n)):
        yield lote


def escribir_lineas_con_buffer(
    ruta: str | Path,
    lineas: Iterable[str],
    tamano_buffer: int = TAMANO_BUFFER_DEFECTO,
    tamano_lote: int = TAMANO_LOTE_DEFECTO,
) -> int:
    """Escribe un flujo de líneas de texto utilizando buffering y writelines por bloques.

    Argumentos:
        ruta: Archivo destino.
        lineas: Generador o iterable de cadenas de texto (deben terminar con newline).
        tamano_buffer: Tamaño del buffer interno de open() en bytes.
        tamano_lote: Cantidad de líneas acumuladas antes de cada llamada a writelines().

    Retorna:
        Cantidad total de líneas escritas.
    """
    path_archivo = Path(ruta)
    path_archivo.parent.mkdir(parents=True, exist_ok=True)

    total_escritas = 0
    with open(path_archivo, "w", encoding="utf-8", buffering=tamano_buffer) as f:
        for bloque in en_lotes(lineas, tamano_lote):
            f.writelines(bloque)
            total_escritas += len(bloque)

    return total_escritas


def leer_productos_streaming_jsonl(
    ruta: str | Path,
    tamano_buffer: int = TAMANO_BUFFER_DEFECTO,
) -> Iterator[Producto]:
    """Lee productos de un archivo .jsonl en streaming, sin cargar el archivo en memoria.

    Cada línea debe ser un objeto JSON válido con campos id, nombre, categoria, stock, precio.
    Lanza ValueError si alguna línea contiene JSON inválido o campos obligatorios faltantes.
    """
    path_archivo = Path(ruta)
    if not path_archivo.is_file():
        raise FileNotFoundError(f"Archivo de productos no encontrado: {path_archivo}")

    with open(path_archivo, encoding="utf-8", buffering=tamano_buffer) as f:
        for num_linea, linea in enumerate(f, start=1):
            linea_limpia = linea.strip()
            if not linea_limpia:
                continue
            try:
                d = json.loads(linea_limpia)
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"Error de sintaxis JSON en línea {num_linea} de {path_archivo.name}: {e}"
                ) from e

            try:
                yield Producto(
                    id=int(d["id"]),
                    nombre=str(d["nombre"]),
                    categoria=str(d["categoria"]),
                    stock=int(d["stock"]),
                    precio=float(d["precio"]),
                )
            except (KeyError, TypeError, ValueError) as e:
                raise ValueError(
                    f"Estructura inválida de Producto en línea {num_linea} de "
                    f"{path_archivo.name}: {e}"
                ) from e


def leer_pedidos_streaming_jsonl(
    ruta: str | Path,
    tamano_buffer: int = TAMANO_BUFFER_DEFECTO,
) -> Iterator[Pedido]:
    """Lee pedidos desde un archivo .jsonl línea a línea en streaming sin materializar la lista.

    Cada línea debe ser un objeto JSON con ``id`` y ``lineas`` (lista de objetos con
    ``id_producto`` y ``cantidad``). Lanza ValueError si alguna línea está corrupta.
    """
    path_archivo = Path(ruta)
    if not path_archivo.is_file():
        raise FileNotFoundError(f"Archivo de pedidos no encontrado: {path_archivo}")

    with open(path_archivo, encoding="utf-8", buffering=tamano_buffer) as f:
        for num_linea, linea in enumerate(f, start=1):
            linea_limpia = linea.strip()
            if not linea_limpia:
                continue
            try:
                d = json.loads(linea_limpia)
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"Error de sintaxis JSON en línea {num_linea} de {path_archivo.name}: {e}"
                ) from e

            try:
                lineas_pedido = [
                    LineaPedido(
                        id_producto=int(lp["id_producto"]),
                        cantidad=int(lp["cantidad"]),
                    )
                    for lp in d.get("lineas", [])
                ]
                yield Pedido(id=int(d["id"]), lineas=lineas_pedido)
            except (KeyError, TypeError, ValueError) as e:
                raise ValueError(
                    f"Estructura inválida de Pedido en línea {num_linea} de "
                    f"{path_archivo.name}: {e}"
                ) from e


def escribir_productos_jsonl(
    ruta: str | Path,
    productos: Iterable[Producto],
    tamano_buffer: int = TAMANO_BUFFER_DEFECTO,
    tamano_lote: int = TAMANO_LOTE_DEFECTO,
) -> int:
    """Serializa y escribe una secuencia de productos en formato .jsonl con buffer."""
    lineas = (
        json.dumps(
            {
                "id": p.id,
                "nombre": p.nombre,
                "categoria": p.categoria,
                "stock": p.stock,
                "precio": p.precio,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
        + "\n"
        for p in productos
    )
    return escribir_lineas_con_buffer(ruta, lineas, tamano_buffer, tamano_lote)


def escribir_pedidos_jsonl(
    ruta: str | Path,
    pedidos: Iterable[Pedido],
    tamano_buffer: int = TAMANO_BUFFER_DEFECTO,
    tamano_lote: int = TAMANO_LOTE_DEFECTO,
) -> int:
    """Serializa y escribe una secuencia de pedidos en formato .jsonl con buffer."""
    lineas = (
        json.dumps(
            {
                "id": p.id,
                "lineas": [
                    {"id_producto": lp.id_producto, "cantidad": lp.cantidad} for lp in p.lineas
                ],
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
        + "\n"
        for p in pedidos
    )
    return escribir_lineas_con_buffer(ruta, lineas, tamano_buffer, tamano_lote)


def _fila_picking_desde_diccionario(datos: dict[str, Any]) -> list[Any]:
    """Fila CSV desde ``a_diccionario()`` o un diccionario equivalente."""
    if "pedidos_solicitantes" in datos:
        total_pedidos = len(datos["pedidos_solicitantes"])
    else:
        total_pedidos = datos.get("total_pedidos", 0)
    return [
        datos.get("id_producto", 0),
        datos.get("nombre_producto", datos.get("nombre", "")),
        datos.get("categoria", ""),
        datos.get("cantidad_total", datos.get("total_demandado", 0)),
        datos.get("stock_disponible", 0),
        total_pedidos,
    ]


def _fila_picking_desde_atributos(item: Any) -> list[Any]:
    """Fila CSV desde un objeto con atributos (por ejemplo, un ítem sin ``a_diccionario``)."""
    producto = getattr(item, "producto", None)
    if hasattr(item, "demandas_por_pedido"):
        total_pedidos = len(item.demandas_por_pedido)
    else:
        total_pedidos = getattr(item, "total_pedidos", 0)
    return [
        getattr(item, "id_producto", 0),
        producto.nombre if producto else getattr(item, "nombre", ""),
        producto.categoria if producto else getattr(item, "categoria", ""),
        getattr(item, "cantidad_total", getattr(item, "total_demandado", 0)),
        producto.stock if producto else getattr(item, "stock_disponible", 0),
        total_pedidos,
    ]


def _fila_picking(item: Any) -> list[Any]:
    """Convierte un ítem de picking (objeto o diccionario) en una fila del CSV."""
    if hasattr(item, "a_diccionario"):
        return _fila_picking_desde_diccionario(item.a_diccionario())
    if isinstance(item, dict):
        return _fila_picking_desde_diccionario(item)
    return _fila_picking_desde_atributos(item)


def exportar_picking_csv_con_buffer(
    ruta: str | Path,
    items_picking: Iterable[Any],
    tamano_buffer: int = TAMANO_BUFFER_DEFECTO,
) -> int:
    """Exporta el reporte consolidado de picking a un archivo CSV con buffer optimizado.

    Argumentos:
        ruta: Destino del archivo CSV.
        items_picking: Iterable de ItemPickingConsolidado o diccionarios equivalentes.
        tamano_buffer: Tamaño del buffer interno de I/O en bytes.

    Retorna:
        Cantidad de filas de items escritas.
    """
    path_archivo = Path(ruta)
    path_archivo.parent.mkdir(parents=True, exist_ok=True)

    filas_escritas = 0
    with open(path_archivo, "w", encoding="utf-8", newline="", buffering=tamano_buffer) as f:
        escritor = csv.writer(f)
        escritor.writerow(
            [
                "id_producto",
                "nombre",
                "categoria",
                "total_demandado",
                "stock_disponible",
                "total_pedidos",
            ]
        )

        for item in items_picking:
            escritor.writerow(_fila_picking(item))
            filas_escritas += 1

    return filas_escritas
