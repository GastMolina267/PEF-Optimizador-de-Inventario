"""Pruebas de validación de artefactos de medición, benchmarks y entry points."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from benchmarks import perfilar_archivos_grandes as bench
from benchmarks.resumir_scalene import cargar_perfil, generar_resumen

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MEDICIONES_DIR = BASE_DIR / "docs" / "mediciones"
DOCS_DIR = BASE_DIR / "docs"


class TestArtefactosMedicionesGenerados:
    def test_tabla_comparativa_existe(self):
        ruta_md = MEDICIONES_DIR / "tabla_comparativa.md"
        ruta_txt = MEDICIONES_DIR / "tabla_comparativa.txt"
        assert ruta_md.is_file()
        assert ruta_txt.is_file()
        contenido = ruta_md.read_text(encoding="utf-8")
        assert "Tabla Comparativa Oficial" in contenido
        assert "Speedup" in contenido
        assert "grande.json" in contenido

    def test_preparacion_pedidos_aisla_concurrencia(self):
        fuente = (BASE_DIR / "benchmarks" / "comparar.py").read_text(encoding="utf-8")
        bloque = fuente.split("# 6. Preparación", 1)[1].split("return filas_resultados", 1)[0]
        assert "procesar_pedidos_secuencial, cat_hash" in bloque
        assert "procesar_pedidos_concurrente, cat_hash" in bloque
        assert "cat_lineal" not in bloque
        assert "aísla" in bloque.lower() or "aisla" in bloque.lower()

    def test_informe_cprofile_existe(self):
        ruta_cprofile = MEDICIONES_DIR / "cprofile_resumen.txt"
        assert ruta_cprofile.is_file()
        contenido = ruta_cprofile.read_text(encoding="utf-8")
        assert "PERFILADO CPROFILE" in contenido
        assert "CUMULATIVE TIME" in contenido

    def test_informe_line_profiler_existe(self):
        ruta_lp = MEDICIONES_DIR / "line_profiler_resumen.txt"
        assert ruta_lp.is_file()
        contenido = ruta_lp.read_text(encoding="utf-8")
        assert "LINE_PROFILER" in contenido
        assert "CatalogoLineal.buscar_por_id" in contenido

    def test_informe_memoria_existe(self):
        ruta_mem = MEDICIONES_DIR / "memoria_resumen.txt"
        assert ruta_mem.is_file()
        contenido = ruta_mem.read_text(encoding="utf-8")
        assert "INFORME DE PERFILADO DE MEMORIA" in contenido
        assert "Catálogo Hash" in contenido
        assert "Min-Heap Acotado" in contenido

    def test_documento_analisis_completo(self):
        ruta_analisis = DOCS_DIR / "analisis.md"
        assert ruta_analisis.is_file()
        contenido = ruta_analisis.read_text(encoding="utf-8")
        assert "Análisis de Complejidad, Perfilado y Optimización" in contenido
        assert "O(N log k)" in contenido
        assert "O(2^N)" in contenido
        assert "Memoización vs. Caching" in contenido
        assert "ProcessPoolExecutor" in contenido
        assert "Defensa Oral" in contenido


def _perfil_scalene(ruta: Path, segundos: float, funciones: list[tuple[str, float]]) -> Path:
    datos = {
        "elapsed_time_sec": segundos,
        "max_footprint_mb": 10.0,
        "files": {
            "/repo/src/pedidos/procesador_concurrente.py": {
                "functions": [
                    {
                        "line": nombre,
                        "n_cpu_percent_python": 1.0,
                        "n_cpu_percent_c": pct,
                        "n_sys_percent": pct,
                        "n_peak_mb": 0.0,
                    }
                    for nombre, pct in funciones
                ]
            }
        },
    }
    ruta.write_text(json.dumps(datos), encoding="utf-8")
    return ruta


def test_resumen_scalene(tmp_path: Path):
    antes = cargar_perfil(_perfil_scalene(tmp_path / "a.json", 4.0, [("procesar", 20.0)]))
    despues = cargar_perfil(_perfil_scalene(tmp_path / "d.json", 3.0, [("_evaluar_en_pool", 5.0)]))
    texto = generar_resumen(antes, despues, "prueba")
    assert "25 % menos" in texto
    assert "`src/pedidos/procesador_concurrente.py · procesar`" in texto
    assert "`src/pedidos/procesador_concurrente.py · _evaluar_en_pool`" in texto


def test_conclusiones_del_benchmark_salen_de_los_datos():
    sin_ganancia = [{"lote": 10, "speedup": 0.8}, {"lote": 20, "speedup": 0.9}]
    assert "no superó" in bench._conclusion_lotes(sin_ganancia, workers=2)
    con_ganancia = [{"lote": 10, "speedup": 0.8}, {"lote": 20, "speedup": 1.4}]
    assert "1.40×" in bench._conclusion_lotes(con_ganancia, workers=4)

    csv_igual = {"filas": 10, "kb": 1.0, "defecto_ms": 10.0, "explicito_ms": 10.2}
    assert "no es significativa" in bench._conclusion_csv(csv_igual)
    csv_mejor = {"filas": 10, "kb": 1.0, "defecto_ms": 10.0, "explicito_ms": 5.0}
    assert "50 % más rápido" in bench._conclusion_csv(csv_mejor)

    lectura = {
        "completa_ms": 10.0,
        "completa_mb": 100.0,
        "streaming_ms": 12.0,
        "streaming_mb": 1.0,
    }
    assert "99.0 % menos" in bench._conclusion_lectura(lectura)
    assert "más lento" in bench._conclusion_lectura(lectura)


def test_resumir_scalene_rechaza_rutas_fuera_del_proyecto(tmp_path: Path):
    from benchmarks.rutas import ruta_en_proyecto

    assert ruta_en_proyecto(Path("docs/mediciones/scalene/resumen.md")).is_relative_to(BASE_DIR)
    with pytest.raises(ValueError, match="fuera del proyecto"):
        ruta_en_proyecto(Path("../fuera.md"))
    with pytest.raises(ValueError, match="fuera del proyecto"):
        ruta_en_proyecto(tmp_path / "x.md")


def test_benchmark_archivos_valida_rangos():
    with pytest.raises(SystemExit):
        bench.main(["--pedidos", "0"])
    with pytest.raises(SystemExit):
        bench.main(["--lotes", "0"])


def test_puntos_de_entrada_llaman_freeze_support():
    main_txt = (BASE_DIR / "main.py").read_text(encoding="utf-8")
    app_txt = (BASE_DIR / "src" / "ui" / "app.py").read_text(encoding="utf-8")
    assert "freeze_support()" in main_txt
    assert "freeze_support()" in app_txt
