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
        for p in productos:
            if p.id <= 0:
                errores.append(f"ID de producto no positivo: {p.id}")
            if p.id in ids_productos:
                errores.append(f"ID de producto duplicado: #{p.id}")
            ids_productos.add(p.id)

            if p.stock < 0:
                errores.append(f"Producto #{p.id} tiene stock negativo ({p.stock})")
            if p.precio < 0:
                errores.append(f"Producto #{p.id} tiene precio negativo ({p.precio})")
        return ids_productos, errores

    @staticmethod
    def verificar_pedidos(pedidos: Sequence[Pedido], ids_productos: set[int]) -> list[str]:
        """Verifica unicidad de pedidos e integridad referencial de líneas."""
        errores: list[str] = []
        ids_pedidos: set[int] = set()
        for ped in pedidos:
            if ped.id <= 0:
                errores.append(f"ID de pedido no positivo: {ped.id}")
            if ped.id in ids_pedidos:
                errores.append(f"ID de pedido duplicado: #{ped.id}")
            ids_pedidos.add(ped.id)

            if not ped.lineas:
                errores.append(f"Pedido #{ped.id} no contiene ninguna línea")

            for linea in ped.lineas:
                if linea.cantidad <= 0:
                    errores.append(
                        f"Pedido #{ped.id}: cantidad demandada inválida ({linea.cantidad}) "
                        f"para producto #{linea.id_producto}"
                    )
                if linea.id_producto not in ids_productos:
                    errores.append(
                        f"Pedido #{ped.id}: producto #{linea.id_producto} no existe en catálogo"
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

    @classmethod
    def validar_diccionario(cls, datos: dict[str, Any]) -> tuple[list[Producto], list[Pedido]]:
        """Valida y deserializa un diccionario de dataset crudo. Lanza ValueError ante errores."""
        cls.validar_estructura_cruda(datos)

        productos: list[Producto] = []
        ids_prods: set[int] = set()
        for idx, item in enumerate(datos["productos"]):
            if not isinstance(item, dict):
                raise ValueError(f"El producto en la posición {idx} no es un objeto JSON válido.")
            try:
                prod = Producto.desde_diccionario(item)
            except Exception as e:
                raise ValueError(
                    f"Error en datos de producto #{idx} (id={item.get('id')}): {e}"
                ) from e
            if prod.id in ids_prods:
                raise ValueError(f"Identificador de producto duplicado en dataset: #{prod.id}")
            ids_prods.add(prod.id)
            productos.append(prod)

        pedidos: list[Pedido] = []
        ids_peds: set[int] = set()
        for idx, item in enumerate(datos["pedidos"]):
            if not isinstance(item, dict):
                raise ValueError(f"El pedido en la posición {idx} no es un objeto JSON válido.")
            try:
                ped = Pedido.desde_diccionario(item)
            except Exception as e:
                raise ValueError(
                    f"Error en datos de pedido #{idx} (id={item.get('id')}): {e}"
                ) from e
            if ped.id in ids_peds:
                raise ValueError(f"Identificador de pedido duplicado en dataset: #{ped.id}")
            ids_peds.add(ped.id)

            for linea in ped.lineas:
                if linea.id_producto not in ids_prods:
                    raise ValueError(
                        f"Integridad rota en pedido #{ped.id}: el producto con id #{linea.id_producto} "
                        "no existe en el catálogo."
                    )
            pedidos.append(ped)

        return productos, pedidos
