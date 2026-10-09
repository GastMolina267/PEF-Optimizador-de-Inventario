"""Pruebas de las piezas que surgieron del refactor de la fase F7."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from automations.analizar_complejidad import EvidenciaAST, _rastros_evidencia
from automations.proponer_mejoras import _fila_line_profiler, _filas_cprofile
from src.datos.streaming import _fila_picking
from src.datos.validador import ValidadorDataset
from src.inventario import Catalogo, CatalogoHash, CatalogoLineal
from src.modelos.producto import Producto
from src.pedidos.combinaciones import _agregar_hasta_limite
from src.ui.app import SECCIONES, AplicacionInventario


@pytest.mark.parametrize("clase", [CatalogoLineal, CatalogoHash])
def test_los_catalogos_cumplen_el_protocolo(clase):
    assert isinstance(clase(), Catalogo)


class TestFilaPicking:
    producto = Producto(7, "Taladro", "Ferretería y Herramientas", 4, 100.0)

    def test_desde_objeto_con_a_diccionario(self):
        item = SimpleNamespace(
            a_diccionario=lambda: {
                "id_producto": 7,
                "nombre_producto": "Taladro",
                "categoria": "Ferretería y Herramientas",
                "stock_disponible": 4,
                "cantidad_total": 9,
                "pedidos_solicitantes": [1, 2],
            }
        )
        assert _fila_picking(item) == [7, "Taladro", "Ferretería y Herramientas", 9, 4, 2]

    def test_desde_diccionario_con_nombres_alternativos(self):
        item = {"id_producto": 3, "nombre": "X", "total_demandado": 5, "total_pedidos": 1}
        assert _fila_picking(item) == [3, "X", "", 5, 0, 1]

    def test_desde_atributos(self):
        item = SimpleNamespace(
            id_producto=7, producto=self.producto, cantidad_total=2, demandas_por_pedido=[1]
        )
        assert _fila_picking(item) == [7, "Taladro", "Ferretería y Herramientas", 2, 4, 1]


class TestValidadorDiccionario:
    def test_id_de_producto_repetido(self):
        datos = {
            "productos": [
                {"id": 1, "nombre": "A", "categoria": "C", "stock": 1, "precio": 1.0},
                {"id": 1, "nombre": "B", "categoria": "C", "stock": 1, "precio": 1.0},
            ],
            "pedidos": [],
        }
        with pytest.raises(ValueError, match="producto duplicado en dataset: #1"):
            ValidadorDataset.validar_diccionario(datos)

    def test_pedido_que_no_es_objeto(self):
        datos = {"productos": [], "pedidos": ["no soy un pedido"]}
        with pytest.raises(ValueError, match="El pedido en la posición 0"):
            ValidadorDataset.validar_diccionario(datos)


def test_agregar_hasta_limite_conserva_el_comportamiento_original():
    resultados = [[0]]
    _agregar_hasta_limite(resultados, iter([[1], [2], [3]]), limite=1)
    # Agrega y después compara: con un elemento previo, queda uno por encima del límite.
    assert resultados == [[0], [1]]
    vacio: list[list[int]] = []
    _agregar_hasta_limite(vacio, iter([[1], [2], [3]]), limite=2)
    assert vacio == [[1], [2]]


def test_parsers_de_profilers_sin_regex():
    pstats = (
        "   ncalls  tottime  percall  cumtime  percall filename:lineno(function)\n"
        "      2/1    0.364    0.182    0.400    0.200 src/a.py:10(f)\n"
        "basura\n"
    )
    assert _filas_cprofile(pstats) == [("0.364", "0.400", "src/a.py:10(f)")]
    assert _fila_line_profiler("    52      3      4.0      1.3     90.8  x = 1") == (
        "52",
        90.8,
        "x = 1",
    )
    assert _fila_line_profiler("Line #  Hits  Time") is None


def test_rastros_de_evidencia_en_orden():
    evidencia = EvidenciaAST(profundidad_bucles=2, llamadas_heapq=True, usa_memo=True)
    evidencia.accesos_hash.append("dict.get")
    assert _rastros_evidencia(evidencia) == ["bucles×2", "hash", "heapq", "memo"]


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
