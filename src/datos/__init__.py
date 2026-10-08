"""Módulo de gestión de datos y persistencia."""

from src.datos.cargador import (
    cargar_dataset,
    cargar_dataset_json,
    guardar_dataset_json,
    validar_dataset,
)
from src.datos.generador_archivos import (
    generar_archivos_grandes_jsonl,
)
from src.datos.procesador_lotes_paralelo import (
    procesar_pedidos_jsonl_paralelo,
    procesar_pedidos_jsonl_secuencial,
)
from src.datos.streaming import (
    TAMANO_BUFFER_DEFECTO,
    TAMANO_LOTE_DEFECTO,
    en_lotes,
    escribir_lineas_con_buffer,
    escribir_pedidos_jsonl,
    escribir_productos_jsonl,
    exportar_picking_csv_con_buffer,
    leer_pedidos_streaming_jsonl,
    leer_productos_streaming_jsonl,
)
from src.datos.validador import ResultadoValidacion, ValidadorDataset

__all__ = [
    "cargar_dataset",
    "cargar_dataset_json",
    "guardar_dataset_json",
    "validar_dataset",
    "ValidadorDataset",
    "ResultadoValidacion",
    "en_lotes",
    "leer_productos_streaming_jsonl",
    "leer_pedidos_streaming_jsonl",
    "escribir_productos_jsonl",
    "escribir_pedidos_jsonl",
    "escribir_lineas_con_buffer",
    "exportar_picking_csv_con_buffer",
    "procesar_pedidos_jsonl_paralelo",
    "procesar_pedidos_jsonl_secuencial",
    "generar_archivos_grandes_jsonl",
    "TAMANO_BUFFER_DEFECTO",
    "TAMANO_LOTE_DEFECTO",
]
