# Línea base de calidad — Primer Parcial

Foto de las métricas de calidad del código **al cierre del Primer Parcial**, tomada antes de cualquier cambio del Segundo Parcial. Sirve como punto de comparación "antes / después" para refactorización, eliminación de código redundante, PEP 8, documentación y testing.

- **Código medido:** commit `faf6605` (`main`), marcado con el tag `parcial-1`.
- **Fecha:** 2026-10-07.
- **Entorno:** Linux, Python 3.10.12. Herramientas: ruff 0.16.10, radon 6.0.1, vulture 2.16, pylint 4.1.2, pytest 9.1.1, coverage 7.16.2, flet 1.0.3.

## Resumen

| Métrica | Valor | Archivo |
|---|---|---|
| Tests | 84 pasan, 0 fallan | `cobertura.txt` |
| Cobertura de `src/` | **80 %** (2005 sentencias, 404 sin cubrir) | `cobertura.txt`, `coverage.xml` |
| Ruff con la configuración actual del repo | 19 problemas (14 F541, 4 F401, 1 F841) | `ruff_config_actual*.txt` |
| Ruff con PEP 8 + docstrings + complejidad | 517 problemas (275 E501 > 100 col., 106 sin docstring, 73 números mágicos) | `ruff_pep8_docstrings.txt` |
| Complejidad ciclomática promedio | A (3,59) sobre 287 bloques | `radon_complejidad.txt` |
| Funciones con complejidad C o peor | 15 | `radon_complejidad.txt` |
| Funciones con complejidad D | `procesar_pedidos_concurrente` (29), `derivar_complejidad` (30), `construir_propuestas` (29) | `radon_complejidad.txt` |
| Bloques de código duplicado (≥ 6 líneas) | 8 pares | `pylint_duplicados.txt` |
| Candidatos a código muerto (vulture ≥ 60 %) | 69 (27 sin contar atributos de controles Flet, que son falsos positivos) | `vulture_codigo_muerto.txt` |
| Tamaño de `src/` | 5375 LOC, 4156 SLOC, comentarios 2 % de las líneas | `radon_tamano.txt` |

## Observaciones

- La cobertura de `src/pedidos/procesador_concurrente.py` (43 %) está subestimada: coverage no mide los procesos hijos del `ProcessPoolExecutor` sin `concurrency = ["multiprocessing"]`.
- vulture marca como "sin uso" métodos que sí usan los tests (`invalidar_clave`, `limpiar_cache`, `_desindexar_nombre`), porque los tests no se incluyeron en su análisis. Verificar antes de borrar.

## Cómo reproducir

```powershell
git checkout parcial-1
pip install ruff radon vulture pylint pytest-cov
ruff check src benchmarks automations tests scripts main.py --statistics
ruff check src benchmarks automations tests main.py --select E,W,N,D,B,SIM,UP,PL,C90 --ignore D203,D213 --statistics
radon cc src benchmarks automations -s -a
radon mi src benchmarks automations -s
radon raw src -s
vulture src benchmarks automations main.py --min-confidence 60
pylint --disable=all --enable=duplicate-code --min-similarity-lines=6 src benchmarks automations
python -m pytest tests --cov=src --cov-report=term --cov-report=xml
```
