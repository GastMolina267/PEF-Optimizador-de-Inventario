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

    def test_instanciacion_y_autoevaluacion_inicial(self, motor_ui: MotorInventario) -> None:
        """Verifica controles iniciales, KPIs y evaluación automática con catálogo cargado."""
        panel_actualizado: dict[str, Any] = {}

        def mock_actualizar(**kw: Any) -> None:
            panel_actualizado.update(kw)

        pantalla = PantallaPrediccionIA(
            motor=motor_ui,
            on_actualizar_panel=mock_actualizar,
            notificar=lambda *a, **kw: None,
        )

        assert pantalla.dd_estrategia.value == EstrategiaPrediccion.HIBRIDA.value
        assert pantalla.dd_riesgo.value == "todos"
        assert pantalla.dd_orden.value == "probabilidad"
        assert pantalla.btn_ejecutar is not None
        assert pantalla.btn_entrenar is not None
        assert len(pantalla.resultados) == len(motor_ui.catalogo.obtener_todos())
        assert len(pantalla.lista_resultados.controls) == len(pantalla.resultados)
        assert isinstance(pantalla.kpi_latencia.content, ft.Column)
        assert isinstance(pantalla.kpi_memoria.content, ft.Column)
        txt_lat = pantalla.kpi_latencia.content.controls[1]
        txt_mem = pantalla.kpi_memoria.content.controls[1]
        assert isinstance(txt_lat, ft.Text) and isinstance(txt_mem, ft.Text)
        assert "µs" in str(txt_lat.value)
        assert "KB" in str(txt_mem.value)
        assert panel_actualizado.get("memoria_mb") is not None

    def test_filtrar_por_riesgo_y_estado_vacio(self, motor_ui: MotorInventario) -> None:
        """Verifica el filtrado interactivo por nivel de riesgo y el mensaje vacío."""
        pantalla = PantallaPrediccionIA(
            motor=motor_ui,
            on_actualizar_panel=lambda **kw: None,
            notificar=lambda *a, **kw: None,
        )
        total_inicial = len(pantalla.lista_resultados.controls)

        pantalla.dd_riesgo.value = "critico"
        pantalla._al_cambiar_filtro_riesgo(None)

        total_criticos = sum(1 for r in pantalla.resultados if r.riesgo.value == "critico")
        if total_criticos > 0:
            assert len(pantalla.lista_resultados.controls) == total_criticos
        else:
            assert len(pantalla.lista_resultados.controls) == 1
        assert len(pantalla.lista_resultados.controls) <= max(1, total_inicial)

    def test_conmutar_estrategia_y_ordenamiento(self, motor_ui: MotorInventario) -> None:
        """Verifica el cambio de estrategia en caliente y alternancia de orden."""
        pantalla = PantallaPrediccionIA(
            motor=motor_ui,
            on_actualizar_panel=lambda **kw: None,
            notificar=lambda *a, **kw: None,
        )

        pantalla.dd_estrategia.value = EstrategiaPrediccion.CONVENCIONAL.value
        pantalla._al_cambiar_estrategia(None)

        assert pantalla.estrategia_seleccionada == EstrategiaPrediccion.CONVENCIONAL
        assert all(r.estrategia == EstrategiaPrediccion.CONVENCIONAL for r in pantalla.resultados)

        pantalla.dd_orden.value = "stock"
        pantalla._al_cambiar_orden(None)
        inicial = pantalla.orden_ascendente
        pantalla._alternar_sentido_orden()
        assert pantalla.orden_ascendente is not inicial

    def test_reentrenar_modelo_ia_compatible_con_notificar_app(
        self, motor_ui: MotorInventario
    ) -> None:
        """Verifica que el botón de reentrenar use la firma real de notificar()."""
        mensajes_notificados: list[str] = []

        def mock_notificar(
            mensaje: str, icono: Any = ft.Icons.INFO_OUTLINE, color: str | None = None
        ) -> None:
            mensajes_notificados.append(mensaje)

        pantalla = PantallaPrediccionIA(
            motor=motor_ui,
            on_actualizar_panel=lambda **kw: None,
            notificar=mock_notificar,
        )

        pantalla._reentrenar_modelo(None)
        assert len(mensajes_notificados) >= 2
        assert any("Modelo entrenado" in m for m in mensajes_notificados)
        assert motor_ui.predictor_ia.modelo_ia.esta_entrenado is True
        assert "F1:" in pantalla._resumen_metricas_modelo

    def test_recargar_dataset_y_diagnostico_rutas(self, motor_ui: MotorInventario) -> None:
        """Verifica recarga de dataset y etiquetado de rutas de ejecución en cascada."""
        pantalla = PantallaPrediccionIA(
            motor=motor_ui,
            on_actualizar_panel=lambda **kw: None,
            notificar=lambda *a, **kw: None,
        )
        pantalla.al_recargar_dataset()
        assert len(pantalla.resultados) == len(motor_ui.catalogo.obtener_todos())
        assert "Cascada:" in str(pantalla.txt_resumen_tabla.value)
