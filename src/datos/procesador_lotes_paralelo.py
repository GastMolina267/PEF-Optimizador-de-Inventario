"""Procesamiento paralelo y secuencial por lotes para archivos JSON Lines masivos.

Enfoque de alto rendimiento:
1. Lectura en streaming del archivo de pedidos (.jsonl) con buffer de 1 MB.
2. Particionado en lotes (chunks) de líneas de texto JSON sin instanciar todos los objetos en RAM.
3. Despacho de lotes a los procesos de trabajo (workers) del ProcessPoolExecutor.
4. Cada worker realiza de forma independiente:
   - Deserialización de JSON por línea.
   - Validación de esquema y consistencia de IDs de productos.
   - Evaluación algorítmica de factibilidad contra el mapa de stock.
5. El proceso principal consolida las métricas y tuplas compactas con memoria constante.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from src.datos.streaming import TAMANO_BUFFER_DEFECTO, TAMANO_LOTE_DEFECTO, en_lotes
from src.modelos.pedido import (
    EstadoPedido,
    ResultadoLinea,
    ResultadoPedido,
    ResumenProcesamiento,
)
from src.pedidos.gestor_pool import pool_pedidos


def _evaluar_lote_lineas_jsonl(
    lote_lineas: tuple[str, ...],
    mapa_stock: dict[int, int],
) -> tuple[int, int, int, int, list[tuple[int, int, tuple[tuple[int, int, int, int], ...]]]]:
    """Función de nivel de módulo ejecutada por cada worker del ProcessPoolExecutor.

    Parsea, valida y evalúa un lote de líneas JSONL.
    Retorna (total_procesados, cubiertos, parciales, imposibles, resultados_compactos).
    """
    cubiertos = 0
    parciales = 0
    imposibles = 0
    resultados_compactos: list[tuple[int, int, tuple[tuple[int, int, int, int], ...]]] = []

    for linea in lote_lineas:
        linea_str = linea.strip()
        if not linea_str:
            continue

        datos = json.loads(linea_str)
        id_pedido = int(datos["id"])
        lineas_raw = datos.get("lineas", [])

        lineas_cubiertas: list[tuple[int, int, int, int]] = []
        lineas_faltantes: list[tuple[int, int, int, int]] = []
        total_lineas = len(lineas_raw)
        satisfechas_count = 0
        con_algo_count = 0

        for lr in lineas_raw:
            id_prod = int(lr["id_producto"])
            cant = int(lr["cantidad"])
            if id_prod not in mapa_stock:
                raise ValueError(
                    f"Pedido {id_pedido} referencia producto inexistente ID {id_prod}"
                )

            stock_disp = mapa_stock.get(id_prod, 0)
            if stock_disp >= cant:
                asig = cant
                falt = 0
                satisfechas_count += 1
                con_algo_count += 1
            elif stock_disp > 0:
                asig = stock_disp
                falt = cant - stock_disp
                con_algo_count += 1
            else:
                asig = 0
                falt = cant

            t_linea = (id_prod, cant, asig, falt)
            if asig == cant:
                lineas_cubiertas.append(t_linea)
            else:
                lineas_faltantes.append(t_linea)

        if total_lineas > 0 and satisfechas_count == total_lineas:
            estado_val = EstadoPedido.CUBIERTO.value
            cubiertos += 1
        elif con_algo_count == 0:
            estado_val = EstadoPedido.IMPOSIBLE.value
            imposibles += 1
        else:
            estado_val = EstadoPedido.PARCIAL.value
            parciales += 1

        resultados_compactos.append(
            (id_pedido, estado_val, tuple(lineas_cubiertas + lineas_faltantes))
        )

    return (
        len(resultados_compactos),
        cubiertos,
        parciales,
        imposibles,
        resultados_compactos,
    )


def procesar_pedidos_jsonl_paralelo(
    ruta_pedidos: str | Path,
    mapa_stock: dict[int, int],
    tamano_lote: int = TAMANO_LOTE_DEFECTO,
    tamano_buffer: int = TAMANO_BUFFER_DEFECTO,
    max_workers: int | None = None,
    reconstruir_dataclasses: bool = False,
) -> ResumenProcesamiento:
    """Procesa un archivo .jsonl completo de pedidos utilizando streaming y workers en paralelo.

    Argumentos:
        ruta_pedidos: Ruta al archivo .jsonl.
        mapa_stock: Mapeo {id_producto: stock} disponible.
        tamano_lote: Cantidad de líneas JSONL despachadas por batch a cada worker.
        tamano_buffer: Buffer interno de lectura (en bytes).
        max_workers: Cantidad de procesos en paralelo (por defecto según CPU cores).
        reconstruir_dataclasses: Si True, materializa ResultadoPedido (útil para tests;
                                 si False, mantiene resultados en tuplas para ahorrar RAM).
    """
    inicio = time.perf_counter()
    path_archivo = Path(ruta_pedidos)
    if not path_archivo.is_file():
        raise FileNotFoundError(f"Archivo de pedidos no encontrado: {path_archivo}")

    executor = pool_pedidos.obtener_executor(max_workers=max_workers)

    total_procesados = 0
    total_cubiertos = 0
    total_parciales = 0
    total_imposibles = 0
    todos_resultados: list[ResultadoPedido] = []

    with open(path_archivo, encoding="utf-8", buffering=tamano_buffer) as f:
        # Despacho en streaming por lotes al pool de procesos
        futuros = [
            executor.submit(_evaluar_lote_lineas_jsonl, lote, mapa_stock)
            for lote in en_lotes(f, tamano_lote)
        ]

        for fut in futuros:
            proc, cub, parc, imp, tuplas_comp = fut.result()
            total_procesados += proc
            total_cubiertos += cub
            total_parciales += parc
            total_imposibles += imp

            if reconstruir_dataclasses:
                for id_ped, estado_val, lineas_tupla in tuplas_comp:
                    lineas_cub = []
                    lineas_fal = []
                    for id_prod, cant_sol, cant_asig, falt in lineas_tupla:
                        rl = ResultadoLinea(
                            id_producto=id_prod,
                            cantidad_solicitada=cant_sol,
                            cantidad_asignada=cant_asig,
                            faltante=falt,
                        )
                        if rl.satisfecha_completamente:
                            lineas_cub.append(rl)
                        else:
                            lineas_fal.append(rl)

                    todos_resultados.append(
                        ResultadoPedido(
                            id_pedido=id_ped,
                            estado=EstadoPedido(estado_val),
                            lineas_cubiertas=lineas_cub,
                            lineas_faltantes=lineas_fal,
                        )
                    )

    tiempo_total_ms = (time.perf_counter() - inicio) * 1000.0

    return ResumenProcesamiento(
        pedidos_procesados=total_procesados,
        pedidos_cubiertos=total_cubiertos,
        pedidos_parciales=total_parciales,
        pedidos_imposibles=total_imposibles,
        tiempo_ejecucion_ms=tiempo_total_ms,
        resultados=todos_resultados,
        estrategia="optimizado_lotes_paralelo",
    )


def procesar_pedidos_jsonl_secuencial(
    ruta_pedidos: str | Path,
    mapa_stock: dict[int, int],
    tamano_lote: int = TAMANO_LOTE_DEFECTO,
    tamano_buffer: int = TAMANO_BUFFER_DEFECTO,
    reconstruir_dataclasses: bool = False,
) -> ResumenProcesamiento:
    """Procesa un archivo .jsonl completo de pedidos en un único hilo por lotes para benchmark."""
    inicio = time.perf_counter()
    path_archivo = Path(ruta_pedidos)
    if not path_archivo.is_file():
        raise FileNotFoundError(f"Archivo de pedidos no encontrado: {path_archivo}")

    total_procesados = 0
    total_cubiertos = 0
    total_parciales = 0
    total_imposibles = 0
    todos_resultados: list[ResultadoPedido] = []

    with open(path_archivo, encoding="utf-8", buffering=tamano_buffer) as f:
        for lote in en_lotes(f, tamano_lote):
            proc, cub, parc, imp, tuplas_comp = _evaluar_lote_lineas_jsonl(lote, mapa_stock)
            total_procesados += proc
            total_cubiertos += cub
            total_parciales += parc
            total_imposibles += imp

            if reconstruir_dataclasses:
                for id_ped, estado_val, lineas_tupla in tuplas_comp:
                    lineas_cub = []
                    lineas_fal = []
                    for id_prod, cant_sol, cant_asig, falt in lineas_tupla:
                        rl = ResultadoLinea(
                            id_producto=id_prod,
                            cantidad_solicitada=cant_sol,
                            cantidad_asignada=cant_asig,
                            faltante=falt,
                        )
                        if rl.satisfecha_completamente:
                            lineas_cub.append(rl)
                        else:
                            lineas_fal.append(rl)

                    todos_resultados.append(
                        ResultadoPedido(
                            id_pedido=id_ped,
                            estado=EstadoPedido(estado_val),
                            lineas_cubiertas=lineas_cub,
                            lineas_faltantes=lineas_fal,
                        )
                    )

    tiempo_total_ms = (time.perf_counter() - inicio) * 1000.0

    return ResumenProcesamiento(
        pedidos_procesados=total_procesados,
        pedidos_cubiertos=total_cubiertos,
        pedidos_parciales=total_parciales,
        pedidos_imposibles=total_imposibles,
        tiempo_ejecucion_ms=tiempo_total_ms,
        resultados=todos_resultados,
        estrategia="baseline_lotes_secuencial",
    )
