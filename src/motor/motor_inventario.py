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
from src.inventario.catalogo_hash import CatalogoHash
from src.inventario.catalogo_lineal import CatalogoLineal
from src.modelos.pedido import Pedido, ResumenProcesamiento
from src.modelos.producto import Producto
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
    def catalogo(self):
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

    def cargar_dataset(self, ruta: str | Path) -> None:
        """Carga un dataset JSON en el motor reemplazando el estado actual."""
        productos, pedidos = cargar_dataset_json(ruta)
        self.cargar_desde_listas(productos, pedidos)

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

    UMBRAL_PEDIDOS_CONCURRENTE: int = 500

    def procesar_pedidos(
        self,
        pedidos: Sequence[Pedido] | None = None,
        concurrente: bool | None = None,
        descontar_stock: bool = False,
        politica_descuento: str = "solo_cubiertos",
    ) -> ResumenProcesamiento:
        """Procesa un lote de pedidos según la estrategia configurada."""
        lote = pedidos if pedidos is not None else self._pedidos

        # El overhead de IPC en Windows solo se amortiza en lotes grandes o pesados.
        es_concurrente = (
            concurrente
            if concurrente is not None
            else (self.es_optimizado and len(lote) >= self.UMBRAL_PEDIDOS_CONCURRENTE)
        )

        if es_concurrente:
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

        # Si mutó stock, invalidamos reactivamente la caché de consultas y alternativas
        if descontar_stock:
            self._cache.invalidar_por_mutacion_stock()
            self._cache.invalidar_por_nuevos_pedidos()
            self._buscador_alternativas = BuscadorAlternativas(self._catalogo.obtener_todos())

        return resumen

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

    def agrupar_pedidos(self, pedidos: Sequence[Pedido] | None = None) -> LotePickingConsolidado:
        """Agrupa las líneas de los pedidos para Batch Picking consolidado."""
        lote = pedidos if pedidos is not None else self._pedidos
        return agrupar_pedidos_batch(lote, self._catalogo)

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
        prods = self._catalogo.obtener_todos()
        stock_total = sum(p.stock for p in prods)
        categorias = sorted({p.categoria for p in prods})
        total_lineas = sum(len(p.lineas) for p in self._pedidos)
        unidades_demandadas = sum(lin.cantidad for p in self._pedidos for lin in p.lineas)

        stats: dict[str, Any] = {
            "estrategia": self._estrategia,
            "tipo_catalogo": type(self._catalogo).__name__,
            "total_productos": len(prods),
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
