"""Pruebas unitarias para la aplicación global Flet."""

from __future__ import annotations

from unittest.mock import MagicMock

from src.ui.app import SECCIONES, AplicacionInventario, main


def test_app_main_inicializacion():
    mock_page = MagicMock()
    mock_page.controls = []
    mock_page.add = lambda ctrl: mock_page.controls.append(ctrl)
    mock_page.update = MagicMock()

    main(mock_page)

    assert len(mock_page.controls) == 1
    col_principal = mock_page.controls[0]
    assert len(col_principal.controls) == 2


def test_la_app_arma_una_seccion_por_pantalla():
    pagina = MagicMock()
    pagina.controls = []
    pagina.add = pagina.controls.append
    app = AplicacionInventario(pagina)
    app.montar()
    assert len(app.rail_navegacion.destinations) == len(SECCIONES)
    for indice, seccion in enumerate(SECCIONES):
        assert isinstance(app.obtener_vista(indice), seccion.pantalla)
    # Un índice fuera de rango muestra Inicio en lugar de fallar.
    assert isinstance(app.obtener_vista(99), SECCIONES[0].pantalla)
