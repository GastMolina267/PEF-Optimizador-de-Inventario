"""Pruebas unitarias para la Etapa 4 (Interfaz de Usuario en Flet).

Verifica:
1. Instanciación y renderizado de componentes de tema y badges accesibles.
2. Inicialización del PanelEstado y callbacks de control de estrategia.
3. Inicialización correcta de las 7 pantallas:
   - PantallaInicio
   - PantallaCatalogo
   - PantallaPedidos
   - PantallaAgrupacion
   - PantallaTopProductos
   - PantallaAlternativas
   - PantallaComparacion
4. Integración fluida entre la fachada MotorInventario y la capa UI.
"""

from __future__ import annotations

from pathlib import Path

import flet as ft
import pytest

from src.motor.motor_inventario import MotorInventario
from src.ui.componentes.panel_estado import PanelEstado
from src.ui.pantallas.agrupacion import PantallaAgrupacion
from src.ui.pantallas.alternativas import PantallaAlternativas
from src.ui.pantallas.catalogo import PantallaCatalogo
from src.ui.pantallas.comparacion import PantallaComparacion
from src.ui.pantallas.inicio import PantallaInicio
from src.ui.pantallas.pedidos import PantallaPedidos
from src.ui.pantallas.top_productos import PantallaTopProductos
from src.ui.tema import (
    crear_badge_estado,
    crear_tarjeta_kpi,
)

BASE_DIR = Path(__file__).resolve().parent.parent
DATASETS_DIR = BASE_DIR / "data" / "datasets"


@pytest.fixture
def motor_cargado() -> MotorInventario:
    motor = MotorInventario(estrategia="baseline")
    ruta = DATASETS_DIR / "demo_oral.json"
    motor.cargar_dataset(ruta)
    return motor


class TestTemaYComponentes:
    """Verifica la generación de componentes visuales accesibles."""

    def test_creacion_badges_accesibles(self):
        b_cubierto = crear_badge_estado("cubierto")
        assert isinstance(b_cubierto, ft.Container)

        b_parcial = crear_badge_estado("parcial")
        assert isinstance(b_parcial, ft.Container)

        b_imposible = crear_badge_estado("imposible")
        assert isinstance(b_imposible, ft.Container)

    def test_creacion_tarjeta_kpi(self):
        card = crear_tarjeta_kpi(
            titulo="Total Pedidos",
            valor="150",
            subtitulo="Escenario mediano",
            icono=ft.Icons.SHOPPING_BAG,
        )
        assert isinstance(card, ft.Container)

    def test_panel_estado_callbacks(self, motor_cargado: MotorInventario):
        estrategia_recibida = []

        def callback_estrategia(nueva: str):
            estrategia_recibida.append(nueva)

        panel = PanelEstado(on_cambiar_estrategia=callback_estrategia)
        assert isinstance(panel, ft.Container)

        panel._elegir("optimizado")
        assert estrategia_recibida == ["optimizado"]


class TestPantallasInstanciacion:
    """Verifica que las 7 pantallas se inicialicen e interactúen con el motor sin errores."""

    def test_pantalla_inicio(self, motor_cargado: MotorInventario):
        pantalla = PantallaInicio(
            motor=motor_cargado,
            on_actualizar_panel=lambda **kw: None,
            notificar=lambda *a, **kw: None,
        )
        assert len(pantalla.fila_kpis.controls) == 4
        # Probar ejecución de escenario
        pantalla._ejecutar_escenario_completo()
        assert len(pantalla.col_resultado_escenario.controls) >= 3

    def test_pantalla_catalogo(self, motor_cargado: MotorInventario):
        pantalla = PantallaCatalogo(
            motor=motor_cargado,
            on_actualizar_panel=lambda **kw: None,
            notificar=lambda *a, **kw: None,
        )
        assert len(pantalla.col_productos.controls) > 0
        # Probar búsqueda por texto
        pantalla.input_busqueda.value = "taladro"
        pantalla._ejecutar_busqueda()
        assert (
            "taladro" in pantalla.txt_tiempo_busqueda.value.lower()
            or "tiempo" in pantalla.txt_tiempo_busqueda.value.lower()
        )

    def test_pantalla_pedidos(self, motor_cargado: MotorInventario):
        pantalla = PantallaPedidos(
            motor=motor_cargado,
            on_actualizar_panel=lambda **kw: None,
            notificar=lambda *a, **kw: None,
        )
        # Ejecutar procesamiento
        pantalla._ejecutar_procesamiento()
        assert len(pantalla.col_pedidos.controls) == 8

    def test_pantalla_agrupacion(self, motor_cargado: MotorInventario):
        pantalla = PantallaAgrupacion(
            motor=motor_cargado,
            on_actualizar_panel=lambda **kw: None,
            notificar=lambda *a, **kw: None,
        )
        assert len(pantalla.col_items_picking.controls) > 0

    def test_pantalla_top_productos(self, motor_cargado: MotorInventario):
        pantalla = PantallaTopProductos(
            motor=motor_cargado,
            on_actualizar_panel=lambda **kw: None,
            notificar=lambda *a, **kw: None,
        )
        assert len(pantalla.col_ranking.controls) <= 5

    def test_pantalla_alternativas(self, motor_cargado: MotorInventario):
        pantalla = PantallaAlternativas(
            motor=motor_cargado,
            on_actualizar_panel=lambda **kw: None,
            notificar=lambda *a, **kw: None,
        )
        assert len(pantalla.fila_kpis.controls) == 4

    def test_pantalla_comparacion(self, motor_cargado: MotorInventario):
        pantalla = PantallaComparacion(
            motor=motor_cargado,
            on_actualizar_panel=lambda **kw: None,
            notificar=lambda *a, **kw: None,
        )
        # Ejecutar comparativa
        pantalla._ejecutar_comparativa()
        assert len(pantalla.col_tabla_comparativa.controls) == 4

    def test_app_main_inicializacion(self):
        """Verifica que la función main arme la estructura completa en una Page."""
        from unittest.mock import MagicMock

        from src.ui.app import main

        mock_page = MagicMock()
        mock_page.controls = []
        mock_page.add = lambda ctrl: mock_page.controls.append(ctrl)
        mock_page.update = MagicMock()

        main(mock_page)

        assert len(mock_page.controls) == 1
        col_principal = mock_page.controls[0]
        assert len(col_principal.controls) == 2  # panel_estado y cuerpo_principal
