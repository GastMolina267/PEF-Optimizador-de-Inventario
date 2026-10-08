"""Pruebas unitarias para componentes visuales, tokens de diseño y tema de la UI."""

from __future__ import annotations

import flet as ft

from src.ui.tema import (
    crear_badge_estado,
    crear_badge_tiempo,
    crear_banner_explicativo,
    crear_dialogo_explicativo_modos,
    crear_dropdown,
    crear_tarjeta_kpi,
    formatear_tiempo_ms,
)


class TestTemaYComponentes:
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
        )
        assert isinstance(card, ft.Container)


class TestComponentesTemaPostEtapas:
    def test_badge_tiempo_formatos(self):
        b_fraccion_ms = crear_badge_tiempo(0.042)
        assert isinstance(b_fraccion_ms, ft.Container)

        b_mili = crear_badge_tiempo(12.5, speedup=24.5)
        assert isinstance(b_mili, ft.Container)

    def test_formatear_tiempo_siempre_en_ms(self):
        assert formatear_tiempo_ms(0.042).endswith(" ms")
        assert "µs" not in formatear_tiempo_ms(0.042)
        assert formatear_tiempo_ms(12.5) == "12.50 ms"

    def test_banner_explicativo(self):
        banner = crear_banner_explicativo(
            titulo="Prueba Teórica",
            descripcion="Descripción de prueba",
            complejidad_base="O(n)",
            complejidad_opt="O(1)",
            por_que_importa="Razón de eficiencia",
        )
        assert isinstance(banner, ft.Container)

    def test_dialogo_explicativo_modos(self):
        page = ft.Page
        dlg = crear_dialogo_explicativo_modos(page)
        assert isinstance(dlg, ft.AlertDialog)

    def test_crear_dropdown_compatibilidad(self):
        dd = crear_dropdown(
            label="Test",
            options=[ft.dropdown.Option("1", "Uno")],
            value="1",
            on_change_callback=lambda _: None,
        )
        assert isinstance(dd, ft.Dropdown)
