"""Pruebas unitarias para las mejoras de Desarrollo Post-Etapas.

Verifica:
1. Funciones auxiliares de diseño: badge de tiempo, banner explicativo y diálogo modal.
2. Persistencia y ordenamiento multidimensional en Catálogo (nombre, precio, stock, id).
3. Despliegue interactivo (ExpansionTile) y auditoría de stock en Pedidos.
4. Ordenamiento en Agrupación, Top-N, Alternativas y Comparativa.
5. Reemplazo formal de la abreviatura 'uds' por 'Unidades en Stock'.
"""

from __future__ import annotations

from pathlib import Path

import flet as ft
import pytest

from src.motor.motor_inventario import MotorInventario
from src.ui.pantallas.agrupacion import PantallaAgrupacion
from src.ui.pantallas.alternativas import PantallaAlternativas
from src.ui.pantallas.catalogo import PantallaCatalogo
from src.ui.pantallas.comparacion import PantallaComparacion
from src.ui.pantallas.pedidos import PantallaPedidos
from src.ui.pantallas.top_productos import PantallaTopProductos
from src.ui.tema import (
    crear_badge_tiempo,
    crear_banner_explicativo,
    crear_dialogo_explicativo_modos,
    crear_dropdown,
    formatear_tiempo_ms,
)

BASE_DIR = Path(__file__).resolve().parent.parent
DATASETS_DIR = BASE_DIR / "data" / "datasets"


@pytest.fixture
def motor_activo() -> MotorInventario:
    motor = MotorInventario(estrategia="baseline")
    ruta = DATASETS_DIR / "demo_oral.json"
    motor.cargar_dataset(ruta)
    return motor


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


class TestOrdenamientoYDesplieguePantallas:
    def test_catalogo_ordenamiento_y_unidades_en_stock(self, motor_activo: MotorInventario):
        pantalla = PantallaCatalogo(motor_activo, lambda **kw: None, lambda *a, **kw: None)

        # Orden por precio ascendente
        pantalla.dropdown_orden.value = "precio"
        pantalla.orden_ascendente = True
        pantalla._aplicar_ordenamiento()
        precios = [p.precio for p in pantalla.productos_actuales]
        assert precios == sorted(precios)

        # Orden por precio descendente
        pantalla._alternar_sentido_orden()
        precios_desc = [p.precio for p in pantalla.productos_actuales]
        assert precios_desc == sorted(precios, reverse=True)

        # Verificar que los widgets usen 'Unidades en Stock'
        row = pantalla.col_productos.controls[0].content
        stock_badge = row.controls[3]
        texto_badge = stock_badge.content.value
        assert "Unidades en Stock" in texto_badge or "SIN STOCK" in texto_badge

    def test_pedidos_expansion_tile_y_ordenamiento(self, motor_activo: MotorInventario):
        pantalla = PantallaPedidos(motor_activo, lambda **kw: None, lambda *a, **kw: None)
        assert len(pantalla.col_pedidos.controls) == 8
        # Verificar que los ítems sean ExpansionTile desplegables
        assert all(isinstance(ctrl, ft.ExpansionTile) for ctrl in pantalla.col_pedidos.controls)

        # Procesar lote y verificar despliegue de cobertura
        pantalla._ejecutar_procesamiento()
        assert len(pantalla.col_pedidos.controls) == 8
        primer_tile = pantalla.col_pedidos.controls[0]
        assert isinstance(primer_tile, ft.ExpansionTile)
        assert len(primer_tile.controls) > 0  # Auditoría línea por línea

        # Orden por unidades demandadas
        pantalla.dropdown_orden.value = "unidades"
        pantalla.orden_ascendente = False
        pantalla._aplicar_ordenamiento()
        assert len(pantalla.col_pedidos.controls) == 8

    def test_agrupacion_ordenamiento(self, motor_activo: MotorInventario):
        pantalla = PantallaAgrupacion(motor_activo, lambda **kw: None, lambda *a, **kw: None)
        pantalla.dropdown_orden.value = "cantidad"
        pantalla.orden_ascendente = False
        pantalla._aplicar_ordenamiento()
        cantidades = [item.cantidad_total for item in pantalla.items_consolidados_actuales]
        assert cantidades == sorted(cantidades, reverse=True)

    def test_top_productos_ordenamiento(self, motor_activo: MotorInventario):
        pantalla = PantallaTopProductos(motor_activo, lambda **kw: None, lambda *a, **kw: None)
        pantalla.dropdown_orden.value = "demanda"
        pantalla.orden_ascendente = False
        pantalla._aplicar_ordenamiento()
        demandas = [cant for _, cant in pantalla.ranking_actual]
        assert demandas == sorted(demandas, reverse=True)

    def test_alternativas_ordenamiento_y_despliegue(self, motor_activo: MotorInventario):
        pantalla = PantallaAlternativas(motor_activo, lambda **kw: None, lambda *a, **kw: None)
        pantalla.dropdown_orden.value = "precio"
        pantalla.orden_ascendente = True
        pantalla._aplicar_ordenamiento()
        costos = [comb.costo_total for comb in pantalla.combinaciones_actuales]
        assert costos == sorted(costos)

        # Si hay combinaciones, deben ser ExpansionTile
        if pantalla.combinaciones_actuales:
            primer_item = pantalla.col_combinaciones.controls[0]
            assert isinstance(primer_item, ft.ExpansionTile)

    def test_comparacion_ordenamiento(self, motor_activo: MotorInventario):
        pantalla = PantallaComparacion(motor_activo, lambda **kw: None, lambda *a, **kw: None)
        pantalla._ejecutar_comparativa()
        assert len(pantalla.col_tabla_comparativa.controls) == 4

        # Ordenar por speedup
        pantalla.dropdown_orden.value = "speedup"
        pantalla.orden_ascendente = False
        pantalla._aplicar_ordenamiento()
        assert len(pantalla.col_tabla_comparativa.controls) == 4

    def test_alternativas_grande_no_recursion_error(self):
        """buscar_alternativas no desborda la pila con un dataset de 10.000 productos."""
        motor_grande = MotorInventario()
        motor_grande.cargar_dataset(DATASETS_DIR / "grande.json")
        res = motor_grande.buscar_alternativas("Ferretería y Herramientas", 45000.0)
        assert res.total_combinaciones > 0
        assert res.tiempo_ejecucion_ms < 50.0

    def test_catalogo_busqueda_por_id_y_boton_buscar(self, motor_activo: MotorInventario):
        pantalla = PantallaCatalogo(motor_activo, lambda **kw: None, lambda *a, **kw: None)
        pantalla.input_id.value = "1"
        pantalla.input_busqueda.value = ""
        pantalla._ejecutar_consulta()
        assert len(pantalla.productos_actuales) == 1
        assert pantalla.productos_actuales[0].id == 1

        pantalla.input_id.value = " 2 "
        pantalla._ejecutar_busqueda_id()
        assert len(pantalla.productos_actuales) == 1
        assert pantalla.productos_actuales[0].id == 2

    def test_catalogo_optimizado_lee_hits_sin_explotar(self, motor_activo: MotorInventario):
        motor_activo.cambiar_estrategia("optimizado")
        pantalla = PantallaCatalogo(motor_activo, lambda **kw: None, lambda *a, **kw: None)
        pantalla.input_busqueda.value = "taladro"
        pantalla.input_id.value = ""
        pantalla._ejecutar_consulta()
        pantalla._ejecutar_consulta()
        assert pantalla._hits_cache_busquedas() >= 1
        assert "HIT" in pantalla.txt_estado_cache.value

    def test_pedidos_optimizado_no_activa_processpool(self, motor_activo: MotorInventario):
        pantalla = PantallaPedidos(motor_activo, lambda **kw: None, lambda *a, **kw: None)
        assert pantalla.switch_concurrente.value is False
        pantalla.al_cambiar_estrategia_global("optimizado")
        assert pantalla.switch_concurrente.value is False

    def test_catalogo_badge_estrategia_sincronizacion(self, motor_activo: MotorInventario):
        """Verifica que el catálogo no duplique el switch y sincronice su badge informativo."""
        pantalla = PantallaCatalogo(motor_activo, lambda **kw: None, lambda *a, **kw: None)
        assert not hasattr(pantalla, "switch_estrategia_local")
        assert hasattr(pantalla, "badge_estrategia")

        pantalla.al_cambiar_estrategia_global("optimizado")
        assert "Hash O(1)" in pantalla.badge_estrategia.content.controls[1].value

        pantalla.al_cambiar_estrategia_global("baseline")
        assert "Lineal O(n)" in pantalla.badge_estrategia.content.controls[1].value

    def test_banner_no_clipping_wrap(self):
        """Verifica que el banner no use expand: eso abre un bloque gris en Flet."""
        banner = crear_banner_explicativo(
            titulo="Operación Crítica",
            descripcion="Descripción técnica amplia",
            complejidad_base="O(n) muy larga para prueba",
            complejidad_opt="O(1) altamente eficiente",
            por_que_importa="Evita clipping horizontal",
        )
        col = banner.content
        assert isinstance(col, ft.Column)
        chip_base = col.controls[1]
        chip_opt = col.controls[2]
        assert isinstance(chip_base, ft.Container)
        assert isinstance(chip_opt, ft.Container)
        assert not chip_base.expand
        assert not chip_opt.expand
        assert "Baseline" in chip_base.content.controls[0].value
        assert "Optimizado" in chip_opt.content.controls[0].value


def test_puntos_de_entrada_llaman_freeze_support():
    """El .exe de PyInstaller debe llamar freeze_support o ProcessPool abre N ventanas."""
    main_txt = (BASE_DIR / "main.py").read_text(encoding="utf-8")
    app_txt = (BASE_DIR / "src" / "ui" / "app.py").read_text(encoding="utf-8")
    assert "freeze_support()" in main_txt
    assert "freeze_support()" in app_txt
    bloque_main = main_txt.split('if __name__ == "__main__":', 1)[1]
    assert "freeze_support()" in bloque_main
    assert bloque_main.index("freeze_support()") < bloque_main.index("run()")
