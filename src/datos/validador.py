"""Módulo para la validación de integridad de colecciones de productos y pedidos."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

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
    """Validador exhaustivo de integridad y coherencia para datasets."""

    def __init__(self, productos: Sequence[Producto], pedidos: Sequence[Pedido]):
        self.productos = list(productos)
        self.pedidos = list(pedidos)

    def validar_todo(self) -> ResultadoValidacion:
        """Valida unicidad de IDs, rangos válidos e integridad referencial."""
        errores: list[str] = []

        ids_productos: set[int] = set()
        for p in self.productos:
            if p.id <= 0:
                errores.append(f"ID de producto no positivo: {p.id}")
            if p.id in ids_productos:
                errores.append(f"ID de producto duplicado: #{p.id}")
            ids_productos.add(p.id)

            if p.stock < 0:
                errores.append(f"Producto #{p.id} tiene stock negativo ({p.stock})")
            if p.precio < 0:
                errores.append(f"Producto #{p.id} tiene precio negativo ({p.precio})")

        ids_pedidos: set[int] = set()
        for ped in self.pedidos:
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

        return ResultadoValidacion(
            es_valido=(len(errores) == 0),
            errores=errores,
            total_productos=len(self.productos),
            total_pedidos=len(self.pedidos),
        )
