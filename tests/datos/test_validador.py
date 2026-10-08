"""Pruebas unitarias para validación de datos e integridad referencial."""

from __future__ import annotations

import pytest

from src.datos.cargador import validar_dataset
from src.datos.validador import ValidadorDataset
from src.modelos.pedido import LineaPedido, Pedido
from src.modelos.producto import Producto


class TestValidador:
    def test_validacion_dataset_valido(
        self, productos_muestra: list[Producto], pedidos_muestra: list[Pedido]
    ):
        validador = ValidadorDataset(productos_muestra, pedidos_muestra)
        res = validador.validar_todo()
        assert res.es_valido is True
        assert len(res.errores) == 0

    def test_validacion_productos_duplicados(self):
        prods = [
            Producto(id=1, nombre="Taladro", categoria="Herramientas", stock=5, precio=100.0),
            Producto(id=1, nombre="Amoladora", categoria="Herramientas", stock=2, precio=200.0),
        ]
        validador = ValidadorDataset(prods, [])
        res = validador.validar_todo()
        assert res.es_valido is False
        assert any("duplicado" in e.lower() for e in res.errores)

    def test_validacion_pedidos_productos_inexistentes(self):
        prods = [Producto(id=1, nombre="Taladro", categoria="Herramientas", stock=5, precio=100.0)]
        peds = [Pedido(id=10, lineas=[LineaPedido(id_producto=999, cantidad=1)])]
        validador = ValidadorDataset(prods, peds)
        res = validador.validar_todo()
        assert res.es_valido is False
        assert any("no existe en catálogo" in e.lower() for e in res.errores)

    def test_validar_dataset_errores_estructura(self):
        with pytest.raises(ValueError, match="objeto JSON"):
            validar_dataset(["no_es_dict"])  # type: ignore
        with pytest.raises(ValueError, match="'productos'"):
            validar_dataset({"pedidos": []})
        with pytest.raises(ValueError, match="'pedidos'"):
            validar_dataset({"productos": []})
        with pytest.raises(ValueError, match="no es un objeto JSON"):
            validar_dataset({"productos": ["invalido"], "pedidos": []})
        with pytest.raises(ValueError, match="no es un objeto JSON"):
            validar_dataset({"productos": [], "pedidos": ["invalido"]})


class TestValidadorDiccionario:
    def test_id_de_producto_repetido(self):
        datos = {
            "productos": [
                {"id": 1, "nombre": "A", "categoria": "C", "stock": 1, "precio": 1.0},
                {"id": 1, "nombre": "B", "categoria": "C", "stock": 1, "precio": 1.0},
            ],
            "pedidos": [],
        }
        with pytest.raises(ValueError, match="producto duplicado en dataset: #1"):
            ValidadorDataset.validar_diccionario(datos)

    def test_pedido_que_no_es_objeto(self):
        datos = {"productos": [], "pedidos": ["no soy un pedido"]}
        with pytest.raises(ValueError, match="El pedido en la posición 0"):
            ValidadorDataset.validar_diccionario(datos)
