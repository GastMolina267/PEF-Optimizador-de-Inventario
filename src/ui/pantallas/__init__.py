"""Vistas y pantallas de la interfaz de usuario en Flet."""

from src.ui.pantallas.agrupacion import PantallaAgrupacion
from src.ui.pantallas.alternativas import PantallaAlternativas
from src.ui.pantallas.base import PantallaBase
from src.ui.pantallas.catalogo import PantallaCatalogo
from src.ui.pantallas.comparacion import PantallaComparacion
from src.ui.pantallas.inicio import PantallaInicio
from src.ui.pantallas.pedidos import PantallaPedidos
from src.ui.pantallas.top_productos import PantallaTopProductos

__all__ = [
    "PantallaBase",
    "PantallaInicio",
    "PantallaCatalogo",
    "PantallaPedidos",
    "PantallaAgrupacion",
    "PantallaTopProductos",
    "PantallaAlternativas",
    "PantallaComparacion",
]
