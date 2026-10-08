"""Pantalla de Exploración y Búsqueda del Catálogo de Productos."""

from __future__ import annotations

import time

import flet as ft

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
    actualizar_control,
    borde_all,
    borde_only,
    crear_badge_tiempo,
    crear_banner_explicativo,
    crear_barra_herramientas,
    crear_dropdown,
    crear_encabezado,
    envolver_lista,
    estilo_boton_primario,
    formatear_tiempo_ms,
    padding_symmetric,
)

TEXTO_BUSQUEDA_LINEAL = "Búsqueda Lineal O(n)"
TEXTO_BUSQUEDA_HASH = "Búsqueda Hash O(1) con LRU"

# Por encima de este stock el producto se muestra en verde; entre 1 y este valor, en ámbar.
STOCK_HOLGADO = 10


class PantallaCatalogo(PantallaBase):
    """Vista de catálogo con búsquedas comparativas entre catálogo lineal y hash."""

    def __init__(self, motor: MotorInventario, on_actualizar_panel, notificar) -> None:
        super().__init__(motor, on_actualizar_panel, notificar)
        self.productos_actuales = []
        self.orden_ascendente = True

        # Campo de búsqueda por texto o ID
        self.input_busqueda = ft.TextField(
            label="Buscar por nombre o descripción",
            hint_text="Ej: 'taladro', 'foco', 'pvc'...",
            prefix_icon=ft.Icons.SEARCH,
            border_color=COLOR_BORDE,
            focused_border_color=COLOR_PRIMARIO,
            color=COLOR_TEXTO_PRIMARIO,
            bgcolor=COLOR_TARJETA,
            width=340,
            dense=True,
            on_change=self._al_cambiar_nombre,
            on_submit=lambda _: self._ejecutar_busqueda(),
        )

        self.input_id = ft.TextField(
            label="ID numérico",
            hint_text="Ej: 1",
            width=130,
            border_color=COLOR_BORDE,
            focused_border_color=COLOR_PRIMARIO,
            color=COLOR_TEXTO_PRIMARIO,
            bgcolor=COLOR_TARJETA,
            dense=True,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=self._al_cambiar_id,
            on_submit=lambda _: self._ejecutar_busqueda_id(),
        )

        self.badge_estrategia = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(
                        ft.Icons.BOLT_ROUNDED
                        if self.motor.es_optimizado
                        else ft.Icons.LIST_ALT_ROUNDED,
                        size=15,
                        color=COLOR_EXITO if self.motor.es_optimizado else COLOR_ADVERTENCIA,
                    ),
                    ft.Text(
                        TEXTO_BUSQUEDA_HASH if self.motor.es_optimizado else TEXTO_BUSQUEDA_LINEAL,
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color=COLOR_EXITO if self.motor.es_optimizado else COLOR_ADVERTENCIA,
                    ),
                ],
                spacing=5,
                tight=True,
            ),
            padding=padding_symmetric(horizontal=10, vertical=5),
            bgcolor=COLOR_TARJETA,
            border_radius=8,
            border=borde_all(1, COLOR_EXITO if self.motor.es_optimizado else COLOR_ADVERTENCIA),
        )

        self.btn_buscar = ft.FilledButton(
            "Buscar",
            icon=ft.Icons.SEARCH,
            style=estilo_boton_primario(),
            on_click=lambda _: self._ejecutar_consulta(),
        )

        self.btn_limpiar = ft.OutlinedButton(
            "Ver Todos",
            icon=ft.Icons.CLEAR_ALL,
            on_click=lambda _: self._mostrar_todos(),
        )

        # Controles de ordenamiento
        self.dropdown_orden = crear_dropdown(
            label="Ordenar por",
            options=[
                ft.dropdown.Option("id", "ID del Producto"),
                ft.dropdown.Option("nombre", "Nombre (Alfabético)"),
                ft.dropdown.Option("precio", "Precio"),
                ft.dropdown.Option("stock", "Unidades en Stock"),
            ],
            value="id",
            width=200,
            on_change_callback=lambda _: self._aplicar_ordenamiento(),
        )

        self.btn_sentido_orden = self._crear_boton_sentido_orden()

        # Diagnóstico de la consulta
        self.txt_tiempo_busqueda = ft.Text(
            "Tiempo: 0.000 ms", size=13, color=COLOR_PRIMARIO, weight=ft.FontWeight.BOLD
        )
        self.contenedor_badge_tiempo = ft.Row(spacing=6)
        self.txt_estado_cache = ft.Text("Caché: --", size=13, color=COLOR_TEXTO_MUTED)
        self.txt_resultados_count = ft.Text(
            "Total: -- productos", size=13, color=COLOR_TEXTO_SECUNDARIO
        )

        self.col_productos = ft.ListView(spacing=0, expand=True, padding=0)

        self._construir_interfaz()
        self._mostrar_todos()

    def _construir_interfaz(self) -> None:
        self.content = ft.Column(
            controls=[
                crear_encabezado(
                    "Catálogo de Productos",
                    (
                        "Comparación en tiempo real: Búsqueda Lineal O(n) vs. Búsqueda Hash O(1) "
                        "con LRU"
                    ),
                    self.badge_estrategia,
                ),
                crear_banner_explicativo(
                    titulo="Acceso a Catálogo e Índices de Búsqueda",
                    descripcion=(
                        "Demostración del desafío experimental: recorrido secuencial de lista "
                        "frente a tabla Hash con índice invertido tokenizado y caché LRU."
                    ),
                    complejidad_base=TEXTO_BUSQUEDA_LINEAL,
                    complejidad_opt="Búsqueda Hash O(1) amortizado",
                    por_que_importa=(
                        "En catálogos de 10.000+ artículos, la búsqueda O(1) reduce el tiempo de "
                        "varios milisegundos a fracciones de milisegundo (speedup > 2000x)."
                    ),
                ),
                crear_barra_herramientas(
                    [
                        self.input_busqueda,
                        self.input_id,
                        self.btn_buscar,
                        self.btn_limpiar,
                        self.dropdown_orden,
                        self.btn_sentido_orden,
                    ],
                    wrap=False,
                ),
                ft.Row(
                    controls=[
                        self.txt_resultados_count,
                        self.contenedor_badge_tiempo,
                        self.txt_estado_cache,
                    ],
                    spacing=16,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                envolver_lista(
                    self.col_productos,
                    encabezado=ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Text(
                                    "ID",
                                    size=12,
                                    weight=ft.FontWeight.W_700,
                                    color=COLOR_TEXTO_MUTED,
                                    width=48,
                                ),
                                ft.Text(
                                    "Producto",
                                    size=12,
                                    weight=ft.FontWeight.W_700,
                                    color=COLOR_TEXTO_MUTED,
                                    expand=True,
                                ),
                                ft.Text(
                                    "Precio",
                                    size=12,
                                    weight=ft.FontWeight.W_700,
                                    color=COLOR_TEXTO_MUTED,
                                    width=90,
                                ),
                                ft.Text(
                                    "Stock",
                                    size=12,
                                    weight=ft.FontWeight.W_700,
                                    color=COLOR_TEXTO_MUTED,
                                    width=180,
                                ),
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=padding_symmetric(horizontal=12, vertical=8),
                        bgcolor=COLOR_SUPERFICIE,
                    ),
                ),
            ],
            spacing=12,
            expand=True,
        )

    def al_recargar_dataset(self) -> None:
        """Callback al cargar un nuevo dataset desde la pantalla Inicio."""
        self._mostrar_todos()

    def al_cambiar_estrategia_global(self, nueva_estrategia: str) -> None:
        """Sincroniza el switch local y el badge cuando cambia la estrategia global."""
        if hasattr(self, "switch_estrategia_local") and self.switch_estrategia_local:
            self.switch_estrategia_local.value = nueva_estrategia == "optimizado"
            actualizar_control(self.switch_estrategia_local)

        if hasattr(self, "badge_estrategia") and self.badge_estrategia:
            es_opt = nueva_estrategia == "optimizado"
            color_badge = COLOR_EXITO if es_opt else COLOR_ADVERTENCIA
            self.badge_estrategia.content = ft.Row(
                controls=[
                    ft.Icon(
                        ft.Icons.BOLT_ROUNDED if es_opt else ft.Icons.LIST_ALT_ROUNDED,
                        size=15,
                        color=color_badge,
                    ),
                    ft.Text(
                        TEXTO_BUSQUEDA_HASH if es_opt else TEXTO_BUSQUEDA_LINEAL,
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color=color_badge,
                    ),
                ],
                spacing=5,
                tight=True,
            )
            self.badge_estrategia.border = borde_all(1, color_badge)
            actualizar_control(self.badge_estrategia)

    def _al_cambiar_switch(self, e):
        nueva = "optimizado" if self.switch_estrategia_local.value else "baseline"
        self.motor.cambiar_estrategia(nueva)
        self.on_actualizar_panel(
            dataset=self.motor.obtener_estadisticas()["categorias"][0]
            if self.motor.catalogo
            else "dataset",
            n_productos=len(self.motor.catalogo),
            n_pedidos=len(self.motor.pedidos),
            estrategia=nueva,
            resultado_negocio=f"Estrategia conmutada a {nueva.upper()}",
        )
        self._ejecutar_busqueda()

    def _aplicar_ordenamiento(self):
        criterio = self.dropdown_orden.value or "id"
        if criterio == "nombre":
            self.productos_actuales.sort(
                key=lambda p: p.nombre.lower(), reverse=not self.orden_ascendente
            )
        elif criterio == "precio":
            self.productos_actuales.sort(key=lambda p: p.precio, reverse=not self.orden_ascendente)
        elif criterio == "stock":
            self.productos_actuales.sort(key=lambda p: p.stock, reverse=not self.orden_ascendente)
        else:
            self.productos_actuales.sort(key=lambda p: p.id, reverse=not self.orden_ascendente)

        self._renderizar_lista(self.productos_actuales)

    def _al_cambiar_nombre(self, e) -> None:
        if e is not None and getattr(e, "control", None) is not None:
            self.input_busqueda.value = e.control.value

    def _al_cambiar_id(self, e) -> None:
        if e is not None and getattr(e, "control", None) is not None:
            self.input_id.value = e.control.value

    def _texto_nombre(self) -> str:
        crudo = self.input_busqueda.value
        return str(crudo).strip() if crudo is not None else ""

    def _texto_id(self) -> str:
        crudo = self.input_id.value
        return str(crudo).strip() if crudo is not None else ""

    def _hits_cache_busquedas(self) -> int:
        if not self.motor.es_optimizado:
            return 0
        return int(self.motor.cache.obtener_estadisticas()["busquedas"]["hits"])

    def _ejecutar_consulta(self) -> None:
        """ID numérico tiene prioridad. Si ambos campos están vacíos, muestra el catálogo."""
        if self._texto_id():
            self._ejecutar_busqueda_id()
            return
        if self._texto_nombre():
            self._ejecutar_busqueda()
            return
        self._mostrar_todos()

    def _ejecutar_busqueda(self):
        texto = self._texto_nombre()
        if not texto:
            self._mostrar_todos()
            return

        inicio = time.perf_counter()
        hits_antes = self._hits_cache_busquedas()

        prods = self.motor.buscar_por_nombre(texto, usar_cache=True)
        duracion_ms = (time.perf_counter() - inicio) * 1000.0

        hits_despues = self._hits_cache_busquedas()
        fue_hit = hits_despues > hits_antes

        self.txt_tiempo_busqueda.value = f"Tiempo: {formatear_tiempo_ms(duracion_ms)}"
        self.contenedor_badge_tiempo.controls = [crear_badge_tiempo(duracion_ms)]
        if self.motor.es_optimizado:
            self.txt_estado_cache.value = "Caché: HIT" if fue_hit else "Caché: MISS (Guardado)"
            self.txt_estado_cache.color = COLOR_EXITO if fue_hit else COLOR_SECUNDARIO
        else:
            self.txt_estado_cache.value = "Caché: DESHABILITADA (Baseline)"
            self.txt_estado_cache.color = COLOR_TEXTO_MUTED

        self.txt_resultados_count.value = f"Total: {len(prods)} productos encontrados"
        self.productos_actuales = list(prods)
        self._aplicar_ordenamiento()

    def _ejecutar_busqueda_id(self):
        txt_id = self._texto_id()
        if not txt_id.isdigit():
            self.notificar("Ingrese un identificador numérico válido.", ft.Icons.WARNING)
            return

        id_num = int(txt_id)
        inicio = time.perf_counter()
        prod = self.motor.buscar_por_id(id_num)
        duracion_ms = (time.perf_counter() - inicio) * 1000.0

        self.txt_tiempo_busqueda.value = f"Tiempo: {formatear_tiempo_ms(duracion_ms)}"
        self.contenedor_badge_tiempo.controls = [crear_badge_tiempo(duracion_ms)]
        modo = "Hash O(1)" if self.motor.es_optimizado else "Lineal O(n)"
        self.txt_estado_cache.value = f"Búsqueda directa por ID ({modo})"
        self.txt_estado_cache.color = COLOR_PRIMARIO

        prods = [prod] if prod else []
        if prod is None:
            self.notificar(f"No existe un producto con ID {id_num}.", ft.Icons.WARNING)
        self.txt_resultados_count.value = f"Total: {len(prods)} producto encontrado"
        self.productos_actuales = list(prods)
        self._aplicar_ordenamiento()

    def _mostrar_todos(self):
        self.input_busqueda.value = ""
        self.input_id.value = ""
        prods = self.motor.catalogo.obtener_todos()
        self.txt_resultados_count.value = f"Total: {len(prods)} productos en catálogo"
        self.txt_tiempo_busqueda.value = f"Tiempo: {formatear_tiempo_ms(0.0)}"
        self.contenedor_badge_tiempo.controls = [crear_badge_tiempo(0.0)]
        self.txt_estado_cache.value = "Vista completa"
        self.txt_estado_cache.color = COLOR_TEXTO_MUTED
        self.productos_actuales = list(prods)
        self._aplicar_ordenamiento()

    def _renderizar_lista(self, productos):
        items = []
        max_mostrar = 150
        for p in productos[:max_mostrar]:
            if p.stock > STOCK_HOLGADO:
                stock_color = COLOR_EXITO
                stock_fondo = COLOR_FONDO_EXITO
            elif p.stock > 0:
                stock_color = COLOR_ADVERTENCIA
                stock_fondo = COLOR_FONDO_ADVERTENCIA
            else:
                stock_color = COLOR_PELIGRO
                stock_fondo = COLOR_FONDO_PELIGRO
            stock_texto = f"{p.stock} Unidades en Stock" if p.stock > 0 else "SIN STOCK"

            items.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Text(
                                f"#{p.id}",
                                size=12,
                                weight=ft.FontWeight.W_600,
                                color=COLOR_SECUNDARIO,
                                width=48,
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        p.nombre,
                                        size=13,
                                        weight=ft.FontWeight.W_600,
                                        color=COLOR_TEXTO_PRIMARIO,
                                    ),
                                    ft.Text(p.categoria, size=11, color=COLOR_TEXTO_MUTED),
                                ],
                                expand=True,
                                spacing=1,
                            ),
                            ft.Text(
                                f"${p.precio:,.2f}",
                                size=13,
                                weight=ft.FontWeight.W_600,
                                color=COLOR_TEXTO_PRIMARIO,
                                width=90,
                            ),
                            ft.Container(
                                content=ft.Text(
                                    stock_texto,
                                    size=11,
                                    weight=ft.FontWeight.W_600,
                                    color=stock_color,
                                ),
                                bgcolor=stock_fondo,
                                padding=padding_symmetric(horizontal=8, vertical=3),
                                border_radius=8,
                                border=borde_all(1, stock_color),
                                width=180,
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=padding_symmetric(horizontal=12, vertical=8),
                    bgcolor=COLOR_TARJETA,
                    border=borde_only(bottom=ft.border.BorderSide(1, COLOR_BORDE)),
                )
            )

        if len(productos) > max_mostrar:
            items.append(
                ft.Container(
                    content=ft.Text(
                        f"Mostrando los primeros {max_mostrar} de {len(productos)} productos...",
                        size=12,
                        color=COLOR_TEXTO_MUTED,
                    ),
                    padding=padding_symmetric(horizontal=12, vertical=10),
                )
            )

        if not items:
            items.append(
                ft.Container(
                    content=ft.Text(
                        "No hay productos en el catálogo.", size=13, color=COLOR_TEXTO_MUTED
                    ),
                    padding=24,
                )
            )

        self.col_productos.controls = items
        actualizar_control(self.col_productos)
        actualizar_control(self)
