"""Módulo de definición del modelo Producto."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class Producto:
    """Representa un producto individual dentro del catálogo de inventario.

    Atributos:
        id: Identificador numérico único del producto.
        nombre: Denominación descriptiva del producto.
        categoria: Clasificación o rubro al que pertenece el producto.
        stock: Cantidad de unidades físicas disponibles en almacén (>= 0).
        precio: Valor unitario monetario del producto (>= 0.0).
    """

    id: int
    nombre: str
    categoria: str
    stock: int
    precio: float

    def __post_init__(self) -> None:
        """Valida la integridad de los datos del producto."""
        if not isinstance(self.id, int) or self.id <= 0:
            raise ValueError(
                f"El identificador del producto debe ser un entero positivo, recibido: {self.id}"
            )
        if not isinstance(self.nombre, str) or not self.nombre.strip():
            raise ValueError("El nombre del producto no puede estar vacío.")
        if not isinstance(self.categoria, str) or not self.categoria.strip():
            raise ValueError("La categoría del producto no puede estar vacía.")
        if not isinstance(self.stock, int) or self.stock < 0:
            raise ValueError(
                "El stock del producto debe ser un entero mayor o igual a 0, recibido: "
                f"{self.stock}"
            )
        if not isinstance(self.precio, (int, float)) or self.precio < 0.0:
            raise ValueError(
                f"El precio del producto debe ser mayor o igual a 0.0, recibido: {self.precio}"
            )
        # Normalizar precio a float
        object.__setattr__(self, "precio", float(self.precio))
        object.__setattr__(self, "nombre", self.nombre.strip())
        object.__setattr__(self, "categoria", self.categoria.strip())

    def a_diccionario(self) -> dict[str, Any]:
        """Serializa el producto a un diccionario plano."""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "categoria": self.categoria,
            "stock": self.stock,
            "precio": self.precio,
        }

    @classmethod
    def desde_diccionario(cls, datos: dict[str, Any]) -> Producto:
        """Construye e inicializa un Producto a partir de un diccionario."""
        return cls(
            id=int(datos["id"]),
            nombre=str(datos["nombre"]),
            categoria=str(datos["categoria"]),
            stock=int(datos["stock"]),
            precio=float(datos["precio"]),
        )

    def clonar(self) -> Producto:
        """Retorna una copia independiente del producto."""
        return Producto(
            id=self.id,
            nombre=self.nombre,
            categoria=self.categoria,
            stock=self.stock,
            precio=self.precio,
        )
