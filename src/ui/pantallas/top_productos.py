"""Pantalla de Productos Más Solicitados (Top-N)."""

from __future__ import annotations

import time

import flet as ft

from src.motor.motor_inventario import MotorInventario
from src.ranking.top_productos import (
    calcular_top_solicitados_heap,
    calcular_top_solicitados_lineal,
)
from src.ui.pantallas.base import PantallaBase
from src.ui.tema import (
    COLOR_BORDE,
    COLOR_EXITO,
    COLOR_PRIMARIO,
    COLOR_SECUNDARIO,
    COLOR_SUPERFICIE,
    COLOR_TARJETA,
    COLOR_TEXTO_MUTED,
    COLOR_TEXTO_PRIMARIO,
    actualizar_control,
    alineacion_center,
    borde_all,
    crear_banner_explicativo,
    crear_barra_herramientas,
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


class PantallaTopProductos(PantallaBase):
    """Vista comparativa de Top-N: Min-Heap O(N log k) vs Ordenamiento Total O(N log N)."""

    def __init__(self, motor: MotorInventario, on_actualizar_panel, notificar) -> None:
        super().__init__(motor, on_actualizar_panel, notificar)

        self.ranking_actual = []
        self.orden_ascendente = False

        # Selector de método
        self.dropdown_metodo = crear_dropdown(
            label="Algoritmo",
            options=[
                ft.dropdown.Option("heap", "Min-Heap heapq.nlargest (O(N log k))"),
                ft.dropdown.Option("sort", "Ordenamiento Completo sort (O(N log N))"),
            ],
            value="heap" if self.motor.es_optimizado else "sort",
            width=290,
            on_change_callback=lambda _: self._ejecutar_calculo(),
        )

        # Selector de k
        self.dropdown_k = crear_dropdown(
            label="k",
            options=[
                ft.dropdown.Option("3", "Top 3"),
                ft.dropdown.Option("5", "Top 5"),
                ft.dropdown.Option("10", "Top 10"),
                ft.dropdown.Option("20", "Top 20"),
            ],
            value="5",
            width=100,
            on_change_callback=lambda _: self._ejecutar_calculo(),
        )

        # Selector de orden secundario
        self.dropdown_orden = crear_dropdown(
            label="Ordenar por",
            options=[
                ft.dropdown.Option("demanda", "Demanda (Unidades)"),
                ft.dropdown.Option("nombre", "Nombre del Producto"),
                ft.dropdown.Option("categoria", "Categoría"),
                ft.dropdown.Option("stock", "Stock en Almacén"),
            ],
            value="demanda",
            width=180,
            on_change_callback=lambda _: self._aplicar_ordenamiento(),
        )

        self.btn_sentido_orden = ft.IconButton(
            icon=ft.Icons.ARROW_DOWNWARD_ROUNDED,
            tooltip="Orden Descendente (Clic para alternar)",
            on_click=lambda _: self._alternar_sentido_orden(),
        )

        self.btn_calcular = ft.FilledButton(
            "Recalcular",
            icon=ft.Icons.LEADERBOARD_ROUNDED,
            style=estilo_boton_primario(),
            on_click=lambda _: self._ejecutar_calculo(),
        )

        self.fila_kpis = ft.Row(spacing=0)
        self.col_ranking = ft.ListView(spacing=0, expand=True, padding=0)

        self._construir_interfaz()
        self._ejecutar_calculo()

    def _construir_interfaz(self) -> None:
        self.content = ft.Column(
            controls=[
                crear_encabezado(
                    "Ranking de Productos Más Solicitados (Top-N)",
                    "Comparación algorítmica: Heap O(N log k) acotado en memoria vs. Ordenamiento global O(N log N)",
                    self.btn_calcular,
                ),
                crear_banner_explicativo(
                    titulo="Ranking Top-N y Priorización de Inventario",
                    descripcion="Identifica los artículos con mayor volumen de demanda acumulada para ubicarlos estratégicamente en zonas de picking rápido.",
                    complejidad_base="Ordenamiento Total O(N log N)",
                    complejidad_opt="Min-Heap acotado O(N log k)",
                    por_que_importa="El algoritmo con Heap mantiene únicamente los k elementos en memoria, ahorrando espacio y tiempo sin ordenar el catálogo completo.",
                ),
                crear_barra_herramientas(
                    [
                        self.dropdown_metodo,
                        self.dropdown_k,
                        self.dropdown_orden,
                        self.btn_sentido_orden,
                    ]
                ),
                envolver_metricas(self.fila_kpis),
                crear_titulo_seccion("Productos con Mayor Demanda en el Lote Activo"),
                envolver_lista(self.col_ranking),
            ],
            spacing=10,
            expand=True,
        )

    def al_recargar_dataset(self) -> None:
        """Callback al recargar dataset."""
        self._ejecutar_calculo()

    def al_cambiar_estrategia_global(self, nueva_estrategia: str) -> None:
        """Sincroniza cuando cambia la estrategia global."""
        self.dropdown_metodo.value = "heap" if nueva_estrategia == "optimizado" else "sort"
        actualizar_control(self.dropdown_metodo)
        self._ejecutar_calculo()

    def _alternar_sentido_orden(self):
        self.orden_ascendente = not self.orden_ascendente
        self.btn_sentido_orden.icon = (
            ft.Icons.ARROW_UPWARD_ROUNDED
            if self.orden_ascendente
            else ft.Icons.ARROW_DOWNWARD_ROUNDED
        )
        self.btn_sentido_orden.tooltip = (
            "Orden Ascendente" if self.orden_ascendente else "Orden Descendente"
        )
        actualizar_control(self.btn_sentido_orden)
        self._aplicar_ordenamiento()

    def _aplicar_ordenamiento(self):
        criterio = self.dropdown_orden.value or "demanda"

        def clave(item):
            p, cant = item
            if criterio == "demanda":
                return cant
            elif criterio == "nombre":
                return p.nombre.lower()
            elif criterio == "categoria":
                return p.categoria.lower()
            elif criterio == "stock":
                return p.stock
            return cant

        self.ranking_actual.sort(key=clave, reverse=not self.orden_ascendente)
        self._renderizar_ranking()

    def _ejecutar_calculo(self):
        metodo = self.dropdown_metodo.value or "heap"
        try:
            k = int(self.dropdown_k.value or "5")
        except ValueError:
            k = 5

        inicio = time.perf_counter()
        if metodo == "heap":
            resultados = calcular_top_solicitados_heap(
                self.motor.pedidos, self.motor.catalogo, k=k
            )
            alg_desc = f"Min-Heap heapq.nlargest (k={k})"
        else:
            resultados = calcular_top_solicitados_lineal(
                self.motor.pedidos, self.motor.catalogo, k=k
            )
            alg_desc = f"Ordenamiento Total sort() (k={k})"
        duracion_ms = (time.perf_counter() - inicio) * 1000.0

        demanda_total_top = sum(cant for _, cant in resultados)

        # Actualizar KPIs
        self.fila_kpis.controls = [
            crear_tarjeta_kpi(
                "Productos en Ranking",
                f"{len(resultados)} / {k}",
                f"Top-{k} solicitado",
                ft.Icons.LEADERBOARD,
                COLOR_PRIMARIO,
            ),
            crear_tarjeta_kpi(
                "Demanda Acumulada",
                f"{demanda_total_top:,}",
                "Unidades requeridas",
                ft.Icons.TRENDING_UP,
                COLOR_EXITO,
            ),
            crear_tarjeta_kpi(
                "Tiempo de Cómputo",
                formatear_tiempo_ms(duracion_ms),
                alg_desc,
                ft.Icons.SPEED,
                COLOR_SECUNDARIO,
            ),
            crear_tarjeta_kpi(
                "Cota de Complejidad",
                "O(N log k)" if metodo == "heap" else "O(N log N)",
                "Consumo acotado a k" if metodo == "heap" else "Ordena universo N",
                ft.Icons.MEMORY,
                COLOR_PRIMARIO,
            ),
        ]

        self.ranking_actual = list(resultados)
        self._aplicar_ordenamiento()

        self.on_actualizar_panel(
            dataset="activo",
            n_productos=len(self.motor.catalogo),
            n_pedidos=len(self.motor.pedidos),
            estrategia=self.motor.estrategia,
            tiempo_ms=duracion_ms,
            resultado_negocio=f"Top-{k} calculado con {metodo.upper()} en {formatear_tiempo_ms(duracion_ms)}",
        )
        actualizar_control(self)

    def _renderizar_ranking(self):
        items = []
        max_demanda = max((cant for _, cant in self.ranking_actual), default=1)

        for i, (prod, cantidad) in enumerate(self.ranking_actual, 1):
            color_medalla = (
                COLOR_PRIMARIO
                if i == 1
                else (COLOR_SECUNDARIO if i == 2 else ("#F59E0B" if i == 3 else COLOR_TEXTO_MUTED))
            )
            fraccion_demanda = (cantidad / max_demanda) if max_demanda > 0 else 0.0

            barra_demanda = ft.ProgressBar(
                value=fraccion_demanda,
                color=COLOR_PRIMARIO if i == 1 else COLOR_SECUNDARIO,
                bgcolor=COLOR_SUPERFICIE,
                height=4,
            )

            items.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Container(
                                        content=ft.Text(
                                            f"#{i}",
                                            size=13,
                                            weight=ft.FontWeight.BOLD,
                                            color=color_medalla,
                                        ),
                                        width=35,
                                        alignment=alineacion_center(),
                                    ),
                                    ft.Column(
                                        controls=[
                                            ft.Text(
                                                prod.nombre,
                                                size=13,
                                                weight=ft.FontWeight.W_600,
                                                color=COLOR_TEXTO_PRIMARIO,
                                            ),
                                            ft.Text(
                                                f"#{prod.id} | {prod.categoria} | Stock: {prod.stock} Unidades",
                                                size=11,
                                                color=COLOR_TEXTO_MUTED,
                                            ),
                                        ],
                                        expand=True,
                                        spacing=1,
                                    ),
                                    ft.Column(
                                        controls=[
                                            ft.Text(
                                                f"{cantidad:,} Unidades demandadas",
                                                size=12,
                                                weight=ft.FontWeight.BOLD,
                                                color=COLOR_EXITO,
                                            ),
                                            ft.Text(
                                                f"${prod.precio:,.2f} c/u",
                                                size=10.5,
                                                color=COLOR_TEXTO_MUTED,
                                            ),
                                        ],
                                        horizontal_alignment=ft.CrossAxisAlignment.END,
                                        spacing=1,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            barra_demanda,
                        ],
                        spacing=4,
                    ),
                    padding=padding_symmetric(horizontal=12, vertical=6),
                    bgcolor=COLOR_TARJETA,
                    border_radius=6,
                    border=borde_all(1, COLOR_BORDE),
                )
            )

        if not items:
            items.append(
                ft.Container(
                    content=ft.Text(
                        "No se encontraron registros de pedidos en este escenario.",
                        size=13,
                        color=COLOR_TEXTO_MUTED,
                    ),
                    padding=20,
                )
            )

        self.col_ranking.controls = items
        actualizar_control(self)
