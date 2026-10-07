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

import multiprocessing
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


def main(page: ft.Page) -> None:
    """Punto de entrada de la aplicación de escritorio Flet."""
    page.title = "Optimizador de Inventario y Pedidos | Programación Eficiente"
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
        page.window.width = 1280
        page.window.height = 840
        page.window.min_width = 1000
        page.window.min_height = 700
    except Exception:
        page.width = 1280
        page.height = 840

    # 1. Inicializar el motor desacoplado y precargar demo_oral.json
    motor = MotorInventario(estrategia="baseline")
    ruta_inicial = DATASETS_DIR / "demo_oral.json"
    if ruta_inicial.is_file():
        motor.cargar_dataset(ruta_inicial)

    # 2. Función auxiliar de notificaciones amigable
    def notificar(
        mensaje: str, icono: str = ft.Icons.INFO_OUTLINE, color: str | None = None
    ) -> None:
        sb = ft.SnackBar(
            content=ft.Row(
                controls=[
                    ft.Icon(icono, color=color or COLOR_MARCA, size=20),
                    ft.Text(mensaje, color=COLOR_NAV_TEXTO, size=13),
                ],
                spacing=8,
            ),
            bgcolor=COLOR_NAV,
        )
        if hasattr(page, "show_dialog") and hasattr(page, "overlay"):
            try:
                page.overlay.append(sb)
                sb.open = True
                page.update()
                return
            except Exception:
                pass
        if hasattr(page, "open"):
            page.open(sb)
        else:
            page.snack_bar = sb
            sb.open = True
            page.update()

    # 3. Función de callback para actualizar la barra de estado
    def actualizar_panel(
        dataset: str | None = None,
        n_productos: int | None = None,
        n_pedidos: int | None = None,
        estrategia: str | None = None,
        tiempo_ms: float | None = None,
        memoria_mb: float | None = None,
        resultado_negocio: str | None = None,
    ) -> None:
        ds = dataset or getattr(panel_estado, "dataset_nombre", "demo_oral.json")
        panel_estado.dataset_nombre = ds
        n_p = n_productos if n_productos is not None else len(motor.catalogo)
        n_ped = n_pedidos if n_pedidos is not None else len(motor.pedidos)
        est = estrategia or motor.estrategia

        panel_estado.actualizar_estado(
            dataset=ds,
            n_productos=n_p,
            n_pedidos=n_ped,
            estrategia=est,
            tiempo_ms=tiempo_ms,
            memoria_mb=memoria_mb,
            resultado_negocio=resultado_negocio,
        )

    def abrir_modal_ayuda_modos() -> None:
        dlg = crear_dialogo_explicativo_modos(page)
        if hasattr(page, "show_dialog") and callable(page.show_dialog):
            page.show_dialog(dlg)
        elif hasattr(page, "open") and callable(page.open):
            page.open(dlg)
        else:
            page.dialog = dlg
            dlg.open = True
            page.update()

    def al_conmutar_estrategia(nueva_estrategia: str) -> None:
        motor.cambiar_estrategia(nueva_estrategia)
        actualizar_panel(
            estrategia=nueva_estrategia,
            resultado_negocio=f"Estrategia conmutada a {nueva_estrategia.upper()}",
        )
        notificar(
            f"Estrategia global cambiada a '{nueva_estrategia.upper()}'.", ft.Icons.SWAP_HORIZ
        )
        # Notificar a las pantallas cacheadas para sincronizar su estado
        for v in vistas.values():
            if hasattr(v, "al_cambiar_estrategia_global"):
                v.al_cambiar_estrategia_global(nueva_estrategia)
        cambiar_vista(rail_navegacion.selected_index)

    # 4. Instanciar panel de estado persistente con botón explicativo
    panel_estado = PanelEstado(
        on_cambiar_estrategia=al_conmutar_estrategia,
        on_mostrar_ayuda_modos=abrir_modal_ayuda_modos,
    )
    actualizar_panel(dataset="demo_oral.json")

    # 5. Contenedor dinámico central y caché de vistas para persistencia total de estado
    contenedor_pantalla = ft.Container(expand=True, bgcolor=COLOR_FONDO_APP)
    vistas: dict[int, ft.Control] = {}

    def notificar_recarga_dataset(nombre_dataset: str) -> None:
        """Propaga la carga de un nuevo dataset a todas las vistas cacheadas."""
        for idx, vista in list(vistas.items()):
            if idx != 0 and hasattr(vista, "al_recargar_dataset"):
                vista.al_recargar_dataset()

    def obtener_vista(indice: int) -> ft.Control:
        if indice not in vistas:
            if indice == 0:
                vistas[indice] = PantallaInicio(
                    motor,
                    actualizar_panel,
                    notificar,
                    on_dataset_cambiado=notificar_recarga_dataset,
                )
            elif indice == 1:
                vistas[indice] = PantallaCatalogo(motor, actualizar_panel, notificar)
            elif indice == 2:
                vistas[indice] = PantallaPedidos(motor, actualizar_panel, notificar)
            elif indice == 3:
                vistas[indice] = PantallaAgrupacion(motor, actualizar_panel, notificar)
            elif indice == 4:
                vistas[indice] = PantallaTopProductos(motor, actualizar_panel, notificar)
            elif indice == 5:
                vistas[indice] = PantallaAlternativas(motor, actualizar_panel, notificar)
            elif indice == 6:
                vistas[indice] = PantallaComparacion(motor, actualizar_panel, notificar)
            else:
                vistas[indice] = PantallaInicio(motor, actualizar_panel, notificar)
        return vistas[indice]

    def cambiar_vista(indice: int) -> None:
        contenedor_pantalla.content = obtener_vista(indice)
        page.update()

    def al_cambiar_rail(e):
        cambiar_vista(rail_navegacion.selected_index)

    # 6. Rail de navegación lateral accesible
    rail_navegacion = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=112,
        min_extended_width=168,
        bgcolor=COLOR_NAV,
        indicator_color=COLOR_NAV_HOVER,
        selected_label_text_style=ft.TextStyle(
            size=12,
            weight=ft.FontWeight.W_700,
            color=COLOR_MARCA,
        ),
        unselected_label_text_style=ft.TextStyle(
            size=12,
            weight=ft.FontWeight.W_500,
            color=COLOR_NAV_MUTED,
        ),
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.Icon(ft.Icons.HOME_OUTLINED, color=COLOR_NAV_MUTED),
                selected_icon=ft.Icon(ft.Icons.HOME_ROUNDED, color=COLOR_MARCA),
                label="Inicio",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icon(ft.Icons.INVENTORY_2_OUTLINED, color=COLOR_NAV_MUTED),
                selected_icon=ft.Icon(ft.Icons.INVENTORY_2_ROUNDED, color=COLOR_MARCA),
                label="Catálogo",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icon(ft.Icons.SHOPPING_BAG_OUTLINED, color=COLOR_NAV_MUTED),
                selected_icon=ft.Icon(ft.Icons.SHOPPING_BAG_ROUNDED, color=COLOR_MARCA),
                label="Pedidos",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icon(ft.Icons.ALL_INBOX_OUTLINED, color=COLOR_NAV_MUTED),
                selected_icon=ft.Icon(ft.Icons.ALL_INBOX_ROUNDED, color=COLOR_MARCA),
                label="Agrupación",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icon(ft.Icons.LEADERBOARD_OUTLINED, color=COLOR_NAV_MUTED),
                selected_icon=ft.Icon(ft.Icons.LEADERBOARD_ROUNDED, color=COLOR_MARCA),
                label="Top-N",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icon(ft.Icons.SWAP_HORIZ_OUTLINED, color=COLOR_NAV_MUTED),
                selected_icon=ft.Icon(ft.Icons.SWAP_HORIZ_ROUNDED, color=COLOR_MARCA),
                label="Alternativas",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icon(ft.Icons.COMPARE_ARROWS_OUTLINED, color=COLOR_NAV_MUTED),
                selected_icon=ft.Icon(ft.Icons.COMPARE_ARROWS_ROUNDED, color=COLOR_MARCA),
                label="Comparativa",
            ),
        ],
        on_change=al_cambiar_rail,
    )

    # Cargar vista inicial (Inicio)
    contenedor_pantalla.content = obtener_vista(0)

    # 7. Composición global de la página
    cuerpo_principal = ft.Row(
        controls=[
            rail_navegacion,
            contenedor_pantalla,
        ],
        spacing=0,
        expand=True,
    )

    page.add(
        ft.Column(
            controls=[
                panel_estado,
                cuerpo_principal,
            ],
            spacing=0,
            expand=True,
        )
    )


if __name__ == "__main__":
    multiprocessing.freeze_support()
    if hasattr(ft, "run") and callable(ft.run):
        ft.run(main)
    elif hasattr(ft, "app") and callable(ft.app):
        ft.app(target=main)
    else:
        ft.run(main)
