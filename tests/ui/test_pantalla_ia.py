"""Pruebas unitarias para PantallaPrediccionIA de la interfaz Flet."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import flet as ft
import pytest

from src.datos.cargador import cargar_dataset_json
from src.ia.tipos import EstrategiaPrediccion
from src.motor.motor_inventario import EstrategiaMotor, MotorInventario
from src.ui.pantallas.prediccion_ia import PantallaPrediccionIA

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATASET_PATH = BASE_DIR / "data" / "datasets" / "demo_oral.json"


@pytest.fixture
def motor_ui() -> MotorInventario:
    """Instancia de MotorInventario configurada con el dataset demo_oral."""
    prods, peds = cargar_dataset_json(DATASET_PATH)
    return MotorInventario(productos=prods, pedidos=peds, estrategia=EstrategiaMotor.OPTIMIZADO)


class TestPantallaPrediccionIA:
    """Verifica el ciclo de vida, eventos y renderizado de la vista de IA."""

    def test_instanciacion_pantalla_ia(self, motor_ui: MotorInventario) -> None:
        """Verifica la construcción de controles iniciales y KPIs."""
        pantalla = PantallaPrediccionIA(
            motor=motor_ui,
            on_actualizar_panel=lambda **kw: None,
            notificar=lambda *a, **kw: None,
        )

        assert pantalla.dd_estrategia.value == EstrategiaPrediccion.HIBRIDA.value
        assert pantalla.dd_riesgo.value == "todos"
        assert pantalla.btn_ejecutar is not None
        assert pantalla.btn_entrenar is not None
        assert len(pantalla.tabla_resultados.rows) == 0

    def test_ejecutar_evaluacion_puebla_tabla_y_kpis(self, motor_ui: MotorInventario) -> None:
        """Verifica que al ejecutar evaluación se calculen predicciones y pueblen las filas."""
        panel_actualizado: dict[str, Any] = {}

        def mock_actualizar(**kw: Any) -> None:
            panel_actualizado.update(kw)

        pantalla = PantallaPrediccionIA(
            motor=motor_ui,
            on_actualizar_panel=mock_actualizar,
            notificar=lambda *a, **kw: None,
        )

        pantalla._ejecutar_evaluacion(None)

        assert len(pantalla.resultados) == len(motor_ui.catalogo.obtener_todos())
        assert len(pantalla.tabla_resultados.rows) == len(pantalla.resultados)
        assert isinstance(pantalla.kpi_latencia.content, ft.Column)
        assert isinstance(pantalla.kpi_memoria.content, ft.Column)
        txt_lat = pantalla.kpi_latencia.content.controls[1]
        txt_mem = pantalla.kpi_memoria.content.controls[1]
        assert isinstance(txt_lat, ft.Text) and isinstance(txt_mem, ft.Text)
        assert "µs" in str(txt_lat.value)
        assert "KB" in str(txt_mem.value)
        assert len(panel_actualizado) > 0

    def test_filtrar_por_riesgo(self, motor_ui: MotorInventario) -> None:
        """Verifica el filtrado interactivo por nivel de riesgo en la tabla."""
        pantalla = PantallaPrediccionIA(
            motor=motor_ui,
            on_actualizar_panel=lambda **kw: None,
            notificar=lambda *a, **kw: None,
        )
        pantalla._ejecutar_evaluacion(None)
        total_inicial = len(pantalla.tabla_resultados.rows)

        # Filtrar solo riesgo crítico
        pantalla.dd_riesgo.value = "critico"
        pantalla._al_cambiar_filtro_riesgo(None)

        total_criticos = sum(1 for r in pantalla.resultados if r.riesgo.value == "critico")
        assert len(pantalla.tabla_resultados.rows) == total_criticos
        assert len(pantalla.tabla_resultados.rows) <= total_inicial

    def test_conmutar_estrategia_actualiza_resultados(self, motor_ui: MotorInventario) -> None:
        """Verifica que al cambiar estrategia se actualice la estrategia en los resultados."""
        pantalla = PantallaPrediccionIA(
            motor=motor_ui,
            on_actualizar_panel=lambda **kw: None,
            notificar=lambda *a, **kw: None,
        )
        pantalla._ejecutar_evaluacion(None)

        pantalla.dd_estrategia.value = EstrategiaPrediccion.CONVENCIONAL.value
        pantalla._al_cambiar_estrategia(None)

        assert pantalla.estrategia_seleccionada == EstrategiaPrediccion.CONVENCIONAL
        assert all(
            r.estrategia == EstrategiaPrediccion.CONVENCIONAL for r in pantalla.resultados
        )

    def test_reentrenar_modelo_ia(self, motor_ui: MotorInventario) -> None:
        """Verifica que el botón de reentrenar ejecute el ajuste y notifique al usuario."""
        mensajes_notificados: list[str] = []

        def mock_notificar(msg: str, tipo: str = "info") -> None:
            mensajes_notificados.append(msg)

        pantalla = PantallaPrediccionIA(
            motor=motor_ui,
            on_actualizar_panel=lambda **kw: None,
            notificar=mock_notificar,
        )

        pantalla._reentrenar_modelo(None)
        assert len(mensajes_notificados) >= 2
        assert any("Modelo entrenado" in m for m in mensajes_notificados)
        assert motor_ui.predictor_ia.modelo_ia.esta_entrenado is True
