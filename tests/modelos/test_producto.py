"""Pruebas unitarias para el modelo Producto."""

from __future__ import annotations

import pytest

from src.modelos.producto import Producto


class TestProducto:
    def test_creacion_producto_valido(self):
        p = Producto(id=1, nombre="Taladro", categoria="Herramientas", stock=10, precio=1500.50)
        assert p.id == 1
        assert p.nombre == "Taladro"
        assert p.categoria == "Herramientas"
        assert p.stock == 10
        assert p.precio == 1500.50

    def test_validaciones_producto_invalido(self):
        with pytest.raises(ValueError, match="identificador"):
            Producto(id=0, nombre="Taladro", categoria="Herramientas", stock=10, precio=10.0)
        with pytest.raises(ValueError, match="nombre"):
            Producto(id=1, nombre="   ", categoria="Herramientas", stock=10, precio=10.0)
        with pytest.raises(ValueError, match="categoría"):
            Producto(id=1, nombre="Taladro", categoria="", stock=10, precio=10.0)
        with pytest.raises(ValueError, match="stock"):
            Producto(id=1, nombre="Taladro", categoria="Herramientas", stock=-1, precio=10.0)
        with pytest.raises(ValueError, match="precio"):
            Producto(id=1, nombre="Taladro", categoria="Herramientas", stock=10, precio=-5.0)

    def test_producto_clonar_y_serializacion(self):
        p = Producto(id=1, nombre="Taladro", categoria="Herramientas", stock=5, precio=150.0)
        clon = p.clonar()
        assert clon.id == p.id
        assert clon.nombre == p.nombre
        assert clon.stock == p.stock
        assert clon is not p

        d = p.a_diccionario()
        reconstruido = Producto.desde_diccionario(d)
        assert reconstruido == p

    def test_producto_validaciones_exhaustivas(self):
        with pytest.raises(ValueError, match="entero positivo"):
            Producto(id=-5, nombre="P", categoria="C", stock=1, precio=10.0)
        with pytest.raises(ValueError, match="vacío"):
            Producto(id=1, nombre="  ", categoria="C", stock=1, precio=10.0)
        with pytest.raises(ValueError, match="vacía"):
            Producto(id=1, nombre="P", categoria="  ", stock=1, precio=10.0)
        with pytest.raises(ValueError, match="mayor o igual a 0"):
            Producto(id=1, nombre="P", categoria="C", stock=-2, precio=10.0)
        with pytest.raises(ValueError, match="mayor o igual a 0.0"):
            Producto(id=1, nombre="P", categoria="C", stock=1, precio=-10.0)
