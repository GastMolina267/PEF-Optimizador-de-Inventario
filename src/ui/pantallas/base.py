"""Módulo con la clase base para las pantallas de la interfaz gráfica Flet."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import flet as ft

from src.motor.motor_inventario import MotorInventario
from src.ui.tema import COLOR_FONDO_APP, actualizar_control, padding_symmetric


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

        # Sentido de orden de las tablas. Cada pantalla fija su valor inicial antes de
        # crear el botón con _crear_boton_sentido_orden().
        self.orden_ascendente = True
        self.btn_sentido_orden: ft.IconButton | None = None

    def al_cambiar_estrategia_global(self, nueva_estrategia: str) -> None:
        """Callback invocado cuando el usuario cambia la estrategia desde el panel global."""

    def _publicar_resultado(
        self, tiempo_ms: float, resultado_negocio: str, dataset: str = "activo"
    ) -> None:
        """Actualiza el panel de estado con el tamaño del dataset y la última operación."""
        self.on_actualizar_panel(
            dataset=dataset,
            n_productos=len(self.motor.catalogo),
            n_pedidos=len(self.motor.pedidos),
            estrategia=self.motor.estrategia,
            tiempo_ms=tiempo_ms,
            resultado_negocio=resultado_negocio,
        )

    def _crear_boton_sentido_orden(self) -> ft.IconButton:
        """Crea el botón que alterna orden ascendente/descendente de la tabla."""
        self.btn_sentido_orden = ft.IconButton(on_click=lambda _: self._alternar_sentido_orden())
        self._refrescar_boton_sentido_orden()
        return self.btn_sentido_orden

    def _refrescar_boton_sentido_orden(self) -> None:
        """Ajusta ícono y tooltip del botón al sentido de orden actual."""
        if self.btn_sentido_orden is None:
            return
        if self.orden_ascendente:
            self.btn_sentido_orden.icon = ft.Icons.ARROW_UPWARD_ROUNDED
            self.btn_sentido_orden.tooltip = "Orden ascendente (clic para alternar)"
        else:
            self.btn_sentido_orden.icon = ft.Icons.ARROW_DOWNWARD_ROUNDED
            self.btn_sentido_orden.tooltip = "Orden descendente (clic para alternar)"

    def _alternar_sentido_orden(self) -> None:
        """Invierte el sentido de orden y vuelve a ordenar la tabla."""
        self.orden_ascendente = not self.orden_ascendente
        self._refrescar_boton_sentido_orden()
        actualizar_control(self.btn_sentido_orden)
        self._aplicar_ordenamiento()

    def _aplicar_ordenamiento(self) -> None:
        """Reordena la tabla de la pantalla. Lo redefinen las pantallas que tienen tabla."""
