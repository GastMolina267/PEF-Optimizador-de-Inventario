"""Pruebas unitarias para el componente PanelEstado."""

from __future__ import annotations

from pathlib import Path

import flet as ft

from src.motor.motor_inventario import MotorInventario
from src.ui.componentes.panel_estado import PanelEstado
from src.ui.pantallas.top_productos import PantallaTopProductos

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEMO_ORAL = BASE_DIR / "data" / "datasets" / "demo_oral.json"


class TestPanelEstado:
    def test_panel_estado_callbacks(self):
        estrategia_recibida = []

        def callback_estrategia(nueva: str):
            estrategia_recibida.append(nueva)

        panel = PanelEstado(on_cambiar_estrategia=callback_estrategia)
        assert isinstance(panel, ft.Container)

        panel._elegir("optimizado")
        assert estrategia_recibida == ["optimizado"]

    def test_publicar_resultado_completa_el_panel(self):
        motor = MotorInventario(estrategia="optimizado")
        motor.cargar_dataset(DEMO_ORAL)
        recibido: dict = {}
        pantalla = PantallaTopProductos(
            motor=motor, on_actualizar_panel=lambda **kw: recibido.update(kw), notificar=print
        )
        pantalla._publicar_resultado(tiempo_ms=1.5, resultado_negocio="ok")
        assert recibido == {
            "dataset": "activo",
            "n_productos": len(motor.catalogo),
            "n_pedidos": len(motor.pedidos),
            "estrategia": "optimizado",
            "tiempo_ms": 1.5,
            "resultado_negocio": "ok",
        }
