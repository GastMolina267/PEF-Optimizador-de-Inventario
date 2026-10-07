"""Pruebas de cierre de la Etapa 6: automatizaciones Origin.

Verifica:
1. El analizador recorre el AST y deriva cotas con evidencia (no un catálogo inventado).
2. El bloque marcado de docs/analisis.md se regenera sin borrar el comentario del grupo.
3. Las propuestas leen docs/mediciones/ y no modifican src/.
4. El inventario cubre las operaciones del enunciado.
5. Skills y prompts de Origin existen y nombran las rutas reales del repo.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from automations.analizar_complejidad import (
    MARCA_FIN,
    MARCA_INICIO,
    analizar_repositorio,
)
from automations.analizar_complejidad import (
    ejecutar as ejecutar_complejidad,
)
from automations.inventario_funciones import (
    FUNCIONES_FUNDAMENTALES,
    MODULOS_FUNDAMENTALES,
    resolver_raiz,
)
from automations.proponer_mejoras import (
    ejecutar as ejecutar_propuestas,
)
from automations.proponer_mejoras import (
    escribir_informe,
    recoger_hotspots,
)

BASE_DIR = resolver_raiz(Path(__file__))
DOCS = BASE_DIR / "docs"


@pytest.fixture
def repo_temporal(tmp_path: Path) -> Path:
    """Copia ``src/`` y ``docs/`` a un directorio temporal.

    Las automatizaciones escriben en ``docs/``. Correrlas sobre una copia evita que
    cada ejecución de la suite modifique ``docs/analisis.md`` y
    ``docs/propuestas-mejora.md`` del repositorio real.
    """
    for carpeta in ("src", "docs"):
        shutil.copytree(BASE_DIR / carpeta, tmp_path / carpeta)
    return tmp_path


def _informe_por_nombre(nombre: str):
    for inf in analizar_repositorio(BASE_DIR):
        if inf.funcion.nombre_calificado == nombre:
            return inf
    raise AssertionError(f"No se analizó {nombre}")


class TestInventarioFundamental:
    def test_modulos_existen_y_no_son_ui(self):
        for ruta in MODULOS_FUNDAMENTALES:
            assert (BASE_DIR / ruta).is_file()
            assert not ruta.startswith("src/ui/")
            assert not ruta.startswith("tests/")

    def test_cubre_operaciones_del_enunciado(self):
        nombres = {f.nombre_calificado for f in FUNCIONES_FUNDAMENTALES}
        assert "CatalogoLineal.buscar_por_id" in nombres
        assert "CatalogoHash.buscar_por_id" in nombres
        assert "agrupar_pedidos_batch" in nombres
        assert "calcular_top_solicitados_heap" in nombres
        assert "BuscadorAlternativas._resolver_dp_memo" in nombres
        assert "procesar_pedidos_concurrente" in nombres
        assert "CacheLRU.obtener" in nombres


class TestDerivacionAST:
    def test_busqueda_lineal_es_o_n(self):
        inf = _informe_por_nombre("CatalogoLineal.buscar_por_id")
        assert inf.evidencia.recorre_lista_productos
        assert inf.evidencia.profundidad_bucles == 1
        promedio = inf.promedio.replace(" ", "").lower()
        peor = inf.peor.replace(" ", "").lower()
        assert "θ(n)" in promedio or "theta(n)" in promedio
        assert "o(n)" in peor
        assert "θ(1)" not in promedio
        assert "o(1)" not in promedio

    def test_busqueda_hash_es_o_1(self):
        inf = _informe_por_nombre("CatalogoHash.buscar_por_id")
        assert inf.evidencia.accesos_hash
        assert inf.evidencia.profundidad_bucles == 0
        assert "1" in inf.promedio

    def test_top_n_sort_vs_heap(self):
        sort = _informe_por_nombre("calcular_top_solicitados_lineal")
        heap = _informe_por_nombre("calcular_top_solicitados_heap")
        assert sort.evidencia.llamadas_sorted
        assert heap.evidencia.llamadas_heapq
        assert "log" in sort.peor.lower()
        assert "log k" in heap.peor.lower() or "log k" in heap.promedio.lower()

    def test_combinaciones_recursion_vs_memo(self):
        puro = _informe_por_nombre("BuscadorAlternativas._resolver_recursivo_puro")
        memo = _informe_por_nombre("BuscadorAlternativas._resolver_dp_memo")
        assert puro.evidencia.es_recursiva
        assert not puro.evidencia.usa_memo
        assert "2" in puro.peor
        assert memo.evidencia.es_recursiva
        assert memo.evidencia.usa_memo
        assert "N" in memo.peor or "n" in memo.peor.lower()

    def test_concurrencia_detecta_process_pool(self):
        inf = _informe_por_nombre("procesar_pedidos_concurrente")
        assert inf.evidencia.usa_process_pool
        assert "IPC" in inf.promedio or "IPC" in inf.peor

    def test_justificacion_cita_el_cuerpo(self):
        inf = _informe_por_nombre("CatalogoHash.buscar_por_id")
        assert inf.justificacion
        assert any(
            token in inf.justificacion.lower() for token in ("hash", "dict", "get", "bucle")
        )


class TestEscrituraAnalisis:
    def test_regenera_bloque_sin_borrar_comentario_del_grupo(self, repo_temporal):
        ejecutar_complejidad(repo_temporal)
        texto = (repo_temporal / "docs" / "analisis.md").read_text(encoding="utf-8")
        assert MARCA_INICIO in texto
        assert MARCA_FIN in texto
        assert texto.index(MARCA_INICIO) < texto.index(MARCA_FIN)
        # Comentario del grupo (Etapa 5) intacto.
        assert "Derivación Formal de Complejidad" in texto
        assert "Memoización vs. Caching" in texto
        assert "Defensa Oral" in texto
        # Bloque automático.
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


class TestArtefactosOrigin:
    def test_skills_y_prompts_existen(self):
        skill_c = BASE_DIR / ".cursor" / "skills" / "analisis-complejidad" / "SKILL.md"
        skill_h = BASE_DIR / ".cursor" / "skills" / "hotspots-propuestas" / "SKILL.md"
        prompt_c = DOCS / "prompts-origin" / "complejidad-temporal.txt"
        prompt_h = DOCS / "prompts-origin" / "hotspots-propuestas.txt"
        guia = DOCS / "automatizaciones-origin.md"
        for ruta in (skill_c, skill_h, prompt_c, prompt_h, guia):
            assert ruta.is_file(), ruta
            contenido = ruta.read_text(encoding="utf-8")
            assert "automations.ejecutar" in contenido
            assert "español" in contenido.lower() or "Español" in contenido

    def test_prompts_prohíben_aplicar_codigo(self):
        prompt = (DOCS / "prompts-origin" / "hotspots-propuestas.txt").read_text(encoding="utf-8")
        assert "NO apliques" in prompt or "No apliques" in prompt
        assert "src/" in prompt
