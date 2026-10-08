"""Combinaciones de productos alternativos (Programación Dinámica / Memoización).

Permite sugerir productos sustitutos cuando un producto de un pedido no tiene stock suficiente,
respetando la misma categoría y un presupuesto máximo asignado.

Compara:
- Búsqueda recursiva exhaustiva sin memoización: O(2^N) en el peor caso (árbol combinatorio).
- Búsqueda con Programación Dinámica y Memoización: O(N * P), donde N es la cantidad de candidatos
  y P es el presupuesto discretizado.
"""

from __future__ import annotations

import time
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from src.modelos.producto import Producto

# Candidatos máximos por modo, para no superar el límite de recursión de Python.
MAX_CANDIDATOS_RECURSION = 16
MAX_CANDIDATOS_MEMOIZACION = 40


@dataclass(slots=True)
class CombinacionAlternativa:
    """Representa una combinación de productos sustitutos sugerida."""

    productos: list[Producto]
    costo_total: float

    def __post_init__(self) -> None:
        """Redondea el costo total a centavos."""
        object.__setattr__(self, "costo_total", round(float(self.costo_total), 2))

    @property
    def cantidad_items(self) -> int:
        """Cantidad de productos incluidos en la combinación."""
        return len(self.productos)


@dataclass(slots=True)
class ResultadoAlternativas:
    """Resultado del cálculo de combinaciones alternativas."""

    id_producto_original: int | None
    categoria: str
    presupuesto_maximo: float
    combinaciones: list[CombinacionAlternativa]
    estrategia: str
    tiempo_ejecucion_ms: float
    total_llamadas_recursivas: int
    hits_memo: int = 0

    @property
    def total_combinaciones(self) -> int:
        """Total de combinaciones válidas encontradas."""
        return len(self.combinaciones)


def _agregar_hasta_limite(
    resultados: list[list[int]], nuevos: Iterable[list[int]], limite: int
) -> None:
    """Agrega combinaciones a ``resultados`` y se detiene al alcanzar ``limite``.

    Como en la versión original, primero agrega y después compara: si ``resultados`` ya
    tenía elementos, puede quedar con uno más que el límite.
    """
    for combo in nuevos:
        resultados.append(combo)
        if len(resultados) >= limite:
            return


class BuscadorAlternativas:
    """Motor de cálculo de combinaciones de sustitución con y sin memoización."""

    def __init__(self, productos: Sequence[Producto]) -> None:
        """Inicializa el buscador con el catálogo de productos disponibles."""
        self._productos_disponibles = [p for p in productos if p.stock > 0]
        # Memoización explícita:
        # (categoria, tupla_ids, presupuesto_entero) -> list[tuple[ids]]
        self._memo_cache: dict[tuple[int, int], list[list[int]]] = {}
        self._contador_llamadas = 0
        self._contador_hits = 0

    def limpiar_cache(self) -> None:
        """Invalida y vacía la tabla de memoización."""
        self._memo_cache.clear()
        self._contador_llamadas = 0
        self._contador_hits = 0

    def buscar_alternativas(
        self,
        categoria: str,
        presupuesto_maximo: float,
        producto_original: Producto | None = None,
        max_combinaciones: int = 15,
        usar_memoizacion: bool = True,
        max_candidatos: int | None = None,
    ) -> ResultadoAlternativas:
        """Encuentra combinaciones de productos de la categoría que no superen el presupuesto.

        Argumentos:
            categoria: Rubro en el que buscar sustitutos.
            presupuesto_maximo: Límite monetario para la suma de productos sustitutos.
            producto_original: Producto que se desea sustituir (se excluye de los candidatos).
            max_combinaciones: Cota superior de combinaciones a retornar para presentación.
            usar_memoizacion: Si True, utiliza programación dinámica con memoización;
                             si False, ejecuta búsqueda recursiva exhaustiva.
            max_candidatos: Límite de productos candidatos a evaluar (sirve para medir el
                costo O(2^N) en los benchmarks).
        """
        inicio = time.perf_counter()
        self._contador_llamadas = 0
        self._contador_hits = 0
        estrategia = "memoizado" if usar_memoizacion else "recursivo_puro"

        if max_candidatos is None:
            # Tope seguro para que la recursión no supere el límite de la pila de Python.
            max_candidatos = (
                MAX_CANDIDATOS_MEMOIZACION if usar_memoizacion else MAX_CANDIDATOS_RECURSION
            )
        candidatos = self._filtrar_candidatos(
            categoria, presupuesto_maximo, producto_original, max_candidatos
        )
        presupuesto_centavos = round(presupuesto_maximo * 100)

        combinaciones: list[CombinacionAlternativa] = []
        if candidatos and presupuesto_centavos > 0:
            if usar_memoizacion:
                self._memo_cache.clear()
                resolver = self._resolver_dp_memo
            else:
                resolver = self._resolver_recursivo_puro
            indices = resolver(candidatos, 0, presupuesto_centavos, max_combinaciones)
            combinaciones = self._armar_combinaciones(candidatos, indices)[:max_combinaciones]

        return ResultadoAlternativas(
            id_producto_original=producto_original.id if producto_original else None,
            categoria=categoria,
            presupuesto_maximo=presupuesto_maximo,
            combinaciones=combinaciones,
            estrategia=estrategia,
            tiempo_ejecucion_ms=(time.perf_counter() - inicio) * 1000.0,
            total_llamadas_recursivas=self._contador_llamadas,
            hits_memo=self._contador_hits,
        )

    def _filtrar_candidatos(
        self,
        categoria: str,
        presupuesto_maximo: float,
        producto_original: Producto | None,
        max_candidatos: int,
    ) -> list[Producto]:
        """Productos de la categoría que entran en el presupuesto, del más barato al más caro.

        Ordenar por precio permite podar ramas temprano; se excluye el producto original.
        """
        categoria_norm = categoria.lower().strip()
        id_excluido = producto_original.id if producto_original else None
        candidatos = sorted(
            (
                producto
                for producto in self._productos_disponibles
                if producto.categoria.lower().strip() == categoria_norm
                and producto.id != id_excluido
                and producto.precio <= presupuesto_maximo
            ),
            key=lambda producto: producto.precio,
        )
        return candidatos[:max_candidatos]

    @staticmethod
    def _armar_combinaciones(
        candidatos: list[Producto], indices: list[list[int]]
    ) -> list[CombinacionAlternativa]:
        """Convierte índices en combinaciones, de la más cara a la más barata.

        Las más caras aprovechan mejor el presupuesto disponible.
        """
        combinaciones = []
        for combo in indices:
            productos = [candidatos[indice] for indice in combo]
            combinaciones.append(
                CombinacionAlternativa(productos, sum(producto.precio for producto in productos))
            )
        combinaciones.sort(key=lambda combinacion: combinacion.costo_total, reverse=True)
        return combinaciones

    def _resolver_recursivo_puro(
        self,
        candidatos: list[Producto],
        indice: int,
        presupuesto_restante: int,
        limite: int,
    ) -> list[list[int]]:
        """Búsqueda exhaustiva sin almacenamiento de estados (O(2^N))."""
        self._contador_llamadas += 1

        if indice >= len(candidatos) or presupuesto_restante <= 0:
            return []

        precio_actual = int(round(candidatos[indice].precio * 100))
        resultados: list[list[int]] = []

        # Opción 1: incluir el producto actual (solo y combinado con los siguientes).
        if precio_actual <= presupuesto_restante:
            resultados.append([indice])
            con_actual = self._resolver_recursivo_puro(
                candidatos, indice + 1, presupuesto_restante - precio_actual, limite
            )
            _agregar_hasta_limite(resultados, ([indice, *combo] for combo in con_actual), limite)

        # Opción 2: excluir el producto actual y avanzar.
        if len(resultados) < limite:
            sin_actual = self._resolver_recursivo_puro(
                candidatos, indice + 1, presupuesto_restante, limite
            )
            _agregar_hasta_limite(resultados, sin_actual, limite)

        return resultados

    def _resolver_dp_memo(
        self,
        candidatos: list[Producto],
        indice: int,
        presupuesto_restante: int,
        limite: int,
    ) -> list[list[int]]:
        """Búsqueda con Programación Dinámica y Memoización de subproblemas (O(N * P))."""
        self._contador_llamadas += 1

        if indice >= len(candidatos) or presupuesto_restante <= 0:
            return []

        # Estado del subproblema: (indice_candidato, presupuesto_restante)
        clave_estado = (indice, presupuesto_restante)
        if clave_estado in self._memo_cache:
            self._contador_hits += 1
            return [list(c) for c in self._memo_cache[clave_estado]]

        precio_actual = int(round(candidatos[indice].precio * 100))
        resultados: list[list[int]] = []

        # Opción 1: incluir el producto actual (solo y combinado con los siguientes).
        if precio_actual <= presupuesto_restante:
            resultados.append([indice])
            con_actual = self._resolver_dp_memo(
                candidatos, indice + 1, presupuesto_restante - precio_actual, limite
            )
            _agregar_hasta_limite(resultados, ([indice, *combo] for combo in con_actual), limite)

        # Opción 2: excluir el producto actual.
        if len(resultados) < limite:
            sin_actual = self._resolver_dp_memo(
                candidatos, indice + 1, presupuesto_restante, limite
            )
            _agregar_hasta_limite(resultados, sin_actual, limite)

        # Guardar en la tabla de memoización para reusar en subárboles convergentes
        self._memo_cache[clave_estado] = [list(c) for c in resultados]
        return resultados
