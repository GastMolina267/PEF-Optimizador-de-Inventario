"""Interfaz común de los catálogos de inventario.

``CatalogoLineal`` (baseline) y ``CatalogoHash`` (optimizado) no comparten una clase
base: son intercambiables porque implementan los mismos métodos. ``Catalogo`` describe
esa interfaz como un ``Protocol`` (tipado estructural), así las funciones que reciben
un catálogo pueden declararlo sin depender de una implementación concreta.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from src.modelos.producto import Producto


@runtime_checkable
class Catalogo(Protocol):
    """Operaciones que ofrece cualquier catálogo de productos."""

    def agregar(self, producto: Producto) -> None:
        """Registra un producto nuevo; falla si el id ya existe."""

    def buscar_por_id(self, id_producto: int) -> Producto | None:
        """Devuelve el producto con ese id, o None."""

    def buscar_por_nombre(self, texto: str) -> list[Producto]:
        """Productos cuyo nombre contiene el texto (sin distinguir mayúsculas)."""

    def buscar_por_categoria(self, categoria: str) -> list[Producto]:
        """Productos de la categoría indicada."""

    def actualizar_stock(self, id_producto: int, nuevo_stock: int) -> bool:
        """Reemplaza el stock de un producto; devuelve False si no existe."""

    def descontar_stock(self, id_producto: int, cantidad: int) -> bool:
        """Descuenta stock si alcanza; devuelve False si no se pudo descontar."""

    def obtener_todos(self) -> list[Producto]:
        """Lista de todos los productos del catálogo."""

    def __len__(self) -> int:
        """Cantidad de productos."""
