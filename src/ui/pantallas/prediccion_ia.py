"""Pantalla de Predicción Inteligente de Demanda y Quiebre de Stock (IA).

Permite interactuar en vivo con las tres estrategias:
1. Heurística Convencional O(1) de punto de reorden
2. Modelo Supervisado scikit-learn (Ridge + LogisticRegression)
3. Cascada Híbrida en cascada reactiva

Muestra métricas de telemetría en tiempo real (latencia µs, memoria heap tracemalloc)
y listado estructurado con diagnóstico de ruta de ejecución.
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
    COLOR_PRIMARIO,
    COLOR_SECUNDARIO,
    COLOR_SUPERFICIE,
    COLOR_TARJETA,
    COLOR_TEXTO_MUTED,
    COLOR_TEXTO_PRIMARIO,
    COLOR_TEXTO_SECUNDARIO,
    FAMILIA_DATOS,
    actualizar_control,
    alineacion_center,
    borde_all,
    borde_only,
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

# Umbral de stock bajo para resaltado visual preventivo.
STOCK_BAJO_UMBRAL = 5

# Claves de ordenamiento de la tabla predictiva.
CLAVES_ORDEN_IA = {
    "probabilidad": lambda r: r.probabilidad_quiebre,
    "demanda": lambda r: r.demanda_proyectada,
    "stock": lambda r: r.stock_actual,
    "latencia": lambda r: r.tiempo_inferencia_us,
    "id": lambda r: r.id_producto,
}


def _color_por_riesgo(nivel: NivelRiesgo) -> str:
    """Devuelve el color semántico asociado al nivel de riesgo."""
    if nivel == NivelRiesgo.CRITICO:
        return COLOR_PELIGRO
    if nivel == NivelRiesgo.MEDIO:
        return COLOR_ADVERTENCIA
    return COLOR_EXITO


def _crear_badge_riesgo(nivel: NivelRiesgo) -> ft.Container:
    """Crea un badge visual accesible según el nivel de riesgo de quiebre."""
    if nivel == NivelRiesgo.CRITICO:
        texto, color, fondo = "CRÍTICO", COLOR_PELIGRO, COLOR_FONDO_PELIGRO
        icono = ft.Icons.ERROR_OUTLINE_ROUNDED
    elif nivel == NivelRiesgo.MEDIO:
        texto, color, fondo = "MEDIO", COLOR_ADVERTENCIA, COLOR_FONDO_ADVERTENCIA
        icono = ft.Icons.WARNING_AMBER_ROUNDED
    else:
        texto, color, fondo = "BAJO", COLOR_EXITO, COLOR_FONDO_EXITO
        icono = ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED

    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Icon(icono, size=13, color=color),
                ft.Text(texto, size=11, weight=ft.FontWeight.BOLD, color=color),
            ],
            spacing=4,
            tight=True,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        padding=padding_symmetric(horizontal=8, vertical=3),
        bgcolor=fondo,
        border_radius=6,
        border=borde_all(1, color),
    )


def _extraer_motor_y_diagnostico(
    resultado: ResultadoPrediccion,
) -> tuple[str, str, str, str]:
    """Deriva etiqueta de ruta ejecutada y diagnóstico legible sin duplicar métricas."""
    texto = resultado.explicacion
    if "Filtro O(1)" in texto:
        return (
            "Filtro rápido O(1)",
            COLOR_EXITO,
            COLOR_FONDO_EXITO,
            "Stock excede margen de seguridad; omitió pipeline IA.",
        )
    if "Inferencia IA" in texto or "Modelo supervisado" in texto:
        es_hib = resultado.estrategia == EstrategiaPrediccion.HIBRIDA
        etiqueta = "Cascada · ML" if es_hib else "Pipeline ML"
        if resultado.stock_actual == 0:
            detalle = "Stock agotado; quiebre crítico confirmado por ML."
        elif resultado.riesgo == NivelRiesgo.CRITICO:
            detalle = "Alto riesgo estimado por Ridge + LogReg; requiere reposición."
        else:
            detalle = "Zona de incertidumbre evaluada con 10 features temporales."
        return etiqueta, COLOR_SECUNDARIO, COLOR_SUPERFICIE, detalle
    if "Fallback" in texto or "no entrenado" in texto:
        return (
            "Fallback O(1)",
            COLOR_ADVERTENCIA,
            COLOR_FONDO_ADVERTENCIA,
            "Modelo ML sin entrenar; respaldo analítico activo.",
        )
    if resultado.stock_actual == 0:
        detalle_conv = "Stock agotado; reposición inmediata requerida."
    elif resultado.alerta_quiebre:
        detalle_conv = "Stock por debajo del punto de reorden proyectado."
    else:
        detalle_conv = "Cobertura holgada bajo regla de punto de reorden."
    return "Heurística O(1)", COLOR_TEXTO_SECUNDARIO, COLOR_SUPERFICIE, detalle_conv


def _texto_cabecera(texto: str, align: ft.TextAlign = ft.TextAlign.LEFT, **kw: Any) -> ft.Text:
    """Construye una celda de encabezado de columna consistente."""
    return ft.Text(
        texto,
        size=12,
        weight=ft.FontWeight.W_700,
        color=COLOR_TEXTO_MUTED,
        text_align=align,
        **kw,
    )


def _crear_encabezado_tabla() -> ft.Container:
    """Crea la barra de encabezados fija alineada con las columnas del listado."""
    return ft.Container(
        content=ft.Row(
            controls=[
                _texto_cabecera("ID", width=46),
                _texto_cabecera("Producto y Categoría", expand=2),
                _texto_cabecera("Stock", align=ft.TextAlign.RIGHT, width=62),
                _texto_cabecera("Demanda", align=ft.TextAlign.RIGHT, width=88),
                _texto_cabecera("Prob. Quiebre", align=ft.TextAlign.RIGHT, width=112),
                _texto_cabecera("Riesgo", align=ft.TextAlign.CENTER, width=96),
                _texto_cabecera("Latencia", align=ft.TextAlign.RIGHT, width=76),
                _texto_cabecera("Motor y Diagnóstico", expand=3),
            ],
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=padding_symmetric(horizontal=14, vertical=9),
        bgcolor=COLOR_SUPERFICIE,
        border=borde_only(bottom=ft.border.BorderSide(1, COLOR_BORDE)),
    )


def _crear_fila_resultado(r: ResultadoPrediccion) -> ft.Container:
    """Construye una fila estructurada y scannable para un resultado predictivo."""
    color_riesgo = _color_por_riesgo(r.riesgo)
    if r.stock_actual == 0:
        color_stock = COLOR_PELIGRO
    elif r.stock_actual <= STOCK_BAJO_UMBRAL:
        color_stock = COLOR_ADVERTENCIA
    else:
        color_stock = COLOR_TEXTO_PRIMARIO

    etiqueta_motor, color_motor, fondo_motor, diagnostico = _extraer_motor_y_diagnostico(r)
    chip_motor = ft.Container(
        content=ft.Text(
            etiqueta_motor,
            size=10.5,
            weight=ft.FontWeight.W_700,
            color=color_motor,
        ),
        padding=padding_symmetric(horizontal=6, vertical=2),
        bgcolor=fondo_motor,
        border=borde_all(1, color_motor if color_motor != COLOR_TEXTO_SECUNDARIO else COLOR_BORDE),
        border_radius=4,
    )

    barra_prob = ft.ProgressBar(
        value=max(0.0, min(1.0, r.probabilidad_quiebre)),
        color=color_riesgo,
        bgcolor=COLOR_SUPERFICIE,
        height=4,
        width=98,
    )

    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Text(
                    f"#{r.id_producto}",
                    size=12,
                    weight=ft.FontWeight.W_700,
                    color=COLOR_PRIMARIO,
                    font_family=FAMILIA_DATOS,
                    width=46,
                ),
                ft.Column(
                    controls=[
                        ft.Text(
                            r.nombre_producto,
                            size=13,
                            weight=ft.FontWeight.W_600,
                            color=COLOR_TEXTO_PRIMARIO,
                        ),
                        ft.Text(r.categoria, size=11, color=COLOR_TEXTO_MUTED),
                    ],
                    expand=2,
                    spacing=1,
                ),
                ft.Text(
                    str(r.stock_actual),
                    size=12.5,
                    weight=(
                        ft.FontWeight.W_700
                        if r.stock_actual <= STOCK_BAJO_UMBRAL
                        else ft.FontWeight.W_500
                    ),
                    font_family=FAMILIA_DATOS,
                    color=color_stock,
                    text_align=ft.TextAlign.RIGHT,
                    width=62,
                ),
                ft.Text(
                    f"{r.demanda_proyectada:.1f} uds",
                    size=12.5,
                    font_family=FAMILIA_DATOS,
                    color=COLOR_TEXTO_PRIMARIO,
                    text_align=ft.TextAlign.RIGHT,
                    width=88,
                ),
                ft.Column(
                    controls=[
                        ft.Text(
                            f"{r.probabilidad_quiebre * 100:.1f}%",
                            size=12.5,
                            weight=ft.FontWeight.W_700,
                            font_family=FAMILIA_DATOS,
                            color=color_riesgo,
                            text_align=ft.TextAlign.RIGHT,
                        ),
                        barra_prob,
                    ],
                    width=112,
                    spacing=4,
                    horizontal_alignment=ft.CrossAxisAlignment.END,
                ),
                ft.Container(
                    content=_crear_badge_riesgo(r.riesgo),
                    width=96,
                    alignment=alineacion_center(),
                ),
                ft.Text(
                    f"{r.tiempo_inferencia_us:.1f} µs",
                    size=12,
                    font_family=FAMILIA_DATOS,
                    color=COLOR_TEXTO_SECUNDARIO,
                    text_align=ft.TextAlign.RIGHT,
                    width=76,
                ),
                ft.Column(
                    controls=[
                        ft.Row(controls=[chip_motor], tight=True),
                        ft.Text(diagnostico, size=11.5, color=COLOR_TEXTO_SECUNDARIO),
                    ],
                    expand=3,
                    spacing=3,
                ),
            ],
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=padding_symmetric(horizontal=14, vertical=8),
        bgcolor=COLOR_TARJETA,
        border=borde_only(bottom=ft.border.BorderSide(1, COLOR_BORDE)),
    )


def _crear_estado_vacio(hay_resultados: bool) -> ft.Container:
    """Construye un mensaje centrado cuando no hay filas visibles para mostrar."""
    titulo = (
        "Sin productos para el nivel de riesgo seleccionado"
        if hay_resultados
        else "Sin predicciones calculadas"
    )
    detalle = (
        "Cambia el filtro a 'Todos los Riesgos' para visualizar el catálogo completo."
        if hay_resultados
        else "Carga un dataset o presiona 'Evaluar Catálogo' para iniciar la inferencia."
    )
    icono = ft.Icons.FILTER_ALT_OFF_ROUNDED if hay_resultados else ft.Icons.PSYCHOLOGY_OUTLINED
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Icon(icono, size=34, color=COLOR_TEXTO_MUTED),
                ft.Text(
                    titulo,
                    size=14,
                    weight=ft.FontWeight.W_600,
                    color=COLOR_TEXTO_PRIMARIO,
                ),
                ft.Text(detalle, size=12, color=COLOR_TEXTO_MUTED),
            ],
            spacing=6,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            tight=True,
        ),
        padding=padding_symmetric(horizontal=24, vertical=36),
        alignment=alineacion_center(),
    )


class PantallaPrediccionIA(PantallaBase):
    """Vista interactiva para predicción de demanda y alerta temprana de quiebres con IA."""

    def __init__(self, motor: MotorInventario, on_actualizar_panel: Any, notificar: Any) -> None:
        super().__init__(motor, on_actualizar_panel, notificar)

        self.resultados: list[ResultadoPrediccion] = []
        self.estrategia_seleccionada: EstrategiaPrediccion = EstrategiaPrediccion.HIBRIDA
        self.filtro_riesgo: str = "todos"
        self.orden_ascendente = False
        self._resumen_metricas_modelo: str = "scikit-learn Pipeline"

        # KPIs reactivos
        self.kpi_latencia = crear_tarjeta_kpi("Latencia Media", "-- µs", "Tiempo por producto")
        self.kpi_memoria = crear_tarjeta_kpi("Memoria Heap", "-- KB", "Pico tracemalloc")
        self.kpi_quiebres = crear_tarjeta_kpi("Alertas Quiebre", "--", "Productos en riesgo")
        self.kpi_modelo = crear_tarjeta_kpi(
            "Estado Modelo",
            "Entrenado" if motor.predictor_ia.modelo_ia.esta_entrenado else "No entrenado",
            self._resumen_metricas_modelo,
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

        # Controles de barra de herramientas
        self.dd_estrategia = crear_dropdown(
            label="Estrategia Predictiva",
            options=[
                ft.dropdown.Option(
                    EstrategiaPrediccion.HIBRIDA.value, "Cascada Híbrida (O(1) + IA)"
                ),
                ft.dropdown.Option(EstrategiaPrediccion.CONVENCIONAL.value, "Heurística O(1)"),
                ft.dropdown.Option(EstrategiaPrediccion.IA.value, "Modelo IA (scikit-learn)"),
            ],
            value=self.estrategia_seleccionada.value,
            width=270,
            on_change_callback=lambda e: self._al_cambiar_estrategia(e),
        )

        self.dd_riesgo = crear_dropdown(
            label="Filtrar por Riesgo",
            options=[
                ft.dropdown.Option("todos", "Todos los Riesgos"),
                ft.dropdown.Option("critico", "Crítico (Inminente)"),
                ft.dropdown.Option("medio", "Medio (Incertidumbre)"),
                ft.dropdown.Option("bajo", "Bajo (Stock Seguro)"),
            ],
            value="todos",
            width=200,
            on_change_callback=lambda e: self._al_cambiar_filtro_riesgo(e),
        )

        self.dd_orden = crear_dropdown(
            label="Ordenar por",
            options=[
                ft.dropdown.Option("probabilidad", "Prob. Quiebre"),
                ft.dropdown.Option("demanda", "Demanda Proy."),
                ft.dropdown.Option("stock", "Stock Actual"),
                ft.dropdown.Option("latencia", "Latencia (µs)"),
                ft.dropdown.Option("id", "ID del Producto"),
            ],
            value="probabilidad",
            width=175,
            on_change_callback=lambda e: self._al_cambiar_orden(e),
        )

        self.btn_sentido_orden = self._crear_boton_sentido_orden()

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

        self.txt_resumen_tabla = ft.Text(
            "Sin evaluación ejecutada",
            size=12,
            color=COLOR_TEXTO_MUTED,
        )

        self.lista_resultados = ft.ListView(spacing=0, expand=True, padding=0)

        self._construir_interfaz()
        if self.motor.catalogo.obtener_todos():
            self._ejecutar_evaluacion(None)
        else:
            self._actualizar_tabla()

    def _construir_interfaz(self) -> None:
        self.content = ft.Column(
            controls=[
                crear_encabezado(
                    titulo="Predicción Inteligente de Demanda y Quiebre de Stock (IA)",
                    subtitulo=(
                        "Contraste experimental: Heurística O(1) vs. scikit-learn "
                        "(Ridge + LogReg) vs. Cascada Híbrida."
                    ),
                    extra=self.btn_ejecutar,
                ),
                crear_banner_explicativo(
                    titulo="Enfoque Dual de IA — Cátedra de Programación Eficiente (UBP 2026)",
                    descripcion=(
                        "Cuantifica el costo computacional de la IA frente a algoritmos clásicos: "
                        "la regla O(1) opera en microsegundos sin heap, scikit-learn captura "
                        "patrones complejos y la Cascada Híbrida optimiza ambas en producción."
                    ),
                    complejidad_base="Heurística Analítica O(1) (~58 µs · 0 KB extra)",
                    complejidad_opt="Cascada Híbrida O(1)+ML (~260 µs · 5.2x speedup sobre IA)",
                    por_que_importa=(
                        "Justifica objetivamente cuándo la IA aporta valor predictivo y cuándo "
                        "una solución convencional resulta más simple, rápida y económica."
                    ),
                ),
                crear_barra_herramientas(
                    [
                        self.dd_estrategia,
                        self.dd_riesgo,
                        self.dd_orden,
                        self.btn_sentido_orden,
                        self.btn_entrenar,
                    ]
                ),
                envolver_metricas(self.fila_kpis),
                ft.Row(
                    controls=[
                        crear_titulo_seccion(
                            "Estado Predictivo de Catálogo y Diagnóstico de Ingeniería"
                        ),
                        self.txt_resumen_tabla,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                envolver_lista(self.lista_resultados, encabezado=_crear_encabezado_tabla()),
            ],
            spacing=10,
            expand=True,
        )

    def al_recargar_dataset(self) -> None:
        """Callback al recargar dataset desde la pantalla de Inicio."""
        self.resultados = []
        self._ejecutar_evaluacion(None)

    def al_cambiar_estrategia_global(self, nueva_estrategia: str) -> None:
        """Mantiene independiente la estrategia del selector predictivo de IA."""

    def _aplicar_ordenamiento(self) -> None:
        """Ordena resultados in-memory según criterio y actualiza la vista."""
        self._actualizar_tabla()

    def _al_cambiar_estrategia(self, e: ft.ControlEvent | None) -> None:
        """Actualiza la estrategia predictiva seleccionada y re-evalúa."""
        if e is not None and getattr(e, "control", None) is not None and e.control.value:
            self.dd_estrategia.value = e.control.value
        val = self.dd_estrategia.value or EstrategiaPrediccion.HIBRIDA.value
        self.estrategia_seleccionada = EstrategiaPrediccion(val)
        self._ejecutar_evaluacion(None)

    def _al_cambiar_filtro_riesgo(self, e: ft.ControlEvent | None) -> None:
        """Filtra la visualización por nivel de riesgo."""
        if e is not None and getattr(e, "control", None) is not None and e.control.value:
            self.dd_riesgo.value = e.control.value
        self.filtro_riesgo = self.dd_riesgo.value or "todos"
        self._actualizar_tabla()

    def _al_cambiar_orden(self, e: ft.ControlEvent | None) -> None:
        """Actualiza el criterio de ordenamiento y re-renderiza la tabla."""
        if e is not None and getattr(e, "control", None) is not None and e.control.value:
            self.dd_orden.value = e.control.value
        self._actualizar_tabla()

    def _reentrenar_modelo(self, e: ft.ControlEvent | None) -> None:
        """Dispara el re-entrenamiento del modelo de IA con los datos del catálogo."""
        self.notificar(
            "Entrenando modelo scikit-learn sobre el catálogo activo...",
            icono=ft.Icons.HOURGLASS_EMPTY,
        )
        t0 = time.perf_counter()
        metricas = self.motor.entrenar_modelo_ia(seed=42, periodos=20, pedidos_por_periodo=25)
        duracion_ms = (time.perf_counter() - t0) * 1000.0

        self._resumen_metricas_modelo = (
            f"F1: {metricas.f1_score:.2f} | R²: {metricas.r2_score:.2f}"
        )
        self.notificar(
            f"Modelo entrenado en {duracion_ms:.1f} ms. F1: {metricas.f1_score:.3f}, "
            f"R²: {metricas.r2_score:.3f}, MAE: {metricas.mae:.2f} uds.",
            icono=ft.Icons.CHECK_CIRCLE,
            color=COLOR_EXITO,
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
        criticos = sum(1 for r in self.resultados if r.riesgo == NivelRiesgo.CRITICO)
        medios = sum(1 for r in self.resultados if r.riesgo == NivelRiesgo.MEDIO)
        quiebres_activos = sum(1 for r in self.resultados if r.alerta_quiebre)

        self.kpi_latencia = crear_tarjeta_kpi(
            "Latencia Media", f"{latencia_us:.2f} µs", f"Total: {duracion_ms:.2f} ms"
        )
        self.kpi_memoria = crear_tarjeta_kpi(
            "Memoria Heap", f"{pico_kb:.1f} KB", "Pico tracemalloc"
        )
        self.kpi_quiebres = crear_tarjeta_kpi(
            "Alertas Quiebre",
            f"{quiebres_activos} / {n_prods}",
            f"{criticos} críticos · {medios} medios",
        )
        self.kpi_modelo = crear_tarjeta_kpi(
            "Estado Modelo",
            "Entrenado" if self.motor.predictor_ia.modelo_ia.esta_entrenado else "No entrenado",
            self._resumen_metricas_modelo,
        )
        self.fila_kpis.controls = [
            self.kpi_latencia,
            self.kpi_memoria,
            self.kpi_quiebres,
            self.kpi_modelo,
        ]

        self.on_actualizar_panel(
            dataset="activo",
            n_productos=len(self.motor.catalogo),
            n_pedidos=len(self.motor.pedidos),
            estrategia=self.motor.estrategia,
            tiempo_ms=duracion_ms,
            memoria_mb=pico_kb / 1024.0,
            resultado_negocio=f"Predicción {self.estrategia_seleccionada.value}",
        )
        self._actualizar_tabla()
        actualizar_control(self)

    def _actualizar_tabla(self) -> None:
        """Filtra, ordena y renderiza las filas estilizadas en el ListView."""
        filas_filtradas = (
            list(self.resultados)
            if self.filtro_riesgo == "todos"
            else [r for r in self.resultados if r.riesgo.value == self.filtro_riesgo]
        )

        criterio = self.dd_orden.value or "probabilidad"
        clave_orden = CLAVES_ORDEN_IA.get(criterio, CLAVES_ORDEN_IA["probabilidad"])
        filas_filtradas.sort(key=clave_orden, reverse=not self.orden_ascendente)

        if not filas_filtradas:
            self.lista_resultados.controls = [_crear_estado_vacio(bool(self.resultados))]
        else:
            self.lista_resultados.controls = [_crear_fila_resultado(r) for r in filas_filtradas]

        if self.estrategia_seleccionada == EstrategiaPrediccion.HIBRIDA and self.resultados:
            n_filtro = sum(1 for r in self.resultados if "Filtro O(1)" in r.explicacion)
            n_ml = len(self.resultados) - n_filtro
            info_ruta = f" · Cascada: {n_filtro} O(1) / {n_ml} ML"
        else:
            info_ruta = ""

        self.txt_resumen_tabla.value = (
            f"Mostrando {len(filas_filtradas)} de {len(self.resultados)} productos{info_ruta}"
        )
        actualizar_control(self.lista_resultados)
        actualizar_control(self.txt_resumen_tabla)
