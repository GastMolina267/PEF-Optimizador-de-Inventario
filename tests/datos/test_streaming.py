"""Pruebas unitarias para streaming, generador en lotes y exportación CSV con buffer."""

from __future__ import annotations

import csv
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.datos.streaming import (
    _fila_picking,
    en_lotes,
    escribir_pedidos_jsonl,
    escribir_productos_jsonl,
    exportar_picking_csv_con_buffer,
    leer_pedidos_streaming_jsonl,
    leer_productos_streaming_jsonl,
)
from src.modelos.pedido import LineaPedido, Pedido
from src.modelos.producto import Producto
from src.motor.motor_inventario import EstrategiaMotor, MotorInventario


class TestGeneradorEnLotes:
    def test_en_lotes_tamano_invalido(self) -> None:
        with pytest.raises(ValueError, match="al menos 1"):
            list(en_lotes([1, 2, 3], 0))
        with pytest.raises(ValueError, match="al menos 1"):
            list(en_lotes([1, 2, 3], -5))

    def test_en_lotes_vacio(self) -> None:
        assert list(en_lotes([], 3)) == []

    def test_en_lotes_exacto(self) -> None:
        datos = [1, 2, 3, 4, 5, 6]
        lotes = list(en_lotes(datos, 2))
        assert lotes == [(1, 2), (3, 4), (5, 6)]

    def test_en_lotes_ultimo_incompleto(self) -> None:
        datos = [1, 2, 3, 4, 5, 6, 7]
        lotes = list(en_lotes(datos, 3))
        assert lotes == [(1, 2, 3), (4, 5, 6), (7,)]

    def test_en_lotes_consumo_lazy(self) -> None:
        def generador_infinito():
            val = 0
            while True:
                yield val
                val += 1

        gen_lotes = en_lotes(generador_infinito(), 4)
        primer_lote = next(gen_lotes)
        assert primer_lote == (0, 1, 2, 3)
        segundo_lote = next(gen_lotes)
        assert segundo_lote == (4, 5, 6, 7)


class TestStreamingLecturaEscritura:
    def test_leer_productos_archivo_inexistente(self, tmp_path: Path) -> None:
        ruta_falsa = tmp_path / "no_existe.jsonl"
        with pytest.raises(FileNotFoundError):
            list(leer_productos_streaming_jsonl(ruta_falsa))

    def test_leer_pedidos_archivo_inexistente(self, tmp_path: Path) -> None:
        ruta_falsa = tmp_path / "no_existe.jsonl"
        with pytest.raises(FileNotFoundError):
            list(leer_pedidos_streaming_jsonl(ruta_falsa))

    def test_archivo_vacio(self, tmp_path: Path) -> None:
        ruta_vacia = tmp_path / "vacio.jsonl"
        ruta_vacia.write_text("", encoding="utf-8")

        assert list(leer_productos_streaming_jsonl(ruta_vacia)) == []
        assert list(leer_pedidos_streaming_jsonl(ruta_vacia)) == []

    def test_linea_corrupta_json(self, tmp_path: Path) -> None:
        ruta = tmp_path / "corrupto.jsonl"
        ruta.write_text(
            '{"id": 1, "nombre": "Martillo", "categoria": "Herramientas", '
            '"stock": 10, "precio": 500.0}\n'
            '{"id": 2, "nombre": "Clavo", BROKEN_JSON\n',
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="Error de sintaxis JSON en línea 2"):
            list(leer_productos_streaming_jsonl(ruta))

    def test_estructura_invalida_producto(self, tmp_path: Path) -> None:
        ruta = tmp_path / "invalido.jsonl"
        ruta.write_text(
            '{"id": "no_es_int", "nombre": "Pintura"}\n',
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="Estructura inválida de Producto en línea 1"):
            list(leer_productos_streaming_jsonl(ruta))

    def test_estructura_invalida_pedido(self, tmp_path: Path) -> None:
        ruta = tmp_path / "pedido_invalido.jsonl"
        ruta.write_text(
            '{"id": 1, "lineas": [{"id_producto": "abc", "cantidad": 5}]}\n',
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="Estructura inválida de Pedido en línea 1"):
            list(leer_pedidos_streaming_jsonl(ruta))

    def test_roundtrip_escritura_lectura_productos(self, tmp_path: Path) -> None:
        productos = [
            Producto(id=1, nombre="Taladro", categoria="Herramientas", stock=5, precio=12000.0),
            Producto(id=2, nombre="Pintura", categoria="Pinturas", stock=20, precio=4500.0),
        ]
        ruta = tmp_path / "productos_salida.jsonl"
        total = escribir_productos_jsonl(ruta, productos, tamano_lote=1)
        assert total == 2

        leidos = list(leer_productos_streaming_jsonl(ruta))
        assert len(leidos) == 2
        assert leidos[0].id == 1
        assert leidos[1].id == 2

    def test_roundtrip_escritura_lectura_pedidos(self, tmp_path: Path) -> None:
        pedidos = [
            Pedido(id=101, lineas=[LineaPedido(id_producto=1, cantidad=2)]),
            Pedido(
                id=102,
                lineas=[
                    LineaPedido(id_producto=1, cantidad=1),
                    LineaPedido(id_producto=2, cantidad=4),
                ],
            ),
        ]
        ruta = tmp_path / "pedidos_salida.jsonl"
        total = escribir_pedidos_jsonl(ruta, pedidos, tamano_lote=1)
        assert total == 2

        leidos = list(leer_pedidos_streaming_jsonl(ruta))
        assert len(leidos) == 2
        assert leidos[0].id == 101
        assert leidos[1].id == 102


class TestExportacionPickingCSV:
    def test_exportar_picking_csv_desde_motor(self, tmp_path: Path) -> None:
        prods = [
            Producto(id=1, nombre="Tornillo", categoria="Fijaciones", stock=100, precio=10.0),
            Producto(id=2, nombre="Tuerca", categoria="Fijaciones", stock=50, precio=5.0),
        ]
        peds = [
            Pedido(id=1, lineas=[LineaPedido(id_producto=1, cantidad=10)]),
            Pedido(
                id=2,
                lineas=[
                    LineaPedido(id_producto=1, cantidad=5),
                    LineaPedido(id_producto=2, cantidad=20),
                ],
            ),
        ]
        motor = MotorInventario(prods, peds, estrategia=EstrategiaMotor.OPTIMIZADO)
        ruta_csv = tmp_path / "picking_reporte.csv"

        filas = motor.exportar_picking_csv(ruta_csv)
        assert filas == 2
        assert ruta_csv.is_file()

        with open(ruta_csv, encoding="utf-8") as f:
            reader = list(csv.reader(f))
            assert reader[0] == [
                "id_producto",
                "nombre",
                "categoria",
                "total_demandado",
                "stock_disponible",
                "total_pedidos",
            ]
            fila_1 = [r for r in reader[1:] if r[0] == "1"][0]
            assert fila_1[1] == "Tornillo"
            assert fila_1[3] == "15"
            assert fila_1[5] == "2"

    def test_exportar_picking_csv_diccionarios(self, tmp_path: Path) -> None:
        datos_dict = [
            {
                "id_producto": 10,
                "nombre_producto": "Cable 2.5mm",
                "categoria": "Electricidad",
                "cantidad_total": 45,
                "stock_disponible": 100,
                "pedidos_solicitantes": [1, 2, 3],
            }
        ]
        ruta_csv = tmp_path / "picking_dict.csv"
        filas = exportar_picking_csv_con_buffer(ruta_csv, datos_dict)
        assert filas == 1

        with open(ruta_csv, encoding="utf-8") as f:
            reader = list(csv.reader(f))
            assert reader[1] == ["10", "Cable 2.5mm", "Electricidad", "45", "100", "3"]


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
