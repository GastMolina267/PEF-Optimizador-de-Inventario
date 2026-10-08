# Línea base de calidad — Segundo Parcial

Foto de las métricas de calidad del código **al cierre del Segundo Parcial**, tomada tras la implementación de todas las fases de refactorización modular, concurrencia segura, streaming de datos, observabilidad APM, documentación con Sphinx y suite de pruebas modularizada. Sirve como demostración empírica y cuantitativa de la evolución respecto a la línea base del Primer Parcial.

- **Código medido:** rama `parcial-2` (preparada para entrega y defensa oral).
- **Fecha:** 2026-10-08.
- **Entorno:** Python 3.14.6, Windows. Herramientas: ruff, radon, vulture, pylint, pytest 9.1.1, coverage 7.16.2, pytest-benchmark 5.1.0, flet.

## Comparativa Oficial: Primer Parcial vs. Segundo Parcial

| Métrica de Calidad | Primer Parcial (`parcial-1`) | Segundo Parcial (`parcial-2`) | Delta / Impacto | Archivo de Evidencia |
|---|---|---|---|---|
| **Suite de Tests** | 84 pasan, 0 fallan | **193 pasan, 0 fallan** | **+109 tests (+130%)**, 11 subpaquetes | `cobertura.txt` |
| **Cobertura de `src/`** | 80% (2005 stmts, 404 miss) | **90%** (2523 stmts, 258 miss) | **+10 puntos porcentuales**, supera umbral 85% | `cobertura.txt`, `coverage.xml` |
| **Ruff (configuración del repo)** | 19 problemas (14 F541, 4 F401, 1 F841) | **0 problemas** (`All checks passed!`) | **100% resuelto y formateado** | `ruff_config_actual.txt`, `ruff_config_actual_detalle.txt` |
| **Ruff (PEP 8 + Docstrings + Complejidad)** | 517 problemas (275 E501 > 100, 106 docstrings) | **36 problemas** (0 E501, 0 docstrings faltantes) | **-93% de problemas** (solo 13 D107 por estilo Google) | `ruff_pep8_docstrings.txt` |
| **Complejidad Ciclomática Promedio** | A (3.59) sobre 287 bloques | **A (2.94)** sobre 455 bloques | **-18% complejidad promedio** | `radon_complejidad.txt` |
| **Funciones con Complejidad C o peor** | 15 funciones | **6 funciones** | **-60% funciones complejas** | `radon_complejidad.txt` |
| **Funciones con Complejidad D o peor** | 3 (`procesar_pedidos_concurrente` 29, `derivar_complejidad` 30, `construir_propuestas` 29) | **0 funciones** | **100% erradicadas (máx CC actual ≤ 12)** | `radon_complejidad.txt` |
| **Duplicación de Código (Pylint ≥ 6 líneas)** | 8 pares duplicados | **0 pares duplicados** (Score 10.00/10) | **Duplicación eliminada al 100%** | `pylint_duplicados.txt` |
| **Candidatos a Código Muerto (Vulture ≥ 60%)** | 69 (27 descartando controles Flet) | **56** (solo callbacks y extensiones) | **Reducción neta y tipado estricto** | `vulture_codigo_muerto.txt` |
| **Tamaño y Modularidad de `src/`** | 5375 LOC, 4156 SLOC | **7604 LOC, 5765 SLOC** | **Arquitectura modular desacoplada en 9 módulos** | `radon_tamano.txt` |

## Rendimiento de Operaciones Críticas (`pytest-benchmark`)

Mediciones empíricas en nanosegundos y microsegundos integradas en la suite de regresión continua:

| Operación | Mínimo | Mediana | Media | Operaciones/segundo (OPS) |
|---|---|---|---|---|
| **Búsqueda Hash por ID** (`test_benchmark_busqueda_hash_id`) | 80.0 ns | 90.0 ns | 90.2 ns | **11,080,503 ops/s** |
| **Búsqueda Lineal por ID** (`test_benchmark_busqueda_lineal_id`) | 800.0 ns | 1,000.0 ns | 976.6 ns | **1,023,942 ops/s** |
| **Ranking Top-N (Min-Heap)** (`test_benchmark_top_n_heap`) | 8.90 µs | 9.30 µs | 9.45 µs | **105,763 ops/s** |
| **Combinaciones Sustitutas DP** (`test_benchmark_combinaciones_dp`) | 20.0 µs | 21.3 µs | 22.49 µs | **44,461 ops/s** |
| **Batch Picking Consolidado** (`test_benchmark_batch_picking`) | 28.5 µs | 29.7 µs | 32.91 µs | **30,384 ops/s** |
| **Procesamiento de Pedidos** (`test_benchmark_procesamiento_pedidos`) | 28.3 µs | 30.4 µs | 31.64 µs | **31,607 ops/s** |

> [!NOTE]
> La búsqueda hash en catálogo ($O(1)$) alcanza una aceleración de **11x** en micro-benchmark respecto a la búsqueda lineal ($O(n)$) en catálogos muestra, escalando a más de **47x - 1600x** en catálogos de 10.000 ítems según `docs/mediciones/tabla_comparativa.md`.

## Observaciones de Ingeniería

1. **Estructura Modular de Pruebas:** Los tests pasaron de un esquema monolítico basado en etapas cronológicas (`test_etapa_*.py`) a una arquitectura por dominio (`tests/modelos/`, `tests/inventario/`, `tests/pedidos/`, `tests/ranking/`, `tests/cache/`, `tests/datos/`, `tests/observabilidad/`, `tests/motor/`, `tests/ui/`, `tests/integracion/`, `tests/automations/`).
2. **Eliminación de Complejidad Crítica:** El refactor arquitectónico en F7 descompuso las funciones de complejidad D (`procesar_pedidos_concurrente`, `derivar_complejidad` y `construir_propuestas`) en sub-rutinas cohesivas y clases especializadas con complejidades A y B, cumpliendo con la cota máxima de `complexipy <= 15`.
3. **Respeto PEP 8 y Formateo:** Se eliminaron todas las líneas largas (> 99 caracteres), imports no utilizados e inconsistencias de ordenamiento, logrando 0 advertencias de Ruff en la configuración oficial.

## Cómo reproducir

```powershell
# En la rama parcial-2
ruff check src benchmarks automations tests scripts main.py --statistics
ruff check src benchmarks automations tests main.py --select E,W,N,D,B,SIM,UP,PL,C90 --ignore D203,D213 --statistics
radon cc src benchmarks automations -s -a
radon mi src benchmarks automations -s
radon raw src -s
vulture src benchmarks automations main.py --min-confidence 60
pylint --disable=all --enable=duplicate-code --min-similarity-lines=6 src benchmarks automations
python -m pytest tests --cov=src --cov-report=term --cov-report=xml:docs/mediciones/linea_base_parcial2/coverage.xml
```
