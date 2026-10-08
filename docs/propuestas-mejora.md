# Propuestas de mejora (Automatización Origin 2)

<!-- Bloque generado por la automatización de hotspots. -->
<!-- No aplicar estos cambios de forma automática: el grupo decide y vuelve a medir. -->

**Commit analizado:** `a393b1b` · **Generado:** 2026-09-08 02:07 UTC

## Fuentes consultadas

- `docs/mediciones/cprofile_resumen.txt`
- `docs/mediciones/line_profiler_resumen.txt`
- `docs/mediciones/memoria_resumen.txt`
- `docs/mediciones/tabla_comparativa.md`
- `docs/mediciones/tabla_comparativa.txt`

No hay informes de Scalene ni py-spy en `docs/mediciones/` (solo comandos en `comandos_profiling.md`). Los números de esta corrida salen de los profilers ya commiteados; no se inventan milisegundos.

## Estado respecto a `a393b1b`

El push que disparó esta corrida (`fix(build): call freeze_support so the frozen exe does not respawn the GUI`) **no tocó** `docs/mediciones/` ni el motor de inventario. Añade `multiprocessing.freeze_support()` en `main.py` y `src/ui/app.py`, hidden imports de spawn en `scripts/compile.py`, y un test que exige esas llamadas.

En el `.exe` de PyInstaller (Windows, `spawn`) cada worker re-ejecuta el mismo binario. Sin `freeze_support`, Comparativa y Pedidos abrían N ventanas y **nunca devolvían** resultados. Eso es un fallo de arranque del pool, no una medición nueva de tottime.

`freeze_support` **no reduce** CreateProcess / pickle / IPC. La pantalla Comparativa sigue llamando `procesar_pedidos_concurrente` en cada clic (`src/ui/pantallas/comparacion.py`). Los tottime / % Time / speedup siguen siendo los mismos informes.

Cobertura que sigue vigente desde `7c6af3d` (el lint `f53e3df` no la cambió):

- `src/ui/pantallas/pedidos.py`: el switch de ProcessPool arranca en `False` y **no se enciende** al pasar a Optimizado. Optimizado usa hash O(1) en secuencial salvo que el operador active IPC.
- `src/ui/pantallas/inicio.py`: el escenario demo llama `procesar_pedidos(concurrente=False)`.
- `src/pedidos/procesador_concurrente.py`: hay un **pool persistente** (`_executor` de módulo) para no pagar `CreateProcess` en cada clic.
- `src/motor/motor_inventario.py`: si el caller no pasa `concurrente`, el default sigue siendo `es_optimizado and len(lote) >= 50`.

Los perfiles de cProfile (CreateProcess 0.364 s / 0.167 s) son **anteriores** al pool persistente y al freeze del `.exe`. Hay que volver a correr `perfilar_cprofile` / `comparar` (y, si se defiende el binario, una comparativa dentro del `.exe`) antes de dar por cerrado el IPC.

## Hotspots detectados

| Origen | Símbolo | Métrica | Valor | Detalle |
|---|---|---|---:|---|
| cProfile | `{built-in method _winapi.CreateProcess}` | tottime_s | 0.364 | cumtime=0.364s (runtime / IPC) |
| cProfile | `{built-in method _winapi.WaitForSingleObject}` | tottime_s | 0.354 | cumtime=0.354s (runtime / IPC) |
| cProfile | `{built-in method _winapi.CreateProcess}` | tottime_s | 0.167 | cumtime=0.167s (runtime / IPC) |
| cProfile | `{built-in method _winapi.WaitForSingleObject}` | tottime_s | 0.161 | cumtime=0.161s (runtime / IPC) |
| cProfile | `C:/Users/edgar/OneDrive/Escritorio/UBP/PEF/Parcial I/src/inventario/catalogo_hash.py:31(_indexar_nombre)` | tottime_s | 0.041 | cumtime=0.105s |
| cProfile | `{method 'dump' of '_pickle.Pickler' objects}` | tottime_s | 0.035 | cumtime=0.038s (runtime / IPC) |
| cProfile | `C:/Users/edgar/OneDrive/Escritorio/UBP/PEF/Parcial I/src/modelos/producto.py:26(__post_init__)` | tottime_s | 0.028 | cumtime=0.042s |
| cProfile | `C:/Users/edgar/OneDrive/Escritorio/UBP/PEF/Parcial I/src/pedidos/agrupador.py:70(agrupar_pedidos_batch)` | tottime_s | 0.02 | cumtime=0.030s |
| line_profiler | `CatalogoHash.buscar_por_id:74` | pct_tiempo | 100.0 | return self._productos_por_id.get(id_producto) |
| line_profiler | `procesar_pedidos_secuencial:52` | pct_tiempo | 90.8 | producto = catalogo.buscar_por_id(linea.id_producto) |
| line_profiler | `CatalogoLineal.buscar_por_nombre:57` | pct_tiempo | 62.6 | if texto_norm in producto.nombre.lower(): |
| line_profiler | `CatalogoLineal.buscar_por_id:45` | pct_tiempo | 50.4 | if producto.id == id_producto: |
| tabla_comparativa | `demo_oral.json / **Ranking Top-N (k=5)**` | speedup | 0.41 | base=0.032 ms · opt=0.078 ms |
| tabla_comparativa | `demo_oral.json / **Batch Picking Consolidado**` | speedup | 0.29 | base=0.079 ms · opt=0.273 ms |
| tabla_comparativa | `demo_oral.json / **Combinaciones Sustitutas**` | speedup | 0.81 | base=0.278 ms · opt=0.342 ms |
| tabla_comparativa | `demo_oral.json / **Preparación de Pedidos**` | speedup | 0.0 | base=0.121 ms · opt=235.131 ms |
| tabla_comparativa | `pequeno.json / **Ranking Top-N (k=5)**` | speedup | 0.64 | base=0.027 ms · opt=0.042 ms |
| tabla_comparativa | `pequeno.json / **Batch Picking Consolidado**` | speedup | 0.26 | base=0.036 ms · opt=0.136 ms |
| tabla_comparativa | `pequeno.json / **Combinaciones Sustitutas**` | speedup | 0.7 | base=0.301 ms · opt=0.432 ms |
| tabla_comparativa | `pequeno.json / **Preparación de Pedidos**` | speedup | 0.0 | base=0.141 ms · opt=294.527 ms |
| memory_profiler | `demo_oral.json / - Catálogo Lineal (Lista): Actual = 0.77` | pico_kb | 0.77 | - Catálogo Lineal (Lista): Actual = 0.77 KB \| Pico = 0.77 KB |
| memory_profiler | `demo_oral.json / - Catálogo Hash (Diccionarios + Índices)` | pico_kb | 33.03 | - Catálogo Hash (Diccionarios + Índices): Actual = 32.57 KB \| Pico = 33.03 KB |

Filas de la tabla comparativa con speedup < 1× que no entran en el cupo de 8: `mediano.json` Combinaciones 0.78×, `mediano.json` Preparación 0.00× y `grande.json` Preparación 0.12× (base=65.725 ms · opt=535.725 ms).

## Propuestas (no aplicadas)

### 1. Reducir el overhead de IPC del pool de procesos

- **Prioridad:** alta
- **Hotspot:** `_winapi.CreateProcess` / `WaitForSingleObject` / `pickle.dumps` dominan tottime en cProfile; la tabla aislada muestra speedup < 1× incluso en `grande.json`. En el `.exe`, el mismo `spawn` reabre el binario empaquetado: sin `freeze_support` el pool no termina; con él, el costo de IPC sigue ahí.
- **Evidencia:** `docs/mediciones/cprofile_resumen.txt` (CreateProcess 0.364 s / 0.167 s) y `docs/mediciones/tabla_comparativa.md` (fila Preparación, mismo CatalogoHash). Tras aislar CatalogoHash, `grande.json / **Preparación de Pedidos**` sigue en speedup 0.12× (base=65.725 ms · opt=535.725 ms). El 1.95× previo mezclaba búsqueda O(n) con el pool. El cProfile es anterior al pool persistente de `7c6af3d`; `a393b1b` corrige el arranque congelado pero no re-midió. Comparativa (`src/ui/pantallas/comparacion.py`) sigue invocando el pool en cada clic: por eso el freeze era obligatorio.
- **Alternativa:** 1) Por defecto procesar en secuencial (ya es el camino de Pedidos/Inicio). 2) Activar ProcessPool solo si el trabajo por pedido es pesado (p. ej. DP de combinaciones) o P es claramente mayor a 2.000. El umbral del motor (`P >= 50`) queda corto: con catálogo O(1), 2.000 pedidos (~21 ms en el lado secuencial de la tabla) no cubren el IPC medido. 3) Pool persistente (ya en `procesador_concurrente`) o `shared_memory` si se insiste en paralelizar. 4) Dejar `freeze_support` (ya está) y regenerar cProfile/`comparar` — idealmente también dentro del `.exe` — para ver cuánto queda de CreateProcess en el primer spawn frente a reutilización. No hay milisegundos nuevos del binario en `docs/mediciones/`.
- **Trade-off (tiempo / memoria / claridad):** Menos latencia de arranque a costa de más ramas de código. En la oral conviene mostrar este negativo: no toda concurrencia escala, y en Windows+PyInstaller el spawn además exige `freeze_support` para ni siquiera completar. El switch «mide el costo IPC» ya sirve para el contraste didáctico.
- **¿Ya cubierta por el motor actual?** Parcial — la UI ya no fuerza ProcessPool en Optimizado, hay pool persistente y `freeze_support` evita el respawn de GUI; el default del motor (`P ≥ 50`) y la tabla aislada (0.12× en `grande.json`) siguen abiertos. Comparativa sigue pagando el pool a propósito. No es el contraste baseline vs hash.

### 2. No usar el catálogo lineal fuera del desafío experimental

- **Prioridad:** media
- **Hotspot:** `CatalogoLineal.buscar_por_id`: el `for` sobre `self._productos` concentra ~99.7 % del tiempo de la función (line_profiler, 197 850 hits).
- **Evidencia:** `docs/mediciones/line_profiler_resumen.txt`
- **Alternativa:** En producción/demo dejar `estrategia='optimizado'`. Conservar el lineal solo como baseline medible. Si se necesita un modo mixto, cachear el último `buscar_por_id` con el LRU ya existente.
- **Trade-off (tiempo / memoria / claridad):** El baseline debe seguir existiendo para la rúbrica; no borrarlo. La caché no cambia la cota O(n) de la primera consulta.
- **¿Ya cubierta por el motor actual?** Sí — ya existe baseline vs optimizado (`CatalogoLineal` vs `CatalogoHash`)

### 3. No pagar concurrencia ni heap en escalas donde no ganan

- **Prioridad:** alta
- **Hotspot:** Speedup < 1× en: demo_oral.json / **Ranking Top-N (k=5)**, demo_oral.json / **Batch Picking Consolidado**, demo_oral.json / **Combinaciones Sustitutas**, demo_oral.json / **Preparación de Pedidos**, pequeno.json / **Ranking Top-N (k=5)**, pequeno.json / **Batch Picking Consolidado**
- **Evidencia:** `docs/mediciones/tabla_comparativa.md` — demo_oral.json / **Ranking Top-N (k=5)** 0.41× (base=0.032 ms · opt=0.078 ms); demo_oral.json / **Batch Picking Consolidado** 0.29× (base=0.079 ms · opt=0.273 ms); demo_oral.json / **Combinaciones Sustitutas** 0.81× (base=0.278 ms · opt=0.342 ms); demo_oral.json / **Preparación de Pedidos** 0.00× (base=0.121 ms · opt=235.131 ms)
- **Alternativa:** Selector automático: heap solo si N > 50 o k/N < 0.1; pool de procesos solo si el trabajo por pedido no es un lookup O(1). Documentar el umbral real (hoy el pool pierde hasta `grande.json` en la tabla aislada) en la oral. En Pedidos el pool ya es opt-in; falta el mismo criterio para Top-N, para el default del motor y para Comparativa (sigue midiendo IPC siempre). `a393b1b` no cambia esos umbrales: solo hace que el spawn congelado no abra ventanas.
- **Trade-off (tiempo / memoria / claridad):** Más ramas de código frente a una regla simple (optimizado siempre). La claridad de la demo oral puede sufrir si el selector oculta el contraste.
- **¿Ya cubierta por el motor actual?** Parcial — Pedidos/Inicio ya evitan IPC por defecto; heap y batch en `demo_oral`/`pequeno` siguen en speedup < 1×. El contraste baseline vs optimizado de catálogo (búsqueda por ID/nombre) sí gana.

### 4. Compactar el índice invertido en catálogos masivos

- **Prioridad:** baja
- **Hotspot:** Catálogo hash en grande.json: pico ~5 MB frente a ~84 KB del lineal.
- **Evidencia:** `docs/mediciones/memoria_resumen.txt` y columna Memoria Opt de la tabla.
- **Alternativa:** Almacenar posting lists como arrays de ids (`array('I')`) en lugar de `set[int]`; o un trie/prefijo si las búsquedas son por comienzo de palabra. Para 100k SKUs evaluar un índice en disco (SQLite FTS) en vez de RAM.
- **Trade-off (tiempo / memoria / claridad):** Menos memoria y peor latencia de mutación (alta/baja de productos). El trade-off actual (tiempo por memoria) ya está justificado para 10k productos.
- **¿Ya cubierta por el motor actual?** No — queda a decisión del grupo

### 5. Evitar el sort final del lote de picking si la UI no lo requiere

- **Prioridad:** baja
- **Hotspot:** `agrupar_pedidos_batch` aparece en tottime de cProfile (grande: 0.020 s).
- **Evidencia:** `docs/mediciones/cprofile_resumen.txt` — `src/pedidos/agrupador.py:70`
- **Alternativa:** La consolidación hash ya es O(L). El `sorted(..., reverse=True)` añade O(U log U) solo para presentación. Diferir el orden a la pantalla o usar `heapq.nlargest` si solo se muestran los U′ más demandados.
- **Trade-off (tiempo / memoria / claridad):** La tabla de agrupación dejaría de venir preordenada. Impacto menor frente a la búsqueda lineal, pero es trabajo evitable.
- **¿Ya cubierta por el motor actual?** No — queda a decisión del grupo

## Qué no hace esta automatización

- No modifica `src/`, `benchmarks/` ni tests.
- No abre un PR de código: solo actualiza este informe.
- No sustituye la tabla obligatoria ni los profilers del grupo.
