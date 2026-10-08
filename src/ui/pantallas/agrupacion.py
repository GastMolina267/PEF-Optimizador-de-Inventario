"""Pantalla de Agrupación de Pedidos y Picking Consolidado (Batch Picking)."""

from __future__ import annotations

import time

import flet as ft

from src.motor.motor_inventario import MotorInventario
from src.ui.pantallas.base import PantallaBase
from src.ui.tema import (
    COLOR_BORDE,
    COLOR_EXITO,
    COLOR_PELIGRO,
    COLOR_PRIMARIO,
    COLOR_SECUNDARIO,
    COLOR_TARJETA,
    COLOR_TEXTO_MUTED,
    COLOR_TEXTO_PRIMARIO,
    actualizar_control,
    borde_all,
    crear_banner_explicativo,
    crear_barra_herramientas,
    crear_columna_titulo_detalle,
    crear_dropdown,
    crear_encabezado,
    crear_tarjeta_kpi,
    crear_titulo_seccion,
    envolver_lista,
    envolver_metricas,
    estilo_boton_primario,
    formatear_tiempo_ms,
    padding_symmetric,
)


class PantallaAgrupacion(PantallaBase):
    """Vista de consolidación de pedidos en una única lista de picking en tiempo O(L)."""

    def __init__(self, motor: MotorInventario, on_actualizar_panel, notificar) -> None:
        super().__init__(motor, on_actualizar_panel, notificar)

        self.items_consolidados_actuales = []
        self.orden_ascendente = False

        self.btn_agrupar = ft.FilledButton(
            "Consolidar",
            icon=ft.Icons.ALL_INBOX_ROUNDED,
            style=estilo_boton_primario(),
            on_click=lambda _: self._ejecutar_agrupacion(),
        )

        # Controles de ordenamiento
        self.dropdown_orden = crear_dropdown(
            label="Ordenar por",
            options=[
                ft.dropdown.Option("cantidad", "Cantidad Total Demandada"),
                ft.dropdown.Option("nombre", "Nombre del Producto"),
                ft.dropdown.Option("stock", "Unidades en Stock"),
                ft.dropdown.Option("estado", "Suficiencia de Stock"),
                ft.dropdown.Option("id", "ID de Producto"),
            ],
            value="cantidad",
            width=200,
            on_change_callback=lambda _: self._aplicar_ordenamiento(),
        )

        self.btn_sentido_orden = self._crear_boton_sentido_orden()

        self.fila_kpis = ft.Row(spacing=0)
        self.col_items_picking = ft.ListView(spacing=0, expand=True, padding=0)

        self._construir_interfaz()
        self._ejecutar_agrupacion()

    def _construir_interfaz(self) -> None:
        self.content = ft.Column(
            controls=[
                crear_encabezado(
                    "Batch Picking Consolidado",
                    "Fusión de demandas en una sola pasada O(L) mediante acumulación en tablas Hash",
                    self.btn_agrupar,
                ),
                crear_banner_explicativo(
                    titulo="Batch Picking Consolidado en Almacén",
                    descripcion="Consolida las demandas de todos los pedidos en una única lista de recolección para que el operario visite cada posición una sola vez.",
                    complejidad_base="Agrupación Anidada O(P·L·n)",
                    complejidad_opt="Agrupación Hash O(L)",
                    por_que_importa="En depósitos con miles de pedidos, elimina búsquedas cuadráticas repetidas y reduce la distancia física recorrida en almacén.",
                ),
                crear_barra_herramientas(
                    [
                        self.dropdown_orden,
                        self.btn_sentido_orden,
                    ]
                ),
                envolver_metricas(self.fila_kpis),
                crear_titulo_seccion("Lista Consolidada de Artículos a Recolectar en Almacén"),
                envolver_lista(self.col_items_picking),
            ],
            spacing=10,
            expand=True,
        )

    def al_recargar_dataset(self) -> None:
        """Callback al recargar dataset."""
        self._ejecutar_agrupacion()

    def al_cambiar_estrategia_global(self, nueva_estrategia: str) -> None:
        """Sincroniza cuando cambia la estrategia."""
        self._ejecutar_agrupacion()

    def _aplicar_ordenamiento(self):
        criterio = self.dropdown_orden.value or "cantidad"

        def clave(item):
            prod = item.producto
            if criterio == "cantidad":
                return item.cantidad_total
            elif criterio == "nombre":
                return prod.nombre.lower() if prod else ""
            elif criterio == "stock":
                return prod.stock if prod else 0
            elif criterio == "estado":
                # Faltantes primero o cubiertos primero
                stock_disp = prod.stock if prod else 0
                return 1 if stock_disp >= item.cantidad_total else 0
            return item.id_producto

        self.items_consolidados_actuales.sort(key=clave, reverse=not self.orden_ascendente)
        self._renderizar_items()

    def _ejecutar_agrupacion(self):
        inicio = time.perf_counter()
        lote = self.motor.agrupar_pedidos()
        duracion_ms = (time.perf_counter() - inicio) * 1000.0

        # Actualizar KPIs
        self.fila_kpis.controls = [
            crear_tarjeta_kpi(
                "Pedidos Consolidados",
                f"{lote.total_pedidos:,}",
                "Órdenes agrupadas",
                ft.Icons.LOCAL_SHIPPING,
                COLOR_PRIMARIO,
            ),
            crear_tarjeta_kpi(
                "Productos Únicos",
                f"{lote.total_productos_distintos:,}",
                "Posiciones a visitar",
                ft.Icons.CATEGORY,
                COLOR_SECUNDARIO,
            ),
            crear_tarjeta_kpi(
                "Unidades Totales",
                f"{lote.total_unidades:,}",
                "Cantidad agregada",
                ft.Icons.INVENTORY_2,
                COLOR_EXITO,
            ),
            crear_tarjeta_kpi(
                "Tiempo de Consolidación",
                formatear_tiempo_ms(duracion_ms),
                "Cómputo en una pasada O(L)",
                ft.Icons.SPEED,
                COLOR_PRIMARIO,
            ),
        ]

        self.items_consolidados_actuales = list(lote.items)
        self._aplicar_ordenamiento()

        self._publicar_resultado(
            tiempo_ms=duracion_ms,
            resultado_negocio=f"Batch Picking: {lote.total_unidades} Unidades en {lote.total_productos_distintos} productos",
        )
        actualizar_control(self)

    def _renderizar_items(self):
        items_visuales = []
        max_mostrar = 100
        for item in self.items_consolidados_actuales[:max_mostrar]:
            prod = item.producto
            stock_disp = prod.stock if prod else 0
            nombre = prod.nombre if prod else f"Producto #{item.id_producto}"
            categoria = prod.categoria if prod else "Sin categoría"

            # Badge de cobertura frente a la demanda total
            alcanza = stock_disp >= item.cantidad_total
            color_alcanza = COLOR_EXITO if alcanza else COLOR_PELIGRO
            texto_alcanza = (
                f"Stock en Almacén: {stock_disp} Unidades (Suficiente)"
                if alcanza
                else f"Stock en Almacén: {stock_disp} Unidades (Faltante)"
            )

            items_visuales.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Text(
                                    f"#{item.id_producto}",
                                    size=12,
                                    weight=ft.FontWeight.BOLD,
                                    color=COLOR_PRIMARIO,
                                ),
                                width=50,
                            ),
                            crear_columna_titulo_detalle(
                                nombre,
                                f"{categoria} | {item.total_pedidos_solicitantes} pedidos solicitantes",
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        f"Demanda Total: {item.cantidad_total} Unidades",
                                        size=12,
                                        weight=ft.FontWeight.BOLD,
                                        color=COLOR_TEXTO_PRIMARIO,
                                    ),
                                    ft.Text(
                                        texto_alcanza,
                                        size=10.5,
                                        color=color_alcanza,
                                        weight=ft.FontWeight.W_600,
                                    ),
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.END,
                                spacing=1,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    padding=padding_symmetric(horizontal=12, vertical=6),
                    bgcolor=COLOR_TARJETA,
                    border_radius=6,
                    border=borde_all(1, COLOR_BORDE),
                )
            )

        if len(self.items_consolidados_actuales) > max_mostrar:
            items_visuales.append(
                ft.Text(
                    f"Mostrando los primeros {max_mostrar} de {len(self.items_consolidados_actuales)} productos consolidados...",
                    size=12,
                    color=COLOR_TEXTO_MUTED,
                    text_align=ft.TextAlign.CENTER,
                )
            )

        self.col_items_picking.controls = items_visuales
        actualizar_control(self)
