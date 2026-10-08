"""Pruebas unitarias para generador sintético determinista de archivos grandes JSONL."""

from __future__ import annotations

from pathlib import Path

from src.datos.generador_archivos import (
    generar_archivos_grandes_jsonl,
    generar_lineas_pedidos,
    generar_lineas_productos,
)
from src.datos.streaming import (
    leer_pedidos_streaming_jsonl,
    leer_productos_streaming_jsonl,
)


class TestGeneradorArchivosGrandes:
    def test_generador_lineas_productos_determinismo(self):
        lineas1 = list(generar_lineas_productos(n_productos=10, seed=42))
        lineas2 = list(generar_lineas_productos(n_productos=10, seed=42))
        assert lineas1 == lineas2
        assert len(lineas1) == 10

    def test_generador_lineas_pedidos_determinismo(self):
        lineas1 = list(generar_lineas_pedidos(n_pedidos=20, n_productos=10, seed=42))
        lineas2 = list(generar_lineas_pedidos(n_pedidos=20, n_productos=10, seed=42))
        assert lineas1 == lineas2
        assert len(lineas1) == 20

    def test_generar_archivos_grandes_jsonl_crea_archivos(self, tmp_path: Path):
        ruta_p, ruta_ped = generar_archivos_grandes_jsonl(
            directorio_destino=tmp_path,
            n_productos=25,
            n_pedidos=50,
            seed=99,
            tamano_lote=10,
        )
        assert ruta_p.is_file()
        assert ruta_ped.is_file()

        prods = list(leer_productos_streaming_jsonl(ruta_p))
        peds = list(leer_pedidos_streaming_jsonl(ruta_ped))
        assert len(prods) == 25
        assert len(peds) == 50
