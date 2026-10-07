"""Sistema de diseño Cloudscape / AWS Console.

Navegación oscura, contenido claro, acción naranja. Dualidad Baseline | Optimizado.
"""

from __future__ import annotations

import contextlib

import flet as ft

# Cromo de consola (top nav + side nav)
COLOR_NAV = "#161D26"
COLOR_NAV_HOVER = "#232F3E"
COLOR_NAV_TEXTO = "#FBFBFB"
COLOR_NAV_MUTED = "#B6BEC9"
COLOR_NAV_BORDE = "#2A3542"

# Contenido (layout main + containers)
COLOR_FONDO_APP = "#F2F3F3"
COLOR_SUPERFICIE = "#F2F3F3"
COLOR_TARJETA = "#FFFFFF"
COLOR_TARJETA_HOVER = "#F9F9FA"
COLOR_BORDE = "#E9EBED"
COLOR_BORDE_ENFOQUE = "#0972D3"

COLOR_TEXTO_PRIMARIO = "#0F141A"
COLOR_TEXTO_SECUNDARIO = "#414D5C"
COLOR_TEXTO_MUTED = "#5F6B7A"

# Naranja de consola para la acción; azul para foco y vínculos
COLOR_PRIMARIO = "#EC7211"
COLOR_PRIMARIO_VARIANTE = "#EB5F07"
COLOR_SECUNDARIO = "#0972D3"
COLOR_SECUNDARIO_VARIANTE = "#033160"
COLOR_MARCA = "#FF9900"

COLOR_EXITO = "#037F0C"
COLOR_FONDO_EXITO = "#F2F8F3"
COLOR_ADVERTENCIA = "#8D6605"
COLOR_FONDO_ADVERTENCIA = "#FFFCE9"
COLOR_PELIGRO = "#D91515"
COLOR_FONDO_PELIGRO = "#FDF3F3"

FAMILIA_DATOS = "Consolas"
RADIO = 8
TAM_TITULO = 20
TAM_CUERPO = 13
TAM_ETIQUETA = 12
TAM_DATO = 22


def borde_all(ancho: float = 1, color: str = COLOR_BORDE) -> ft.border.Border:
    """Crea un borde completo compatible con todas las versiones de Flet."""
    if hasattr(ft.border, "all"):
        return ft.border.all(ancho, color)
    return ft.border.Border.all(ancho, color)


def borde_only(
    bottom: ft.border.BorderSide | None = None,
    top: ft.border.BorderSide | None = None,
    left: ft.border.BorderSide | None = None,
    right: ft.border.BorderSide | None = None,
) -> ft.border.Border:
    """Crea un borde parcial compatible con todas las versiones de Flet."""
    if hasattr(ft.border, "only"):
        return ft.border.only(bottom=bottom, top=top, left=left, right=right)
    return ft.border.Border.only(bottom=bottom, top=top, left=left, right=right)


def padding_symmetric(horizontal: float = 0, vertical: float = 0) -> ft.padding.Padding:
    """Crea un padding simétrico compatible con todas las versiones de Flet."""
    if hasattr(ft.padding, "symmetric"):
        return ft.padding.symmetric(horizontal=horizontal, vertical=vertical)
    return ft.padding.Padding.symmetric(horizontal=horizontal, vertical=vertical)


def padding_all(valor: float) -> ft.padding.Padding:
    """Crea un padding uniforme compatible con todas las versiones de Flet."""
    if hasattr(ft.padding, "all"):
        return ft.padding.all(valor)
    return ft.padding.Padding.all(valor)


def alineacion_center() -> ft.alignment.Alignment:
    """Retorna alineación central compatible con versiones antiguas y nuevas de Flet."""
    if hasattr(ft.alignment, "center"):
        return ft.alignment.center
    return ft.alignment.Alignment.CENTER


def actualizar_control(control) -> None:
    """Invoca update() de forma segura capturando excepciones si el control aún no está montado."""
    with contextlib.suppress(Exception):
        control.update()


def estilo_boton_primario() -> ft.ButtonStyle:
    """Botón de acción principal."""
    return ft.ButtonStyle(
        bgcolor=COLOR_PRIMARIO,
        color="#FFFFFF",
        padding=padding_symmetric(horizontal=16, vertical=8),
        shape=ft.RoundedRectangleBorder(radius=RADIO),
    )


def crear_encabezado(titulo: str, subtitulo: str, extra=None) -> ft.Row:
    """Título de pantalla + acción. Sin divisor extra."""
    controles = [
        ft.Column(
            controls=[
                ft.Text(
                    titulo, size=TAM_TITULO, weight=ft.FontWeight.W_600, color=COLOR_TEXTO_PRIMARIO
                ),
                ft.Text(subtitulo, size=TAM_CUERPO, color=COLOR_TEXTO_MUTED),
            ],
            spacing=2,
            tight=True,
        ),
    ]
    if extra is not None:
        controles.append(extra)
    return ft.Row(
        controls=controles,
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=12,
    )


def crear_barra_herramientas(controles: list, wrap: bool = True) -> ft.Container:
    """Barra de filtros estilo consola, en un contenedor blanco."""
    return ft.Container(
        content=ft.Row(
            controls=controles,
            spacing=8,
            wrap=wrap,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=padding_symmetric(horizontal=12, vertical=8),
        bgcolor=COLOR_TARJETA,
        border=borde_all(1, COLOR_BORDE),
        border_radius=RADIO,
    )


def envolver_lista(lista: ft.ListView, encabezado: ft.Control | None = None) -> ft.Container:
    """Tabla scrolleable con altura acotada. Evita que la lista colapse a 0."""
    lista.expand = True
    controles = [encabezado, lista] if encabezado is not None else [lista]
    return ft.Container(
        content=ft.Column(controls=controles, spacing=0, expand=True),
        expand=True,
        bgcolor=COLOR_TARJETA,
        border=borde_all(1, COLOR_BORDE),
        border_radius=RADIO,
    )


def crear_titulo_seccion(texto: str) -> ft.Text:
    """Etiqueta de lista o bloque."""
    return ft.Text(texto, size=TAM_ETIQUETA, weight=ft.FontWeight.W_600, color=COLOR_TEXTO_MUTED)


def envolver_metricas(fila: ft.Row) -> ft.Container:
    """Une las celdas KPI en una sola franja."""
    fila.spacing = 0
    return ft.Container(
        content=fila,
        bgcolor=COLOR_TARJETA,
        border=borde_all(1, COLOR_BORDE),
        border_radius=RADIO,
    )


def formatear_tiempo_ms(tiempo_ms: float) -> str:
    """Formatea un tiempo de pared siempre en milisegundos (ms)."""
    if tiempo_ms < 1.0:
        return f"{tiempo_ms:.3f} ms"
    return f"{tiempo_ms:.2f} ms"


def crear_dropdown(
    label: str,
    options: list[ft.dropdown.Option],
    value: str,
    on_change_callback=None,
    width: float | None = None,
    **kwargs,
) -> ft.Dropdown:
    """Crea un Dropdown compatible con versiones antiguas (on_change) y nuevas (on_select) de Flet."""
    params = {
        "label": label,
        "options": options,
        "value": value,
        "border_color": COLOR_BORDE,
        "focused_border_color": COLOR_BORDE_ENFOQUE,
        "color": COLOR_TEXTO_PRIMARIO,
        "bgcolor": COLOR_TARJETA,
        "border_radius": RADIO,
        **kwargs,
    }
    if width is not None:
        params["width"] = width

    if on_change_callback is not None:
        try:
            return ft.Dropdown(**params, on_select=on_change_callback)
        except TypeError:
            return ft.Dropdown(**params, on_change=on_change_callback)
    return ft.Dropdown(**params)


def crear_badge_estado(estado: str) -> ft.Container:
    """Crea un indicador visual accesible con icono y texto explícito."""
    estado_norm = estado.lower().strip()
    if estado_norm in ("cubierto", "exito", "ok"):
        icono = ft.Icons.CHECK_CIRCLE
        color_texto = COLOR_EXITO
        color_fondo = COLOR_FONDO_EXITO
        texto = "Cubierto"
    elif estado_norm in ("parcial", "warning", "advertencia"):
        icono = ft.Icons.WARNING_AMBER_ROUNDED
        color_texto = COLOR_ADVERTENCIA
        color_fondo = COLOR_FONDO_ADVERTENCIA
        texto = "Parcial"
    else:
        icono = ft.Icons.CANCEL_ROUNDED
        color_texto = COLOR_PELIGRO
        color_fondo = COLOR_FONDO_PELIGRO
        texto = "Imposible"

    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Icon(icono, size=16, color=color_texto),
                ft.Text(value=texto, size=12, weight=ft.FontWeight.W_600, color=color_texto),
            ],
            spacing=4,
            tight=True,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        padding=padding_symmetric(horizontal=8, vertical=3),
        bgcolor=color_fondo,
        border_radius=RADIO,
        border=borde_all(1, color_texto),
    )


def crear_tarjeta_kpi(
    titulo: str,
    valor: str,
    subtitulo: str | None = None,
    icono: str = ft.Icons.INFO_OUTLINE,
    color_icono: str = COLOR_PRIMARIO,
) -> ft.Container:
    """Celda de métrica: etiqueta, valor, nota."""
    controles = [
        ft.Text(
            value=titulo,
            size=TAM_ETIQUETA,
            weight=ft.FontWeight.W_500,
            color=COLOR_TEXTO_MUTED,
            no_wrap=True,
        ),
        ft.Text(
            value=valor,
            size=TAM_DATO,
            weight=ft.FontWeight.W_700,
            color=COLOR_TEXTO_PRIMARIO,
            font_family=FAMILIA_DATOS,
            no_wrap=True,
        ),
    ]
    if subtitulo:
        controles.append(
            ft.Text(
                value=subtitulo,
                size=TAM_ETIQUETA,
                color=COLOR_TEXTO_MUTED,
                no_wrap=True,
            )
        )

    return ft.Container(
        content=ft.Column(controls=controles, spacing=2, tight=True),
        padding=padding_symmetric(horizontal=12, vertical=8),
        bgcolor=COLOR_TARJETA,
        border_radius=0,
        border=borde_only(right=ft.border.BorderSide(1, COLOR_BORDE)),
        expand=True,
    )


def crear_badge_tiempo(tiempo_ms: float, speedup: float | None = None) -> ft.Container:
    """Chip de duración como en el panel Performance. Sin emoji."""
    tiempo_texto = formatear_tiempo_ms(tiempo_ms)
    color_tiempo = (
        COLOR_EXITO
        if tiempo_ms < 1.0
        else (COLOR_ADVERTENCIA if tiempo_ms < 20.0 else COLOR_PRIMARIO)
    )

    controles = [
        ft.Text(
            value=tiempo_texto,
            size=13,
            weight=ft.FontWeight.W_700,
            color=color_tiempo,
            font_family=FAMILIA_DATOS,
        ),
    ]

    if speedup is not None and speedup > 0:
        texto_speedup = f"{speedup:.1f}x" if speedup >= 1.0 else f"{speedup:.2f}x"
        color_speedup = COLOR_EXITO if speedup >= 1.0 else COLOR_PELIGRO
        controles.extend(
            [
                ft.Text("·", size=12, color=COLOR_TEXTO_MUTED),
                ft.Text(
                    texto_speedup,
                    size=13,
                    weight=ft.FontWeight.W_700,
                    color=color_speedup,
                    font_family=FAMILIA_DATOS,
                ),
            ]
        )

    return ft.Container(
        content=ft.Row(
            controls=controles,
            spacing=6,
            tight=True,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        padding=padding_symmetric(horizontal=8, vertical=3),
        bgcolor=COLOR_TARJETA,
        border_radius=RADIO,
        border=borde_all(1, COLOR_BORDE),
    )


def crear_banner_explicativo(
    titulo: str,
    descripcion: str,
    complejidad_base: str,
    complejidad_opt: str,
    por_que_importa: str,
) -> ft.Container:
    """Panel denso: Baseline y Optimizado apilados. Sin expand (evita el bloque gris)."""
    chip_base = ft.Container(
        content=ft.Row(
            controls=[
                ft.Text(
                    "Baseline",
                    size=TAM_ETIQUETA,
                    weight=ft.FontWeight.W_700,
                    color=COLOR_ADVERTENCIA,
                ),
                ft.Text(
                    complejidad_base,
                    size=TAM_CUERPO,
                    weight=ft.FontWeight.W_600,
                    color=COLOR_TEXTO_PRIMARIO,
                ),
            ],
            spacing=8,
            tight=True,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=padding_symmetric(horizontal=8, vertical=6),
        bgcolor=COLOR_FONDO_ADVERTENCIA,
        border=borde_all(1, COLOR_ADVERTENCIA),
        border_radius=RADIO,
    )
    chip_opt = ft.Container(
        content=ft.Row(
            controls=[
                ft.Text(
                    "Optimizado", size=TAM_ETIQUETA, weight=ft.FontWeight.W_700, color=COLOR_EXITO
                ),
                ft.Text(
                    complejidad_opt,
                    size=TAM_CUERPO,
                    weight=ft.FontWeight.W_600,
                    color=COLOR_TEXTO_PRIMARIO,
                ),
            ],
            spacing=8,
            tight=True,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=padding_symmetric(horizontal=8, vertical=6),
        bgcolor=COLOR_FONDO_EXITO,
        border=borde_all(1, COLOR_EXITO),
        border_radius=RADIO,
    )

    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.INFO_OUTLINE, size=16, color=COLOR_SECUNDARIO),
                        ft.Text(
                            value=f"Fundamento Algorítmico: {titulo}",
                            size=TAM_CUERPO,
                            weight=ft.FontWeight.W_600,
                            color=COLOR_TEXTO_PRIMARIO,
                        ),
                    ],
                    spacing=8,
                    tight=True,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                chip_base,
                chip_opt,
                ft.Text(value=descripcion, size=TAM_CUERPO, color=COLOR_TEXTO_SECUNDARIO),
                ft.Text(
                    value=f"Relevancia oral: {por_que_importa}",
                    size=TAM_ETIQUETA,
                    color=COLOR_TEXTO_MUTED,
                    weight=ft.FontWeight.W_500,
                ),
            ],
            spacing=6,
            tight=True,
        ),
        padding=padding_symmetric(horizontal=14, vertical=12),
        bgcolor=COLOR_TARJETA,
        border_radius=RADIO,
        border=borde_all(1, COLOR_BORDE),
    )


def crear_columna_corrida(titulo: str, tiempo_ms: float, es_baseline: bool) -> ft.Container:
    """Una columna de la comparativa Lighthouse: Baseline o Optimizado."""
    color = COLOR_ADVERTENCIA if es_baseline else COLOR_EXITO
    fondo = COLOR_FONDO_ADVERTENCIA if es_baseline else COLOR_FONDO_EXITO
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Text(titulo, size=TAM_ETIQUETA, weight=ft.FontWeight.W_700, color=color),
                ft.Text(
                    formatear_tiempo_ms(tiempo_ms),
                    size=TAM_DATO,
                    weight=ft.FontWeight.W_700,
                    color=COLOR_TEXTO_PRIMARIO,
                    font_family=FAMILIA_DATOS,
                ),
            ],
            spacing=2,
            tight=True,
        ),
        expand=True,
        padding=padding_symmetric(horizontal=12, vertical=8),
        bgcolor=fondo,
        border=borde_all(1, color),
        border_radius=RADIO,
    )


def crear_dialogo_explicativo_modos(page: ft.Page) -> ft.AlertDialog:
    """Genera un modal interactivo completo con la comparativa conceptual entre Modo Baseline y Optimizado."""
    filas_tabla = [
        ft.DataRow(
            cells=[
                ft.DataCell(
                    ft.Text(
                        "Búsqueda de Productos",
                        weight=ft.FontWeight.BOLD,
                        color=COLOR_TEXTO_PRIMARIO,
                        size=12,
                    )
                ),
                ft.DataCell(
                    ft.Text(
                        "Lineal O(n)\nRecorrido secuencial de lista",
                        color=COLOR_ADVERTENCIA,
                        size=11,
                    )
                ),
                ft.DataCell(
                    ft.Text(
                        "Hash O(1) amort.\nDict + Índice Invertido + LRU",
                        color=COLOR_EXITO,
                        size=11,
                    )
                ),
                ft.DataCell(
                    ft.Text(
                        "Acceso inmediato sin importar tamaño de catálogo.",
                        color=COLOR_TEXTO_SECUNDARIO,
                        size=11,
                    )
                ),
            ]
        ),
        ft.DataRow(
            cells=[
                ft.DataCell(
                    ft.Text(
                        "Batch Picking (Agrupación)",
                        weight=ft.FontWeight.BOLD,
                        color=COLOR_TEXTO_PRIMARIO,
                        size=12,
                    )
                ),
                ft.DataCell(
                    ft.Text(
                        "Anidada O(P·L·n)\nBúsqueda por línea y pedido",
                        color=COLOR_ADVERTENCIA,
                        size=11,
                    )
                ),
                ft.DataCell(
                    ft.Text(
                        "Consolidada O(L)\n1 pasada con acumulación hash",
                        color=COLOR_EXITO,
                        size=11,
                    )
                ),
                ft.DataCell(
                    ft.Text(
                        "Elimina el producto cartesiano en almacén.",
                        color=COLOR_TEXTO_SECUNDARIO,
                        size=11,
                    )
                ),
            ]
        ),
        ft.DataRow(
            cells=[
                ft.DataCell(
                    ft.Text(
                        "Ranking Top-N",
                        weight=ft.FontWeight.BOLD,
                        color=COLOR_TEXTO_PRIMARIO,
                        size=12,
                    )
                ),
                ft.DataCell(
                    ft.Text(
                        "Sort Global O(N log N)\nOrdena todo el catálogo",
                        color=COLOR_ADVERTENCIA,
                        size=11,
                    )
                ),
                ft.DataCell(
                    ft.Text(
                        "Heap O(N log k)\nMin-Heap acotado a k nodos", color=COLOR_EXITO, size=11
                    )
                ),
                ft.DataCell(
                    ft.Text(
                        "Memoria O(k) constante sin ordenar N completo.",
                        color=COLOR_TEXTO_SECUNDARIO,
                        size=11,
                    )
                ),
            ]
        ),
        ft.DataRow(
            cells=[
                ft.DataCell(
                    ft.Text(
                        "Alternativas Sustitutas",
                        weight=ft.FontWeight.BOLD,
                        color=COLOR_TEXTO_PRIMARIO,
                        size=12,
                    )
                ),
                ft.DataCell(
                    ft.Text(
                        "Recursión O(2^N)\nExplosión combinatorial",
                        color=COLOR_ADVERTENCIA,
                        size=11,
                    )
                ),
                ft.DataCell(
                    ft.Text(
                        "DP Memoizada O(N·P)\nReutilización de subproblemas",
                        color=COLOR_EXITO,
                        size=11,
                    )
                ),
                ft.DataCell(
                    ft.Text(
                        "Explora miles de opciones en milisegundos.",
                        color=COLOR_TEXTO_SECUNDARIO,
                        size=11,
                    )
                ),
            ]
        ),
        ft.DataRow(
            cells=[
                ft.DataCell(
                    ft.Text(
                        "Caché de Consultas",
                        weight=ft.FontWeight.BOLD,
                        color=COLOR_TEXTO_PRIMARIO,
                        size=12,
                    )
                ),
                ft.DataCell(
                    ft.Text("Sin Caché\nRecálculo repetido", color=COLOR_ADVERTENCIA, size=11)
                ),
                ft.DataCell(
                    ft.Text(
                        "LRU Reactiva O(1)\nInvalidación por mutación de stock",
                        color=COLOR_EXITO,
                        size=11,
                    )
                ),
                ft.DataCell(
                    ft.Text(
                        "Evita consultas redundantes sin datos obsoletos.",
                        color=COLOR_TEXTO_SECUNDARIO,
                        size=11,
                    )
                ),
            ]
        ),
        ft.DataRow(
            cells=[
                ft.DataCell(
                    ft.Text(
                        "Procesamiento de Pedidos",
                        weight=ft.FontWeight.BOLD,
                        color=COLOR_TEXTO_PRIMARIO,
                        size=12,
                    )
                ),
                ft.DataCell(
                    ft.Text(
                        "Secuencial O(P·L)\nMono-hilo atado al GIL",
                        color=COLOR_ADVERTENCIA,
                        size=11,
                    )
                ),
                ft.DataCell(
                    ft.Text(
                        "Concurrente O((P·L)/C + IPC)\nProcessPoolExecutor",
                        color=COLOR_EXITO,
                        size=11,
                    )
                ),
                ft.DataCell(
                    ft.Text(
                        "Paralelismo real multivariado en lotes masivos.",
                        color=COLOR_TEXTO_SECUNDARIO,
                        size=11,
                    )
                ),
            ]
        ),
    ]

    tabla_comparativa = ft.DataTable(
        columns=[
            ft.DataColumn(
                ft.Text(
                    "Operación", weight=ft.FontWeight.BOLD, color=COLOR_TEXTO_PRIMARIO, size=12
                )
            ),
            ft.DataColumn(
                ft.Text(
                    "Modo Baseline", weight=ft.FontWeight.BOLD, color=COLOR_ADVERTENCIA, size=12
                )
            ),
            ft.DataColumn(
                ft.Text(
                    "Modo Optimizado O(1)", weight=ft.FontWeight.BOLD, color=COLOR_EXITO, size=12
                )
            ),
            ft.DataColumn(
                ft.Text(
                    "Justificación Técnica",
                    weight=ft.FontWeight.BOLD,
                    color=COLOR_TEXTO_SECUNDARIO,
                    size=12,
                )
            ),
        ],
        rows=filas_tabla,
        heading_row_color=COLOR_SUPERFICIE,
        border=borde_all(1, COLOR_BORDE),
        border_radius=RADIO,
    )

    def cerrar_dialogo(_):
        if hasattr(page, "pop_dialog") and callable(page.pop_dialog):
            page.pop_dialog()
        elif hasattr(page, "close") and callable(page.close):
            page.close(dlg)
        else:
            dlg.open = False
            actualizar_control(page)

    dlg = ft.AlertDialog(
        title=ft.Row(
            controls=[
                ft.Icon(ft.Icons.COMPARE_ARROWS_ROUNDED, size=24, color=COLOR_PRIMARIO),
                ft.Text(
                    "Diferencias Arquitecturales: Baseline vs. Optimizado",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=COLOR_TEXTO_PRIMARIO,
                ),
            ],
            spacing=8,
        ),
        content=ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "El sistema implementa dos versiones simultáneas para cada operación fundamental del almacén. "
                        "Esto permite contrastar empíricamente en la defensa oral cómo la elección de algoritmos y estructuras de datos "
                        "transforma la escalabilidad y el consumo de recursos:",
                        size=13,
                        color=COLOR_TEXTO_SECUNDARIO,
                    ),
                    ft.Container(height=8),
                    tabla_comparativa,
                ],
                spacing=8,
                scroll=ft.ScrollMode.AUTO,
                tight=True,
            ),
            width=850,
        ),
        actions=[
            ft.FilledButton(
                "Entendido",
                style=estilo_boton_primario(),
                on_click=cerrar_dialogo,
            )
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        bgcolor=COLOR_TARJETA,
    )
    return dlg
