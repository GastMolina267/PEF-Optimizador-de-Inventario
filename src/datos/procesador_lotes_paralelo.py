"""Procesamiento por lotes (secuencial y paralelo) de archivos JSON Lines de pedidos.

Flujo:

1. El archivo se lee en streaming, con un buffer de lectura explícito.
2. Las líneas se agrupan en lotes con :func:`en_lotes`, sin materializar el archivo.
3. Cada lote se parsea, valida y evalúa con el núcleo único de
   ``src/pedidos/evaluador.py``. En la versión paralela esto ocurre en los workers.

Decisiones de eficiencia de la versión paralela:

- **Stock enviado una sola vez por worker.** El mapa de stock es el mismo para todo el
  archivo, así que viaja en el ``initializer`` del pool y no en cada lote.
- **Memoria acotada.** Como máximo hay ``max_lotes_en_vuelo`` lotes enviados y sin
  consumir (por defecto, dos por worker). Sin ese límite, la lectura encolaría el
  archivo completo en el pool y el streaming perdería sentido.
- **Orden preservado.** Los resultados se consumen en el orden en que se enviaron.
- **Pool propio.** Usa ``pool_archivos``, separado del pool de pedidos en memoria,
  para que cargar un archivo no obligue a recrear el otro.
"""

from __future__ import annotations

import json
import os
import time
from collections import deque
from collections.abc import Iterable
from concurrent.futures import Future
from pathlib import Path

from src.datos.streaming import TAMANO_BUFFER_DEFECTO, TAMANO_LOTE_DEFECTO, en_lotes
from src.modelos.pedido import ResultadoPedido, ResumenProcesamiento
from src.observabilidad import etiquetar, span
from src.pedidos.evaluador import (
    ContadorEstados,
    ResultadoCompacto,
    crear_consulta_stock,
    evaluar_pedido_compacto,
    resultado_desde_compacto,
)
from src.pedidos.gestor_pool import pool_archivos

# Stock disponible dentro de cada worker. Lo carga _inicializar_worker una vez.
_STOCK_WORKER: dict[int, int] = {}


def _inicializar_worker(mapa_stock: dict[int, int]) -> None:
    """Guarda el mapa de stock en el worker (se ejecuta una vez por proceso)."""
    global _STOCK_WORKER
    _STOCK_WORKER = mapa_stock


def _parsear_pedido(linea: str, mapa_stock: dict[int, int]):
    """Convierte una línea JSONL en ``(id_pedido, ((id_producto, cantidad), ...))``.

    Retorna ``None`` para líneas en blanco.

    Lanza:
        ValueError: Si el pedido no tiene líneas o referencia un producto inexistente.
    """
    texto = linea.strip()
    if not texto:
        return None
    datos = json.loads(texto)
    id_pedido = int(datos["id"])
    lineas = tuple(
        (int(item["id_producto"]), int(item["cantidad"])) for item in datos.get("lineas", [])
    )
    if not lineas:
        raise ValueError(f"Pedido {id_pedido} no tiene líneas")
    for id_producto, _ in lineas:
        if id_producto not in mapa_stock:
            raise ValueError(
                f"Pedido {id_pedido} referencia producto inexistente ID {id_producto}"
            )
    return id_pedido, lineas


def _evaluar_lote_lineas_jsonl(
    lote_lineas: tuple[str, ...],
    mapa_stock: dict[int, int] | None = None,
) -> list[ResultadoCompacto]:
    """Parsea, valida y evalúa un lote de líneas JSONL.

    En los workers se llama sin ``mapa_stock`` y usa el que cargó el initializer.

    Argumentos:
        lote_lineas: Líneas crudas del archivo.
        mapa_stock: Stock a usar. Si es None, se usa el del worker.

    Retorna:
        Resultados compactos, en el mismo orden que las líneas.
    """
    stock = _STOCK_WORKER if mapa_stock is None else mapa_stock
    stock_de = crear_consulta_stock(stock)
    resultados: list[ResultadoCompacto] = []
    for linea in lote_lineas:
        pedido = _parsear_pedido(linea, stock)
        if pedido is not None:
            resultados.append(evaluar_pedido_compacto(*pedido, stock_de))
    return resultados


class _Acumulador:
    """Consolida los resultados de los lotes en contadores y, opcionalmente, dataclasses."""

    def __init__(self, reconstruir_dataclasses: bool) -> None:
        self.contador = ContadorEstados()
        self.resultados: list[ResultadoPedido] = []
        self._reconstruir = reconstruir_dataclasses

    def agregar(self, compactos: Iterable[ResultadoCompacto]) -> None:
        for compacto in compactos:
            self.contador.registrar(compacto[1])
            if self._reconstruir:
                self.resultados.append(resultado_desde_compacto(compacto))

    def resumen(self, inicio: float, estrategia: str) -> ResumenProcesamiento:
        return ResumenProcesamiento(
            pedidos_procesados=self.contador.total,
            pedidos_cubiertos=self.contador.cubiertos,
            pedidos_parciales=self.contador.parciales,
            pedidos_imposibles=self.contador.imposibles,
            tiempo_ejecucion_ms=(time.perf_counter() - inicio) * 1000.0,
            resultados=self.resultados,
            estrategia=estrategia,
        )


def _validar_ruta(ruta_pedidos: str | Path) -> Path:
    ruta = Path(ruta_pedidos)
    if not ruta.is_file():
        raise FileNotFoundError(f"Archivo de pedidos no encontrado: {ruta}")
    return ruta


def procesar_pedidos_jsonl_paralelo(
    ruta_pedidos: str | Path,
    mapa_stock: dict[int, int],
    tamano_lote: int = TAMANO_LOTE_DEFECTO,
    tamano_buffer: int = TAMANO_BUFFER_DEFECTO,
    max_workers: int | None = None,
    reconstruir_dataclasses: bool = False,
    max_lotes_en_vuelo: int | None = None,
) -> ResumenProcesamiento:
    """Procesa un archivo ``.jsonl`` de pedidos en streaming con workers en paralelo.

    Argumentos:
        ruta_pedidos: Ruta al archivo ``.jsonl``.
        mapa_stock: Stock disponible ``{id_producto: stock}``.
        tamano_lote: Líneas por lote enviado a un worker.
        tamano_buffer: Buffer de lectura del archivo, en bytes.
        max_workers: Procesos en paralelo (por defecto, núcleos disponibles, hasta 8).
        reconstruir_dataclasses: Si es True, devuelve cada ``ResultadoPedido``. Si es
            False, solo los contadores (memoria constante).
        max_lotes_en_vuelo: Lotes enviados y sin consumir como máximo (por defecto,
            dos por worker). Acota la memoria del proceso principal.

    Retorna:
        Resumen con los contadores y, si se pidió, los resultados en orden.
    """
    inicio = time.perf_counter()
    ruta = _validar_ruta(ruta_pedidos)
    workers = max_workers or min(os.cpu_count() or 4, 8)
    limite_en_vuelo = max(1, max_lotes_en_vuelo or 2 * workers)
    executor = pool_archivos.obtener_executor(
        max_workers=workers, initializer=_inicializar_worker, initargs=(mapa_stock,)
    )

    acumulador = _Acumulador(reconstruir_dataclasses)
    en_vuelo: deque[Future] = deque()
    lotes_enviados = 0
    with (
        span("lotes.procesar_archivo", "ipc", {"workers": workers}),
        open(ruta, encoding="utf-8", buffering=tamano_buffer) as archivo,
    ):
        for lote in en_lotes(archivo, tamano_lote):
            en_vuelo.append(executor.submit(_evaluar_lote_lineas_jsonl, lote))
            lotes_enviados += 1
            if len(en_vuelo) >= limite_en_vuelo:
                acumulador.agregar(en_vuelo.popleft().result())
        while en_vuelo:
            acumulador.agregar(en_vuelo.popleft().result())
    etiquetar(lotes=lotes_enviados, workers=workers)

    return acumulador.resumen(inicio, "optimizado_lotes_paralelo")


def procesar_pedidos_jsonl_secuencial(
    ruta_pedidos: str | Path,
    mapa_stock: dict[int, int],
    tamano_lote: int = TAMANO_LOTE_DEFECTO,
    tamano_buffer: int = TAMANO_BUFFER_DEFECTO,
    reconstruir_dataclasses: bool = False,
) -> ResumenProcesamiento:
    """Procesa un archivo ``.jsonl`` de pedidos en streaming, en un solo proceso.

    Usa exactamente la misma función por lote que la versión paralela, así que ambas
    dan el mismo resultado y la comparación de tiempos aísla el efecto del pool.
    """
    inicio = time.perf_counter()
    ruta = _validar_ruta(ruta_pedidos)
    acumulador = _Acumulador(reconstruir_dataclasses)
    with open(ruta, encoding="utf-8", buffering=tamano_buffer) as archivo:
        for lote in en_lotes(archivo, tamano_lote):
            acumulador.agregar(_evaluar_lote_lineas_jsonl(lote, mapa_stock))
    return acumulador.resumen(inicio, "baseline_lotes_secuencial")
