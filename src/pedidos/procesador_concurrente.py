"""Procesador concurrente de pedidos con multiprocessing (ProcessPoolExecutor).

Justificación técnica y propuesta Origin 1 (reducir el overhead de IPC):

1. Qué se paraleliza: la evaluación de factibilidad de pedidos independientes contra
   una foto del stock. Es trabajo CPU-bound, por eso se usan procesos y no hilos (GIL).
2. Menos datos por el canal IPC:

   - Los pedidos viajan como tuplas de enteros, no como dataclasses.
   - Cada fragmento lleva solo el stock de los productos que referencia, no el
     catálogo completo. Con 10.000 productos y fragmentos de 500 pedidos, el payload
     de stock baja de 10.000 entradas a unas pocas centenas.
   - Los resultados vuelven como tuplas compactas (ver ``src/pedidos/evaluador.py``).
3. Sin trabajo redundante: los fragmentos son contiguos y los futuros se consumen en
   orden de envío, así que el resultado sale ordenado sin un ``sort`` final.
4. Descuento de stock: cada pedido debe ver el stock que dejó el anterior, así que el
   descuento es intrínsecamente secuencial. En ese caso no se usa el pool (pagaría
   IPC para un resultado que igual habría que recalcular en orden) y se delega en el
   procesador secuencial, que garantiza el mismo resultado.
5. Ciclo de vida: el pool persistente lo administra ``GestorPool``.

Cuándo conviene: la evaluación de un pedido en memoria es un lookup O(1) por línea,
más barato que serializarlo. Por eso el motor usa el procesador secuencial por defecto
y este módulo queda como opción explícita (y como contraste medible para la oral).
"""

from __future__ import annotations

import os
import time
from collections.abc import Sequence
from concurrent.futures import Executor
from concurrent.futures.process import BrokenProcessPool

from src.inventario.protocolo import Catalogo
from src.modelos.pedido import (
    Pedido,
    PoliticaDescuento,
    ResultadoPedido,
    ResumenProcesamiento,
)
from src.observabilidad import registrar_error, span
from src.pedidos.evaluador import (
    ContadorEstados,
    ResultadoCompacto,
    crear_consulta_stock,
    evaluar_pedido_compacto,
    resultado_desde_compacto,
)
from src.pedidos.gestor_pool import pool_pedidos
from src.pedidos.procesador_secuencial import procesar_pedidos_secuencial

ESTRATEGIA = "optimizado_concurrente"

PedidoCompacto = tuple[int, tuple[tuple[int, int], ...]]
"""``(id_pedido, ((id_producto, cantidad), ...))``."""

FragmentoCompacto = tuple[list[PedidoCompacto], dict[int, int]]
"""Pedidos del fragmento y stock de los productos que referencian."""

# Alias de retrocompatibilidad (tests y UI del parcial 1).
_cerrar_executor = pool_pedidos.cerrar


def _evaluar_fragmento_compacto(
    pedidos_fragmento: list[PedidoCompacto],
    stock_fragmento: dict[int, int],
) -> list[ResultadoCompacto]:
    """Evalúa un fragmento de pedidos dentro de un worker.

    Función de nivel de módulo para que sea serializable con ``spawn`` (Windows).
    """
    stock_de = crear_consulta_stock(stock_fragmento)
    return [
        evaluar_pedido_compacto(id_pedido, lineas, stock_de)
        for id_pedido, lineas in pedidos_fragmento
    ]


def _armar_fragmentos(
    catalogo, pedidos: Sequence[Pedido], workers: int
) -> list[FragmentoCompacto]:
    """Parte los pedidos en fragmentos contiguos con su sub-mapa de stock."""
    stock_de = crear_consulta_stock(catalogo)
    tamano = max(1, -(-len(pedidos) // workers))  # división entera hacia arriba
    fragmentos: list[FragmentoCompacto] = []
    for inicio in range(0, len(pedidos), tamano):
        compactos: list[PedidoCompacto] = []
        stock_fragmento: dict[int, int] = {}
        for pedido in pedidos[inicio : inicio + tamano]:
            lineas = tuple((linea.id_producto, linea.cantidad) for linea in pedido.lineas)
            compactos.append((pedido.id, lineas))
            for id_producto, _ in lineas:
                if id_producto not in stock_fragmento:
                    stock_fragmento[id_producto] = stock_de(id_producto)
        fragmentos.append((compactos, stock_fragmento))
    return fragmentos


def _evaluar_en_pool(
    executor: Executor, fragmentos: list[FragmentoCompacto], workers: int
) -> list[ResultadoCompacto]:
    """Envía los fragmentos al pool y junta los resultados en el orden original."""
    try:
        futuros = [executor.submit(_evaluar_fragmento_compacto, *frag) for frag in fragmentos]
        return [resultado for futuro in futuros for resultado in futuro.result()]
    except (BrokenProcessPool, RuntimeError):
        # El pool quedó inutilizable (p. ej. un worker murió): se recrea una vez.
        registrar_error("Pool de procesos inutilizable: se recrea y se reintenta")
        executor = pool_pedidos.reiniciar(max_workers=workers)
        futuros = [executor.submit(_evaluar_fragmento_compacto, *frag) for frag in fragmentos]
        return [resultado for futuro in futuros for resultado in futuro.result()]


def procesar_pedidos_concurrente(
    catalogo: Catalogo,
    pedidos: Sequence[Pedido],
    max_workers: int | None = None,
    descontar_stock: bool = False,
    politica_descuento: PoliticaDescuento | str = PoliticaDescuento.SOLO_CUBIERTOS,
) -> ResumenProcesamiento:
    """Procesa un lote de pedidos en paralelo con un pool de procesos.

    Argumentos:
        catalogo: Catálogo de productos (``CatalogoHash`` o ``CatalogoLineal``).
        pedidos: Pedidos a procesar.
        max_workers: Procesos en paralelo (por defecto, núcleos disponibles).
        descontar_stock: Si es True, se delega en el procesador secuencial, porque cada
            pedido debe ver el stock que dejó el anterior.
        politica_descuento: ``solo_cubiertos`` o ``todo_lo_posible``.

    Retorna:
        Resumen con los resultados en el mismo orden que ``pedidos``.
    """
    if descontar_stock:
        resumen = procesar_pedidos_secuencial(
            catalogo, pedidos, descontar_stock=True, politica_descuento=politica_descuento
        )
        resumen.estrategia = f"{ESTRATEGIA}_descuento_secuencial"
        return resumen

    if not pedidos:
        return ResumenProcesamiento(0, 0, 0, 0, 0.0, [], ESTRATEGIA)

    inicio = time.perf_counter()
    workers = max_workers or min(os.cpu_count() or 4, len(pedidos))
    with span("pool.armar_fragmentos"):
        fragmentos = _armar_fragmentos(catalogo, pedidos, workers)
    executor = pool_pedidos.obtener_executor(max_workers=workers)

    with span("pool.evaluar", "ipc", {"workers": workers, "fragmentos": len(fragmentos)}):
        compactos = _evaluar_en_pool(executor, fragmentos, workers)

    resultados: list[ResultadoPedido] = []
    contador = ContadorEstados()
    for compacto in compactos:
        resultado = resultado_desde_compacto(compacto)
        contador.registrar(resultado.estado)
        resultados.append(resultado)

    return ResumenProcesamiento(
        pedidos_procesados=len(pedidos),
        pedidos_cubiertos=contador.cubiertos,
        pedidos_parciales=contador.parciales,
        pedidos_imposibles=contador.imposibles,
        tiempo_ejecucion_ms=(time.perf_counter() - inicio) * 1000.0,
        resultados=resultados,
        estrategia=ESTRATEGIA,
    )
