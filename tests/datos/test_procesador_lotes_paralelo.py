"""Pruebas unitarias para procesador_lotes_paralelo y lotes JSONL."""

from __future__ import annotations

import json
from concurrent.futures import Future
from pathlib import Path

import pytest

from src.datos import procesador_lotes_paralelo as lotes
from src.datos.generador_archivos import generar_archivos_grandes_jsonl
from src.datos.procesador_lotes_paralelo import (
    procesar_pedidos_jsonl_paralelo,
    procesar_pedidos_jsonl_secuencial,
)
from src.datos.streaming import leer_productos_streaming_jsonl
from src.motor.motor_inventario import EstrategiaMotor, MotorInventario


def _escribir_jsonl(ruta: Path, pedidos: list[dict]) -> Path:
    ruta.write_text("\n".join(json.dumps(p) for p in pedidos) + "\n", encoding="utf-8")
    return ruta


class _ExecutorSincronico:
    """Executor que corre cada tarea al instante y registra cuántas quedan sin consumir."""

    def __init__(self, initializer=None, initargs=()):
        if initializer:
            initializer(*initargs)
        self.pendientes = 0
        self.maximo_pendientes = 0

    def submit(self, funcion, *args):
        futuro: Future = Future()
        futuro.set_result(funcion(*args))
        self.pendientes += 1
        self.maximo_pendientes = max(self.maximo_pendientes, self.pendientes)
        original = futuro.result

        def result(*a, **kw):
            self.pendientes -= 1
            return original(*a, **kw)

        futuro.result = result
        return futuro


class TestProcesamientoLotesYEquivalencia:
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
        assert res_sec.pedidos_cubiertos == res_par.pedidos_cubiertos
        assert res_sec.pedidos_parciales == res_par.pedidos_parciales
        assert res_sec.pedidos_imposibles == res_par.pedidos_imposibles

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

        resumen_par = motor.procesar_pedidos_jsonl(ruta_peds, tamano_lote=25, paralelo=True)
        resumen_sec = motor.procesar_pedidos_jsonl(ruta_peds, tamano_lote=25, paralelo=False)

        assert resumen_par.pedidos_procesados == 200
        assert resumen_sec.pedidos_procesados == 200
        assert resumen_par.pedidos_cubiertos == resumen_sec.pedidos_cubiertos
        assert resumen_par.pedidos_parciales == resumen_sec.pedidos_parciales
        assert resumen_par.pedidos_imposibles == resumen_sec.pedidos_imposibles


class TestLotesJsonl:
    @pytest.fixture
    def archivo_pedidos(self, tmp_path: Path) -> Path:
        pedidos = [
            {"id": i, "lineas": [{"id_producto": 1 + i % 3, "cantidad": 1 + i % 4}]}
            for i in range(1, 51)
        ]
        return _escribir_jsonl(tmp_path / "pedidos.jsonl", pedidos)

    def test_paralelo_igual_a_secuencial(self, archivo_pedidos):
        stock = {1: 2, 2: 0, 3: 50}
        sec = procesar_pedidos_jsonl_secuencial(
            archivo_pedidos, stock, tamano_lote=7, reconstruir_dataclasses=True
        )
        par = procesar_pedidos_jsonl_paralelo(
            archivo_pedidos,
            stock,
            tamano_lote=7,
            max_workers=2,
            reconstruir_dataclasses=True,
            max_lotes_en_vuelo=1,
        )
        assert par.resultados == sec.resultados
        assert (par.pedidos_cubiertos, par.pedidos_parciales, par.pedidos_imposibles) == (
            sec.pedidos_cubiertos,
            sec.pedidos_parciales,
            sec.pedidos_imposibles,
        )
        assert par.pedidos_procesados == 50

    def test_lotes_en_vuelo_acotados(self, archivo_pedidos, monkeypatch):
        executor_falso: dict[str, _ExecutorSincronico] = {}

        def obtener_executor(max_workers=None, initializer=None, initargs=()):
            executor_falso["e"] = _ExecutorSincronico(initializer, initargs)
            return executor_falso["e"]

        monkeypatch.setattr(lotes.pool_archivos, "obtener_executor", obtener_executor)
        resumen = procesar_pedidos_jsonl_paralelo(
            archivo_pedidos, {1: 5, 2: 5, 3: 5}, tamano_lote=5, max_workers=2
        )
        assert resumen.pedidos_procesados == 50
        assert executor_falso["e"].maximo_pendientes == 4

    def test_pedido_sin_lineas_es_error(self, tmp_path: Path):
        ruta = _escribir_jsonl(tmp_path / "vacio.jsonl", [{"id": 1, "lineas": []}])
        with pytest.raises(ValueError, match="no tiene líneas"):
            procesar_pedidos_jsonl_secuencial(ruta, {1: 1})

    def test_archivo_inexistente(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            procesar_pedidos_jsonl_paralelo(tmp_path / "no.jsonl", {})
