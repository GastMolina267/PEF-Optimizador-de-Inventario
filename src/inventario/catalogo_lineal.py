"""Catálogo de inventario con almacenamiento lineal (Baseline).

Esta implementación utiliza una lista estándar de Python como estructura de datos
interna para almacenar los productos. Todas las operaciones de búsqueda y verificación
requieren un recorrido secuencial de complejidad temporal O(n).
Sirve como línea base (baseline) para el desafío experimental frente a la tabla hash O(1).
"""

from __future__ import annotations

from collections.abc import Sequence

from src.modelos.producto import Producto


class CatalogoLineal:
    """Catálogo de productos implementado sobre una lista de Python (O(n))."""

    def __init__(self, productos: Sequence[Producto] | None = None) -> None:
        """Inicializa el catálogo con una lista interna de productos.

        Complejidad temporal de inicialización: O(n) para copiar los elementos.
        """
        self._productos: list[Producto] = []
        if productos:
            for producto in productos:
                self.agregar(producto)

    def agregar(self, producto: Producto) -> None:
        """Agrega un producto al catálogo previa verificación de identificador único.

        Complejidad temporal: O(n) debido a la verificación de unicidad en la lista.
        """
        for existente in self._productos:
            if existente.id == producto.id:
                raise ValueError(
                    f"Conflicto de identificador: ya existe un producto con id #{producto.id} "
                    f"({existente.nombre})"
                )
        self._productos.append(producto)

    def buscar_por_id(self, id_producto: int) -> Producto | None:
        """Busca un producto por su identificador recorriendo linealmente la lista.

        Complejidad temporal: O(n) en el peor y caso promedio. O(1) si está al inicio.
        """
        for producto in self._productos:
            if producto.id == id_producto:
                return producto
        return None

    def buscar_por_nombre(self, texto: str) -> list[Producto]:
        """Busca productos cuyo nombre contenga el texto buscado (insensible a mayúsculas).

        Complejidad temporal: O(n * L), con n la cantidad de productos y L la longitud media
        del nombre.
        """
        texto_norm = texto.lower()
        coincidencias: list[Producto] = []
        for producto in self._productos:
            if texto_norm in producto.nombre.lower():
                coincidencias.append(producto)
        return coincidencias

    def buscar_por_categoria(self, categoria: str) -> list[Producto]:
        """Busca todos los productos pertenecientes a una categoría exacta.

        Complejidad temporal: O(n).
        """
        cat_norm = categoria.lower()
        coincidencias: list[Producto] = []
        for producto in self._productos:
            if producto.categoria.lower() == cat_norm:
                coincidencias.append(producto)
        return coincidencias

    def actualizar_stock(self, id_producto: int, nuevo_stock: int) -> bool:
        """Modifica el stock disponible de un producto identificado por su id.

        Complejidad temporal: O(n).
        """
        if nuevo_stock < 0:
            raise ValueError(f"El nuevo stock no puede ser negativo: {nuevo_stock}")
        for producto in self._productos:
            if producto.id == id_producto:
                producto.stock = nuevo_stock
                return True
        return False

    def descontar_stock(self, id_producto: int, cantidad: int) -> bool:
        """Descuenta una cantidad determinada de stock si existe disponibilidad suficiente.

        Complejidad temporal: O(n).
        """
        if cantidad <= 0:
            raise ValueError(f"La cantidad a descontar debe ser positiva: {cantidad}")
        for producto in self._productos:
            if producto.id == id_producto:
                if producto.stock >= cantidad:
                    producto.stock -= cantidad
                    return True
                return False
        return False

    def obtener_todos(self) -> list[Producto]:
        """Retorna una lista superficial con todos los productos registrados.

        Complejidad temporal: O(n).
        """
        return list(self._productos)

    def clonar(self) -> CatalogoLineal:
        """Genera una réplica profunda e independiente del catálogo lineal."""
        copias = [producto.clonar() for producto in self._productos]
        catalogo_nuevo = CatalogoLineal()
        catalogo_nuevo._productos = copias
        return catalogo_nuevo

    def __len__(self) -> int:
        """Cantidad total de productos registrados en el catálogo."""
        return len(self._productos)

    def __iter__(self):
        """Permite iterar sobre los productos del catálogo."""
        return iter(self._productos)
