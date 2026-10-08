"""Aplicación principal de escritorio en Flet.

Integra la barra de estado persistente, el menú de navegación lateral (NavigationRail)
y las 7 pantallas del sistema:

0. Inicio y selección de datasets
1. Catálogo de productos (búsquedas lineales vs hash con LRU)
2. Preparación de pedidos (secuencial vs concurrente)
3. Agrupación y Batch Picking consolidado
4. Ranking de productos más solicitados (Top-N con Heaps vs Sort)
5. Sugerencia de alternativas sustitutas (Memoización DP vs Recursión)
6. Comparativa experimental global (mediciones para la defensa oral)
"""

from __future__ import annotations

import contextlib
import multiprocessing
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import flet as ft

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
    COLOR_FONDO_APP,
    COLOR_MARCA,
    COLOR_NAV,
    COLOR_NAV_HOVER,
    COLOR_NAV_MUTED,
    COLOR_NAV_TEXTO,
    COLOR_PRIMARIO,
    COLOR_TARJETA,
    crear_dialogo_explicativo_modos,
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATASETS_DIR = BASE_DIR / "data" / "datasets"
DATASET_INICIAL = "demo_oral.json"

TITULO_VENTANA = "Optimizador de Inventario y Pedidos | Programación Eficiente"
ANCHO_VENTANA, ALTO_VENTANA = 1280, 840
ANCHO_MINIMO, ALTO_MINIMO = 1000, 700
INDICE_INICIO = 0


@dataclass(frozen=True)
class Seccion:
    """Entrada del menú lateral y la pantalla que muestra."""

    etiqueta: str
    icono: str
    icono_seleccionado: str
    pantalla: type[ft.Control]


SECCIONES: tuple[Seccion, ...] = (
    Seccion("Inicio", ft.Icons.HOME_OUTLINED, ft.Icons.HOME_ROUNDED, PantallaInicio),
    Seccion(
        "Catálogo",
        ft.Icons.INVENTORY_2_OUTLINED,
        ft.Icons.INVENTORY_2_ROUNDED,
        PantallaCatalogo,
    ),
    Seccion(
        "Pedidos",
        ft.Icons.SHOPPING_BAG_OUTLINED,
        ft.Icons.SHOPPING_BAG_ROUNDED,
        PantallaPedidos,
    ),
    Seccion(
        "Agrupación",
        ft.Icons.ALL_INBOX_OUTLINED,
        ft.Icons.ALL_INBOX_ROUNDED,
        PantallaAgrupacion,
    ),
    Seccion(
        "Top-N",
        ft.Icons.LEADERBOARD_OUTLINED,
        ft.Icons.LEADERBOARD_ROUNDED,
        PantallaTopProductos,
    ),
    Seccion(
        "Alternativas",
        ft.Icons.SWAP_HORIZ_OUTLINED,
        ft.Icons.SWAP_HORIZ_ROUNDED,
        PantallaAlternativas,
    ),
    Seccion(
        "Comparativa",
        ft.Icons.COMPARE_ARROWS_OUTLINED,
        ft.Icons.COMPARE_ARROWS_ROUNDED,
        PantallaComparacion,
    ),
)


def _mostrar_superpuesto(page: ft.Page, control: ft.Control) -> None:
    """Muestra un SnackBar o un diálogo con la API que tenga la versión de Flet instalada."""
    if hasattr(page, "show_dialog") and isinstance(control, ft.AlertDialog):
        page.show_dialog(control)
        return
    if hasattr(page, "show_dialog") and hasattr(page, "overlay"):
        with contextlib.suppress(Exception):
            page.overlay.append(control)
            control.open = True
            page.update()
            return
    if hasattr(page, "open") and callable(page.open):
        page.open(control)
        return
    # Flet muy antiguo: un atributo por tipo de control.
    if isinstance(control, ft.AlertDialog):
        page.dialog = control
    else:
        page.snack_bar = control
    control.open = True
    page.update()


class AplicacionInventario:
    """Arma la ventana principal: panel de estado, menú lateral y pantallas.

    Las pantallas se crean la primera vez que se visitan y se conservan, así cada una
    mantiene su estado (filtros, resultados) al cambiar de sección.

    Argumentos:
        page: Página de Flet donde se monta la aplicación.
        motor: Motor de inventario. Por defecto, uno nuevo con ``demo_oral.json`` cargado.
    """

    def __init__(self, page: ft.Page, motor: MotorInventario | None = None) -> None:
        self.page = page
        self.motor = motor or self._crear_motor_inicial()
        self.vistas: dict[int, ft.Control] = {}
        self.contenedor_pantalla = ft.Container(expand=True, bgcolor=COLOR_FONDO_APP)
        self.panel_estado = PanelEstado(
            on_cambiar_estrategia=self.al_conmutar_estrategia,
            on_mostrar_ayuda_modos=self.abrir_ayuda_modos,
        )
        self.rail_navegacion = self._crear_rail()

    @staticmethod
    def _crear_motor_inicial() -> MotorInventario:
        motor = MotorInventario(estrategia="baseline")
        ruta_inicial = DATASETS_DIR / DATASET_INICIAL
        if ruta_inicial.is_file():
            motor.cargar_dataset(ruta_inicial)
        return motor

    # ------------------------------------------------------------------ montaje

    def montar(self) -> None:
        """Configura la página y agrega el panel de estado y el cuerpo principal."""
        self._configurar_pagina()
        self.actualizar_panel(dataset=DATASET_INICIAL)
        self.contenedor_pantalla.content = self.obtener_vista(INDICE_INICIO)
        cuerpo_principal = ft.Row(
            controls=[self.rail_navegacion, self.contenedor_pantalla],
            spacing=0,
            expand=True,
        )
        self.page.add(
            ft.Column(controls=[self.panel_estado, cuerpo_principal], spacing=0, expand=True)
        )

    def _configurar_pagina(self) -> None:
        page = self.page
        page.title = TITULO_VENTANA
        page.bgcolor = COLOR_FONDO_APP
        page.theme_mode = ft.ThemeMode.LIGHT
        page.padding = 0
        page.theme = ft.Theme(
            font_family="Segoe UI",
            visual_density=ft.VisualDensity.COMPACT,
            color_scheme=ft.ColorScheme(
                primary=COLOR_PRIMARIO,
                on_primary="#FFFFFF",
                surface=COLOR_TARJETA,
                on_surface="#0F141A",
            ),
        )
        try:
            page.window.width = ANCHO_VENTANA
            page.window.height = ALTO_VENTANA
            page.window.min_width = ANCHO_MINIMO
            page.window.min_height = ALTO_MINIMO
        except AttributeError:
            # Versiones de Flet sin page.window.
            page.width = ANCHO_VENTANA
            page.height = ALTO_VENTANA

    def _crear_rail(self) -> ft.NavigationRail:
        return ft.NavigationRail(
            selected_index=INDICE_INICIO,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=112,
            min_extended_width=168,
            bgcolor=COLOR_NAV,
            indicator_color=COLOR_NAV_HOVER,
            selected_label_text_style=ft.TextStyle(
                size=12, weight=ft.FontWeight.W_700, color=COLOR_MARCA
            ),
            unselected_label_text_style=ft.TextStyle(
                size=12, weight=ft.FontWeight.W_500, color=COLOR_NAV_MUTED
            ),
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.Icon(seccion.icono, color=COLOR_NAV_MUTED),
                    selected_icon=ft.Icon(seccion.icono_seleccionado, color=COLOR_MARCA),
                    label=seccion.etiqueta,
                )
                for seccion in SECCIONES
            ],
            on_change=lambda _: self.cambiar_vista(self.rail_navegacion.selected_index),
        )

    # ------------------------------------------------------------------ vistas

    def obtener_vista(self, indice: int) -> ft.Control:
        """Devuelve la pantalla de la sección; la crea la primera vez que se visita."""
        if indice not in self.vistas:
            seccion = SECCIONES[indice] if 0 <= indice < len(SECCIONES) else SECCIONES[0]
            argumentos: dict[str, Callable] = {}
            if seccion.pantalla is PantallaInicio:
                argumentos["on_dataset_cambiado"] = self.al_recargar_dataset
            self.vistas[indice] = seccion.pantalla(
                self.motor, self.actualizar_panel, self.notificar, **argumentos
            )
        return self.vistas[indice]

    def cambiar_vista(self, indice: int) -> None:
        """Muestra la pantalla de la sección indicada."""
        self.contenedor_pantalla.content = self.obtener_vista(indice)
        self.page.update()

    def al_recargar_dataset(self, nombre_dataset: str) -> None:
        """Avisa a las pantallas ya creadas (salvo Inicio) que cambió el dataset."""
        for indice, vista in list(self.vistas.items()):
            if indice != INDICE_INICIO and hasattr(vista, "al_recargar_dataset"):
                vista.al_recargar_dataset()

    # ------------------------------------------------------------------ callbacks

    def notificar(
        self, mensaje: str, icono: str = ft.Icons.INFO_OUTLINE, color: str | None = None
    ) -> None:
        """Muestra un aviso breve (SnackBar) en la parte inferior de la ventana."""
        aviso = ft.SnackBar(
            content=ft.Row(
                controls=[
                    ft.Icon(icono, color=color or COLOR_MARCA, size=20),
                    ft.Text(mensaje, color=COLOR_NAV_TEXTO, size=13),
                ],
                spacing=8,
            ),
            bgcolor=COLOR_NAV,
        )
        _mostrar_superpuesto(self.page, aviso)

    def actualizar_panel(
        self,
        dataset: str | None = None,
        n_productos: int | None = None,
        n_pedidos: int | None = None,
        estrategia: str | None = None,
        tiempo_ms: float | None = None,
        memoria_mb: float | None = None,
        resultado_negocio: str | None = None,
    ) -> None:
        """Actualiza el panel de estado; lo que no se indica se toma del motor."""
        nombre_dataset = dataset or getattr(self.panel_estado, "dataset_nombre", DATASET_INICIAL)
        self.panel_estado.dataset_nombre = nombre_dataset
        self.panel_estado.actualizar_estado(
            dataset=nombre_dataset,
            n_productos=len(self.motor.catalogo) if n_productos is None else n_productos,
            n_pedidos=len(self.motor.pedidos) if n_pedidos is None else n_pedidos,
            estrategia=estrategia or self.motor.estrategia,
            tiempo_ms=tiempo_ms,
            memoria_mb=memoria_mb,
            resultado_negocio=resultado_negocio,
        )

    def abrir_ayuda_modos(self) -> None:
        """Abre el diálogo que explica la diferencia entre Baseline y Optimizado."""
        _mostrar_superpuesto(self.page, crear_dialogo_explicativo_modos(self.page))

    def al_conmutar_estrategia(self, nueva_estrategia: str) -> None:
        """Cambia la estrategia del motor y sincroniza todas las pantallas creadas."""
        self.motor.cambiar_estrategia(nueva_estrategia)
        self.actualizar_panel(
            estrategia=nueva_estrategia,
            resultado_negocio=f"Estrategia conmutada a {nueva_estrategia.upper()}",
        )
        self.notificar(
            f"Estrategia global cambiada a '{nueva_estrategia.upper()}'.", ft.Icons.SWAP_HORIZ
        )
        for vista in self.vistas.values():
            if hasattr(vista, "al_cambiar_estrategia_global"):
                vista.al_cambiar_estrategia_global(nueva_estrategia)
        self.cambiar_vista(self.rail_navegacion.selected_index)


def main(page: ft.Page) -> None:
    """Punto de entrada de la aplicación de escritorio Flet."""
    AplicacionInventario(page).montar()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    if hasattr(ft, "run") and callable(ft.run):
        ft.run(main)
    elif hasattr(ft, "app") and callable(ft.app):
        ft.app(target=main)
    else:
        ft.run(main)
