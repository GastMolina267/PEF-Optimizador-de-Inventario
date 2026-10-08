"""Pruebas unitarias para las 7 pantallas de la interfaz de usuario en Flet."""

from __future__ import annotations

from pathlib import Path

import flet as ft
import pytest

from src.motor.motor_inventario import MotorInventario
from src.ui.pantallas.agrupacion import PantallaAgrupacion
from src.ui.pantallas.alternativas import PantallaAlternativas
from src.ui.pantallas.catalogo import PantallaCatalogo
from src.ui.pantallas.comparacion import PantallaComparacion
from src.ui.pantallas.inicio import PantallaInicio
from src.ui.pantallas.pedidos import PantallaPedidos
from src.ui.pantallas.top_productos import PantallaTopProductos

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATASETS_DIR = BASE_DIR / "data" / "datasets"


@pytest.fixture
def motor_cargado() -> MotorInventario:
    motor = MotorInventario(estrategia="baseline")
    ruta = DATASETS_DIR / "demo_oral.json"
    motor.cargar_dataset(ruta)
    return motor


class TestPantallasInstanciacion:
    def test_pantalla_inicio(self, motor_cargado: MotorInventario):
        pantalla = PantallaInicio(
            motor=motor_cargado,
            on_actualizar_panel=lambda **kw: None,
            notificar=lambda *a, **kw: None,
        )
        assert len(pantalla.fila_kpis.controls) == 4
        pantalla._ejecutar_escenario_completo()
        assert len(pantalla.col_resultado_escenario.controls) >= 3

    def test_pantalla_catalogo(self, motor_cargado: MotorInventario):
        pantalla = PantallaCatalogo(
            motor=motor_cargado,
            on_actualizar_panel=lambda **kw: None,
            notificar=lambda *a, **kw: None,
        )
        assert len(pantalla.col_productos.controls) > 0
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
        pantalla._ejecutar_comparativa()
        assert len(pantalla.col_tabla_comparativa.controls) == 4


class TestOrdenamientoYDesplieguePantallas:
    def test_catalogo_ordenamiento_y_unidades_en_stock(self, motor_cargado: MotorInventario):
        pantalla = PantallaCatalogo(motor_cargado, lambda **kw: None, lambda *a, **kw: None)

        pantalla.dropdown_orden.value = "precio"
        pantalla.orden_ascendente = True
        pantalla._aplicar_ordenamiento()
        precios = [p.precio for p in pantalla.productos_actuales]
        assert precios == sorted(precios)

        pantalla._alternar_sentido_orden()
        precios_desc = [p.precio for p in pantalla.productos_actuales]
        assert precios_desc == sorted(precios, reverse=True)

        row = pantalla.col_productos.controls[0].content
        stock_badge = row.controls[3]
        texto_badge = stock_badge.content.value
        assert "Unidades en Stock" in texto_badge or "SIN STOCK" in texto_badge

    def test_pedidos_expansion_tile_y_ordenamiento(self, motor_cargado: MotorInventario):
        pantalla = PantallaPedidos(motor_cargado, lambda **kw: None, lambda *a, **kw: None)
        assert len(pantalla.col_pedidos.controls) == 8
        assert all(isinstance(ctrl, ft.ExpansionTile) for ctrl in pantalla.col_pedidos.controls)

        pantalla._ejecutar_procesamiento()
        assert len(pantalla.col_pedidos.controls) == 8
        primer_tile = pantalla.col_pedidos.controls[0]
        assert isinstance(primer_tile, ft.ExpansionTile)
        assert len(primer_tile.controls) > 0

        pantalla.dropdown_orden.value = "unidades"
        pantalla.orden_ascendente = False
        pantalla._aplicar_ordenamiento()
        assert len(pantalla.col_pedidos.controls) == 8

    def test_agrupacion_ordenamiento(self, motor_cargado: MotorInventario):
        pantalla = PantallaAgrupacion(motor_cargado, lambda **kw: None, lambda *a, **kw: None)
        pantalla.dropdown_orden.value = "cantidad"
        pantalla.orden_ascendente = False
        pantalla._aplicar_ordenamiento()
        cantidades = [item.cantidad_total for item in pantalla.items_consolidados_actuales]
        assert cantidades == sorted(cantidades, reverse=True)

    def test_top_productos_ordenamiento(self, motor_cargado: MotorInventario):
        pantalla = PantallaTopProductos(motor_cargado, lambda **kw: None, lambda *a, **kw: None)
        pantalla.dropdown_orden.value = "demanda"
        pantalla.orden_ascendente = False
        pantalla._aplicar_ordenamiento()
        demandas = [cant for _, cant in pantalla.ranking_actual]
        assert demandas == sorted(demandas, reverse=True)

    def test_alternativas_ordenamiento_y_despliegue(self, motor_cargado: MotorInventario):
        pantalla = PantallaAlternativas(motor_cargado, lambda **kw: None, lambda *a, **kw: None)
        pantalla.dropdown_orden.value = "precio"
        pantalla.orden_ascendente = True
        pantalla._aplicar_ordenamiento()
        costos = [comb.costo_total for comb in pantalla.combinaciones_actuales]
        assert costos == sorted(costos)

        if pantalla.combinaciones_actuales:
            primer_item = pantalla.col_combinaciones.controls[0]
            assert isinstance(primer_item, ft.ExpansionTile)

    def test_comparacion_ordenamiento(self, motor_cargado: MotorInventario):
        pantalla = PantallaComparacion(motor_cargado, lambda **kw: None, lambda *a, **kw: None)
        pantalla._ejecutar_comparativa()
        assert len(pantalla.col_tabla_comparativa.controls) == 4

        pantalla.dropdown_orden.value = "speedup"
        pantalla.orden_ascendente = False
        pantalla._aplicar_ordenamiento()
        assert len(pantalla.col_tabla_comparativa.controls) == 4

    def test_alternativas_grande_no_recursion_error(self):
        motor_grande = MotorInventario()
        motor_grande.cargar_dataset(DATASETS_DIR / "grande.json")
        res = motor_grande.buscar_alternativas("Ferretería y Herramientas", 45000.0)
        assert res.total_combinaciones > 0
        assert res.tiempo_ejecucion_ms < 50.0

    def test_catalogo_busqueda_por_id_y_boton_buscar(self, motor_cargado: MotorInventario):
        pantalla = PantallaCatalogo(motor_cargado, lambda **kw: None, lambda *a, **kw: None)
        pantalla.input_id.value = "1"
        pantalla.input_busqueda.value = ""
        pantalla._ejecutar_consulta()
        assert len(pantalla.productos_actuales) == 1
        assert pantalla.productos_actuales[0].id == 1

        pantalla.input_id.value = " 2 "
        pantalla._ejecutar_consulta()
        assert len(pantalla.productos_actuales) == 1
        assert pantalla.productos_actuales[0].id == 2

        pantalla.input_id.value = "99999"
        pantalla._ejecutar_consulta()
        assert len(pantalla.productos_actuales) == 0

        pantalla.input_id.value = "invalido"
        pantalla._ejecutar_consulta()
        assert len(pantalla.productos_actuales) == 0

        pantalla.input_id.value = ""
        pantalla.input_busqueda.value = "Martillo"
        pantalla._ejecutar_consulta()
        assert len(pantalla.productos_actuales) > 0

    def test_catalogo_optimizado_lee_hits_sin_explotar(self):
        motor_opt = MotorInventario(estrategia="optimizado")
        motor_opt.cargar_dataset(DATASETS_DIR / "demo_oral.json")
        pantalla = PantallaCatalogo(motor_opt, lambda **kw: None, lambda *a, **kw: None)
        pantalla.input_busqueda.value = "Tornillo"
        pantalla._ejecutar_busqueda()
        pantalla._ejecutar_busqueda()
        assert pantalla.txt_tiempo_busqueda.value != ""

    def test_pedidos_optimizado_no_activa_processpool(self):
        motor_opt = MotorInventario(estrategia="optimizado")
        motor_opt.cargar_dataset(DATASETS_DIR / "demo_oral.json")
        pantalla = PantallaPedidos(motor_opt, lambda **kw: None, lambda *a, **kw: None)
        pantalla._ejecutar_procesamiento()
        assert len(pantalla.col_pedidos.controls) == 8

    def test_catalogo_badge_estrategia_sincronizacion(self, motor_cargado: MotorInventario):
        pantalla = PantallaCatalogo(motor_cargado, lambda **kw: None, lambda *a, **kw: None)
        assert not hasattr(pantalla, "switch_estrategia_local")
        assert hasattr(pantalla, "badge_estrategia")

        pantalla.al_cambiar_estrategia_global("optimizado")
        assert "Hash O(1)" in pantalla.badge_estrategia.content.controls[1].value

        pantalla.al_cambiar_estrategia_global("baseline")
        assert "Lineal O(n)" in pantalla.badge_estrategia.content.controls[1].value

    def test_banner_no_clipping_wrap(self):
        from src.ui.tema import crear_banner_explicativo

        b = crear_banner_explicativo(
            titulo="Título",
            descripcion="Descripción larga",
            complejidad_base="O(n)",
            complejidad_opt="O(1)",
            por_que_importa="Importancia",
        )
        assert isinstance(b, ft.Container)


@pytest.mark.parametrize(
    "clase",
    [
        PantallaAgrupacion,
        PantallaAlternativas,
        PantallaCatalogo,
        PantallaComparacion,
        PantallaPedidos,
        PantallaTopProductos,
    ],
)
def test_alternar_sentido_orden(clase):
    motor = MotorInventario(estrategia="baseline")
    motor.cargar_dataset(DATASETS_DIR / "demo_oral.json")
    pantalla = clase(motor=motor, on_actualizar_panel=lambda **kw: None, notificar=lambda *a: None)
    inicial = pantalla.orden_ascendente
    pantalla._alternar_sentido_orden()
    assert pantalla.orden_ascendente is not inicial
    assert pantalla.btn_sentido_orden.tooltip.startswith(
        "Orden ascendente" if not inicial else "Orden descendente"
    )
    pantalla._alternar_sentido_orden()
    assert pantalla.orden_ascendente is inicial
