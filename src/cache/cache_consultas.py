"""Módulo de Caching Inteligente con desalojo LRU e invalidación reactiva.

Diferenciación conceptual clave frente a la memoización:

- Memoización: Guarda subestados algorítmicos dentro de una función pura (DP en combinaciones).
- Caching Inteligente: Capa de persistencia en memoria para consultas repetitivas de lectura
  (búsquedas por texto, por categoría y rankings Top-N), con desalojo acotado (LRU) e
  invalidación reactiva ante mutaciones de datos para no servir información obsoleta.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from src.modelos.producto import Producto

T = TypeVar("T")


@dataclass
class MetricasCache:
    """Métricas operativas de rendimiento de una caché."""

    hits: int = 0
    misses: int = 0
    evicciones: int = 0
    invalidaciones: int = 0

    @property
    def total_consultas(self) -> int:
        """Total de consultas recibidas."""
        return self.hits + self.misses

    @property
    def tasa_aciertos(self) -> float:
        """Porcentaje de aciertos (hit ratio) de la caché."""
        if self.total_consultas == 0:
            return 0.0
        return (self.hits / self.total_consultas) * 100.0


class CacheLRU(Generic[T]):
    """Estructura de caché Least Recently Used (LRU) acotada en memoria."""

    def __init__(self, capacidad_maxima: int = 128) -> None:
        """Inicializa la caché LRU con una capacidad máxima de entradas."""
        if capacidad_maxima <= 0:
            raise ValueError("La capacidad de la caché debe ser mayor a 0.")
        self._capacidad = capacidad_maxima
        self._almacen: OrderedDict[str, T] = OrderedDict()
        self.metricas = MetricasCache()

    @property
    def capacidad(self) -> int:
        """Límite superior de elementos almacenados."""
        return self._capacidad

    def __len__(self) -> int:
        """Cantidad actual de entradas en caché."""
        return len(self._almacen)

    def obtener(self, clave: str) -> T | None:
        """Recupera un valor de la caché marcándolo como recientemente usado (Hit)."""
        if clave in self._almacen:
            self._almacen.move_to_end(clave)
            self.metricas.hits += 1
            return self._almacen[clave]
        self.metricas.misses += 1
        return None

    def guardar(self, clave: str, valor: T) -> None:
        """Almacena o actualiza un valor. Desaloja el más antiguo si supera la capacidad."""
        if clave in self._almacen:
            self._almacen.move_to_end(clave)
        elif len(self._almacen) >= self._capacidad:
            # Desalojar el elemento menos recientemente usado (primer elemento del OrderedDict)
            self._almacen.popitem(last=False)
            self.metricas.evicciones += 1
        self._almacen[clave] = valor

    def invalidar_clave(self, clave: str) -> bool:
        """Elimina una clave específica de la caché."""
        if clave in self._almacen:
            del self._almacen[clave]
            self.metricas.invalidaciones += 1
            return True
        return False

    def limpiar(self) -> None:
        """Purga todos los elementos de la caché."""
        self.metricas.invalidaciones += len(self._almacen)
        self._almacen.clear()


class GestorCacheConsultas:
    """Administrador centralizado de cachés para el sistema de inventario."""

    def __init__(self, capacidad_busquedas: int = 64, capacidad_ranking: int = 16) -> None:
        """Inicializa los depósitos de caché para búsquedas y rankings."""
        self._cache_busquedas = CacheLRU[list[Producto]](capacidad_busquedas)
        self._cache_categorias = CacheLRU[list[Producto]](capacidad_busquedas)
        self._cache_top_n = CacheLRU[list[tuple[Producto, int]]](capacidad_ranking)

    @property
    def metricas(self) -> MetricasCache:
        """Métricas de búsquedas por texto. Es la partición que usa Catálogo."""
        return self._cache_busquedas.metricas

    # --- Búsquedas por nombre ---
    def obtener_busqueda_nombre(self, texto: str) -> list[Producto] | None:
        """Obtiene el resultado almacenado para una búsqueda por texto."""
        return self._cache_busquedas.obtener(texto.lower().strip())

    def guardar_busqueda_nombre(self, texto: str, resultados: list[Producto]) -> None:
        """Almacena el resultado de una búsqueda por texto."""
        self._cache_busquedas.guardar(texto.lower().strip(), resultados)

    # --- Búsquedas por categoría ---
    def obtener_busqueda_categoria(self, categoria: str) -> list[Producto] | None:
        """Obtiene el resultado almacenado para una consulta de categoría."""
        return self._cache_categorias.obtener(categoria.lower().strip())

    def guardar_busqueda_categoria(self, categoria: str, resultados: list[Producto]) -> None:
        """Almacena el resultado de una consulta de categoría."""
        self._cache_categorias.guardar(categoria.lower().strip(), resultados)

    # --- Ranking Top-N ---
    def obtener_top_solicitados(self, k: int) -> list[tuple[Producto, int]] | None:
        """Obtiene el ranking Top-N previamente calculado."""
        return self._cache_top_n.obtener(str(k))

    def guardar_top_solicitados(self, k: int, resultados: list[tuple[Producto, int]]) -> None:
        """Almacena el ranking Top-N."""
        self._cache_top_n.guardar(str(k), resultados)

    # --- Protocolo de invalidación reactiva ---
    def invalidar_por_mutacion_stock(self) -> None:
        """Invalida las cachés afectadas ante una mutación de existencias.

        Garantiza que ninguna consulta devuelva datos de inventario obsoletos.
        """
        self._cache_busquedas.limpiar()
        self._cache_categorias.limpiar()

    def invalidar_por_nuevos_pedidos(self) -> None:
        """Invalida la caché del ranking Top-N ante la recepción o procesamiento de pedidos."""
        self._cache_top_n.limpiar()

    def invalidar_todo(self) -> None:
        """Purga completa de todas las cachés del sistema."""
        self._cache_busquedas.limpiar()
        self._cache_categorias.limpiar()
        self._cache_top_n.limpiar()

    def obtener_estadisticas(self) -> dict[str, Any]:
        """Consolida las métricas de rendimiento de todas las particiones de caché."""
        m_busq = self._cache_busquedas.metricas
        m_cat = self._cache_categorias.metricas
        m_top = self._cache_top_n.metricas

        total_hits = m_busq.hits + m_cat.hits + m_top.hits
        total_misses = m_busq.misses + m_cat.misses + m_top.misses
        total_consultas = total_hits + total_misses
        ratio_global = (total_hits / total_consultas * 100.0) if total_consultas > 0 else 0.0

        return {
            "total_entradas_activas": len(self._cache_busquedas)
            + len(self._cache_categorias)
            + len(self._cache_top_n),
            "hits_globales": total_hits,
            "misses_globales": total_misses,
            "tasa_aciertos_global_pct": round(ratio_global, 2),
            "busquedas": {
                "entradas": len(self._cache_busquedas),
                "hits": m_busq.hits,
                "misses": m_busq.misses,
                "evicciones": m_busq.evicciones,
            },
            "categorias": {
                "entradas": len(self._cache_categorias),
                "hits": m_cat.hits,
                "misses": m_cat.misses,
                "evicciones": m_cat.evicciones,
            },
            "top_n": {
                "entradas": len(self._cache_top_n),
                "hits": m_top.hits,
                "misses": m_top.misses,
                "evicciones": m_top.evicciones,
            },
        }
