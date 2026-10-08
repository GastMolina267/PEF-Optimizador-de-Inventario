"""Pruebas unitarias para CatalogoLineal (Baseline)."""

from __future__ import annotations

import pytest

from src.inventario.catalogo_lineal import CatalogoLineal
from src.modelos.producto import Producto


class TestCatalogoLineal:
    def test_busqueda_por_id_existente_e_inexistente(
        self, catalogo_lineal_muestra: CatalogoLineal
    ):
        prod = catalogo_lineal_muestra.buscar_por_id(1)
        assert prod is not None
        assert prod.nombre == "Taladro Percutor 750W"

        prod_inexistente = catalogo_lineal_muestra.buscar_por_id(999)
        assert prod_inexistente is None

    def test_busqueda_por_nombre_parcial_case_insensitive(
        self, catalogo_lineal_muestra: CatalogoLineal
    ):
        res = catalogo_lineal_muestra.buscar_por_nombre("taladro")
        assert len(res) == 1
        assert res[0].id == 1

        res_vacio = catalogo_lineal_muestra.buscar_por_nombre("inexistente")
        assert len(res_vacio) == 0

    def test_busqueda_por_categoria(self, catalogo_lineal_muestra: CatalogoLineal):
        herramientas = catalogo_lineal_muestra.buscar_por_categoria("Herramientas")
        assert len(herramientas) == 3

        pinturas = catalogo_lineal_muestra.buscar_por_categoria("Pinturas")
        assert len(pinturas) == 3

    def test_agregar_y_actualizar_stock(self, catalogo_lineal_muestra: CatalogoLineal):
        nuevo = Producto(id=99, nombre="Lija Fina", categoria="Abrasivos", stock=50, precio=120.0)
        catalogo_lineal_muestra.agregar(nuevo)
        assert catalogo_lineal_muestra.buscar_por_id(99) is not None

        exito = catalogo_lineal_muestra.actualizar_stock(99, 40)
        assert exito is True
        assert catalogo_lineal_muestra.buscar_por_id(99).stock == 40

        exito_inexistente = catalogo_lineal_muestra.actualizar_stock(9999, 10)
        assert exito_inexistente is False

    def test_actualizar_stock_invalido(self, catalogo_lineal_muestra: CatalogoLineal):
        with pytest.raises(ValueError, match="no puede ser negativo"):
            catalogo_lineal_muestra.actualizar_stock(1, -5)

    def test_catalogo_lineal_agregar_duplicado(self):
        cat = CatalogoLineal([Producto(id=1, nombre="P", categoria="C", stock=1, precio=10.0)])
        with pytest.raises(ValueError, match="Conflicto de identificador"):
            cat.agregar(Producto(id=1, nombre="Otro", categoria="C", stock=1, precio=10.0))
