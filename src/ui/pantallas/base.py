"""Módulo con la clase base para las pantallas de la interfaz gráfica Flet."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import flet as ft

from src.motor.motor_inventario import MotorInventario
from src.ui.tema import COLOR_FONDO_APP, padding_symmetric


class PantallaBase(ft.Container):
    """Clase base para las vistas de la aplicación.

    Unifica la inicialización del contenedor, la inyección de dependencias
    (motor, callbacks de notificación y panel de estado) y estilos visuales comunes.
    """

    def __init__(
        self,
        motor: MotorInventario,
        on_actualizar_panel: Callable[[], None] | Any,
        notificar: Callable[..., None] | Any,
        pad_h: int = 16,
        pad_v: int = 12,
    ) -> None:
        super().__init__()
        self.motor = motor
        self.on_actualizar_panel = on_actualizar_panel
        self.notificar = notificar
        self.expand = True
        self.bgcolor = COLOR_FONDO_APP
        self.padding = padding_symmetric(horizontal=pad_h, vertical=pad_v)

    def al_cambiar_estrategia_global(self, nueva_estrategia: str) -> None:
        """Callback invocado cuando el usuario cambia la estrategia desde el panel global."""
        pass
