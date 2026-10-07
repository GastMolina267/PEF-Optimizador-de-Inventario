"""Módulo para el cálculo de productos más solicitados (Top-N).

Permite comparar:
- Algoritmo baseline: ordenamiento total de frecuencias O(N log N).
- Algoritmo optimizado: montículo binario (Heap) con heapq.nlargest O(N log k).
"""

from __future__ import annotations

import heapq
from collections.abc import Sequence

from src.modelos.pedido import Pedido
from src.modelos.producto import Producto


def calcular_top_solicitados_lineal(
    pedidos: Sequence[Pedido],
    catalogo,
    k: int = 10,
) -> list[tuple[Producto, int]]:
    """Calcula los k productos más solicitados utilizando ordenamiento total (Baseline).

    Estrategia algorítmica:
    1. Agrega las cantidades demandadas de cada producto en un mapa de frecuencias.
    2. Ordena la totalidad de los pares (id_producto, frecuencia) en O(N log N).
    3. Corta los primeros k elementos.
    4. Resuelve los objetos Producto contra el catálogo.

    Complejidad temporal: O(L + N log N + k * T_busqueda).
    """
    if k <= 0 or not pedidos:
        return []

    frecuencias: dict[int, int] = {}
    for pedido in pedidos:
        for linea in pedido.lineas:
            frecuencias[linea.id_producto] = frecuencias.get(linea.id_producto, 0) + linea.cantidad

    if not frecuencias:
        return []

    # Ordenamiento completo de TODAS las frecuencias O(N log N)
    items_ordenados = sorted(
        frecuencias.items(),
        key=lambda item: (item[1], item[0]),
        reverse=True,
    )
    top_k_items = items_ordenados[:k]

    resultado: list[tuple[Producto, int]] = []
    for id_prod, total in top_k_items:
        prod = catalogo.buscar_por_id(id_prod)
        if prod is not None:
            resultado.append((prod, total))

    return resultado


def calcular_top_solicitados_heap(
    pedidos: Sequence[Pedido],
    catalogo,
    k: int = 10,
) -> list[tuple[Producto, int]]:
    """Calcula los k productos más solicitados utilizando un Min/Max Heap (Optimizado).

    Estrategia algorítmica:
    1. Agrega las cantidades demandadas en un mapa hash O(1).
    2. Utiliza heapq.nlargest para mantener un montículo acotado de tamaño k.
       Para cada uno de los N elementos, la inserción/reemplazo en el heap cuesta O(log k).
    3. Resuelve los objetos Producto contra el catálogo (en O(1) si es CatalogoHash).

    Complejidad temporal: O(L + N log k + k * T_busqueda).
    Ventaja: Cuando k << N, O(N log k) reduce drásticamente las comparaciones
    frente a O(N log N) y solo almacena k elementos en la estructura de selección.
    """
    if k <= 0 or not pedidos:
        return []

    frecuencias: dict[int, int] = {}
    for pedido in pedidos:
        for linea in pedido.lineas:
            frecuencias[linea.id_producto] = frecuencias.get(linea.id_producto, 0) + linea.cantidad

    if not frecuencias:
        return []

    # Selección óptima mediante heap O(N log k)
    top_k_items = heapq.nlargest(
        k,
        frecuencias.items(),
        key=lambda item: (item[1], item[0]),
    )

    resultado: list[tuple[Producto, int]] = []
    for id_prod, total in top_k_items:
        prod = catalogo.buscar_por_id(id_prod)
        if prod is not None:
            resultado.append((prod, total))

    return resultado


def calcular_top_solicitados(
    pedidos: Sequence[Pedido],
    catalogo,
    k: int = 10,
    metodo: str = "heap",
) -> list[tuple[Producto, int]]:
    """Función de conveniencia para invocar el cálculo de Top-N según la estrategia."""
    if metodo.lower() == "heap":
        return calcular_top_solicitados_heap(pedidos, catalogo, k)
    return calcular_top_solicitados_lineal(pedidos, catalogo, k)
