"""Pantalla de Predicción Inteligente de Demanda y Quiebre de Stock (IA).

Permite interactuar en vivo con las tres estrategias:
1. Heurística Convencional O(1) de punto de reorden
2. Modelo Supervisado scikit-learn (Ridge + LogisticRegression)
3. Cascada Híbrida en cascada reactiva

Muestra métricas de telemetría en tiempo real (latencia µs, memoria heap tracemalloc)
y tabla interactiva de riesgo con justificaciones técnicas.
"""

from __future__ import annotations

import time
import tracemalloc
from typing import Any

import flet as ft

from src.ia.tipos import EstrategiaPrediccion, NivelRiesgo, ResultadoPrediccion
from src.motor.motor_inventario import MotorInventario
from src.ui.pantallas.base import PantallaBase
from src.ui.tema import (
    COLOR_ADVERTENCIA,
    COLOR_BORDE,
    COLOR_EXITO,
    COLOR_FONDO_ADVERTENCIA,
    COLOR_FONDO_EXITO,
    COLOR_FONDO_PELIGRO,
    COLOR_PELIGRO,
    COLOR_SUPERFICIE,
    COLOR_TEXTO_SECUNDARIO,
    FAMILIA_DATOS,
    actualizar_control,
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
    padding_symmetric,
)


def _crear_badge_riesgo(nivel: NivelRiesgo) -> ft.Container:
    """Crea un badge visual accesible según el nivel de riesgo de quiebre."""
    if nivel == NivelRiesgo.CRITICO:
        texto = "CRÍTICO"
        color = COLOR_PELIGRO
        fondo = COLOR_FONDO_PELIGRO
        icono = ft.Icons.ERROR_OUTLINE_ROUNDED
    elif nivel == NivelRiesgo.MEDIO:
        texto = "MEDIO"
        color = COLOR_ADVERTENCIA
        fondo = COLOR_FONDO_ADVERTENCIA
        icono = ft.Icons.WARNING_AMBER_ROUNDED
    else:
        texto = "BAJO"
        color = COLOR_EXITO
        fondo = COLOR_FONDO_EXITO
        icono = ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED

    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Icon(icono, size=14, color=color),
                ft.Text(texto, size=11, weight=ft.FontWeight.BOLD, color=color),
            ],
            spacing=4,
            tight=True,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        padding=padding_symmetric(horizontal=8, vertical=2),
        bgcolor=fondo,
        border_radius=4,
        border=borde_all(1, color),
    )


class PantallaPrediccionIA(PantallaBase):
    """Vista interactiva para predicción de demanda y alerta temprana de quiebres con IA."""

    def __init__(self, motor: MotorInventario, on_actualizar_panel: Any, notificar: Any) -> None:
        super().__init__(motor, on_actualizar_panel, notificar)

        self.resultados: list[ResultadoPrediccion] = []
        self.estrategia_seleccionada: EstrategiaPrediccion = EstrategiaPrediccion.HIBRIDA
        self.filtro_riesgo: str = "todos"

        # KPIs reactivos
        self.kpi_latencia = crear_tarjeta_kpi("Latencia Media", "-- µs", "Tiempo por producto")
        self.kpi_memoria = crear_tarjeta_kpi("Memoria Heap", "-- KB", "Pico tracemalloc")
        self.kpi_quiebres = crear_tarjeta_kpi("Alertas Quiebre", "--", "Productos en riesgo")
        self.kpi_modelo = crear_tarjeta_kpi(
            "Estado Modelo",
            "Entrenado" if motor.predictor_ia.modelo_ia.esta_entrenado else "No entrenado",
            "scikit-learn Pipeline",
        )
        self.fila_kpis = ft.Row(
            controls=[
                self.kpi_latencia,
                self.kpi_memoria,
                self.kpi_quiebres,
                self.kpi_modelo,
            ],
            spacing=0,
        )

        # Controles
        self.dd_estrategia = crear_dropdown(
            label="Estrategia Predictiva",
            options=[
                ft.dropdown.Option(
                    EstrategiaPrediccion.HIBRIDA.value, "Cascada Híbrida (O(1) + IA)"
                ),
                ft.dropdown.Option(
                    EstrategiaPrediccion.CONVENCIONAL.value, "Heurística Convencional O(1)"
                ),
                ft.dropdown.Option(
                    EstrategiaPrediccion.IA.value, "Modelo Supervisado IA (scikit-learn)"
                ),
            ],
            value=self.estrategia_seleccionada.value,
            width=260,
            on_change_callback=lambda _: self._al_cambiar_estrategia(None),
        )

        self.dd_riesgo = crear_dropdown(
            label="Filtrar por Riesgo",
            options=[
                ft.dropdown.Option("todos", "Todos los Niveles"),
                ft.dropdown.Option("critico", "Solo Crítico (Quiebre Inminente)"),
                ft.dropdown.Option("medio", "Riesgo Medio (Incertidumbre)"),
                ft.dropdown.Option("bajo", "Riesgo Bajo (Stock Abundante)"),
            ],
            value="todos",
            width=220,
            on_change_callback=lambda _: self._al_cambiar_filtro_riesgo(None),
        )

        self.btn_ejecutar = ft.FilledButton(
            "Evaluar Catálogo",
            icon=ft.Icons.AUTO_AWESOME_ROUNDED,
            style=estilo_boton_primario(),
            on_click=lambda _: self._ejecutar_evaluacion(None),
        )

        self.btn_entrenar = ft.OutlinedButton(
            "Re-entrenar Modelo",
            icon=ft.Icons.MODEL_TRAINING_ROUNDED,
            on_click=lambda _: self._reentrenar_modelo(None),
        )

        # Tabla de resultados
        self.tabla_resultados = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID", font_family=FAMILIA_DATOS, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Producto", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Categoría", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Stock", weight=ft.FontWeight.BOLD), numeric=True),
                ft.DataColumn(ft.Text("Demanda Proy.", weight=ft.FontWeight.BOLD), numeric=True),
                ft.DataColumn(ft.Text("Prob. Quiebre", weight=ft.FontWeight.BOLD), numeric=True),
                ft.DataColumn(ft.Text("Riesgo", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Latencia", weight=ft.FontWeight.BOLD), numeric=True),
                ft.DataColumn(ft.Text("Justificación Técnica", weight=ft.FontWeight.BOLD)),
            ],
            rows=[],
            heading_row_color=COLOR_SUPERFICIE,
            border=borde_all(1, COLOR_BORDE),
            horizontal_margin=12,
            column_spacing=16,
        )
        self.col_tabla = ft.ListView([self.tabla_resultados], expand=True, padding=8)

        # Construcción visual de la pantalla
        self._construir_interfaz()

    def _construir_interfaz(self) -> None:
        self.content = ft.Column(
            controls=[
                crear_encabezado(
                    titulo="Predicción Inteligente de Demanda y Quiebre de Stock (IA)",
                    subtitulo=(
                        "Enfrentamiento experimental: Heurística O(1) vs. Pipeline scikit-learn "
                        "vs. Cascada Híbrida."
                    ),
                    extra=self.btn_ejecutar,
                ),
                crear_banner_explicativo(
                    titulo="Enfoque Dual de IA — Cátedra de Programación Eficiente (UBP 2026)",
                    descripcion=(
                        "Demuestra y cuantifica empíricamente el costo computacional de la IA: "
                        "mientras la fórmula O(1) opera en < 60 µs sin heap, scikit-learn predice "
                        "quiebres futuros con overhead medido. La cascada híbrida combina ambas."
                    ),
                    complejidad_base="O(1) / ~58 µs (Convencional sin overhead)",
                    complejidad_opt=(
                        "Ridge + LogReg (~1360 µs) / Cascada Híbrida (~260 µs, 5x speedup)"
                    ),
                    por_que_importa=(
                        "Permite justificar objetivamente cuándo la IA aporta valor predictivo y "
                        "cuándo una solución algorítmica convencional resulta más simple y rápida."
                    ),
                ),
                envolver_metricas(self.fila_kpis),
                crear_barra_herramientas(
                    [
                        self.dd_estrategia,
                        self.dd_riesgo,
                        self.btn_ejecutar,
                        self.btn_entrenar,
                    ]
                ),
                crear_titulo_seccion(
                    "Estado Predictivo de Catálogo y Justificación de Ingeniería"
                ),
                envolver_lista(self.col_tabla),
            ],
            spacing=10,
            expand=True,
        )

    def al_recargar_dataset(self) -> None:
        """Callback al recargar dataset desde la barra lateral."""
        self.resultados = []
        self._ejecutar_evaluacion(None)

    def al_cambiar_estrategia_global(self, nueva_estrategia: str) -> None:
        """No afecta la estrategia interna de predicción IA."""

    def _al_cambiar_estrategia(self, e: ft.ControlEvent | None) -> None:
        """Actualiza la estrategia predictiva seleccionada."""
        val = self.dd_estrategia.value or EstrategiaPrediccion.HIBRIDA.value
        self.estrategia_seleccionada = EstrategiaPrediccion(val)
        if self.resultados:
            self._ejecutar_evaluacion(None)

    def _al_cambiar_filtro_riesgo(self, e: ft.ControlEvent | None) -> None:
        """Filtra la visualización por nivel de riesgo."""
        self.filtro_riesgo = self.dd_riesgo.value or "todos"
        self._actualizar_tabla()

    def _reentrenar_modelo(self, e: ft.ControlEvent | None) -> None:
        """Dispara el re-entrenamiento del modelo de IA con los datos del catálogo."""
        self.notificar("Entrenando modelo scikit-learn sobre el catálogo activo...", tipo="info")
        t0 = time.perf_counter()
        metricas = self.motor.entrenar_modelo_ia(seed=42, periodos=20, pedidos_por_periodo=25)
        duracion_ms = (time.perf_counter() - t0) * 1000.0

        # Actualizar KPI
        self.kpi_modelo.content.controls[1].value = (
            f"F1: {metricas.f1_score:.2f} | R²: {metricas.r2_score:.2f}"
        )
        actualizar_control(self.kpi_modelo)

        self.notificar(
            f"Modelo entrenado en {duracion_ms:.1f} ms. F1: {metricas.f1_score:.3f}, "
            f"R²: {metricas.r2_score:.3f}, MAE: {metricas.mae:.2f} uds.",
            tipo="exito",
        )
        self._ejecutar_evaluacion(None)

    def _ejecutar_evaluacion(self, e: ft.ControlEvent | None) -> None:
        """Ejecuta la inferencia sobre el catálogo completo y actualiza KPIs y tabla."""
        tracemalloc.start()
        inicio_bytes, _ = tracemalloc.get_traced_memory()
        t0 = time.perf_counter_ns()

        self.resultados = self.motor.predecir_quiebres_stock(
            estrategia=self.estrategia_seleccionada
        )

        t_fin = time.perf_counter_ns()
        _, fin_pico = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        duracion_ms = (t_fin - t0) / 1_000_000.0
        n_prods = len(self.resultados)
        latencia_us = (duracion_ms * 1000.0) / max(1, n_prods)
        pico_kb = max(0.0, (fin_pico - inicio_bytes) / 1024.0)
        quiebres_activos = sum(1 for r in self.resultados if r.alerta_quiebre)

        # Actualizar KPIs
        self.kpi_latencia.content.controls[1].value = f"{latencia_us:.2f} µs"
        self.kpi_memoria.content.controls[1].value = f"{pico_kb:.1f} KB"
        self.kpi_quiebres.content.controls[1].value = f"{quiebres_activos} / {n_prods}"
        self.kpi_modelo.content.controls[1].value = (
            "Entrenado" if self.motor.predictor_ia.modelo_ia.esta_entrenado else "No entrenado"
        )

        actualizar_control(self.kpi_latencia)
        actualizar_control(self.kpi_memoria)
        actualizar_control(self.kpi_quiebres)
        actualizar_control(self.kpi_modelo)

        self._publicar_resultado(duracion_ms, f"Predicción {self.estrategia_seleccionada.value}")
        self._actualizar_tabla()

    def _actualizar_tabla(self) -> None:
        """Filtra y renderiza las filas de la tabla de resultados."""
        filas_filtradas = self.resultados
        if self.filtro_riesgo != "todos":
            filas_filtradas = [
                r for r in self.resultados if r.riesgo.value == self.filtro_riesgo
            ]

        nuevas_filas: list[ft.DataRow] = []
        for r in filas_filtradas:
            badge_riesgo = _crear_badge_riesgo(r.riesgo)

            nuevas_filas.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(r.id_producto), font_family=FAMILIA_DATOS)),
                        ft.DataCell(ft.Text(r.nombre_producto, weight=ft.FontWeight.W_500)),
                        ft.DataCell(ft.Text(r.categoria, color=COLOR_TEXTO_SECUNDARIO)),
                        ft.DataCell(
                            ft.Text(
                                str(r.stock_actual),
                                font_family=FAMILIA_DATOS,
                                color=COLOR_PELIGRO if r.stock_actual == 0 else None,
                            )
                        ),
                        ft.DataCell(
                            ft.Text(f"{r.demanda_proyectada:.1f}", font_family=FAMILIA_DATOS)
                        ),
                        ft.DataCell(
                            ft.Text(
                                f"{r.probabilidad_quiebre * 100:.1f}%",
                                font_family=FAMILIA_DATOS,
                                weight=ft.FontWeight.BOLD,
                            )
                        ),
                        ft.DataCell(badge_riesgo),
                        ft.DataCell(
                            ft.Text(f"{r.tiempo_inferencia_us:.1f} µs", font_family=FAMILIA_DATOS)
                        ),
                        ft.DataCell(
                            ft.Text(
                                r.explicacion,
                                size=11,
                                color=COLOR_TEXTO_SECUNDARIO,
                                max_lines=2,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            )
                        ),
                    ]
                )
            )

        self.tabla_resultados.rows = nuevas_filas
        actualizar_control(self.tabla_resultados)
