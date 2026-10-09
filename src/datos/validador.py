"""Módulo para la validación de integridad de colecciones de productos y pedidos."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from src.modelos.pedido import Pedido
from src.modelos.producto import Producto


@dataclass
class ResultadoValidacion:
    """Resultado de la validación estructural y referencial de un dataset."""

    es_valido: bool
    errores: list[str] = field(default_factory=list)
    total_productos: int = 0
    total_pedidos: int = 0


class ValidadorDataset:
    """Validador unificado de integridad y coherencia para datasets."""

    def __init__(self, productos: Sequence[Producto], pedidos: Sequence[Pedido]):
        self.productos = list(productos)
        self.pedidos = list(pedidos)

    @staticmethod
    def validar_estructura_cruda(datos: dict[str, Any]) -> None:
        """Verifica que el contenido raíz sea un diccionario con 'productos' y 'pedidos'."""
        if not isinstance(datos, dict):
            raise ValueError(
                "El contenido raíz del dataset debe ser un objeto JSON (diccionario)."
            )
        if "productos" not in datos or not isinstance(datos["productos"], list):
            raise ValueError(
                "El dataset debe incluir una clave 'productos' con una lista de elementos."
            )
        if "pedidos" not in datos or not isinstance(datos["pedidos"], list):
            raise ValueError(
                "El dataset debe incluir una clave 'pedidos' con una lista de elementos."
            )

    @staticmethod
    def verificar_productos(productos: Sequence[Producto]) -> tuple[set[int], list[str]]:
        """Verifica unicidad de IDs y rangos válidos en la lista de productos."""
        errores: list[str] = []
        ids_productos: set[int] = set()
        for producto in productos:
            if producto.id <= 0:
                errores.append(f"ID de producto no positivo: {producto.id}")
            if producto.id in ids_productos:
                errores.append(f"ID de producto duplicado: #{producto.id}")
            ids_productos.add(producto.id)

            if producto.stock < 0:
                errores.append(f"Producto #{producto.id} tiene stock negativo ({producto.stock})")
            if producto.precio < 0:
                errores.append(
                    f"Producto #{producto.id} tiene precio negativo ({producto.precio})"
                )
        return ids_productos, errores

    @staticmethod
    def verificar_pedidos(pedidos: Sequence[Pedido], ids_productos: set[int]) -> list[str]:
        """Verifica unicidad de pedidos e integridad referencial de líneas."""
        errores: list[str] = []
        ids_pedidos: set[int] = set()
        for pedido in pedidos:
            if pedido.id <= 0:
                errores.append(f"ID de pedido no positivo: {pedido.id}")
            if pedido.id in ids_pedidos:
                errores.append(f"ID de pedido duplicado: #{pedido.id}")
            ids_pedidos.add(pedido.id)

            if not pedido.lineas:
                errores.append(f"Pedido #{pedido.id} no contiene ninguna línea")

            for linea in pedido.lineas:
                if linea.cantidad <= 0:
                    errores.append(
                        f"Pedido #{pedido.id}: cantidad demandada inválida ({linea.cantidad}) "
                        f"para producto #{linea.id_producto}"
                    )
                if linea.id_producto not in ids_productos:
                    errores.append(
                        f"Pedido #{pedido.id}: producto #{linea.id_producto} no existe en catálogo"
                    )
        return errores

    def validar_todo(self) -> ResultadoValidacion:
        """Valida unicidad de IDs, rangos válidos e integridad referencial."""
        ids_productos, errores_prods = self.verificar_productos(self.productos)
        errores_peds = self.verificar_pedidos(self.pedidos, ids_productos)
        todos_errores = errores_prods + errores_peds

        return ResultadoValidacion(
            es_valido=(len(todos_errores) == 0),
            errores=todos_errores,
            total_productos=len(self.productos),
            total_pedidos=len(self.pedidos),
        )

    @staticmethod
    def _deserializar_unicos(items: list[Any], modelo: type, nombre: str) -> list:
        """Construye ``modelo`` desde cada diccionario y verifica que los ids no se repitan.

        Lanza:
            ValueError: Si un elemento no es un objeto, tiene datos inválidos o repite id.
        """
        objetos = []
        ids: set[int] = set()
        for posicion, item in enumerate(items):
            if not isinstance(item, dict):
                raise ValueError(
                    f"El {nombre} en la posición {posicion} no es un objeto JSON válido."
                )
            try:
                objeto = modelo.desde_diccionario(item)
            except Exception as error:
                raise ValueError(
                    f"Error en datos de {nombre} #{posicion} (id={item.get('id')}): {error}"
                ) from error
            if objeto.id in ids:
                raise ValueError(f"Identificador de {nombre} duplicado en dataset: #{objeto.id}")
            ids.add(objeto.id)
            objetos.append(objeto)
        return objetos

    @classmethod
    def validar_diccionario(cls, datos: dict[str, Any]) -> tuple[list[Producto], list[Pedido]]:
        """Valida y deserializa un diccionario de dataset crudo. Lanza ValueError ante errores."""
        cls.validar_estructura_cruda(datos)

        productos = cls._deserializar_unicos(datos["productos"], Producto, "producto")
        pedidos = cls._deserializar_unicos(datos["pedidos"], Pedido, "pedido")
        ids_productos = {producto.id for producto in productos}
        for pedido in pedidos:
            for linea in pedido.lineas:
                if linea.id_producto not in ids_productos:
                    raise ValueError(
                        f"Integridad rota en pedido #{pedido.id}: el producto con id "
                        f"#{linea.id_producto} no existe en el catálogo."
                    )

        return productos, pedidos
