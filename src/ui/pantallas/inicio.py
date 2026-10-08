"""Pantalla de Inicio y Selección de Escenarios / Datasets."""

from __future__ import annotations

import time
from pathlib import Path

import flet as ft

from src.datos.generador_archivos import generar_archivos_grandes_jsonl
from src.motor.motor_inventario import MotorInventario
from src.ui.pantallas.base import PantallaBase
from src.ui.tema import (
    COLOR_BORDE,
    COLOR_EXITO,
    COLOR_PRIMARIO,
    COLOR_SECUNDARIO,
    COLOR_TARJETA,
    COLOR_TEXTO_MUTED,
    COLOR_TEXTO_PRIMARIO,
    COLOR_TEXTO_SECUNDARIO,
    actualizar_control,
    borde_all,
    crear_badge_tiempo,
    crear_banner_explicativo,
    crear_barra_herramientas,
    crear_encabezado,
    crear_tarjeta_kpi,
    crear_titulo_seccion,
    envolver_metricas,
    estilo_boton_primario,
    formatear_tiempo_ms,
    padding_symmetric,
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATASETS_DIR = BASE_DIR / "data" / "datasets"
GENERADOS_DIR = BASE_DIR / "data" / "generados"


class PantallaInicio(PantallaBase):
    """Vista principal de bienvenida, carga de datos y ejecución global de escenarios."""

    def __init__(
        self, motor: MotorInventario, on_actualizar_panel, notificar, on_dataset_cambiado=None
    ) -> None:
        super().__init__(motor, on_actualizar_panel, notificar)
        self.on_dataset_cambiado = on_dataset_cambiado

        # Dropdown de datasets estándar y masivo
        self.dropdown_datasets = ft.Dropdown(
            label="Dataset empaquetado",
            options=[
                ft.dropdown.Option(
                    "demo_oral.json", "demo_oral.json (30 productos, 8 pedidos - Oral)"
                ),
                ft.dropdown.Option(
                    "pequeno.json", "pequeno.json (100 productos, 20 pedidos - Rápido)"
                ),
                ft.dropdown.Option(
                    "mediano.json", "mediano.json (1.000 productos, 200 pedidos - Medio)"
                ),
                ft.dropdown.Option(
                    "grande.json", "grande.json (10.000 productos, 2.000 pedidos - Grande)"
                ),
                ft.dropdown.Option(
                    "masivo.jsonl", "masivo.jsonl (10.000 prod, 50.000 ped - Streaming JSONL)"
                ),
            ],
            value="demo_oral.json",
            border_color=COLOR_BORDE,
            focused_border_color=COLOR_PRIMARIO,
            color=COLOR_TEXTO_PRIMARIO,
            width=380,
            dense=True,
            on_select=self._al_seleccionar_dataset,
        )

        self.btn_cargar = ft.FilledButton(
            "Recargar",
            icon=ft.Icons.REFRESH,
            style=estilo_boton_primario(),
            on_click=lambda _: self._cargar_dataset_actual(),
        )

        self.btn_ejecutar_escenario = ft.FilledButton(
            "Ejecutar Escenario",
            icon=ft.Icons.PLAY_ARROW_ROUNDED,
            style=estilo_boton_primario(),
            on_click=lambda _: self._ejecutar_escenario_completo(),
        )

        self.barra_progreso = ft.ProgressBar(
            visible=False, width=380, color=COLOR_PRIMARIO, bgcolor=COLOR_BORDE
        )

        # Contenedores de KPIs dinámicos
        self.fila_kpis = ft.Row(spacing=0)
        # Contenedor de resultados del escenario completo
        self.col_resultado_escenario = ft.Column(spacing=4)
        self.fila_tiempo_escenario = ft.Row(spacing=6)

        self._construir_interfaz()
        self._actualizar_metricas_visuales()

    def _construir_interfaz(self) -> None:
        self.content = ft.Column(
            expand=True,
            controls=[
                crear_encabezado(
                    "Optimizador de Inventario y Pedidos",
                    "Primer Parcial – Programación Eficiente (Opción 6) | Universidad Blas Pascal",
                ),
                crear_banner_explicativo(
                    titulo="Gestión Logística y Optimización a Escala",
                    descripcion=(
                        "Simulación de almacén inteligente para comparar estrategias ingenuas vs. "
                        "optimizadas ante catálogos crecientes."
                    ),
                    complejidad_base="Operaciones no coordinadas O(n) a O(P·L·n)",
                    complejidad_opt="Flujo integral hash y sub-lineal O(1) a O(L)",
                    por_que_importa=(
                        "Permite auditar el impacto marginal de cada técnica algorítmica sobre el "
                        "mismo volumen de datos."
                    ),
                ),
                crear_barra_herramientas(
                    [
                        self.dropdown_datasets,
                        self.btn_cargar,
                        self.btn_ejecutar_escenario,
                    ]
                ),
                self.barra_progreso,
                envolver_metricas(self.fila_kpis),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    crear_titulo_seccion(
                                        "Diagnóstico y Ejecución Global del Escenario"
                                    ),
                                    ft.Container(expand=True),
                                    self.fila_tiempo_escenario,
                                ],
                                spacing=8,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Text(
                                (
                                    "Al presionar 'Ejecutar Escenario', el motor procesa "
                                    "secuencialmente pedidos, batch picking, ranking Top-N y "
                                    "cálculo de alternativas sustitutas para faltantes."
                                ),
                                size=12,
                                color=COLOR_TEXTO_MUTED,
                            ),
                            self.col_resultado_escenario,
                        ],
                        spacing=6,
                    ),
                    padding=padding_symmetric(horizontal=12, vertical=10),
                    bgcolor=COLOR_TARJETA,
                    border_radius=6,
                    border=borde_all(1, COLOR_BORDE),
                ),
            ],
            spacing=12,
        )

    def _al_seleccionar_dataset(self, e):
        self._cargar_dataset_actual()

    def _cargar_dataset_actual(self):
        nombre = self.dropdown_datasets.value
        if nombre == "masivo.jsonl":
            ruta_prods = GENERADOS_DIR / "productos.jsonl"
            ruta_peds = GENERADOS_DIR / "pedidos.jsonl"
            try:
                self.barra_progreso.visible = True
                actualizar_control(self.barra_progreso)
                if not ruta_prods.is_file() or not ruta_peds.is_file():
                    self.notificar(
                        "Generando archivos JSON Lines masivos deterministas...",
                        ft.Icons.HOURGLASS_BOTTOM,
                    )
                    generar_archivos_grandes_jsonl(
                        GENERADOS_DIR, n_productos=10000, n_pedidos=50000, seed=42
                    )

                inicio = time.perf_counter()
                self.motor.cargar_dataset_jsonl(ruta_prods, ruta_peds)
                duracion_ms = (time.perf_counter() - inicio) * 1000.0

                self.barra_progreso.visible = False
                actualizar_control(self.barra_progreso)
                self._actualizar_metricas_visuales()
                stats = self.motor.obtener_estadisticas()
                self.on_actualizar_panel(
                    dataset=nombre,
                    n_productos=stats["total_productos"],
                    n_pedidos=stats["total_pedidos"],
                    estrategia=self.motor.estrategia,
                    tiempo_ms=duracion_ms,
                    resultado_negocio=(
                        "Dataset masivo cargado en streaming en "
                        f"{formatear_tiempo_ms(duracion_ms)}"
                    ),
                )
                if self.on_dataset_cambiado:
                    self.on_dataset_cambiado(nombre)
                self.notificar(f"Dataset streaming '{nombre}' cargado con éxito.", ft.Icons.CHECK)
            except Exception as err:
                self.barra_progreso.visible = False
                actualizar_control(self.barra_progreso)
                self.notificar(
                    f"Error al cargar dataset masivo: {err}", ft.Icons.ERROR, color=COLOR_EXITO
                )
            return

        ruta = DATASETS_DIR / nombre
        try:
            inicio = time.perf_counter()
            self.motor.cargar_dataset(ruta)
            duracion_ms = (time.perf_counter() - inicio) * 1000.0

            self._actualizar_metricas_visuales()
            stats = self.motor.obtener_estadisticas()
            self.on_actualizar_panel(
                dataset=nombre,
                n_productos=stats["total_productos"],
                n_pedidos=stats["total_pedidos"],
                estrategia=self.motor.estrategia,
                tiempo_ms=duracion_ms,
                resultado_negocio=(
                    f"Dataset {nombre} cargado en {formatear_tiempo_ms(duracion_ms)}"
                ),
            )
            if self.on_dataset_cambiado:
                self.on_dataset_cambiado(nombre)
            self.notificar(f"Dataset '{nombre}' cargado con éxito.", ft.Icons.CHECK)
        except Exception as err:
            self.notificar(f"Error al cargar dataset: {err}", ft.Icons.ERROR, color=COLOR_EXITO)

    def _actualizar_metricas_visuales(self):
        stats = self.motor.obtener_estadisticas()
        self.fila_kpis.controls = [
            crear_tarjeta_kpi(
                "Catálogo de Productos",
                f"{stats['total_productos']:,}",
                f"{stats['total_categorias']} categorías registradas",
                ft.Icons.INVENTORY_2,
                COLOR_PRIMARIO,
            ),
            crear_tarjeta_kpi(
                "Lote de Pedidos",
                f"{stats['total_pedidos']:,}",
                f"{stats['total_lineas_pedidos']} líneas de demanda",
                ft.Icons.SHOPPING_BAG,
                COLOR_SECUNDARIO,
            ),
            crear_tarjeta_kpi(
                "Unidades en Stock",
                f"{stats['stock_total_unidades']:,}",
                "Disponibilidad total en almacén",
                ft.Icons.WAREHOUSE,
                COLOR_EXITO,
            ),
            crear_tarjeta_kpi(
                "Demanda Total",
                f"{stats['unidades_demandadas']:,}",
                f"Estrategia: {self.motor.estrategia.upper()}",
                ft.Icons.TRENDING_UP,
                COLOR_PRIMARIO,
            ),
        ]
        actualizar_control(self)

    def al_cambiar_estrategia_global(self, nueva_estrategia: str) -> None:
        """Refresca las métricas de la pantalla con la estrategia nueva."""
        self._actualizar_metricas_visuales()

    def _ejecutar_escenario_completo(self):
        try:
            inicio_total = time.perf_counter()

            # 1. Preparar pedidos
            res_pedidos = self.motor.procesar_pedidos(concurrente=False, descontar_stock=False)
            # 2. Batch picking
            picking = self.motor.agrupar_pedidos()
            # 3. Top-N
            top_5 = self.motor.obtener_top_solicitados(k=5)

            # 4. Alternativas para el primer pedido con faltantes (si existe)
            pedido_faltante = next((r for r in res_pedidos.resultados if not r.es_exitoso), None)
            res_alternativas = None
            if pedido_faltante and pedido_faltante.lineas_faltantes:
                linea_f = pedido_faltante.lineas_faltantes[0]
                prod_f = self.motor.buscar_por_id(linea_f.id_producto)
                if prod_f:
                    presupuesto = prod_f.precio * linea_f.cantidad_solicitada
                    res_alternativas = self.motor.buscar_alternativas(
                        categoria=prod_f.categoria,
                        presupuesto_maximo=max(presupuesto, 10000.0),
                        producto_original=prod_f,
                        max_combinaciones=3,
                    )

            duracion_total_ms = (time.perf_counter() - inicio_total) * 1000.0
            self.fila_tiempo_escenario.controls = [crear_badge_tiempo(duracion_total_ms)]

            # Renderizar resumen compacto
            items_resumen = [
                ft.ListTile(
                    leading=ft.Icon(
                        ft.Icons.SHOPPING_CART_CHECKOUT, color=COLOR_PRIMARIO, size=18
                    ),
                    title=ft.Text(
                        f"Preparación de Pedidos: {res_pedidos.pedidos_procesados} pedidos",
                        size=13,
                        weight=ft.FontWeight.BOLD,
                    ),
                    subtitle=ft.Text(
                        f"Cubiertos: {res_pedidos.pedidos_cubiertos} | "
                        f"Parciales: {res_pedidos.pedidos_parciales} | "
                        f"Imposibles: {res_pedidos.pedidos_imposibles} "
                        f"({formatear_tiempo_ms(res_pedidos.tiempo_ejecucion_ms)})",
                        size=11,
                        color=COLOR_TEXTO_SECUNDARIO,
                    ),
                    dense=True,
                ),
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.ALL_INBOX, color=COLOR_SECUNDARIO, size=18),
                    title=ft.Text(
                        (
                            f"Batch Picking Consolidado: {picking.total_productos_distintos} "
                            "productos únicos"
                        ),
                        size=13,
                        weight=ft.FontWeight.BOLD,
                    ),
                    subtitle=ft.Text(
                        (
                            f"Total unidades a recolectar: {picking.total_unidades} en "
                            f"{picking.total_pedidos} pedidos."
                        ),
                        size=11,
                        color=COLOR_TEXTO_SECUNDARIO,
                    ),
                    dense=True,
                ),
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.LEADERBOARD, color=COLOR_EXITO, size=18),
                    title=ft.Text(
                        "Productos Top-3 más solicitados", size=13, weight=ft.FontWeight.BOLD
                    ),
                    subtitle=ft.Text(
                        ", ".join(f"{p.nombre} ({c} Unidades)" for p, c in top_5[:3])
                        if top_5
                        else "Sin demanda",
                        size=11,
                        color=COLOR_TEXTO_SECUNDARIO,
                    ),
                    dense=True,
                ),
            ]

            if res_alternativas and res_alternativas.total_combinaciones > 0:
                items_resumen.append(
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.SWAP_HORIZ, color="#F59E0B", size=18),
                        title=ft.Text(
                            f"Alternativas para Pedido #{pedido_faltante.id_pedido}",
                            size=13,
                            weight=ft.FontWeight.BOLD,
                        ),
                        subtitle=ft.Text(
                            (
                                f"{res_alternativas.total_combinaciones} combinaciones en "
                                f"{res_alternativas.categoria} ("
                                f"{formatear_tiempo_ms(res_alternativas.tiempo_ejecucion_ms)})."
                            ),
                            size=11,
                            color=COLOR_TEXTO_SECUNDARIO,
                        ),
                        dense=True,
                    )
                )

            self.col_resultado_escenario.controls = items_resumen
            self._publicar_resultado(
                tiempo_ms=duracion_total_ms,
                resultado_negocio=(
                    f"Escenario ejecutado: {res_pedidos.pedidos_cubiertos}/"
                    f"{res_pedidos.pedidos_procesados} cubiertos"
                ),
                dataset=self.dropdown_datasets.value,
            )
            actualizar_control(self)
            self.notificar(
                f"Escenario completo ejecutado en {formatear_tiempo_ms(duracion_total_ms)}.",
                ft.Icons.DONE_ALL,
            )
        except Exception as err:
            self.notificar(f"Error en ejecución de escenario: {err}", ft.Icons.ERROR)
