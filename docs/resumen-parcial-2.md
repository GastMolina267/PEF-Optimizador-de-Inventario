# Resumen Ejecutivo y Técnico — Segundo Parcial

**Materia:** Programación Eficiente — Opción 6 (Universidad Blas Pascal, 2026)  
**Proyecto:** Optimizador de Inventario y Preparación de Pedidos en Escala Masiva  
**Rama de Entrega:** `parcial-2`  
**Base de Referencia:** Tag `parcial-1` (Commit `e3230a1`)  

Este documento resume exhaustivamente todas las transformaciones arquitectónicas, algorítmicas, métricas de calidad y optimizaciones introducidas a lo largo de las **fases F1 a F9 del Segundo Parcial**. Sirve como documento canónico y base conceptual para la **defensa oral** y la presentación interactiva (`docs/presentation/`).

---

## 1. Cumplimiento de Requisitos de la Cátedra (Parcial II)

A continuación se detalla la correspondencia entre los temas solicitados por la cátedra en `docs/Parcial-II.txt` y su implementación efectiva en el proyecto:

| Requisito de la Cátedra | Fase | Subsistema / Archivos Clave | Evidencia e Implementación |
|---|:---:|---|---|
| **Eliminar código redundante** | F3 | `src/pedidos/agrupador.py`, `src/inventario/catalogo_hash.py` | Eliminación de búsquedas anidadas repetidas en picking consolidado; unificación de índices invertidos de texto y categorías; borrado de pasadas redundantes. |
| **Compiladores y perfilado** | F4 | `benchmarks/perfilar_scalene.py`, `benchmarks/resumir_scalene.py`, `docs/mediciones/scalene/` | Diagnóstico con Scalene (distinción CPU Python vs. nativo C/C++ y memoria), cProfile, line_profiler y tracemalloc. Detección del cuello de botella de IPC. |
| **Herramientas de APM** | F6 | `src/observabilidad/apm.py`, `scripts/demo_apm.py`, `docs/observabilidad-apm.md` | Integración de **Elastic APM** con decoradores `@apm_transaction` y `@apm_span`, captura de métricas y errores transaccionales, y fallback desacoplado sin dependencias duras. |
| **Lectura/escritura de archivos grandes** | F5 | `src/datos/streaming.py`, `src/datos/procesador_lotes_paralelo.py`, `src/datos/generador_archivos.py` | Lectura generativa en streaming línea a línea (JSONL), buffers de escritura atómicos (`BufferEscritura`), validación de datasets masivos y chunking paralelo con pools de procesos. |
| **Legibilidad y mantenibilidad** | F1, F7 | Todo el código base en `src/`, `automations/`, `benchmarks/` | Nombres de variables explícitos en español, tipado estricto con `typing` / `Protocol`, docstrings estilo Google en español (Argumentos, Retorna, Lanza), formateo PEP 8 integral con `ruff`. |
| **Generadores de documentación** | F8 | `docs/sphinx/`, `.github/workflows/verify.yml` | Documentación técnica con **Sphinx**, tema **Furo**, `autodoc`, `napoleon`, `viewcode`, `myst-parser` (inclusión Markdown sin duplicación), build estricto con `-W` (0 advertencias) y GitHub Pages. |
| **Herramientas de calidad** | F1, F9 | `sonar-project.properties`, `docs/mediciones/linea_base_parcial2/` | Configuración de SonarQube Cloud, verificación con `radon` (complejidad ciclomática y mantenibilidad), `vulture` (código muerto), `pylint` (duplicados) y `complexipy <= 15`. |
| **Refactorización modular** | F7 | `src/modelos/`, `src/inventario/`, `src/pedidos/`, `src/ranking/`, `src/cache/`, `src/datos/`, `src/motor/`, `src/ui/` | Descomposición en 9 paquetes cohesivos; desacoplamiento con `CatalogoProtocol`; reducción de funciones con complejidad D a funciones modulares de complejidad A/B (máx CC ≤ 12). |
| **Testing integral y regresión** | F2, F9 | `tests/` (11 subdirectorios modulares), `tests/integracion/test_benchmarks.py` | 193 pruebas automatizadas (0 fallos), 90% de cobertura en `src/`, CI con `--cov-fail-under=85`, microbenchmarks continuos con `pytest-benchmark` y property-based testing con Hypothesis. |
| **Uso de frameworks** | F7, F8 | `src/ui/app.py`, `tests/`, `docs/sphinx/` | **Flet** (interfaz gráfica moderna sobre Flutter Engine), **pytest** (framework de pruebas y benchmarks) y **Sphinx** (framework de documentación técnica). |

---

## 2. Cuadro Comparativo Maestro de Calidad (Parcial 1 vs. Parcial 2)

Las siguientes métricas fueron tomadas con los **mismos 9 comandos instrumentales** en el commit de cierre de cada parcial:

| Métrica de Calidad | Primer Parcial (`parcial-1`) | Segundo Parcial (`parcial-2`) | Delta / Impacto | Evidencia |
|---|:---:|:---:|:---:|---|
| **Pruebas Automatizadas** | 84 tests (0 fallos) | **193 tests (0 fallos)** | **+109 tests (+130%)** | `cobertura.txt` |
| **Organización de Tests** | Monolítica por etapas (`test_etapa_*.py`) | **11 subdirectorios modulares** | Modularizado por dominio | `tests/` |
| **Cobertura en `src/`** | 80% (2.005 stmts, 404 miss) | **90%** (2.523 stmts, 258 miss) | **+10 puntos porcentuales** | `cobertura.txt`, `coverage.xml` |
| **Umbral de Fallo en CI** | 75% | **85%** (`--cov-fail-under=85`) | **+10 pp más exigente** | `.github/workflows/verify.yml` |
| **Ruff (Configuración del Repo)** | 19 problemas (F541, F401, F841) | **0 problemas** (`All checks passed!`) | **100% resuelto** | `ruff_config_actual_detalle.txt` |
| **Ruff (PEP 8 + Docstrings + CC)** | 517 problemas (275 líneas > 100, 106 sin docstring) | **36 problemas** (0 líneas largas, 0 sin docstrings) | **-93% de observaciones** | `ruff_pep8_docstrings.txt` |
| **Complejidad Ciclomática Promedio** | A (3.59) sobre 287 bloques | **A (2.94)** sobre 455 bloques | **-18% complejidad** | `radon_complejidad.txt` |
| **Funciones Complejidad C o peor** | 15 funciones | **6 funciones** | **-60% funciones complejas** | `radon_complejidad.txt` |
| **Funciones Complejidad D o peor** | 3 funciones (hasta CC 30) | **0 funciones** | **100% erradicadas (máx CC ≤ 12)** | `radon_complejidad.txt` |
| **Duplicación de Código (Pylint ≥ 6 lín.)** | 8 pares duplicados | **0 pares duplicados** (Rating 10.00/10) | **Duplicación eliminada al 100%** | `pylint_duplicados.txt` |
| **Candidatos a Código Muerto (Vulture)** | 69 candidatos | **56 candidatos** (solo callbacks UI) | **Reducción neta** | `vulture_codigo_muerto.txt` |
| **Cognitive Complexity (complexipy)** | No integrada | **Aprobada** (máximo permitido 15) | Verificación continua en CI | `.github/workflows/verify.yml` |
| **Documentación Sphinx (`-W`)** | Inexistente | **0 advertencias** (20 páginas generadas) | Build limpio y estricto | `docs/sphinx/` |
| **Tamaño de `src/`** | 5.375 LOC / 4.156 SLOC | **7.604 LOC / 5.765 SLOC** | Arquitectura modular desacoplada | `radon_tamano.txt` |

---

## 3. Comparativa de Rendimiento Algorítmico y Tiempos de Ejecución

### Microbenchmarks de Regresión Continua (`pytest-benchmark`)
Mediciones reproducibles ejecutadas sobre el hardware de evaluación en nanosegundos y microsegundos:

| Operación Crítica | Mínimo | Mediana | Media | Operaciones/segundo (OPS) | Speedup / Orden |
|---|:---:|:---:|:---:|:---:|:---:|
| **Búsqueda Hash por ID** | 80.0 ns | 87.0 ns | 93.2 ns | **10.729.841 ops/s** | **11.4x** vs. Lineal |
| **Búsqueda Lineal por ID** | 800.0 ns | 1.000.0 ns | 1.061.5 ns | **942.075 ops/s** | $O(n)$ referencia |
| **Ranking Top-N (Min-Heap)** | 8.80 µs | 9.80 µs | 10.12 µs | **98.772 ops/s** | $O(N \log k)$ |
| **Combinaciones DP Memoizadas** | 20.00 µs | 21.10 µs | 21.92 µs | **45.617 ops/s** | $O(N \cdot P)$ |
| **Procesamiento de Pedidos** | 28.30 µs | 30.00 µs | 31.69 µs | **31.551 ops/s** | $O(P \cdot L)$ |
| **Batch Picking Consolidado** | 28.50 µs | 29.50 µs | 31.04 µs | **32.220 ops/s** | $O(L_{\text{total}})$ |

### Escalabilidad Macroscópica (Dataset Grande: 10.000 Productos, 2.000 Pedidos)
Resultados de `docs/mediciones/tabla_comparativa.md` que contrastan el comportamiento en escala masiva:

| Operación | Complejidad Base | Complejidad Opt | Tiempo Base (ms) | Tiempo Opt (ms) | Speedup Empírico | Conclusión Algorítmica |
|---|:---:|:---:|---:|---:|:---:|---|
| **Búsqueda por ID** | $O(n)$ | $O(1)$ | 0.369 ms | 0.008 ms | **47.07x** | Acceso hash indexado directo vs. escaneo de lista contigua. |
| **Búsqueda por Nombre** | $O(n)$ | $O(1)$ amort. | 20.677 ms | 0.012 ms | **1692.08x** | Índice invertido tokenizado + caché reactiva LRU de 128 slots. |
| **Ranking Top-N (k=5)** | $O(N \log N)$ | $O(N \log k)$ | 15.150 ms | 9.013 ms | **1.68x** | `heapq.nlargest` acota la memoria estrictamente a $k$ elementos en vez de ordenar todo el conjunto. |
| **Batch Picking Consolidado** | $O(P \cdot L \cdot n)$ | $O(L)$ | 827.524 ms | 106.052 ms | **7.80x** | Acumulación de líneas en una sola pasada hash eliminando el producto cartesiano en almacén. |
| **Combinaciones Sustitutas** | $O(2^N)$ | $O(N \cdot P)$ | 42.295 ms | 21.883 ms | **1.93x** | La memoización DP poda ramas idénticas y evita el colapso del call stack recursivo. |
| **Preparación Multiproceso (Windows)** | $O(P \cdot L)$ | $O((P \cdot L)/C + \text{IPC})$ | 65.725 ms | 535.725 ms | **0.12x** (Overhead) | La sobrecarga de IPC, spawn y serialización pickle supera el costo de cómputo en RAM para ítems livianos. |

---

## 4. Nuevos Subsistemas y Aportes Arquitectónicos de Parcial 2

### A. Refactorización en 9 Paquetes de Dominio y Protocolo Tipado (F7)
El diseño se desacopló del esquema original mediante paquetes cohesivos:
- `src/modelos/`: Dataclasses inmutables y validadas (`Producto`, `Pedido`, `LineaPedido`).
- `src/inventario/`: Implementación de `CatalogoProtocol` (`src/inventario/protocolo.py`), permitiendo que `CatalogoLineal` y `CatalogoHash` sean intercambiables en tiempo de ejecución bajo tipado estructural (`typing.Protocol`).
- `src/pedidos/`: Procesamiento secuencial y concurrente con `GestorPool`, evaluación línea a línea (`EvaluadorPedido`) y combinaciones sustitutas (`BuscadorCombinaciones`).
- `src/ranking/`: Algoritmo `top_n_productos` con `heapq`.
- `src/cache/`: `CacheConsultas` con política de desalojo LRU (128 slots) e invalidación reactiva atómica ante eventos de negocio.
- `src/datos/`: Módulo de streaming, batching, validación y generadores reproducibles.
- `src/observabilidad/`: Instrumentación de Elastic APM.
- `src/motor/`: Fachada unificada `MotorInventario` que orquesta los subsistemas y gestiona el switch de modo *Baseline* vs. *Optimizado*.
- `src/ui/`: Aplicación gráfica reactiva en Flet (Flutter Engine).

### B. Streaming, Buffering y Procesamiento de Archivos Grandes (F5)
- **Generadores puros en streaming:** `leer_productos_streaming_jsonl()` y `leer_pedidos_streaming_jsonl()` leen archivos masivos línea a línea (`O(1)` en RAM), previniendo saturación de memoria por parseo completo de JSON.
- **Buffer atómico:** `BufferEscritura` retiene registros y vacía en disco al alcanzar un tamaño umbral configurable o al cerrar el contexto, reduciendo drásticamente las llamadas a I/O del sistema operativo.
- **Procesamiento paralelo por lotes:** `procesar_archivo_en_lotes()` divide el archivo en bloques y los despacha mediante `ProcessPoolExecutor`.
- **Validación robusta:** `ValidadorDataset` detecta tipos incompatibles, precios/stock negativos y referencias rotas sin fallar silenciosamente.

### C. Observabilidad con Elastic APM (F6)
- **Transacciones y spans instrumentados:** Decoradores `@apm_transaction` y `@apm_span` en `src/observabilidad/apm.py` capturan el tiempo de CPU y wall-clock de operaciones clave.
- **Desacoplamiento total:** Si las variables de entorno de Elastic (`ELASTIC_APM_SERVER_URL`) no están presentes, el cliente opera en modo pasivo (*no-op*), garantizando que el sistema funcione normalmente en cualquier entorno local o de CI.
- **Script interactivo:** `scripts/demo_apm.py` permite simular cargas y validar el envío de eventos hacia el APM Server.

### D. Documentación Técnica Rigurosa con Sphinx (F8)
- Generación de sitio HTML estático en `docs/sphinx/_build/html/`.
- Uso de `myst-parser` con directivas `{include}` para que los manuales de `docs/` se documenten sin duplicación.
- Compilación automatizada en CI con el flag estricto `-W` (**0 advertencias** permitidas).
- Despliegue automático a GitHub Pages desde la rama de trabajo.

---

## 5. Puntos Estratégicos para la Defensa Oral (Guión de Exposición)

1. **Rigor Científico y Dualidad Preservada:**
   *Mensaje clave:* Nunca eliminamos el código Baseline. Ambas versiones conviven bajo la fachada `MotorInventario` y comparten la misma suite de tests de equivalencia, permitiendo demostrar empíricamente el speedup en cualquier momento con exactitud transaccional.

2. **Lección Empírica sobre Paralelismo y Ley de Amdahl:**
   *Mensaje clave:* Cuando el trabajo unitario en memoria es extremadamente veloz ($O(1)$ en tabla hash, ~90 nanosegundos), el paralelismo con procesos en Windows introduce un costo de spawn, pipes IPC y serialización `pickle` que resulta **28 veces más lento** que la ejecución mono-hilo optimizada. Esto demuestra comprensión de los límites del paralelismo y los costos de hardware.

3. **Concurrencia Segura y Mutación de Inventario:**
   *Mensaje clave:* En el Segundo Parcial, el despacho concurrente de pedidos descuenta el stock de manera atómica con sincronización thread-safe, evitando *data races* y preservando la consistencia transaccional cuando múltiples pedidos compiten por los mismos ítems.

4. **Deuda Técnica y Calidad de Código:**
   *Mensaje clave:* Erradicamos todas las funciones de complejidad ciclomática D (que llegaban a 30 en el primer parcial). Hoy ninguna función supera complejidad 12, el 100% de los archivos pasa `ruff` y `radon`, la duplicación de código según Pylint es del 0%, y la cobertura de pruebas saltó del 80% al 90%.

5. **Testing Transversal e Invariantes:**
   *Mensaje clave:* No solo escribimos tests unitarios tradicionales; implementamos property-based testing con **Hypothesis** para descubrir casos de borde automáticamente, pruebas de regresión continua con **pytest-benchmark** para detectar degradaciones de rendimiento en nanosegundos, y pruebas de carga con archivos corruptos y vacíos.
