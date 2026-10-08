"""Barra superior estilo AWS Console (top navigation).

Muestra dataset, conmutador Baseline | Optimizado, tiempo líder y resultado.
"""

from __future__ import annotations

import flet as ft

from src.ui.tema import (
    COLOR_ADVERTENCIA,
    COLOR_EXITO,
    COLOR_FONDO_ADVERTENCIA,
    COLOR_FONDO_EXITO,
    COLOR_MARCA,
    COLOR_NAV,
    COLOR_NAV_BORDE,
    COLOR_NAV_HOVER,
    COLOR_NAV_MUTED,
    COLOR_NAV_TEXTO,
    FAMILIA_DATOS,
    actualizar_control,
    borde_all,
    formatear_tiempo_ms,
    padding_symmetric,
)


class PanelEstado(ft.Container):
    """Barra superior persistente de métricas y control de estrategia."""

    def __init__(self, on_cambiar_estrategia, on_mostrar_ayuda_modos=None) -> None:
        super().__init__()
        self.on_cambiar_estrategia = on_cambiar_estrategia
        self.on_mostrar_ayuda_modos = on_mostrar_ayuda_modos
        self.dataset_nombre = "demo_oral.json"
        self._estrategia = "baseline"

        self.txt_dataset = ft.Text(
            value="demo_oral.json",
            size=13,
            weight=ft.FontWeight.W_600,
            color=COLOR_NAV_TEXTO,
        )
        self.txt_volumen = ft.Text(
            value="30 prods · 8 pedidos",
            size=12,
            color=COLOR_NAV_MUTED,
        )
        self.txt_tiempo = ft.Text(
            value="-- ms",
            size=22,
            weight=ft.FontWeight.W_700,
            color=COLOR_NAV_TEXTO,
            font_family=FAMILIA_DATOS,
        )
        self.txt_memoria = ft.Text(
            value="-- MB",
            size=12,
            color=COLOR_NAV_MUTED,
            font_family=FAMILIA_DATOS,
        )
        self.txt_resultado_negocio = ft.Text(
            value="Listo para operar",
            size=12,
            weight=ft.FontWeight.W_500,
            color=COLOR_NAV_MUTED,
        )

        self.btn_baseline = ft.Container()
        self.btn_optimizado = ft.Container()
        self._pintar_conmutador()

        self.btn_info_modos = ft.IconButton(
            icon=ft.Icons.HELP_OUTLINE,
            icon_color=COLOR_MARCA,
            icon_size=18,
            tooltip=(
                "¿Qué cambia entre Modo Optimizado O(1) y Modo Baseline? Clic para ver comparativa"
            ),
            on_click=lambda _: self._abrir_ayuda_modos(),
        )

        self.padding = padding_symmetric(horizontal=16, vertical=8)
        self.bgcolor = COLOR_NAV
        self.border = None
        self.height = 56

        marca = ft.Row(
            controls=[
                ft.Container(width=10, height=10, bgcolor=COLOR_MARCA, border_radius=2),
                ft.Text(
                    "Optimizador",
                    size=15,
                    weight=ft.FontWeight.W_700,
                    color=COLOR_NAV_TEXTO,
                ),
            ],
            spacing=8,
            tight=True,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        self.content = ft.Row(
            controls=[
                marca,
                ft.VerticalDivider(width=1, color=COLOR_NAV_BORDE),
                ft.Column(
                    controls=[self.txt_dataset, self.txt_volumen],
                    spacing=1,
                    tight=True,
                ),
                ft.VerticalDivider(width=1, color=COLOR_NAV_BORDE),
                ft.Row(
                    controls=[self.btn_baseline, self.btn_optimizado, self.btn_info_modos],
                    spacing=4,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(expand=True),
                ft.Column(
                    controls=[
                        self.txt_tiempo,
                        ft.Row(
                            controls=[self.txt_memoria, self.txt_resultado_negocio],
                            spacing=10,
                            tight=True,
                        ),
                    ],
                    spacing=1,
                    tight=True,
                    horizontal_alignment=ft.CrossAxisAlignment.END,
                ),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _abrir_ayuda_modos(self):
        if self.on_mostrar_ayuda_modos:
            self.on_mostrar_ayuda_modos()

    def _pintar_conmutador(self) -> None:
        es_opt = self._estrategia == "optimizado"
        self.btn_baseline = self._boton_modo(
            "Baseline  O(n)",
            activo=not es_opt,
            color=COLOR_ADVERTENCIA,
            fondo=COLOR_FONDO_ADVERTENCIA,
            al_clic=lambda _: self._elegir("baseline"),
        )
        self.btn_optimizado = self._boton_modo(
            "Optimizado  O(1)",
            activo=es_opt,
            color=COLOR_EXITO,
            fondo=COLOR_FONDO_EXITO,
            al_clic=lambda _: self._elegir("optimizado"),
        )

    def _boton_modo(
        self, texto: str, activo: bool, color: str, fondo: str, al_clic
    ) -> ft.Container:
        return ft.Container(
            content=ft.Text(
                texto,
                size=13,
                weight=ft.FontWeight.W_700,
                color=color if activo else COLOR_NAV_MUTED,
            ),
            padding=padding_symmetric(horizontal=12, vertical=6),
            bgcolor=fondo if activo else COLOR_NAV_HOVER,
            border=borde_all(1, color if activo else COLOR_NAV_BORDE),
            border_radius=8,
            on_click=al_clic,
        )

    def _elegir(self, nueva: str) -> None:
        if nueva == self._estrategia:
            return
        self._estrategia = nueva
        self._reconstruir_conmutador()
        self.on_cambiar_estrategia(nueva)

    def _reconstruir_conmutador(self) -> None:
        self._pintar_conmutador()
        fila = self.content
        if isinstance(fila, ft.Row) and len(fila.controls) >= 5:
            fila.controls[4] = ft.Row(
                controls=[self.btn_baseline, self.btn_optimizado, self.btn_info_modos],
                spacing=4,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        actualizar_control(self)

    def actualizar_estado(
        self,
        dataset: str,
        n_productos: int,
        n_pedidos: int,
        estrategia: str,
        tiempo_ms: float | None = None,
        memoria_mb: float | None = None,
        resultado_negocio: str | None = None,
    ) -> None:
        """Actualiza la información visible en el panel."""
        self.dataset_nombre = dataset
        self.txt_dataset.value = dataset
        self.txt_volumen.value = f"{n_productos:,} prods · {n_pedidos:,} pedidos"

        if estrategia in ("baseline", "optimizado") and estrategia != self._estrategia:
            self._estrategia = estrategia
            self._reconstruir_conmutador()

        if tiempo_ms is not None:
            self.txt_tiempo.value = formatear_tiempo_ms(tiempo_ms)
            self.txt_memoria.value = f"{memoria_mb:.2f} MB" if memoria_mb is not None else "-- MB"

        if resultado_negocio is not None:
            self.txt_resultado_negocio.value = resultado_negocio

        actualizar_control(self)
