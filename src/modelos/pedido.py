"""Módulo de definición de modelos asociados a Pedidos y resultados de procesamiento."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EstadoPedido(str, Enum):
    """Estado de resolución de un pedido en el almacén."""

    CUBIERTO = "cubierto"  # Todo el stock requerido estuvo disponible y se asignó
    PARCIAL = "parcial"  # Se pudo cubrir al menos una línea, pero hubo faltantes
    IMPOSIBLE = "imposible"  # Ninguna línea pudo ser satisfecha por falta total de stock


@dataclass(slots=True)
class LineaPedido:
    """Representa un renglón individual dentro de un pedido.

    Atributos:
        id_producto: Identificador del producto solicitado.
        cantidad: Unidades demandadas del producto (> 0).
    """

    id_producto: int
    cantidad: int

    def __post_init__(self) -> None:
        """Valida que la cantidad y el identificador sean válidos."""
        if not isinstance(self.id_producto, int) or self.id_producto <= 0:
            raise ValueError(
                f"El id_producto de la línea debe ser un entero positivo, recibido: {self.id_producto}"
            )
        if not isinstance(self.cantidad, int) or self.cantidad <= 0:
            raise ValueError(
                f"La cantidad demandada debe ser un entero mayor a 0, recibido: {self.cantidad}"
            )

    def a_diccionario(self) -> dict[str, Any]:
        """Serializa la línea de pedido a un diccionario plano."""
        return {
            "id_producto": self.id_producto,
            "cantidad": self.cantidad,
        }

    @classmethod
    def desde_diccionario(cls, datos: dict[str, Any]) -> LineaPedido:
        """Construye una LineaPedido a partir de un diccionario."""
        return cls(
            id_producto=int(datos["id_producto"]),
            cantidad=int(datos["cantidad"]),
        )


@dataclass(slots=True)
class Pedido:
    """Representa una orden de compra o preparación de pedido.

    Atributos:
        id: Identificador numérico único del pedido.
        lineas: Lista de líneas o renglones que componen el pedido.
    """

    id: int
    lineas: list[LineaPedido]

    def __post_init__(self) -> None:
        """Valida la integridad del pedido y sus líneas."""
        if not isinstance(self.id, int) or self.id <= 0:
            raise ValueError(f"El id del pedido debe ser un entero positivo, recibido: {self.id}")
        if not isinstance(self.lineas, list) or len(self.lineas) == 0:
            raise ValueError(f"El pedido #{self.id} debe contener al menos una línea de pedido.")

    def a_diccionario(self) -> dict[str, Any]:
        """Serializa el pedido a un diccionario plano."""
        return {
            "id": self.id,
            "lineas": [linea.a_diccionario() for linea in self.lineas],
        }

    @classmethod
    def desde_diccionario(cls, datos: dict[str, Any]) -> Pedido:
        """Construye un Pedido a partir de un diccionario estructurado."""
        lineas = [LineaPedido.desde_diccionario(item) for item in datos["lineas"]]
        return cls(id=int(datos["id"]), lineas=lineas)


@dataclass(slots=True)
class ResultadoLinea:
    """Detalle de asignación de stock para una línea de pedido."""

    id_producto: int
    cantidad_solicitada: int
    cantidad_asignada: int
    faltante: int

    @property
    def satisfecha_completamente(self) -> bool:
        """Indica si la línea se cubrió al 100%."""
        return self.faltante == 0


@dataclass(slots=True)
class ResultadoPedido:
    """Resultado de preparar un pedido individual frente al inventario."""

    id_pedido: int
    estado: EstadoPedido
    lineas_cubiertas: list[ResultadoLinea] = field(default_factory=list)
    lineas_faltantes: list[ResultadoLinea] = field(default_factory=list)

    @property
    def es_exitoso(self) -> bool:
        """Indica si el pedido fue cubierto en su totalidad."""
        return self.estado == EstadoPedido.CUBIERTO


@dataclass(slots=True)
class ResumenProcesamiento:
    """Resumen cuantitativo de la preparación de un lote de pedidos."""

    pedidos_procesados: int
    pedidos_cubiertos: int
    pedidos_parciales: int
    pedidos_imposibles: int
    tiempo_ejecucion_ms: float
    resultados: list[ResultadoPedido] = field(default_factory=list)
    estrategia: str = "baseline"

    @property
    def porcentaje_cobertura(self) -> float:
        """Porcentaje de pedidos que se cubrieron por completo."""
        if self.pedidos_procesados == 0:
            return 0.0
        return (self.pedidos_cubiertos / self.pedidos_procesados) * 100.0
