"""Prueba de regresión que reproduce el error de concurrencia al descontar stock.

Fase F2: Red de seguridad antes de refactorizaciones.
Se marca con @pytest.mark.xfail(strict=True) conforme a docs/planificacion-parcial-2.md.
Cuando la fase F4 implemente la corrección (evaluar en workers y asignar en el proceso principal),
este test pasará como 'xpass', obligando al desarrollador a retirar la marca xfail.
"""

from __future__ import annotations

import pytest

from src.inventario.catalogo_hash import CatalogoHash
from src.inventario.catalogo_lineal import CatalogoLineal
from src.modelos.pedido import EstadoPedido, LineaPedido, Pedido
from src.modelos.producto import Producto
from src.pedidos.procesador_concurrente import procesar_pedidos_concurrente
from src.pedidos.procesador_secuencial import procesar_pedidos_secuencial


@pytest.mark.xfail(
    strict=True,
    reason="El procesador concurrente no respeta consumo secuencial de stock entre pedidos (se corrige en F4)",
)
def test_concurrencia_respeta_descuento_de_stock():
    """El procesamiento concurrente con descuento de stock debe ser idéntico al secuencial.

    Escenario:
    Producto #1 tiene 5 unidades de stock.
    Pedido #1 solicita 5 unidades.
    Pedido #2 solicita 5 unidades.

    Comportamiento esperado (secuencial):
    - Pedido #1: CUBIERTO (stock remanente: 0).
    - Pedido #2: IMPOSIBLE (faltante: 5 unidades).
    - Total cubiertos: 1, Total imposibles: 1.

    Falla actual en concurrente (bug detectado):
    Ambos pedidos se evalúan contra la misma instantánea estática del stock (5 unidades),
    reportando ambos pedidos como CUBIERTO (2 cubiertos), pese a que físicamente solo uno
    pudo descontar sus existencias.
    """
    prods_sec = [
        Producto(id=1, nombre="Taladro Percutor", categoria="Herramientas", stock=5, precio=500.0)
    ]
    prods_conc = [
        Producto(id=1, nombre="Taladro Percutor", categoria="Herramientas", stock=5, precio=500.0)
    ]

    pedidos = [
        Pedido(id=1, lineas=[LineaPedido(id_producto=1, cantidad=5)]),
        Pedido(id=2, lineas=[LineaPedido(id_producto=1, cantidad=5)]),
    ]

    cat_sec = CatalogoLineal(prods_sec)
    cat_conc = CatalogoHash(prods_conc)

    res_sec = procesar_pedidos_secuencial(
        cat_sec, pedidos, descontar_stock=True, politica_descuento="solo_cubiertos"
    )
    res_conc = procesar_pedidos_concurrente(
        cat_conc, pedidos, descontar_stock=True, politica_descuento="solo_cubiertos"
    )

    # 1. El stock físico remanente en ambos catálogos debe ser 0
    assert cat_sec.buscar_por_id(1).stock == 0
    assert cat_conc.buscar_por_id(1).stock == 0

    # 2. Las métricas cuantitativas deben coincidir
    assert res_conc.pedidos_cubiertos == res_sec.pedidos_cubiertos, (
        f"Concurrente cubrió {res_conc.pedidos_cubiertos} pedidos pero secuencial {res_sec.pedidos_cubiertos}"
    )
    assert res_conc.pedidos_imposibles == res_sec.pedidos_imposibles

    # 3. El estado de cada pedido individual debe ser equivalente
    estados_sec = [r.estado for r in res_sec.resultados]
    estados_conc = [r.estado for r in res_conc.resultados]
    assert estados_conc == estados_sec, (
        f"Estados difieren: concurrente={estados_conc} vs secuencial={estados_sec}"
    )
    assert estados_sec == [EstadoPedido.CUBIERTO, EstadoPedido.IMPOSIBLE]
