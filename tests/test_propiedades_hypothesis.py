"""Pruebas de propiedades con Hypothesis (Fase F2: Red de seguridad).

Verifica equivalencia matemática y funcional estricta entre las estructuras
y algoritmos baseline y optimizados frente a combinaciones arbitrarias de datos:
1. Búsqueda por ID y por nombre: CatalogoLineal vs. CatalogoHash.
2. Ranking Top-N: calcular_top_solicitados_lineal vs. calcular_top_solicitados_heap.
3. Agrupación Batch Picking: agrupar_pedidos_batch vs. acumulación independiente.
4. Procesamiento sin descuento: procesar_pedidos_secuencial vs. procesar_pedidos_concurrente.
"""

from __future__ import annotations

import hypothesis.strategies as st
from hypothesis import given, settings

from src.inventario.catalogo_hash import CatalogoHash
from src.inventario.catalogo_lineal import CatalogoLineal
from src.modelos.pedido import LineaPedido, Pedido
from src.modelos.producto import Producto
from src.pedidos.agrupador import agrupar_pedidos_batch
from src.pedidos.procesador_concurrente import procesar_pedidos_concurrente
from src.pedidos.procesador_secuencial import procesar_pedidos_secuencial
from src.ranking.top_productos import (
    calcular_top_solicitados_heap,
    calcular_top_solicitados_lineal,
)

# Estrategias generativas de Hypothesis
CATEGORIAS = ["Herramientas", "Pinturas", "Electricidad", "Seguridad", "Plomería"]
ALFABETO = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


@st.composite
def producto_valido(draw, id_fijo: int | None = None) -> Producto:
    pid = id_fijo if id_fijo is not None else draw(st.integers(min_value=1, max_value=2000))
    palabra1 = draw(st.text(alphabet=ALFABETO, min_size=3, max_size=10))
    palabra2 = draw(st.text(alphabet=ALFABETO, min_size=3, max_size=10))
    nombre = f"{palabra1} {palabra2}"
    categoria = draw(st.sampled_from(CATEGORIAS))
    stock = draw(st.integers(min_value=0, max_value=200))
    precio = round(draw(st.floats(min_value=10.0, max_value=50000.0)), 2)
    return Producto(id=pid, nombre=nombre, categoria=categoria, stock=stock, precio=precio)


@st.composite
def lista_productos_unicos(
    draw, min_size: int = 2, max_size: int = 25
) -> list[Producto]:
    n = draw(st.integers(min_value=min_size, max_value=max_size))
    # Generar IDs correlativos y únicos garantizados
    prods = [draw(producto_valido(id_fijo=i)) for i in range(1, n + 1)]
    return prods


@st.composite
def lista_pedidos_sobre_productos(
    draw, productos: list[Producto], min_pedidos: int = 1, max_pedidos: int = 15
) -> list[Pedido]:
    ids_disponibles = [p.id for p in productos]
    n_pedidos = draw(st.integers(min_value=min_pedidos, max_value=max_pedidos))
    pedidos: list[Pedido] = []

    for id_pedido in range(1, n_pedidos + 1):
        num_lineas = draw(st.integers(min_value=1, max_value=min(5, len(ids_disponibles))))
        ids_elegidos = draw(
            st.lists(
                st.sampled_from(ids_disponibles),
                min_size=num_lineas,
                max_size=num_lineas,
                unique=True,
            )
        )
        lineas = [
            LineaPedido(id_producto=pid, cantidad=draw(st.integers(min_value=1, max_value=20)))
            for pid in ids_elegidos
        ]
        pedidos.append(Pedido(id=id_pedido, lineas=lineas))

    return pedidos


# =========================================================================
# Propiedades de equivalencia
# =========================================================================


@settings(max_examples=30, deadline=None)
@given(prods=lista_productos_unicos(min_size=3, max_size=20), consulta_id=st.integers(min_value=1, max_value=30))
def test_propiedad_busqueda_por_id_y_nombre(prods: list[Producto], consulta_id: int):
    """Para cualquier catálogo arbitrario, las búsquedas por ID y nombre son idénticas."""
    cat_lineal = CatalogoLineal([p.clonar() for p in prods])
    cat_hash = CatalogoHash([p.clonar() for p in prods])

    # 1. Búsqueda por ID
    res_lin_id = cat_lineal.buscar_por_id(consulta_id)
    res_hash_id = cat_hash.buscar_por_id(consulta_id)
    if res_lin_id is None:
        assert res_hash_id is None
    else:
        assert res_hash_id is not None
        assert res_lin_id.id == res_hash_id.id
        assert res_lin_id.nombre == res_hash_id.nombre

    # 2. Búsqueda por texto (primer palabra del primer producto)
    termino = prods[0].nombre.split()[0].lower()
    ids_lin = {p.id for p in cat_lineal.buscar_por_nombre(termino)}
    ids_hash = {p.id for p in cat_hash.buscar_por_nombre(termino)}
    assert ids_lin == ids_hash


@settings(max_examples=25, deadline=None)
@given(data=st.data())
def test_propiedad_top_n_sort_vs_heap(data):
    """calcular_top_solicitados_lineal y calcular_top_solicitados_heap producen idéntico ranking."""
    prods = data.draw(lista_productos_unicos(min_size=5, max_size=20))
    pedidos = data.draw(lista_pedidos_sobre_productos(prods, min_pedidos=2, max_pedidos=10))
    k = data.draw(st.integers(min_value=1, max_value=10))

    cat_lineal = CatalogoLineal([p.clonar() for p in prods])
    cat_hash = CatalogoHash([p.clonar() for p in prods])

    top_sort = calcular_top_solicitados_lineal(pedidos, cat_lineal, k=k)
    top_heap = calcular_top_solicitados_heap(pedidos, cat_hash, k=k)

    assert len(top_sort) == len(top_heap)
    # Verificar frecuencias y productos ordenados
    for (p_sort, frec_sort), (p_heap, frec_heap) in zip(top_sort, top_heap, strict=True):
        assert frec_sort == frec_heap
        assert p_sort.id == p_heap.id


@settings(max_examples=25, deadline=None)
@given(data=st.data())
def test_propiedad_agrupacion_batch_picking(data):
    """agrupar_pedidos_batch totaliza exactamente la demanda de todas las líneas."""
    prods = data.draw(lista_productos_unicos(min_size=3, max_size=15))
    pedidos = data.draw(lista_pedidos_sobre_productos(prods, min_pedidos=1, max_pedidos=10))

    cat_hash = CatalogoHash([p.clonar() for p in prods])
    lote = agrupar_pedidos_batch(pedidos, cat_hash)

    # Suma total de unidades
    suma_esperada = sum(lp.cantidad for p in pedidos for lp in p.lineas)
    assert lote.total_unidades == suma_esperada
    assert lote.total_pedidos == len(pedidos)

    # Cada ítem consolidado debe sumar exactamente las demandas de sus pedidos
    for item in lote.items:
        demanda_manual = sum(
            lp.cantidad
            for p in pedidos
            for lp in p.lineas
            if lp.id_producto == item.id_producto
        )
        assert item.cantidad_total == demanda_manual


@settings(max_examples=20, deadline=None)
@given(data=st.data())
def test_propiedad_procesamiento_secuencial_vs_concurrente_sin_descuento(data):
    """Sin descuento de stock, el procesamiento secuencial y concurrente arrojan resultados idénticos."""
    prods = data.draw(lista_productos_unicos(min_size=3, max_size=15))
    pedidos = data.draw(lista_pedidos_sobre_productos(prods, min_pedidos=1, max_pedidos=8))

    cat_lineal = CatalogoLineal([p.clonar() for p in prods])
    cat_hash = CatalogoHash([p.clonar() for p in prods])

    res_sec = procesar_pedidos_secuencial(cat_lineal, pedidos, descontar_stock=False)
    res_conc = procesar_pedidos_concurrente(cat_hash, pedidos, descontar_stock=False)

    assert res_sec.pedidos_procesados == res_conc.pedidos_procesados
    assert res_sec.pedidos_cubiertos == res_conc.pedidos_cubiertos
    assert res_sec.pedidos_parciales == res_conc.pedidos_parciales
    assert res_sec.pedidos_imposibles == res_conc.pedidos_imposibles

    for p_sec, p_conc in zip(res_sec.resultados, res_conc.resultados, strict=True):
        assert p_sec.id_pedido == p_conc.id_pedido
        assert p_sec.estado == p_conc.estado
