"""Tests de la fase F5: archivos grandes, streaming y procesamiento por lotes."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from src.datos.generador_archivos import (
    generar_archivos_grandes_jsonl,
)
from src.datos.procesador_lotes_paralelo import (
    procesar_pedidos_jsonl_paralelo,
    procesar_pedidos_jsonl_secuencial,
)
from src.datos.streaming import (
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
    """Verifica el generador propio en_lotes compatible con Python 3.10+."""

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
    """Verifica la lectura y escritura en formato JSON Lines (.jsonl) con buffer."""

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
        assert leidos[0].nombre == "Taladro"
        assert leidos[1].id == 2
        assert leidos[1].stock == 20

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
        assert len(leidos[0].lineas) == 1
        assert leidos[1].id == 102
        assert len(leidos[1].lineas) == 2


class TestExportacionPickingCSV:
    """Verifica la exportación con buffer del reporte de picking consolidado a CSV."""

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
            # id 1: total_demandado=15, 2 pedidos
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


class TestProcesamientoLotesYEquivalencia:
    """El procesamiento por lotes secuencial y el paralelo dan el mismo resultado."""

    @pytest.fixture
    def dataset_jsonl(self, tmp_path: Path) -> tuple[Path, Path, dict[int, int]]:
        ruta_prods, ruta_peds = generar_archivos_grandes_jsonl(
            directorio_destino=tmp_path,
            n_productos=50,
            n_pedidos=200,
            seed=123,
            tamano_lote=50,
        )
        prods = list(leer_productos_streaming_jsonl(ruta_prods))
        mapa_stock = {p.id: p.stock for p in prods}
        return ruta_prods, ruta_peds, mapa_stock

    def test_id_inexistente_referenciado_lanza_error(self, tmp_path: Path) -> None:
        peds_file = tmp_path / "pedidos_invalido.jsonl"
        peds_file.write_text(
            '{"id": 1, "lineas": [{"id_producto": 999999, "cantidad": 2}]}\n',
            encoding="utf-8",
        )
        mapa_stock = {1: 10, 2: 20}

        with pytest.raises(ValueError, match="referencia producto inexistente ID 999999"):
            procesar_pedidos_jsonl_secuencial(peds_file, mapa_stock)

        with pytest.raises(Exception, match="referencia producto inexistente ID 999999"):
            procesar_pedidos_jsonl_paralelo(peds_file, mapa_stock, tamano_lote=10)

    def test_equivalencia_secuencial_vs_paralelo(
        self, dataset_jsonl: tuple[Path, Path, dict[int, int]]
    ) -> None:
        _, ruta_peds, mapa_stock = dataset_jsonl

        res_sec = procesar_pedidos_jsonl_secuencial(
            ruta_peds, mapa_stock, tamano_lote=35, reconstruir_dataclasses=True
        )
        res_par = procesar_pedidos_jsonl_paralelo(
            ruta_peds, mapa_stock, tamano_lote=35, reconstruir_dataclasses=True
        )

        assert res_sec.pedidos_procesados == 200
        assert res_par.pedidos_procesados == 200

        # Totales idénticos
        assert res_sec.pedidos_cubiertos == res_par.pedidos_cubiertos
        assert res_sec.pedidos_parciales == res_par.pedidos_parciales
        assert res_sec.pedidos_imposibles == res_par.pedidos_imposibles

        # Mapeo id_pedido -> estado_val debe coincidir exactamente
        estados_sec = {r.id_pedido: r.estado for r in res_sec.resultados}
        estados_par = {r.id_pedido: r.estado for r in res_par.resultados}
        assert estados_sec == estados_par

    def test_motor_inventario_procesar_jsonl(
        self, dataset_jsonl: tuple[Path, Path, dict[int, int]]
    ) -> None:
        ruta_prods, ruta_peds, _ = dataset_jsonl
        motor = MotorInventario(estrategia=EstrategiaMotor.OPTIMIZADO)
        motor.cargar_dataset_jsonl(ruta_prods, ruta_peds)

        assert len(motor.catalogo.obtener_todos()) == 50
        assert len(motor.pedidos) == 200

        # Procesar con el método del motor
        resumen_par = motor.procesar_pedidos_jsonl(ruta_peds, tamano_lote=25, paralelo=True)
        resumen_sec = motor.procesar_pedidos_jsonl(ruta_peds, tamano_lote=25, paralelo=False)

        assert resumen_par.pedidos_procesados == 200
        assert resumen_sec.pedidos_procesados == 200
        assert resumen_par.pedidos_cubiertos == resumen_sec.pedidos_cubiertos
        assert resumen_par.pedidos_parciales == resumen_sec.pedidos_parciales
        assert resumen_par.pedidos_imposibles == resumen_sec.pedidos_imposibles
