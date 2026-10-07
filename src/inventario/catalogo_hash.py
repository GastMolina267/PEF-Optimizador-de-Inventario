"""Catálogo de inventario optimizado basado en Tablas Hash (O(1)).

Utiliza un diccionario principal (hash map) para acceso por identificador en tiempo O(1) promedio,
un índice secundario agrupado por categoría en O(1), y un índice invertido de palabras para acelerar
búsquedas por texto.
Mantiene exactamente la misma API pública que CatalogoLineal para permitir la sustitución transparente.
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
            for prod in productos:
                self.agregar(prod)

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

        palabras_busqueda = re.findall(r"\w+", texto_norm)
        if palabras_busqueda:
            # Candidatos por intersección de conjuntos hash O(1)
            conjuntos_candidatos = [
                self._indice_palabras.get(palabra, set()) for palabra in palabras_busqueda
            ]
            if any(len(c) == 0 for c in conjuntos_candidatos):
                # Si alguna palabra no existe en ningún producto, comprobamos subcadena
                candidatos_ids = set()
            else:
                candidatos_ids = set.intersection(*conjuntos_candidatos)

            # Si el índice invertido arrojó resultados, los devolvemos verificando la subcadena
            if candidatos_ids:
                coincidencias = [
                    self._productos_por_id[pid]
                    for pid in candidatos_ids
                    if texto_norm in self._productos_por_id[pid].nombre.lower()
                ]
                if coincidencias:
                    return coincidencias

        # Fallback de coincidencia general por subcadena sobre el universo
        return [
            prod for prod in self._productos_por_id.values() if texto_norm in prod.nombre.lower()
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
