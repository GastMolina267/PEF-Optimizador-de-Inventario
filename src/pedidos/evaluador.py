"""Evaluación de pedidos: núcleo único compartido por todos los procesadores.

Antes de esta versión la misma regla (asignar stock línea por línea y clasificar el
pedido como CUBIERTO, PARCIAL o IMPOSIBLE) estaba escrita cuatro veces: en el
procesador secuencial, en el concurrente y en los dos procesadores de archivos JSONL.
Ahora existe una sola implementación, :func:`evaluar_lineas`, que trabaja con tuplas
de tipos primitivos. Eso la hace apta para correr dentro de los workers de un
``ProcessPoolExecutor`` (se serializa barato) y también en el proceso principal.

Representación compacta usada para el IPC:

- Línea: ``(id_producto, cantidad_solicitada, cantidad_asignada, faltante)``.
- Pedido: ``(id_pedido, estado.value, lineas)``, con las líneas cubiertas primero y
  las faltantes después, conservando el orden original dentro de cada grupo.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from src.modelos.pedido import (
    EstadoPedido,
    Pedido,
    PoliticaDescuento,
    ResultadoLinea,
    ResultadoPedido,
)

LineaCompacta = tuple[int, int, int, int]
"""``(id_producto, cantidad_solicitada, cantidad_asignada, faltante)``."""

ResultadoCompacto = tuple[int, str, tuple[LineaCompacta, ...]]
"""``(id_pedido, estado.value, lineas_compactas)``."""


def crear_consulta_stock(fuente_stock: Any) -> Callable[[int], int]:
    """Devuelve una función ``id_producto -> stock`` para la fuente indicada.

    La fuente puede ser un catálogo (``CatalogoLineal`` o ``CatalogoHash``) o un
    mapeo ``{id_producto: stock}``. El tipo se resuelve una sola vez, fuera del bucle
    de líneas, para no pagar ``hasattr`` en cada línea del pedido.

    Argumentos:
        fuente_stock: Catálogo con ``buscar_por_id`` o mapeo con ``get``.

    Retorna:
        Función que devuelve el stock disponible (0 si el producto no existe).

    Lanza:
        TypeError: Si la fuente no es un catálogo ni un mapeo.
    """
    if hasattr(fuente_stock, "buscar_por_id"):
        buscar = fuente_stock.buscar_por_id

        def stock_desde_catalogo(id_producto: int) -> int:
            producto = buscar(id_producto)
            return producto.stock if producto is not None else 0

        return stock_desde_catalogo

    if isinstance(fuente_stock, Mapping):
        obtener = fuente_stock.get
        return lambda id_producto: obtener(id_producto, 0)

    raise TypeError(
        f"Fuente de stock no soportada: {type(fuente_stock).__name__}. "
        "Se espera un catálogo o un mapeo {id_producto: stock}."
    )


def evaluar_lineas(
    lineas: Iterable[tuple[int, int]],
    stock_de: Callable[[int], int],
) -> tuple[EstadoPedido, tuple[LineaCompacta, ...]]:
    """Asigna stock a cada línea y clasifica el pedido.

    Es la única implementación de la regla de evaluación del proyecto.

    Argumentos:
        lineas: Pares ``(id_producto, cantidad_solicitada)``.
        stock_de: Función que devuelve el stock disponible de un producto.

    Retorna:
        Tupla ``(estado, lineas_compactas)``. Las líneas cubiertas van primero.
    """
    cubiertas: list[LineaCompacta] = []
    faltantes: list[LineaCompacta] = []
    lineas_con_asignacion = 0

    for id_producto, solicitada in lineas:
        disponible = stock_de(id_producto)
        if disponible >= solicitada:
            cubiertas.append((id_producto, solicitada, solicitada, 0))
            lineas_con_asignacion += 1
        elif disponible > 0:
            faltantes.append((id_producto, solicitada, disponible, solicitada - disponible))
            lineas_con_asignacion += 1
        else:
            faltantes.append((id_producto, solicitada, 0, solicitada))

    if not faltantes:
        estado = EstadoPedido.CUBIERTO
    elif lineas_con_asignacion == 0:
        estado = EstadoPedido.IMPOSIBLE
    else:
        estado = EstadoPedido.PARCIAL

    return estado, tuple(cubiertas + faltantes)


def evaluar_pedido_compacto(
    id_pedido: int,
    lineas: Iterable[tuple[int, int]],
    stock_de: Callable[[int], int],
) -> ResultadoCompacto:
    """Evalúa un pedido y devuelve el resultado en formato compacto (apto para IPC)."""
    estado, lineas_compactas = evaluar_lineas(lineas, stock_de)
    return id_pedido, estado.value, lineas_compactas


def resultado_desde_compacto(resultado: ResultadoCompacto) -> ResultadoPedido:
    """Reconstruye un :class:`ResultadoPedido` a partir de su forma compacta.

    Argumentos:
        resultado: Tupla ``(id_pedido, estado.value, lineas_compactas)``.

    Retorna:
        El resultado como dataclass, con las líneas separadas en cubiertas y faltantes.
    """
    id_pedido, estado_valor, lineas_compactas = resultado
    return _armar_resultado(id_pedido, EstadoPedido(estado_valor), lineas_compactas)


def _armar_resultado(
    id_pedido: int, estado: EstadoPedido, lineas_compactas: tuple[LineaCompacta, ...]
) -> ResultadoPedido:
    """Crea el :class:`ResultadoPedido` a partir del estado y las líneas compactas."""
    cubiertas: list[ResultadoLinea] = []
    faltantes: list[ResultadoLinea] = []
    for id_producto, solicitada, asignada, faltante in lineas_compactas:
        linea = ResultadoLinea(id_producto, solicitada, asignada, faltante)
        if faltante == 0:
            cubiertas.append(linea)
        else:
            faltantes.append(linea)
    return ResultadoPedido(id_pedido, estado, cubiertas, faltantes)


def evaluar_pedido(
    pedido: Pedido,
    fuente_stock: Any = None,
    stock_de: Callable[[int], int] | None = None,
) -> ResultadoPedido:
    """Evalúa la factibilidad de un pedido frente al stock disponible.

    Argumentos:
        pedido: Pedido a evaluar.
        fuente_stock: Catálogo (lineal o hash) o mapeo ``{id_producto: stock}``.
        stock_de: Consulta de stock ya creada con :func:`crear_consulta_stock`. Los
            procesadores la crean una vez por lote y la reutilizan en cada pedido.

    Retorna:
        :class:`ResultadoPedido` con el detalle línea por línea y el estado general.
    """
    if stock_de is None:
        stock_de = crear_consulta_stock(fuente_stock)
    lineas = [(linea.id_producto, linea.cantidad) for linea in pedido.lineas]
    estado, lineas_compactas = evaluar_lineas(lineas, stock_de)
    return _armar_resultado(pedido.id, estado, lineas_compactas)


@dataclass
class ContadorEstados:
    """Acumula cuántos pedidos terminaron en cada estado."""

    cubiertos: int = 0
    parciales: int = 0
    imposibles: int = 0

    def registrar(self, estado: EstadoPedido | str) -> None:
        """Suma un pedido al contador del estado indicado."""
        # EstadoPedido hereda de str: la comparación sirve tanto para el miembro del
        # enum como para su valor ("cubierto"), sin convertir en cada llamada.
        if estado == EstadoPedido.CUBIERTO:
            self.cubiertos += 1
        elif estado == EstadoPedido.PARCIAL:
            self.parciales += 1
        else:
            self.imposibles += 1

    @property
    def total(self) -> int:
        """Cantidad total de pedidos registrados."""
        return self.cubiertos + self.parciales + self.imposibles


def debe_descontar(
    estado: EstadoPedido,
    politica: PoliticaDescuento | str = PoliticaDescuento.SOLO_CUBIERTOS,
) -> bool:
    """Determina si un pedido califica para descontar stock según la política elegida."""
    politica_norm = (
        politica.value if isinstance(politica, PoliticaDescuento) else str(politica).lower()
    )
    if politica_norm == PoliticaDescuento.SOLO_CUBIERTOS:
        return estado == EstadoPedido.CUBIERTO
    if politica_norm == PoliticaDescuento.TODO_LO_POSIBLE:
        return estado in (EstadoPedido.CUBIERTO, EstadoPedido.PARCIAL)
    return False
