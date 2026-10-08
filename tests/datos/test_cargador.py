"""Pruebas unitarias para cargador de datasets JSON."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.datos.cargador import (
    cargar_dataset_json,
    guardar_dataset_json,
)
from src.modelos.pedido import LineaPedido, Pedido
from src.modelos.producto import Producto

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATASETS_DIR = BASE_DIR / "data" / "datasets"


class TestCargador:
    def test_cargar_dataset_demo_oral(self):
        prods, peds = cargar_dataset_json(DATASETS_DIR / "demo_oral.json")
        assert len(prods) == 30
        assert len(peds) == 8
        assert all(isinstance(p, Producto) for p in prods)
        assert all(isinstance(ped, Pedido) for ped in peds)

    def test_guardar_y_cargar_dataset_roundtrip(self, tmp_path: Path):
        prods = [Producto(id=1, nombre="Taladro", categoria="Herramientas", stock=5, precio=100.0)]
        peds = [Pedido(id=10, lineas=[LineaPedido(id_producto=1, cantidad=2)])]
        ruta = tmp_path / "dataset_test.json"

        guardar_dataset_json(ruta, prods, peds)
        assert ruta.is_file()

        cargados_prods, cargados_peds = cargar_dataset_json(ruta)
        assert cargados_prods == prods
        assert cargados_peds == peds

    def test_archivo_inexistente_lanza_error(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            cargar_dataset_json(tmp_path / "no_existe.json")

    def test_cargar_dataset_json_invalido(self, tmp_path: Path):
        corrupto = tmp_path / "corrupto.json"
        corrupto.write_text("{ esto no es json valido", encoding="utf-8")
        with pytest.raises(ValueError, match="JSON"):
            cargar_dataset_json(corrupto)

        no_dicc = tmp_path / "lista.json"
        no_dicc.write_text("[]", encoding="utf-8")
        with pytest.raises(ValueError, match="objeto"):
            cargar_dataset_json(no_dicc)
