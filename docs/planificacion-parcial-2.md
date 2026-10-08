# Planificación del Segundo Parcial

Optimizador de Inventario y Pedidos (Python), Programación Eficiente, Opción 6.

Este documento define **qué** se construye en el Segundo Parcial, **en qué orden** y **cómo se integra**. Sigue la misma lógica que [project-planning.md](project-planning.md): se trabaja por fases, y una fase no arranca hasta que la anterior cumple su criterio de cierre y su PR está mergeado.

**Punto de partida:** tag `parcial-1` (commit `e3230a1`), con las métricas en [mediciones/linea_base_parcial1/](mediciones/linea_base_parcial1/README.md).

---

## Flujo de trabajo

- Cada fase tiene **su propia rama**, creada desde `parcial-2` actualizada: `git switch parcial-2 && git pull && git switch -c p2/fN-nombre`.
- Todo se pushea a la rama de la fase. El **PR se abre contra `parcial-2`**.
- Los commits son chicos y con prefijo convencional (`feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `chore`).
- Cada PR debe: pasar CI (lint + tests), no bajar la cobertura, pasar el Quality Gate de SonarQube (desde F1), e incluir sus propios tests.
- Las automatizaciones Origin siguen corriendo en cada push. Su informe en la rama `cursor/...` del commit sirve como evidencia en la descripción del PR.
- Al cerrar el parcial: merge de `parcial-2` a `main` y tag `parcial-2`.

| Fase | Rama | Tema del enunciado | Depende de |
|---|---|---|---|
| F0 | `p2/f0-plan` | Planificación (este documento) | — |
| F1 | `p2/f1-calidad-sonarqube` | SonarQube, formato PEP 8 automático, CI | F0 |
| F2 | `p2/f2-tests-red-seguridad` | Testing (antes de refactorizar) | F1 |
| F3 | `p2/f3-eliminar-redundancia` | Eliminar código redundante, nuevas incorporaciones | F2 |
| F4 | `p2/f4-scalene-ipc` | Scalene, propuesta Origin elegida (IPC), paralelismo | F3 |
| F5 | `p2/f5-archivos-grandes` | Batching, buffering, procesamiento paralelo de archivos | F4 |
| F6 | `p2/f6-elastic-apm` | Elastic APM (métricas y errores) | F5 |
| F7 | `p2/f7-legibilidad-refactor` | Legibilidad, mantenibilidad, refactorización | F6 |
| F8 | `p2/f8-sphinx` | Documentación con Sphinx (migración) | F7 |
| F9 | `p2/f9-cierre` | Testing final, remedición, análisis y oral | F8 |

> El formateo automático (`ruff format`) va en F1 y no en F7: así toca todos los archivos una sola vez, antes de que existan otras ramas, y no genera conflictos de merge en las fases siguientes.

---

## Evaluación de las automatizaciones Origin

Fuente: último informe de hotspots (`cursor/hotspots-y-propuestas-faf6605`) y bloque de complejidad de `docs/analisis.md`.

| # | Propuesta Origin | Prioridad | Estado actual | Decisión |
|---|---|---|---|---|
| 1 | Reducir el overhead de IPC del pool de procesos | Alta | Parcial: pool persistente y opt-in en UI, pero el default del motor (`P >= 50`) sigue activando el pool y `grande.json` da 0,12× | **Elegida** (F4) |
| 2 | No usar el catálogo lineal fuera del experimento | Media | Cubierta: el baseline se mantiene solo para la comparación | Sin cambios de código. Se documenta |
| 3 | No pagar heap ni pool en escalas chicas (selector automático) | Alta | Parcial | Se absorbe **solo la parte del pool** dentro de la propuesta 1. El heap se mantiene siempre para no ocultar el contraste en la oral |
| 4 | Compactar el índice invertido (`array('I')`) | Baja | No | Descartada: el trade-off memoria/tiempo ya está justificado para 10k productos |
| 5 | Evitar el `sorted` final del lote de picking | Baja | No | Descartada como propuesta. Se revisa en F7 solo si Scalene lo marca |

### Por qué la propuesta 1

- Es el hotspot de mayor peso absoluto: cientos de milisegundos de `CreateProcess`, `WaitForSingleObject` y `pickle` contra microsegundos del resto.
- Se conecta directamente con los temas nuevos: Scalene distingue tiempo de Python, tiempo nativo y tiempo de sistema, y F5 necesita un paralelismo que de verdad compense.
- Al revisarla apareció un **error de correctitud** en el procesador concurrente (ver abajo), que hay que corregir de todas formas.

### Error encontrado: el procesador concurrente no respeta el consumo de stock

El procesador concurrente evalúa todos los pedidos contra **una misma foto inicial** del stock. Recién después descuenta. El secuencial, en cambio, descuenta pedido por pedido. Con `descontar_stock=True` los resultados difieren:

```text
Producto 1 con stock 5. Pedidos #1 y #2 piden 5 unidades cada uno.
procesar_pedidos_secuencial   -> [CUBIERTO, IMPOSIBLE]   stock final 0
procesar_pedidos_concurrente  -> [CUBIERTO, CUBIERTO]    stock final 0
```

El segundo descuento falla en silencio (`descontar_stock` devuelve `False`), pero el pedido queda informado como cubierto. Es alcanzable desde la pantalla Pedidos (switch de ProcessPool más "descontar stock"). Se reproduce con un test en F2 y se corrige en F4.

### Implementación elegida para la propuesta 1 (F4)

1. **Separar evaluación de asignación.** Los workers solo calculan la *demanda* de cada pedido (trabajo puro, paralelizable). La asignación de stock se hace en el proceso principal, en orden, con la misma regla que el secuencial. Esto corrige el error y garantiza resultados idénticos.
2. **Mandar menos datos.** El snapshot de stock se envía una sola vez por worker (`initializer`/`initargs`) y no en cada fragmento. Los resultados vuelven como tuplas compactas, no como dataclasses.
3. **Eliminar trabajo redundante.** El `sort` final por posición original sobra: los futuros ya se recorren en orden de envío y los fragmentos son contiguos.
4. **Umbral medido, no supuesto.** El default del motor deja de ser `P >= 50`. Se mide el punto de equilibrio real (secuencial vs pool) con Scalene y `comparar.py`, y el pool queda reservado para trabajo pesado: lotes de archivos grandes (F5) y combinaciones con DP.
5. **Encapsular el pool.** Las variables `global` `_executor`/`_executor_workers` pasan a una clase `GestorPool` con ciclo de vida explícito.

---

## F0 — Planificación

**Rama:** `p2/f0-plan`

- Este documento.
- **Cierre:** el grupo está de acuerdo con las fases, ramas y decisiones.

## F1 — Calidad continua: SonarQube y formato

**Rama:** `p2/f1-calidad-sonarqube`

**Objetivo.** Que desde la primera fase cada PR muestre su impacto en calidad.

**Incluye**

- **SonarQube Cloud** (el repo es público y el plan gratuito alcanza): proyecto vinculado al repo, `sonar-project.properties` y un job en `verify.yml` que sube el análisis. El Quality Gate se aplica sobre código nuevo.
- Importar a Sonar el `coverage.xml` y el reporte de ruff (`sonar.python.coverage.reportPaths`, `sonar.python.ruff.reportPaths`).
- Corregir el CI: el paso que sube la cobertura exige `python-version == '3.11'`, pero la matriz solo tiene 3.14, así que nunca se ejecuta.
- Medir la cobertura de los procesos hijos: `concurrency = ["multiprocessing"]` y `parallel = true` en `[tool.coverage.run]`.
- Ruff: fijar la línea en 99 caracteres (PEP 8 permite hasta 99 por acuerdo del equipo) y sumar las reglas `I`, `N`, `B`, `SIM` y `UP`. Tres reglas se dejan para F7, porque activarlas antes rompe el CI sin que el formateador pueda resolverlas: `E501` (87 líneas largas en strings y comentarios), `C90` (7 funciones con complejidad mayor a 10) y `D` (docstrings).
- Una pasada de `ruff format` y `ruff check --fix` en un **commit separado**, registrado en `.git-blame-ignore-revs`.
- `pre-commit` con ruff (lint y formato).
- Hacer que los tests no reescriban `docs/analisis.md` ni `docs/propuestas-mejora.md`: hoy cada `pytest` modifica sus cabeceras. Los tests de automatizaciones deben escribir en `tmp_path`.

**Fuera de esta fase:** corregir los hallazgos de Sonar (se hace en F3 y F7).

**Cierre:** el PR muestra el análisis de Sonar, el CI sube la cobertura y `pytest` deja el árbol de trabajo limpio.

## F2 — Tests de red de seguridad

**Rama:** `p2/f2-tests-red-seguridad`

**Objetivo.** Blindar el comportamiento antes de refactorizar.

**Incluye**

- `tests/conftest.py` con fixtures compartidas (catálogos, datasets, motor por estrategia).
- **Hypothesis**: propiedades de equivalencia baseline vs optimizado con datos aleatorios (búsqueda, top-N, agrupación, procesamiento sin descuento).
- Test que reproduce el error de concurrencia, marcado `xfail(strict=True)`: cuando F4 lo corrija, el test pasa a fallar como "xpass" y obliga a quitar la marca.
- Tests de las funciones públicas que hoy no se ejercitan (vulture las marca sin uso).
- Corregir la advertencia de pytest por fixtures de clase definidas como métodos de instancia (`test_etapa_5.py`).

**Cierre:** los tests nuevos pasan (salvo el `xfail`), la cobertura no baja del 80 %.

## F3 — Eliminar código redundante

**Rama:** `p2/f3-eliminar-redundancia`

**Objetivo.** Quitar duplicación y código muerto sin cambiar el comportamiento. Los tests de F2 lo garantizan.

**Incluye** (cada punto, un commit)

- Extraer `evaluar_pedido(...)`, hoy duplicado entre `procesador_secuencial.py` y `procesador_concurrente.py` (unas 28 líneas iguales), y la regla `debe_descontar(...)`, también duplicada.
- Unificar `cargador.validar_dataset` y `ValidadorDataset.validar_todo`, que repiten las mismas reglas. Queda un único validador.
- `MotorInventario._crear_catalogo()` en lugar de la misma construcción repetida en 3 métodos.
- `PantallaBase` para las 6 pantallas que repiten la inicialización (detectado por pylint).
- Código muerto confirmado: el import de `memory_usage`, `r_base`/`r_puro`, las 14 f-strings sin variables, los 4 imports y 1 variable sin uso. Cada candidato de vulture se verifica contra los tests antes de borrarlo.
- El alias `cargar_dataset = cargar_dataset_json`: se elige un único nombre.
- **No se borra**: `CatalogoLineal` ni las versiones baseline (propuesta Origin 2: son el experimento).

**Nuevas incorporaciones** (requisitos de fases siguientes que conviene dejar preparados acá):

- `Enum EstrategiaMotor` (`BASELINE`, `OPTIMIZADO`) en lugar de los strings sueltos.
- `Enum PoliticaDescuento` en lugar de `"solo_cubiertos"` / `"todo_lo_posible"`.

**Cierre:** pylint no reporta duplicados en `src/`, vulture queda solo con falsos positivos de Flet, los tests siguen en verde.

## F4 — Scalene y propuesta Origin 1 (IPC)

**Rama:** `p2/f4-scalene-ipc`

**Objetivo.** Usar Scalene como herramienta de optimización y aplicar la propuesta Origin elegida, con medición antes/después.

**Incluye**

- `benchmarks/perfilar_scalene.py`: escenarios reproducibles (búsquedas, picking, combinaciones, procesamiento secuencial vs pool) con los mismos datasets del parcial 1.
- Salidas en `docs/mediciones/scalene/`: reporte JSON (`--json`, para la automatización) y HTML (para la oral). Se lee el desglose de tiempo Python / nativo / sistema y la memoria por línea.
- **Medición "antes"** con Scalene sobre el código de F3, **implementación** de los 5 puntos de la propuesta 1, y **medición "después"**.
- Quitar la marca `xfail` del test de concurrencia de F2.
- Extender `automations/proponer_mejoras.py` para que lea el JSON de Scalene (hoy el informe aclara que no hay datos de Scalene).
- Actualizar `docs/mediciones/comandos_profiling.md`.

**Riesgos**

- Scalene 2.3 publica binarios para Windows con Python 3.10, 3.12, 3.13 y 3.14, pero **no para 3.11**. Conviene acordar una versión de Python para el grupo (sugerido: 3.13).
- Si la memoria por línea no funciona en Windows, se perfila en el job de CI (Linux) y se commitean esos reportes.

**Cierre:** el reporte de Scalene muestra la reducción de tiempo de sistema/IPC, el procesamiento concurrente da los mismos resultados que el secuencial en todos los casos y el umbral del pool queda documentado con datos.

## F5 — Archivos grandes: batching, buffering y paralelismo

**Rama:** `p2/f5-archivos-grandes`

**Estado actual**

| Técnica | Hoy | Problema |
|---|---|---|
| Lectura | `json.load` del archivo entero | La memoria crece con el archivo. El dataset más grande pesa 2,4 MB: no hay ningún caso realmente grande |
| Escritura | `json.dump(..., indent=2)` en una sola llamada | Archivo inflado por la indentación, sin control del buffer |
| Batching | Solo los fragmentos del pool (`ceil(P / workers)`) | No hay procesamiento por lotes de archivos |
| Buffering | Ninguno explícito | — |
| Paralelismo | Pool sobre pedidos ya cargados en memoria | No compensa: el trabajo por pedido es un lookup O(1) |

**Incluye**

- **Formato por líneas (JSON Lines):** `productos.jsonl` y `pedidos.jsonl`. Se mantiene la lectura del JSON actual por compatibilidad.
- **Escritura con buffer:** `open(..., buffering=1 << 20)` y escritura por lotes (`writelines` de bloques serializados), sin indentación. Generador con semilla fija para 100k productos / 1M de pedidos.
- **Lectura en streaming:** generador línea por línea y `en_lotes(iterable, n)` propio (`itertools.batched` exige Python 3.12 y el proyecto declara 3.10+). Validación por lote.
- **Procesamiento paralelo por lotes:** cada worker parsea, valida y evalúa un lote completo. Aquí el pool sí debería compensar, porque el trabajo por lote es grande frente al IPC. Hay que confirmarlo midiendo.
- **Exportación con buffer** del resultado (por ejemplo, el reporte de picking consolidado en CSV), para cubrir también la escritura.
- **Benchmarks:** carga completa vs streaming vs lotes en paralelo, midiendo tiempo, pico de memoria (`tracemalloc`) y Scalene. Barrido de tamaños de lote (1k, 10k, 50k) para justificar el elegido.
- **UI:** cargar un `.jsonl` desde Flet con barra de progreso por lote. No se renderizan millones de filas: solo un resumen y vista paginada.

**Implicancias**

- Los archivos grandes **no se commitean** ni se generan dentro de OneDrive: se generan con semilla en una carpeta ignorada por git (`data/generados/`).
- Para validar que cada línea de pedido apunte a un producto existente, primero se carga el set de IDs de productos y después se recorren los pedidos.
- Los tests usan archivos chicos generados en `tmp_path` (archivo vacío, línea corrupta, último lote incompleto, ID inexistente).

**Cierre:** la tabla muestra memoria constante en streaming y un speedup mayor a 1× en lotes paralelos a partir de un tamaño documentado.

## F6 — Elastic APM

**Rama:** `p2/f6-elastic-apm`

**Objetivo.** Enviar métricas de rendimiento y errores de la aplicación a Elastic.

**Incluye**

- Módulo `src/observabilidad/apm.py`. Crea el `elasticapm.Client` **solo si** existe `ELASTIC_APM_SERVER_URL` (en el entorno o en `.env`). Sin ella todo funciona igual y no se envía nada (tests y CI incluidos).
- **Transacciones** en las operaciones de la fachada `MotorInventario` (decorador `@medir`): cargar dataset JSON y JSONL, buscar, top-N, agrupar, exportar CSV, alternativas, procesar pedidos y procesar archivos por lotes. Si la operación corre dentro de otra transacción (por ejemplo, un escenario), aparece como span de esa transacción.
- **Spans** internos: armado de fragmentos y espera del pool (`pool.armar_fragmentos`, `pool.evaluar`) y procesamiento de un archivo por lotes (`lotes.procesar_archivo`).
- **Etiquetas** para filtrar en Kibana: estrategia, productos, pedidos, dataset, tamaño de lote, workers, concurrente, cubiertos y parciales.
- **Errores:** las excepciones de las operaciones instrumentadas se envían solas (la transacción queda como `failure`), `BrokenProcessPool` se registra como error controlado y los registros de `logging` con nivel ERROR o superior se envían con `ManejadorErroresAPM`.
- **Infraestructura:** proyecto serverless *Observability Complete* en Elastic Cloud (prueba gratuita). La alternativa local con Docker se descartó para no exigir Docker a todo el grupo.
- `scripts/demo_apm.py`: genera actividad (baseline vs optimizado, secuencial vs pool) y un error de carga a propósito para la oral.
- Guía de uso: `docs/observabilidad-apm.md`.

**Implicancias**

- Los workers del `ProcessPoolExecutor` no comparten el cliente APM: se instrumenta el lado del proceso principal (envío y recepción de lotes).
- La API key nunca va al repo. Hay un `.env.example` y `.env` está en `.gitignore`.
- La prueba de Elastic Cloud dura 14 días (creada el 8/10). Si la defensa es después, hay que crear otra prueba o pasar al stack local.
- `elastic-apm` 6.26 declara soporte hasta Python 3.13. Es otro motivo para fijar 3.13 en el entorno del grupo.
- El `.exe` de PyInstaller tiene que incluir el agente (revisar `scripts/compile.py`).

**Cierre:** una corrida de la demo aparece en Kibana con transacciones, spans y al menos un error capturado a propósito (dataset inválido).

## F7 — Legibilidad, mantenibilidad y refactorización

**Rama:** `p2/f7-legibilidad-refactor`

**Incluye**

- **Docstrings** en las 106 clases y funciones públicas que no tienen. Estilo Google con secciones en español (`Argumentos`, `Retorna`, `Lanza`), que Sphinx interpreta en F8 con `napoleon_custom_sections`. Se activan las reglas `D` de ruff.
- **Nombres:** se terminan los nombres mezclados (`lineas_satisfechas_count` → `cantidad_lineas_satisfechas`) y las abreviaturas (`p`, `ped`, `prod`, `e`, `rl`).
- **Constantes con nombre** en lugar de números mágicos (73 casos).
- **Líneas largas:** corregir a mano las 87 líneas que `ruff format` no puede partir y quitar `ignore = ["E501"]`.
- **Complejidad:** activar `C90` y partir las funciones D de radon que queden después de F4 (`derivar_complejidad` 30, `construir_propuestas` 29) y las C más altas (`buscar_alternativas` 19, `validar_dataset` 16).
- **Organización:** tipos explícitos en las fachadas (`catalogo: Catalogo` con un `Protocol` común a lineal y hash).
- Sonar: llevar a cero los *code smells* críticos y mayores.

**Cierre:** ruff sin errores con `E501`, `C90` y `D` activadas, ninguna función con complejidad D, Sonar sin smells críticos ni mayores.

**Resultado**

| Métrica | Base (F6) | F7 |
|---|---|---|
| Hallazgos de ruff con `E501`, `C90`, `D` y `PLR2004` | 149 (105 líneas largas, 18 docstrings, 21 números mágicos, 4 funciones complejas) | 0 |
| Funciones con complejidad cognitiva > 15 (complexipy / Sonar S3776) | 14 (máx. 46, `main` de la UI) | 0 |
| Funciones con complejidad ciclomática > 10 | 4 | 0 |
| Tests | — | +11 (`tests/test_f7_refactor.py`) |

- **UI:** `main` (complejidad 46) pasó a la clase `AplicacionInventario` y a una tupla `SECCIONES` que declara las siete pantallas.
- **Automatizaciones:** `derivar_complejidad` y `construir_propuestas` pasaron a tablas de reglas (una función por caso). Se verificó que los informes generados son idénticos byte a byte.
- **Refactors de lógica** (`combinaciones`, `catalogo_hash`, `validador`, `streaming`): se verificaron contra la versión anterior con los mismos datasets y 864 casos de alternativas. Las salidas son idénticas.
- `Catalogo` es un `typing.Protocol` (`src/inventario/protocolo.py`) que cumplen `CatalogoLineal` y `CatalogoHash`.
- **Seguridad del CI:**
  - dependencias fijadas en `uv.lock` e instaladas con `uv sync --locked --no-build`;
  - actions de terceros fijadas por SHA;
  - permisos mínimos por job;
  - inputs de `workflow_dispatch` pasados por variables de entorno y validados (sin inyección en scripts).

**Decisiones**

- **`D107` desactivada:** el docstring de la clase documenta el constructor (estilo Google).
- **Tests sin `D1` ni `PLR2004`:** el nombre del test describe el caso, y los valores esperados literales son la forma más legible de un assert.
- **complexipy en el CI y en pre-commit** con umbral 15, para que la complejidad cognitiva no dependa de que Sonar corra.
- **`requirements*.txt` se mantienen** para quien instale con pip. `uv.lock` es la fuente de verdad del CI.
- **S2245 (random no criptográfico) excluida solo en los generadores de datos de prueba,** donde la semilla fija es intencional.

## F8 — Documentación con Sphinx

**Rama:** `p2/f8-sphinx`

**Incluye**

- `docs/sphinx/` con `sphinx-quickstart`, `language = "es"` y el tema Furo.
- **Extensiones:** `autodoc`, `napoleon` (con secciones en español), `viewcode` y `myst-parser`. Con `myst-parser` se migran los `.md` existentes (`analisis.md`, `app-flow-explanation.md`, `project-planning.md`, este plan y las mediciones) sin reescribirlos.
- **Referencia de la API** generada desde los docstrings: modelos, inventario, pedidos, ranking, caché, datos y motor. La UI (Flet) se documenta con `autodoc_mock_imports = ["flet"]`.
- Job de CI que construye con `-W` (las advertencias cortan el build) y **publica en GitHub Pages**. Requisito: activar Pages en *Settings → Pages → Source: GitHub Actions*.
- Enlace a la documentación publicada en el README.

**Cierre:** la documentación compila sin advertencias y está publicada.

## F9 — Cierre: testing final, remedición y oral

**Rama:** `p2/f9-cierre`

**Incluye**

- Tests reorganizados por módulo (`tests/inventario/`, `tests/pedidos/`, …) en lugar de por etapa.
- `--cov-fail-under=85` en el CI.
- `pytest-benchmark` para detectar regresiones de rendimiento en las operaciones principales.
- `docs/mediciones/linea_base_parcial2/` con las **mismas herramientas** que la línea base del parcial 1, y una tabla antes/después.
- Actualizar `docs/analisis.md`, `tabla_comparativa.md`, las automatizaciones (`MODULOS_FUNDAMENTALES` con los módulos nuevos) y la presentación.
- Merge de `parcial-2` a `main` y tag `parcial-2`.

**Cierre:** todo en verde y la tabla antes/después completa para la oral.

---

## Testing transversal

Además de F2 y F9, **cada fase trae sus propios tests**:

| Fase | Tests mínimos |
|---|---|
| F3 | Los existentes siguen pasando sin modificarse (salvo imports) |
| F4 | Equivalencia secuencial vs concurrente **con** descuento de stock; ciclo de vida de `GestorPool` |
| F5 | Lectura en streaming, lotes, archivo corrupto, archivo vacío, escritura con buffer |
| F6 | El APM queda desactivado sin variables de entorno; el cliente se crea con variables simuladas |
| F7 | El refactor no cambia el comportamiento (la suite existente pasa, salvo ajustes de firma e imports); tests de las piezas nuevas: `Protocol`, filas de picking, parsers, `AplicacionInventario` |
| F8 | El build de Sphinx es el test |

## Decisiones pendientes del grupo

1. **Versión de Python común:** sugerido 3.13 (Scalene no publica binario de Windows para 3.11, y `elastic-apm` declara soporte hasta 3.13).
2. **Elastic:** stack local con Docker o prueba de Elastic Cloud.
3. **SonarQube:** SonarQube Cloud (sugerido, gratis para repos públicos) o instancia propia con Docker.
4. **Framework:** el enunciado original pide "uso de algún framework". Flet (UI), pytest (testing) y Sphinx (documentación) ya lo cubren. Conviene confirmarlo con la cátedra.
