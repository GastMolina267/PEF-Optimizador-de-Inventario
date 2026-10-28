"""Pruebas de presupuesto y regresión de memoria heap con tracemalloc.

Verifica que el consumo de memoria heap de las operaciones críticas
se mantenga estrictamente dentro de los presupuestos acotados (O(1) espacial en streaming,
acotamiento de la caché LRU y consumo controlado del catálogo hash).
"""

from __future__ import annotations

import gc
import tracemalloc
from pathlib import Path

from src.cache.cache_consultas import CacheLRU
from src.datos.cargador import cargar_dataset_json
from src.datos.generador_archivos import generar_archivos_grandes_jsonl
from src.datos.streaming import (
    leer_pedidos_streaming_jsonl,
    leer_productos_streaming_jsonl,
)
from src.inventario.catalogo_hash import CatalogoHash
from src.modelos.producto import Producto
from src.pedidos.agrupador import agrupar_pedidos_batch

DATASETS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "datasets"

# Presupuestos máximos admisibles de memoria heap (en Megabytes)
# Definidos en base a las mediciones empíricas de docs/mediciones/linea_base_parcial2/
LIMITE_STREAMING_MB = 10.0
LIMITE_CATALOGO_HASH_1K_MB = 3.0
LIMITE_CACHE_LRU_MB = 2.0
LIMITE_BATCH_PICKING_MB = 5.0


def _bytes_a_mb(cantidad_bytes: int) -> float:
    """Convierte bytes a Megabytes con precisión decimal."""
    return cantidad_bytes / (1024 * 1024)


class TestPresupuestoMemoria:
    """Verifica que ninguna operación crítica exceda su presupuesto de memoria heap."""

    def test_presupuesto_streaming_jsonl_memoria_acotada(self, tmp_path: Path) -> None:
        """Verifica que el generador streaming lea miles de líneas con memoria heap O(1).

        A diferencia de cargar todo el JSON en memoria, la lectura en streaming
        debe mantenerse por debajo de LIMITE_STREAMING_MB.
        """
        # 1. Generar archivo JSONL temporal de prueba (1.000 productos y 2.000 pedidos)
        ruta_prods, ruta_peds = generar_archivos_grandes_jsonl(
            directorio_destino=tmp_path,
            n_productos=1000,
            n_pedidos=2000,
            seed=42,
        )

        gc.collect()
        tracemalloc.start()
        try:
            # 2. Consumir productos en streaming
            contador_prods = sum(1 for _ in leer_productos_streaming_jsonl(ruta_prods))
            assert contador_prods == 1000

            # 3. Consumir pedidos en streaming
            contador_peds = sum(1 for _ in leer_pedidos_streaming_jsonl(ruta_peds))
            assert contador_peds == 2000

            _, pico_bytes = tracemalloc.get_traced_memory()
            pico_mb = _bytes_a_mb(pico_bytes)

            assert pico_mb < LIMITE_STREAMING_MB, (
                f"Regresión de memoria en streaming: consumo de {pico_mb:.2f} MB "
                f"supera el límite de {LIMITE_STREAMING_MB} MB."
            )
        finally:
            tracemalloc.stop()

    def test_presupuesto_catalogo_hash_indexado(self) -> None:
        """Verifica que el Catálogo Hash con índices respete el presupuesto espacial."""
        prods, _ = cargar_dataset_json(DATASETS_DIR / "mediano.json")
        assert len(prods) == 1000

        gc.collect()
        tracemalloc.start()
        try:
            catalogo = CatalogoHash(prods)
            assert len(catalogo) == 1000

            # Realizar búsquedas por id y por texto para activar índices
            for id_p in range(1, 101):
                assert catalogo.buscar_por_id(id_p) is not None
            catalogo.buscar_por_nombre("Producto")

            actual_bytes, pico_bytes = tracemalloc.get_traced_memory()
            pico_mb = _bytes_a_mb(pico_bytes)

            assert pico_mb < LIMITE_CATALOGO_HASH_1K_MB, (
                f"El Catálogo Hash consumió {pico_mb:.2f} MB en 1.000 productos, "
                f"superando el límite presupuestado de {LIMITE_CATALOGO_HASH_1K_MB} MB."
            )
        finally:
            tracemalloc.stop()

    def test_presupuesto_cache_lru_con_desalojo(self) -> None:
        """Verifica que la Caché LRU de consultas no crezca indefinidamente ante alto volumen."""
        cache_lru = CacheLRU[list[Producto]](capacidad_maxima=128)
        prods_mock = [Producto(id=1, nombre="Item", categoria="Cat", stock=10, precio=100.0)]

        gc.collect()
        tracemalloc.start()
        try:
            # Insertar 2.000 consultas distintas; solo 128 deben permanecer en memoria
            for i in range(2000):
                cache_lru.guardar(f"consulta_{i}", prods_mock)

            assert len(cache_lru) == 128
            assert cache_lru.metricas.evicciones == 2000 - 128

            actual_bytes, _ = tracemalloc.get_traced_memory()
            actual_mb = _bytes_a_mb(actual_bytes)

            assert actual_mb < LIMITE_CACHE_LRU_MB, (
                f"La caché LRU retuvo {actual_mb:.2f} MB tras 2.000 consultas, "
                f"superando el límite de {LIMITE_CACHE_LRU_MB} MB."
            )
        finally:
            tracemalloc.stop()

    def test_presupuesto_batch_picking_consolidado(self) -> None:
        """Verifica que el batch picking consolidado tenga cota de memoria controlada."""
        prods, peds = cargar_dataset_json(DATASETS_DIR / "mediano.json")
        catalogo = CatalogoHash(prods)

        gc.collect()
        tracemalloc.start()
        try:
            lote = agrupar_pedidos_batch(peds, catalogo)
            assert lote.total_pedidos == len(peds)

            _, pico_bytes = tracemalloc.get_traced_memory()
            pico_mb = _bytes_a_mb(pico_bytes)

            assert pico_mb < LIMITE_BATCH_PICKING_MB, (
                f"El lote de picking consolidado consumió {pico_mb:.2f} MB, "
                f"superando el límite de {LIMITE_BATCH_PICKING_MB} MB."
            )
        finally:
            tracemalloc.stop()
