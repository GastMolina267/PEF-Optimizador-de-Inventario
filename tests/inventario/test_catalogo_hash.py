"""Pruebas unitarias para CatalogoHash (Optimizado)."""

from __future__ import annotations

import pytest

from src.inventario.catalogo_hash import CatalogoHash
from src.modelos.producto import Producto


class TestCatalogoHash:
    def test_busqueda_por_id_en_tiempo_constante(self, catalogo_hash_muestra: CatalogoHash):
        prod = catalogo_hash_muestra.buscar_por_id(1)
        assert prod is not None
        assert prod.nombre == "Taladro Percutor 750W"

        assert catalogo_hash_muestra.buscar_por_id(999) is None

    def test_busqueda_por_categoria_mediante_indice_invertido(
        self, catalogo_hash_muestra: CatalogoHash
    ):
        herramientas = catalogo_hash_muestra.buscar_por_categoria("Herramientas")
        assert len(herramientas) == 3
        ids_esperados = {1, 2, 3}
        assert {p.id for p in herramientas} == ids_esperados

        assert catalogo_hash_muestra.buscar_por_categoria("Inexistente") == []

    def test_busqueda_por_nombre_y_consistencia_al_agregar(
        self, catalogo_hash_muestra: CatalogoHash
    ):
        res = catalogo_hash_muestra.buscar_por_nombre("amoladora")
        assert len(res) == 1
        assert res[0].id == 2

        nuevo = Producto(
            id=99,
            nombre="Amoladora Recta",
            categoria="Herramientas",
            stock=10,
            precio=8500.0,
        )
        catalogo_hash_muestra.agregar(nuevo)

        assert catalogo_hash_muestra.buscar_por_id(99) == nuevo
        res_post = catalogo_hash_muestra.buscar_por_nombre("amoladora")
        assert len(res_post) == 2
        assert len(catalogo_hash_muestra.buscar_por_categoria("Herramientas")) == 4

    def test_actualizar_stock_y_validaciones(self, catalogo_hash_muestra: CatalogoHash):
        assert catalogo_hash_muestra.actualizar_stock(1, 25) is True
        assert catalogo_hash_muestra.buscar_por_id(1).stock == 25
        assert catalogo_hash_muestra.actualizar_stock(999, 10) is False

        with pytest.raises(ValueError, match="no puede ser negativo"):
            catalogo_hash_muestra.actualizar_stock(1, -1)

    def test_catalogo_hash_agregar_duplicado(self):
        cat = CatalogoHash([Producto(id=1, nombre="P", categoria="C", stock=1, precio=10.0)])
        with pytest.raises(ValueError, match="Conflicto de identificador"):
            cat.agregar(Producto(id=1, nombre="Otro", categoria="C", stock=1, precio=10.0))
