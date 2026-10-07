"""Módulo de agrupación y consolidación de pedidos (Batch Picking).

Permite fusionar y totalizar las líneas de múltiples pedidos independientes
en una única lista consolidada para optimizar el recorrido físico del almacén
y reducir la cantidad de consultas individuales al inventario.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from src.modelos.pedido import Pedido
from src.modelos.producto import Producto


@dataclass(slots=True)
class DetalleDemandaPedido:
    """Registra la demanda que un pedido específico ejerce sobre un producto."""

    id_pedido: int
    cantidad: int


@dataclass(slots=True)
class ItemPickingConsolidado:
    """Representa la demanda acumulada de un producto para el lote de pedidos."""

    id_producto: int
    producto: Producto | None
    cantidad_total: int
    demandas_por_pedido: list[DetalleDemandaPedido] = field(default_factory=list)

    @property
    def total_pedidos_solicitantes(self) -> int:
        """Cantidad de pedidos individuales que solicitaron este producto."""
        return len(self.demandas_por_pedido)

    def a_diccionario(self) -> dict[str, Any]:
        """Serializa el ítem consolidado a diccionario."""
        return {
            "id_producto": self.id_producto,
            "nombre_producto": self.producto.nombre if self.producto else "Desconocido",
            "categoria": self.producto.categoria if self.producto else "Sin categoría",
            "stock_disponible": self.producto.stock if self.producto else 0,
            "cantidad_total": self.cantidad_total,
            "pedidos_solicitantes": [d.id_pedido for d in self.demandas_por_pedido],
        }


@dataclass(slots=True)
class LotePickingConsolidado:
    """Contenedor de la lista consolidada de picking de un lote de pedidos."""

    total_pedidos: int
    total_unidades: int
    items: list[ItemPickingConsolidado]

    @property
    def total_productos_distintos(self) -> int:
        """Cantidad de productos diferentes requeridos en el lote."""
        return len(self.items)

    def obtener_por_producto(self, id_producto: int) -> ItemPickingConsolidado | None:
        """Busca un ítem consolidado por su ID de producto."""
        for item in self.items:
            if item.id_producto == id_producto:
                return item
        return None


def agrupar_pedidos_batch(
    pedidos: Sequence[Pedido],
    catalogo=None,
) -> LotePickingConsolidado:
    """Fusiona y consolida las demandas de una secuencia de pedidos (Batch Picking).

    Estrategia algorítmica:
    Recorre las líneas de todos los pedidos y las acumula en un diccionario hash O(1).
    Luego resuelve los metadatos del producto contra el catálogo provisto.

    Complejidad temporal: O(L + P_dist), donde L es la sumatoria de todas las líneas
    de todos los pedidos y P_dist es la cantidad de productos únicos demandados.
    """
    if not pedidos:
        return LotePickingConsolidado(total_pedidos=0, total_unidades=0, items=[])

    # Mapa de acumulación: id_producto -> ItemPickingConsolidado
    acumulador: dict[int, ItemPickingConsolidado] = {}
    total_unidades = 0

    for pedido in pedidos:
        for linea in pedido.lineas:
            total_unidades += linea.cantidad
            if linea.id_producto not in acumulador:
                prod_obj = catalogo.buscar_por_id(linea.id_producto) if catalogo else None
                acumulador[linea.id_producto] = ItemPickingConsolidado(
                    id_producto=linea.id_producto,
                    producto=prod_obj,
                    cantidad_total=linea.cantidad,
                    demandas_por_pedido=[
                        DetalleDemandaPedido(id_pedido=pedido.id, cantidad=linea.cantidad)
                    ],
                )
            else:
                item_existente = acumulador[linea.id_producto]
                item_existente.cantidad_total += linea.cantidad
                item_existente.demandas_por_pedido.append(
                    DetalleDemandaPedido(id_pedido=pedido.id, cantidad=linea.cantidad)
                )

    # Ordenar por id_producto o cantidad para presentación predecible
    items_consolidados = sorted(
        acumulador.values(), key=lambda it: it.cantidad_total, reverse=True
    )

    return LotePickingConsolidado(
        total_pedidos=len(pedidos),
        total_unidades=total_unidades,
        items=items_consolidados,
    )
