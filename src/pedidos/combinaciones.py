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
from collections.abc import Sequence
from dataclasses import dataclass

from src.modelos.producto import Producto


@dataclass(slots=True)
class CombinacionAlternativa:
    """Representa una combinación de productos sustitutos sugerida."""

    productos: list[Producto]
    costo_total: float

    def __post_init__(self) -> None:
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

        # Filtrar candidatos de la categoría con stock disponible
        cat_norm = categoria.lower().strip()
        candidatos = [
            p
            for p in self._productos_disponibles
            if p.categoria.lower().strip() == cat_norm
            and (producto_original is None or p.id != producto_original.id)
            and p.precio <= presupuesto_maximo
        ]

        # Ordenar candidatos por precio para podas de ramas tempranas
        candidatos.sort(key=lambda p: p.precio)

        # Si se especifica o si supera un límite seguro, acotar para evitar stack overflow
        if max_candidatos is not None:
            candidatos = candidatos[:max_candidatos]
        elif not usar_memoizacion:
            if len(candidatos) > 16:
                candidatos = candidatos[:16]
        else:
            # En modo memoizado, acotar a un conjunto seguro (ej. 40) para garantizar
            # que la profundidad de recursión nunca exceda el límite del call stack de Python
            if len(candidatos) > 40:
                candidatos = candidatos[:40]

        presupuesto_centavos = int(round(presupuesto_maximo * 100))

        if not candidatos or presupuesto_centavos <= 0:
            tiempo_ms = (time.perf_counter() - inicio) * 1000.0
            return ResultadoAlternativas(
                id_producto_original=producto_original.id if producto_original else None,
                categoria=categoria,
                presupuesto_maximo=presupuesto_maximo,
                combinaciones=[],
                estrategia="memoizado" if usar_memoizacion else "recursivo_puro",
                tiempo_ejecucion_ms=tiempo_ms,
                total_llamadas_recursivas=0,
                hits_memo=0,
            )

        if usar_memoizacion:
            self._memo_cache.clear()
            combinaciones_indices = self._resolver_dp_memo(
                candidatos, 0, presupuesto_centavos, max_combinaciones
            )
            estrategia = "memoizado"
        else:
            combinaciones_indices = self._resolver_recursivo_puro(
                candidatos, 0, presupuesto_centavos, max_combinaciones
            )
            estrategia = "recursivo_puro"

        tiempo_ms = (time.perf_counter() - inicio) * 1000.0

        # Reconstruir combinaciones de objetos Producto
        resultado_comb: list[CombinacionAlternativa] = []
        for combo in combinaciones_indices:
            prods_combo = [candidatos[idx] for idx in combo]
            costo_total = sum(p.precio for p in prods_combo)
            resultado_comb.append(CombinacionAlternativa(prods_combo, costo_total))

        # Ordenar por costo total descendente (mejores opciones más cercanas al presupuesto)
        resultado_comb.sort(key=lambda c: c.costo_total, reverse=True)

        return ResultadoAlternativas(
            id_producto_original=producto_original.id if producto_original else None,
            categoria=categoria,
            presupuesto_maximo=presupuesto_maximo,
            combinaciones=resultado_comb[:max_combinaciones],
            estrategia=estrategia,
            tiempo_ejecucion_ms=tiempo_ms,
            total_llamadas_recursivas=self._contador_llamadas,
            hits_memo=self._contador_hits,
        )

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

        # Opción 1: Incluir el producto actual (si el presupuesto lo permite)
        if precio_actual <= presupuesto_restante:
            # La combinación unitaria formada solo por este producto
            resultados.append([indice])
            # Combinar con los subsiguientes
            sub_combos = self._resolver_recursivo_puro(
                candidatos, indice + 1, presupuesto_restante - precio_actual, limite
            )
            for sc in sub_combos:
                resultados.append([indice] + sc)
                if len(resultados) >= limite:
                    return resultados

        # Opción 2: Excluir el producto actual y avanzar
        if len(resultados) < limite:
            sub_combos_sin = self._resolver_recursivo_puro(
                candidatos, indice + 1, presupuesto_restante, limite
            )
            for sc in sub_combos_sin:
                resultados.append(sc)
                if len(resultados) >= limite:
                    break

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

        # Opción 1: Incluir el producto actual
        if precio_actual <= presupuesto_restante:
            resultados.append([indice])
            sub_combos = self._resolver_dp_memo(
                candidatos, indice + 1, presupuesto_restante - precio_actual, limite
            )
            for sc in sub_combos:
                resultados.append([indice] + sc)
                if len(resultados) >= limite:
                    break

        # Opción 2: Excluir el producto actual
        if len(resultados) < limite:
            sub_combos_sin = self._resolver_dp_memo(
                candidatos, indice + 1, presupuesto_restante, limite
            )
            for sc in sub_combos_sin:
                resultados.append(sc)
                if len(resultados) >= limite:
                    break

        # Guardar en la tabla de memoización para reusar en subárboles convergentes
        self._memo_cache[clave_estado] = [list(c) for c in resultados]
        return resultados
