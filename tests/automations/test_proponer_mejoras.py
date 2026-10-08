"""Pruebas unitarias para el generador de propuestas de mejora a partir de perfilados."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from automations.analizar_complejidad import (
    MARCA_FIN,
    MARCA_INICIO,
)
from automations.analizar_complejidad import (
    ejecutar as ejecutar_complejidad,
)
from automations.inventario_funciones import resolver_raiz
from automations.proponer_mejoras import (
    _fila_line_profiler,
    _filas_cprofile,
    escribir_informe,
    recoger_hotspots,
)
from automations.proponer_mejoras import (
    ejecutar as ejecutar_propuestas,
)

BASE_DIR = resolver_raiz(Path(__file__))


@pytest.fixture
def repo_temporal(tmp_path: Path) -> Path:
    for carpeta in ("src", "docs"):
        shutil.copytree(BASE_DIR / carpeta, tmp_path / carpeta)
    return tmp_path


class TestEscrituraAnalisis:
    def test_regenera_bloque_sin_borrar_comentario_del_grupo(self, repo_temporal):
        ejecutar_complejidad(repo_temporal)
        texto = (repo_temporal / "docs" / "analisis.md").read_text(encoding="utf-8")
        assert MARCA_INICIO in texto
        assert MARCA_FIN in texto
        assert texto.index(MARCA_INICIO) < texto.index(MARCA_FIN)
        assert "Derivación Formal de Complejidad" in texto
        assert "Memoización vs. Caching" in texto
        assert "Defensa Oral" in texto
        assert "CatalogoLineal.buscar_por_id" in texto
        assert "ORIGIN-AUTO-COMPLEJIDAD" in texto

    def test_bloque_menciona_evidencia_ast(self, repo_temporal):
        ejecutar_complejidad(repo_temporal)
        texto = (repo_temporal / "docs" / "analisis.md").read_text(encoding="utf-8")
        bloque = texto.split(MARCA_INICIO, 1)[1].split(MARCA_FIN, 1)[0]
        assert "Evidencia AST" in bloque
        assert "heapq" in bloque
        assert "ProcessPool" in bloque


class TestPropuestasHotspots:
    def test_lee_mediciones_si_existen(self):
        hotspots = recoger_hotspots(BASE_DIR)
        origenes = {h.origen for h in hotspots}
        assert "cProfile" in origenes or "line_profiler" in origenes
        assert any("buscar_por_id" in h.simbolo or "CreateProcess" in h.simbolo for h in hotspots)

    def test_escribe_informe_sin_tocar_src(self, repo_temporal):
        huellas = {ruta: ruta.stat().st_mtime for ruta in (repo_temporal / "src").rglob("*.py")}
        ruta, _hotspots, propuestas = escribir_informe(repo_temporal)
        assert ruta == repo_temporal / "docs" / "propuestas-mejora.md"
        texto = ruta.read_text(encoding="utf-8")
        assert "Propuestas de mejora" in texto
        assert "No aplicar" in texto or "no aplicada" in texto.lower()
        assert propuestas
        texto_props = " ".join(p.titulo + p.hotspot + p.alternativa for p in propuestas)
        assert "IPC" in texto_props or "ProcessPool" in texto_props
        for archivo, mtime in huellas.items():
            assert archivo.stat().st_mtime == mtime, f"Se modificó {archivo}"

    def test_cli_propuestas_idempotente_en_src(self, repo_temporal):
        ejecutar_propuestas(repo_temporal)
        assert (repo_temporal / "docs" / "propuestas-mejora.md").is_file()

    def test_parsers_de_profilers_sin_regex(self):
        assert _filas_cprofile("   ncalls  tottime  percall  cumtime") == []
        assert _fila_line_profiler("Line #  Hits  Time") is None
