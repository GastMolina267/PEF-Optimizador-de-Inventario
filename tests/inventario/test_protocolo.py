"""Pruebas de cumplimiento del protocolo Catalogo."""

from __future__ import annotations

import pytest

from src.inventario import Catalogo, CatalogoHash, CatalogoLineal


@pytest.mark.parametrize("clase", [CatalogoLineal, CatalogoHash])
def test_los_catalogos_cumplen_el_protocolo(clase):
    assert isinstance(clase(), Catalogo)
