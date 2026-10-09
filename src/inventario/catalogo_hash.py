"""Catálogo de inventario optimizado basado en Tablas Hash (O(1)).

Usa un diccionario principal (hash map) para acceder por identificador en O(1) promedio,
un índice secundario por categoría en O(1) y un índice invertido de palabras para acelerar
las búsquedas por texto.

Mantiene la misma API pública que CatalogoLineal, así que uno reemplaza al otro sin cambios.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from src.modelos.producto import Producto


class CatalogoHash:
    """Catálogo de productos implementado sobre estructuras Hash (O(1) promedio)."""

    def __init__(self, productos: Sequence[Producto] | None = None) -> None:
        """Inicializa el catálogo hash y sus índices secundarios.

        Complejidad temporal de inicialización: O(n), construyendo los diccionarios.
        """
        self._productos_por_id: dict[int, Producto] = {}
        self._indice_categoria: dict[str, list[Producto]] = {}
        self._indice_palabras: dict[str, set[int]] = {}

        if productos:
            for producto in productos:
                self.agregar(producto)

    def _indexar_nombre(self, producto: Producto) -> None:
        """Descompone el nombre del producto en palabras clave para el índice invertido."""
        palabras = re.findall(r"\w+", producto.nombre.lower())
        for palabra in palabras:
            if palabra not in self._indice_palabras:
                self._indice_palabras[palabra] = set()
            self._indice_palabras[palabra].add(producto.id)

    def _desindexar_nombre(self, producto: Producto) -> None:
        """Remueve los identificadores del producto del índice invertido."""
        palabras = re.findall(r"\w+", producto.nombre.lower())
        for palabra in palabras:
            if palabra in self._indice_palabras:
                self._indice_palabras[palabra].discard(producto.id)
                if not self._indice_palabras[palabra]:
                    del self._indice_palabras[palabra]

    def agregar(self, producto: Producto) -> None:
        """Agrega un producto al catálogo e indexa sus campos clave.

        Complejidad temporal: O(1) promedio para inserción en hash tables.
        """
        if producto.id in self._productos_por_id:
            raise ValueError(
                f"Conflicto de identificador: ya existe un producto con id #{producto.id}"
            )

        self._productos_por_id[producto.id] = producto

        # Índice secundario por categoría
        cat_norm = producto.categoria.lower()
        if cat_norm not in self._indice_categoria:
            self._indice_categoria[cat_norm] = []
        self._indice_categoria[cat_norm].append(producto)

        # Índice invertido de palabras para el nombre
        self._indexar_nombre(producto)

    def buscar_por_id(self, id_producto: int) -> Producto | None:
        """Busca un producto por su clave primaria en la tabla hash.

        Complejidad temporal: O(1) promedio y en el mejor caso.
        """
        return self._productos_por_id.get(id_producto)

    def buscar_por_nombre(self, texto: str) -> list[Producto]:
        """Busca productos por texto.

        Utiliza el índice invertido de palabras clave cuando sea posible,
        garantizando coincidencia por subcadena exacta para mantener
        equivalencia total con CatalogoLineal.
        """
        texto_norm = texto.lower().strip()
        if not texto_norm:
            return []
        # Candidatos por intersección de conjuntos del índice invertido (hash, O(1) por palabra),
        # verificando la subcadena para dar exactamente lo mismo que CatalogoLineal.
        coincidencias = [
            self._productos_por_id[id_producto]
            for id_producto in self._candidatos_por_indice(texto_norm)
            if texto_norm in self._productos_por_id[id_producto].nombre.lower()
        ]
        # Fallback: el índice no encontró nada (p. ej. la consulta es parte de una palabra).
        return coincidencias or self._buscar_por_subcadena(texto_norm)

    def _candidatos_por_indice(self, texto_norm: str) -> set[int]:
        """Ids de productos cuyo nombre contiene todas las palabras de la consulta."""
        conjuntos = [
            self._indice_palabras.get(palabra, set()) for palabra in re.findall(r"\w+", texto_norm)
        ]
        if not conjuntos or not all(conjuntos):
            return set()
        return set.intersection(*conjuntos)

    def _buscar_por_subcadena(self, texto_norm: str) -> list[Producto]:
        """Recorre todo el catálogo comparando por subcadena (O(n · m))."""
        return [
            producto
            for producto in self._productos_por_id.values()
            if texto_norm in producto.nombre.lower()
        ]

    def buscar_por_categoria(self, categoria: str) -> list[Producto]:
        """Recupera la lista de productos de una categoría mediante búsqueda indexada O(1).

        Complejidad temporal: O(1) para el acceso al bucket del diccionario.
        """
        cat_norm = categoria.lower().strip()
        return list(self._indice_categoria.get(cat_norm, []))

    def actualizar_stock(self, id_producto: int, nuevo_stock: int) -> bool:
        """Modifica el stock en tiempo constante O(1)."""
        if nuevo_stock < 0:
            raise ValueError(f"El nuevo stock no puede ser negativo: {nuevo_stock}")

        producto = self._productos_por_id.get(id_producto)
        if producto is not None:
            producto.stock = nuevo_stock
            return True
        return False

    def descontar_stock(self, id_producto: int, cantidad: int) -> bool:
        """Descuenta stock en tiempo constante O(1) si la disponibilidad es suficiente."""
        if cantidad <= 0:
            raise ValueError(f"La cantidad a descontar debe ser positiva: {cantidad}")

        producto = self._productos_por_id.get(id_producto)
        if producto is not None and producto.stock >= cantidad:
            producto.stock -= cantidad
            return True
        return False

    def obtener_todos(self) -> list[Producto]:
        """Retorna una lista con todos los productos registrados."""
        return list(self._productos_por_id.values())

    def clonar(self) -> CatalogoHash:
        """Genera una réplica profunda e independiente del catálogo hash."""
        copias = [p.clonar() for p in self._productos_por_id.values()]
        return CatalogoHash(copias)

    def __len__(self) -> int:
        """Cantidad total de productos registrados en el catálogo hash."""
        return len(self._productos_por_id)

    def __iter__(self):
        """Itera sobre los productos del catálogo."""
        return iter(self._productos_por_id.values())
