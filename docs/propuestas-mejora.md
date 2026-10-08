# Propuestas de mejora (Automatización Origin 2)

<!-- Bloque generado por la automatización de hotspots. -->
<!-- No aplicar estos cambios de forma automática: el grupo decide y vuelve a medir. -->

**Commit analizado:** `ceeaca3` · **Generado:** 2026-10-08 21:18 UTC

## Fuentes consultadas

- `docs/mediciones/cprofile_resumen.txt`
- `docs/mediciones/line_profiler_resumen.txt`
- `docs/mediciones/memoria_resumen.txt`
- `docs/mediciones/tabla_comparativa.md`
- `docs/mediciones/tabla_comparativa.txt`
- `docs/mediciones/scalene/scalene_despues.json`
- `docs/mediciones/scalene/scalene_antes.json`

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
| Scalene | `src/pedidos/procesador_concurrente.py:103` | cpu_sys_ipc_pct | 13.07 | py=0.0% c=8.6% sys=13.1% peak=0.0MB \| return [resultado for futuro in futuros for resultado in futuro.result()] |
| Scalene | `src/pedidos/procesador_concurrente.py:88` | cpu_python_pct | 3.5 | py=3.5% c=3.4% sys=1.4% peak=1.0MB \| lineas = tuple((linea.id_producto, linea.cantidad) for linea in pedido.lineas) |
| Scalene | `src/pedidos/evaluador.py:57` | cpu_python_pct | 2.55 | py=2.5% c=0.0% sys=0.2% peak=0.0MB \| def stock_desde_catalogo(id_producto: int) -\u003e int: |
| Scalene | `src/pedidos/agrupador.py:115` | cpu_python_pct | 2.23 | py=2.2% c=0.3% sys=0.0% peak=0.0MB \| acumulador.values(), key=lambda it: it.cantidad_total, reverse=True |
| Scalene | `src/pedidos/evaluador.py:73` | cpu_python_pct | 1.51 | py=1.5% c=0.7% sys=0.0% peak=0.0MB \| def evaluar_lineas( |
| Scalene | `src/pedidos/evaluador.py:96` | cpu_python_pct | 1.25 | py=1.2% c=0.0% sys=0.0% peak=0.0MB \| lineas_con_asignacion += 1 |
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

## Propuestas (no aplicadas)

### 1. Reducir el overhead de IPC del pool de procesos

- **Prioridad:** alta
- **Hotspot:** `_winapi.CreateProcess` / `WaitForSingleObject` / `pickle.dumps` dominan tottime en cProfile; la tabla aislada muestra speedup < 1× incluso en `grande.json`.
- **Evidencia:** docs/mediciones/cprofile_resumen.txt (CreateProcess 0.364 s / 0.167 s) y docs/mediciones/tabla_comparativa.md (fila Preparación, mismo CatalogoHash). Tras aislar CatalogoHash, `grande.json / **Preparación de Pedidos**` sigue en speedup 0.12× (base=65.725 ms · opt=535.725 ms). El 1.95× previo mezclaba búsqueda O(n) con el pool.
- **Alternativa:** 1) Por defecto procesar en secuencial. 2) Activar ProcessPool solo si el trabajo por pedido es pesado (p. ej. DP de combinaciones) o P es claramente mayor a 2.000. El umbral «P < 200» queda corto: con catálogo O(1), 2.000 pedidos (~21 ms) no cubren el IPC. 3) Pool persistente o `shared_memory` si se insiste en paralelizar.
- **Trade-off (tiempo / memoria / claridad):** Menos latencia de arranque a costa de más ramas de código. En la oral conviene mostrar este negativo: no toda concurrencia escala.
- **¿Ya cubierta por el motor actual?** No — queda a decisión del grupo

### 2. No usar el catálogo lineal fuera del desafío experimental

- **Prioridad:** media
- **Hotspot:** `CatalogoLineal.buscar_por_id`: el `for` sobre `self._productos` concentra ~99.7 % del tiempo de la función (line_profiler, 197 850 hits).
- **Evidencia:** docs/mediciones/line_profiler_resumen.txt
- **Alternativa:** En producción/demo dejar `estrategia='optimizado'`. Conservar el lineal solo como baseline medible. Si se necesita un modo mixto, cachear el último `buscar_por_id` con el LRU ya existente.
- **Trade-off (tiempo / memoria / claridad):** El baseline debe seguir existiendo para la rúbrica; no borrarlo. La caché no cambia la cota O(n) de la primera consulta.
- **¿Ya cubierta por el motor actual?** Sí — ya existe baseline vs optimizado

### 3. No pagar concurrencia ni heap en escalas donde no ganan

- **Prioridad:** alta
- **Hotspot:** Speedup < 1× en: demo_oral.json / **Ranking Top-N (k=5)**, demo_oral.json / **Batch Picking Consolidado**, demo_oral.json / **Combinaciones Sustitutas**, demo_oral.json / **Preparación de Pedidos**, pequeno.json / **Ranking Top-N (k=5)**, pequeno.json / **Batch Picking Consolidado**
- **Evidencia:** docs/mediciones/tabla_comparativa.md — demo_oral.json / **Ranking Top-N (k=5)** 0.41× (base=0.032 ms · opt=0.078 ms); demo_oral.json / **Batch Picking Consolidado** 0.29× (base=0.079 ms · opt=0.273 ms); demo_oral.json / **Combinaciones Sustitutas** 0.81× (base=0.278 ms · opt=0.342 ms); demo_oral.json / **Preparación de Pedidos** 0.00× (base=0.121 ms · opt=235.131 ms)
- **Alternativa:** Selector automático: heap solo si N > 50 o k/N < 0.1; pool de procesos solo si el trabajo por pedido no es un lookup O(1). Documentar el umbral real (hoy el pool pierde hasta grande.json) en la oral.
- **Trade-off (tiempo / memoria / claridad):** Más ramas de código frente a una regla simple (optimizado siempre). La claridad de la demo oral puede sufrir si el selector oculta el contraste.
- **¿Ya cubierta por el motor actual?** No — queda a decisión del grupo

### 4. Compactar el índice invertido en catálogos masivos

- **Prioridad:** baja
- **Hotspot:** Catálogo hash en grande.json: pico ~5 MB frente a ~84 KB del lineal.
- **Evidencia:** docs/mediciones/memoria_resumen.txt y columna Memoria Opt de la tabla.
- **Alternativa:** Almacenar posting lists como arrays de ids (`array('I')`) en lugar de `set[int]`; o un trie/prefijo si las búsquedas son por comienzo de palabra. Para 100k SKUs evaluar un índice en disco (SQLite FTS) en vez de RAM.
- **Trade-off (tiempo / memoria / claridad):** Menos memoria y peor latencia de mutación (alta/baja de productos). El trade-off actual (tiempo por memoria) ya está justificado para 10k productos.
- **¿Ya cubierta por el motor actual?** No — queda a decisión del grupo

### 5. Evitar el sort final del lote de picking si la UI no lo requiere

- **Prioridad:** baja
- **Hotspot:** `agrupar_pedidos_batch` aparece en tottime de cProfile (grande: 0.020 s).
- **Evidencia:** docs/mediciones/cprofile_resumen.txt — src/pedidos/agrupador.py:70
- **Alternativa:** La consolidación hash ya es O(L). El `sorted(..., reverse=True)` añade O(U log U) solo para presentación. Diferir el orden a la pantalla o usar `heapq.nlargest` si solo se muestran los U′ más demandados.
- **Trade-off (tiempo / memoria / claridad):** La tabla de agrupación dejaría de venir preordenada. Impacto menor frente a la búsqueda lineal, pero es trabajo evitable.
- **¿Ya cubierta por el motor actual?** No — queda a decisión del grupo

## Qué no hace esta automatización

- No modifica `src/`, `benchmarks/` ni tests.
- No abre un PR de código: solo actualiza este informe.
- No sustituye la tabla obligatoria ni los profilers del grupo.
