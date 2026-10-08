"""Módulo de catálogos de inventario."""

from src.inventario.catalogo_hash import CatalogoHash
from src.inventario.catalogo_lineal import CatalogoLineal
from src.inventario.protocolo import Catalogo

__all__ = ["Catalogo", "CatalogoLineal", "CatalogoHash"]
