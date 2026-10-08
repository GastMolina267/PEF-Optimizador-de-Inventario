"""Fachada unificada del Motor de Inventario y Pedidos.

Provee la interfaz común de alto nivel que consumen la interfaz gráfica Flet,
los scripts de benchmarking y los tests automatizados.

Permite alternar dinámicamente entre:

- Estrategia 'baseline': Catálogo lineal O(n), ordenamiento completo O(n log n),
  procesamiento secuencial y búsqueda de combinaciones puramente recursiva sin caché.
- Estrategia 'optimizado': Catálogo hash O(1), min/max heaps O(n log k),
  procesamiento paralelo con ProcessPoolExecutor, DP memoizada y Caching LRU inteligente con
  invalidación reactiva.
"""

from __future__ import annotations

from collections.abc import Sequence
from enum import Enum
from pathlib import Path
from typing import Any

from src.cache.cache_consultas import GestorCacheConsultas
from src.datos.cargador import cargar_dataset_json
from src.datos.procesador_lotes_paralelo import (
    procesar_pedidos_jsonl_paralelo,
    procesar_pedidos_jsonl_secuencial,
)
from src.datos.streaming import (
    exportar_picking_csv_con_buffer,
    leer_pedidos_streaming_jsonl,
    leer_productos_streaming_jsonl,
)
from src.inventario.catalogo_hash import CatalogoHash
from src.inventario.catalogo_lineal import CatalogoLineal
from src.inventario.protocolo import Catalogo
from src.modelos.pedido import Pedido, ResumenProcesamiento
from src.modelos.producto import Producto
from src.observabilidad import etiquetar, medir
from src.pedidos.agrupador import LotePickingConsolidado, agrupar_pedidos_batch
from src.pedidos.combinaciones import BuscadorAlternativas, ResultadoAlternativas
from src.pedidos.procesador_concurrente import procesar_pedidos_concurrente
from src.pedidos.procesador_secuencial import procesar_pedidos_secuencial
from src.ranking.top_productos import (
    calcular_top_solicitados_heap,
    calcular_top_solicitados_lineal,
)


class EstrategiaMotor(str, Enum):
    """Estrategia algorítmica de ejecución del motor de inventario."""

    BASELINE = "baseline"
    OPTIMIZADO = "optimizado"


class MotorInventario:
    """Controlador central del dominio de inventario y pedidos."""

    def __init__(
        self,
        productos: Sequence[Producto] | None = None,
        pedidos: Sequence[Pedido] | None = None,
        estrategia: EstrategiaMotor | str = EstrategiaMotor.BASELINE,
    ) -> None:
        """Inicializa el motor con una estrategia ('baseline' u 'optimizado')."""
        self._estrategia = (
            estrategia.value if isinstance(estrategia, EstrategiaMotor) else estrategia.lower()
        )
        self._pedidos: list[Pedido] = list(pedidos) if pedidos else []
        self._cache = GestorCacheConsultas()

        lista_inicial = list(productos) if productos else []
        self._catalogo = self._crear_catalogo(lista_inicial)
        self._buscador_alternativas = BuscadorAlternativas(self._catalogo.obtener_todos())

    def _crear_catalogo(self, productos: Sequence[Producto]) -> CatalogoHash | CatalogoLineal:
        """Instancia la estructura de catálogo correspondiente a la estrategia activa."""
        if self._estrategia == EstrategiaMotor.OPTIMIZADO:
            return CatalogoHash(productos)
        return CatalogoLineal(productos)

    @property
    def estrategia(self) -> str:
        """Estrategia algorítmica actualmente activa ('baseline' u 'optimizado')."""
        return self._estrategia

    @property
    def es_optimizado(self) -> bool:
        """Indica si la estrategia activa es la optimizada."""
        return self._estrategia == EstrategiaMotor.OPTIMIZADO

    @property
    def catalogo(self) -> Catalogo:
        """Acceso al catálogo de inventario activo."""
        return self._catalogo

    @property
    def pedidos(self) -> list[Pedido]:
        """Lista de pedidos cargados en el motor."""
        return self._pedidos

    @property
    def cache(self) -> GestorCacheConsultas:
        """Acceso al gestor de caché inteligente."""
        return self._cache

    def _etiquetar(self, **extra: Any) -> None:
        """Etiqueta la operación en curso en Elastic APM con el contexto del motor."""
        etiquetar(
            estrategia=self.estrategia,
            productos=len(self._catalogo),
            pedidos=len(self._pedidos),
            **extra,
        )

    @medir("motor.cambiar_estrategia")
    def cambiar_estrategia(self, nueva_estrategia: EstrategiaMotor | str) -> None:
        """Permite alternar entre 'baseline' y 'optimizado' conservando los datos cargados."""
        if isinstance(nueva_estrategia, EstrategiaMotor):
            estrategia_norm = nueva_estrategia.value
        else:
            estrategia_norm = nueva_estrategia.lower().strip()

        if estrategia_norm not in (EstrategiaMotor.BASELINE, EstrategiaMotor.OPTIMIZADO):
            raise ValueError(
                f"Estrategia inválida: '{nueva_estrategia}'. Debe ser 'baseline' u 'optimizado'."
            )

        if self._estrategia == estrategia_norm:
            return

        self._estrategia = estrategia_norm
        todos_prods = self._catalogo.obtener_todos()
        self._catalogo = self._crear_catalogo(todos_prods)

        self._cache.invalidar_todo()
        self._buscador_alternativas = BuscadorAlternativas(todos_prods)

    @medir("motor.cargar_dataset")
    def cargar_dataset(self, ruta: str | Path) -> None:
        """Carga un dataset JSON en el motor reemplazando el estado actual."""
        productos, pedidos = cargar_dataset_json(ruta)
        self.cargar_desde_listas(productos, pedidos)
        self._etiquetar(dataset=Path(ruta).name)

    @medir("motor.cargar_dataset_jsonl")
    def cargar_dataset_jsonl(
        self,
        ruta_productos: str | Path,
        ruta_pedidos: str | Path,
    ) -> None:
        """Carga datos desde archivos .jsonl en streaming con memoria constante."""
        productos_cargados = list(leer_productos_streaming_jsonl(ruta_productos))
        pedidos_cargados = list(leer_pedidos_streaming_jsonl(ruta_pedidos))
        self.cargar_desde_listas(productos_cargados, pedidos_cargados)
        self._etiquetar(dataset=Path(ruta_pedidos).name)

    def cargar_desde_listas(
        self, productos: Sequence[Producto], pedidos: Sequence[Pedido]
    ) -> None:
        """Carga datos directamente desde secuencias en memoria."""
        self._pedidos = list(pedidos)
        lista_prods = list(productos)
        self._catalogo = self._crear_catalogo(lista_prods)

        self._cache.invalidar_todo()
        self._buscador_alternativas = BuscadorAlternativas(lista_prods)

    def buscar_por_id(self, id_producto: int) -> Producto | None:
        """Busca un producto por identificador (O(1) en optimizado, O(n) en baseline)."""
        return self._catalogo.buscar_por_id(id_producto)

    @medir("motor.buscar_por_nombre")
    def buscar_por_nombre(self, texto: str, usar_cache: bool = True) -> list[Producto]:
        """Busca productos por denominación. Utiliza caché LRU si la estrategia es optimizada."""
        if self.es_optimizado and usar_cache:
            cacheado = self._cache.obtener_busqueda_nombre(texto)
            if cacheado is not None:
                return cacheado

        resultados = self._catalogo.buscar_por_nombre(texto)

        if self.es_optimizado and usar_cache:
            self._cache.guardar_busqueda_nombre(texto, resultados)

        return resultados

    @medir("motor.buscar_por_categoria")
    def buscar_por_categoria(self, categoria: str, usar_cache: bool = True) -> list[Producto]:
        """Busca productos de una categoría (con o sin caché LRU)."""
        if self.es_optimizado and usar_cache:
            cacheado = self._cache.obtener_busqueda_categoria(categoria)
            if cacheado is not None:
                return cacheado

        resultados = self._catalogo.buscar_por_categoria(categoria)

        if self.es_optimizado and usar_cache:
            self._cache.guardar_busqueda_categoria(categoria, resultados)

        return resultados

    @medir("motor.procesar_pedidos")
    def procesar_pedidos(
        self,
        pedidos: Sequence[Pedido] | None = None,
        concurrente: bool = False,
        descontar_stock: bool = False,
        politica_descuento: str = "solo_cubiertos",
    ) -> ResumenProcesamiento:
        """Procesa un lote de pedidos según la estrategia configurada.

        El procesamiento es secuencial salvo que se pida ``concurrente=True``. Evaluar un
        pedido en memoria es un lookup O(1) por línea y cuesta menos que serializarlo
        hacia un worker: con ``grande.json`` el pool tarda más del doble que el
        secuencial aun con el pool ya creado (ver ``docs/mediciones/archivos_grandes.md``,
        sección 3). Por eso el pool queda como opción explícita (switch de la UI y
        comparativa de la oral).

        Argumentos:
            pedidos: Pedidos a procesar (por defecto, los cargados en el motor).
            concurrente: Si es True, usa el ProcessPoolExecutor.
            descontar_stock: Si es True, descuenta del catálogo lo asignado.
            politica_descuento: ``solo_cubiertos`` o ``todo_lo_posible``.
        """
        lote = pedidos if pedidos is not None else self._pedidos
        self._etiquetar(lote_pedidos=len(lote), concurrente=concurrente, descontar=descontar_stock)

        if concurrente:
            resumen = procesar_pedidos_concurrente(
                catalogo=self._catalogo,
                pedidos=lote,
                descontar_stock=descontar_stock,
                politica_descuento=politica_descuento,
            )
        else:
            resumen = procesar_pedidos_secuencial(
                catalogo=self._catalogo,
                pedidos=lote,
                descontar_stock=descontar_stock,
                politica_descuento=politica_descuento,
            )

        etiquetar(cubiertos=resumen.pedidos_cubiertos, parciales=resumen.pedidos_parciales)

        # Si mutó stock, invalidamos reactivamente la caché de consultas y alternativas
        if descontar_stock:
            self._cache.invalidar_por_mutacion_stock()
            self._cache.invalidar_por_nuevos_pedidos()
            self._buscador_alternativas = BuscadorAlternativas(self._catalogo.obtener_todos())

        return resumen

    @medir("motor.procesar_pedidos_jsonl")
    def procesar_pedidos_jsonl(
        self,
        ruta_pedidos: str | Path,
        tamano_lote: int = 5000,
        paralelo: bool | None = None,
        reconstruir_dataclasses: bool = False,
    ) -> ResumenProcesamiento:
        """Procesa un archivo masivo de pedidos .jsonl en streaming por lotes.

        Aprovecha el procesamiento paralelo con workers si la estrategia es optimizada
        o si se indica explícitamente paralelo=True.
        """
        mapa_stock = {p.id: p.stock for p in self._catalogo.obtener_todos()}
        es_paralelo = self.es_optimizado if paralelo is None else paralelo
        self._etiquetar(
            archivo=Path(ruta_pedidos).name, tamano_lote=tamano_lote, paralelo=es_paralelo
        )

        if es_paralelo:
            return procesar_pedidos_jsonl_paralelo(
                ruta_pedidos=ruta_pedidos,
                mapa_stock=mapa_stock,
                tamano_lote=tamano_lote,
                reconstruir_dataclasses=reconstruir_dataclasses,
            )
        return procesar_pedidos_jsonl_secuencial(
            ruta_pedidos=ruta_pedidos,
            mapa_stock=mapa_stock,
            tamano_lote=tamano_lote,
            reconstruir_dataclasses=reconstruir_dataclasses,
        )

    @medir("motor.obtener_top_solicitados")
    def obtener_top_solicitados(
        self,
        k: int = 10,
        pedidos: Sequence[Pedido] | None = None,
        usar_cache: bool = True,
    ) -> list[tuple[Producto, int]]:
        """Determina los k productos más demandados.

        Usa heapq.nlargest en 'optimizado' y sort completo en 'baseline'.
        En 'optimizado' almacena y recupera de la caché LRU si usar_cache=True.
        """
        lote = pedidos if pedidos is not None else self._pedidos

        # Revisar caché si corresponde y el lote es el del motor
        consulta_lote_motor = (pedidos is None) or (pedidos == self._pedidos)
        if self.es_optimizado and usar_cache and consulta_lote_motor:
            cacheado = self._cache.obtener_top_solicitados(k)
            if cacheado is not None:
                return cacheado

        if self.es_optimizado:
            resultados = calcular_top_solicitados_heap(lote, self._catalogo, k=k)
        else:
            resultados = calcular_top_solicitados_lineal(lote, self._catalogo, k=k)

        if self.es_optimizado and usar_cache and consulta_lote_motor:
            self._cache.guardar_top_solicitados(k, resultados)

        return resultados

    calcular_top_productos = obtener_top_solicitados

    @medir("motor.agrupar_pedidos")
    def agrupar_pedidos(self, pedidos: Sequence[Pedido] | None = None) -> LotePickingConsolidado:
        """Agrupa las líneas de los pedidos para Batch Picking consolidado."""
        lote = pedidos if pedidos is not None else self._pedidos
        return agrupar_pedidos_batch(lote, self._catalogo)

    @medir("motor.exportar_picking_csv")
    def exportar_picking_csv(
        self, ruta_csv: str | Path, pedidos: Sequence[Pedido] | None = None
    ) -> int:
        """Exporta el reporte consolidado de picking a CSV con buffer de 1 MB."""
        lote_picking = self.agrupar_pedidos(pedidos)
        return exportar_picking_csv_con_buffer(ruta_csv, lote_picking.items)

    @medir("motor.buscar_alternativas")
    def buscar_alternativas(
        self,
        categoria: str,
        presupuesto_maximo: float,
        producto_original: Producto | None = None,
        max_combinaciones: int = 15,
        forzar_memoizacion: bool | None = None,
        max_candidatos: int | None = None,
    ) -> ResultadoAlternativas:
        """Calcula alternativas y combinaciones para productos agotados o pedidos parciales."""
        usar_memo = forzar_memoizacion if forzar_memoizacion is not None else self.es_optimizado
        return self._buscador_alternativas.buscar_alternativas(
            categoria=categoria,
            presupuesto_maximo=presupuesto_maximo,
            producto_original=producto_original,
            max_combinaciones=max_combinaciones,
            usar_memoizacion=usar_memo,
            max_candidatos=max_candidatos,
        )

    def obtener_estadisticas(self) -> dict[str, Any]:
        """Retorna estadísticas descriptivas del estado del sistema y de la caché."""
        productos_cargados = self._catalogo.obtener_todos()
        stock_total = sum(p.stock for p in productos_cargados)
        categorias = sorted({p.categoria for p in productos_cargados})
        total_lineas = sum(len(p.lineas) for p in self._pedidos)
        unidades_demandadas = sum(lin.cantidad for p in self._pedidos for lin in p.lineas)

        stats: dict[str, Any] = {
            "estrategia": self._estrategia,
            "tipo_catalogo": type(self._catalogo).__name__,
            "total_productos": len(productos_cargados),
            "stock_total_unidades": stock_total,
            "total_categorias": len(categorias),
            "categorias": categorias,
            "total_pedidos": len(self._pedidos),
            "total_lineas_pedidos": total_lineas,
            "unidades_demandadas": unidades_demandadas,
        }

        if self.es_optimizado:
            stats["metricas_cache"] = self._cache.obtener_estadisticas()

        return stats
