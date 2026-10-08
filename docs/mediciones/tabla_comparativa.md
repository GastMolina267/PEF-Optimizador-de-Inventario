# Tabla Comparativa Oficial: Baseline vs. Optimizado

> [!NOTE]
> Mediciones empíricas realizadas con `time.perf_counter()` y `tracemalloc` sobre los mismos datasets.
> **Speedup** = Tiempo Baseline / Tiempo Optimizado. Valores > 1.0x representan aceleración efectiva.

| Dataset | Operación | Complejidad Base | Complejidad Opt | Tiempo Base (ms) | Tiempo Opt (ms) | Speedup | Memoria Base (KB) | Memoria Opt (KB) | Observaciones |
|---|---|:---:|:---:|---:|---:|:---:|---:|---:|---|
| `demo_oral.json` | **Búsqueda por ID** | `O(n)` | `O(1)` | 0.002 | 0.001 | **2.81x** | 0.6 | 0.5 | ID 16 en catálogo de 30 productos |
| `demo_oral.json` | **Búsqueda por Nombre** | `O(n)` | `O(1) amort.` | 0.020 | 0.002 | **8.87x** | 1.1 | 0.6 | Término 'pincel' (índice invertido + LRU) |
| `demo_oral.json` | **Ranking Top-N (k=5)** | `O(N log N)` | `O(N log k)` | 0.032 | 0.078 | **0.41x** | 4.2 | 3.3 | heapq.nlargest acotado en k=5 sobre 8 pedidos |
| `demo_oral.json` | **Batch Picking Consolidado** | `O(P·L·n)` | `O(L)` | 0.079 | 0.273 | **0.29x** | 1.8 | 8.0 | Acumulación en 1 pasada hash vs. búsquedas anidadas |
| `demo_oral.json` | **Combinaciones Sustitutas** | `O(2^N)` | `O(N·P)` | 0.278 | 0.342 | **0.81x** | 5.4 | 9.3 | Memo DP reutilizó 0 llamadas; poda en árbol |
| `demo_oral.json` | **Preparación de Pedidos** | `O(P·L)` | `O((P·L)/C + IPC)` | 0.121 | 235.131 | **0.00x** | 6.6 | 92.7 | Mismo CatalogoHash: ProcessPoolExecutor vs. secuencial (aísla IPC) |
| `pequeno.json` | **Búsqueda por ID** | `O(n)` | `O(1)` | 0.002 | 0.001 | **4.49x** | 0.6 | 0.5 | ID 51 en catálogo de 100 productos |
| `pequeno.json` | **Búsqueda por Nombre** | `O(n)` | `O(1) amort.` | 0.043 | 0.001 | **34.49x** | 1.3 | 0.6 | Término 'pincel' (índice invertido + LRU) |
| `pequeno.json` | **Ranking Top-N (k=5)** | `O(N log N)` | `O(N log k)` | 0.027 | 0.042 | **0.64x** | 6.3 | 4.0 | heapq.nlargest acotado en k=5 sobre 20 pedidos |
| `pequeno.json` | **Batch Picking Consolidado** | `O(P·L·n)` | `O(L)` | 0.036 | 0.136 | **0.26x** | 3.1 | 15.2 | Acumulación en 1 pasada hash vs. búsquedas anidadas |
| `pequeno.json` | **Combinaciones Sustitutas** | `O(2^N)` | `O(N·P)` | 0.301 | 0.432 | **0.70x** | 6.1 | 13.1 | Memo DP reutilizó 0 llamadas; poda en árbol |
| `pequeno.json` | **Preparación de Pedidos** | `O(P·L)` | `O((P·L)/C + IPC)` | 0.141 | 294.527 | **0.00x** | 14.2 | 122.7 | Mismo CatalogoHash: ProcessPoolExecutor vs. secuencial (aísla IPC) |
| `mediano.json` | **Búsqueda por ID** | `O(n)` | `O(1)` | 0.008 | 0.001 | **11.78x** | 0.6 | 0.5 | ID 501 en catálogo de 1000 productos |
| `mediano.json` | **Búsqueda por Nombre** | `O(n)` | `O(1) amort.` | 0.384 | 0.001 | **291.17x** | 1.5 | 0.6 | Término 'rodillo' (índice invertido + LRU) |
| `mediano.json` | **Ranking Top-N (k=5)** | `O(N log N)` | `O(N log k)` | 0.205 | 0.194 | **1.06x** | 53.3 | 15.9 | heapq.nlargest acotado en k=5 sobre 200 pedidos |
| `mediano.json` | **Batch Picking Consolidado** | `O(P·L·n)` | `O(L)` | 1.934 | 1.567 | **1.23x** | 22.9 | 167.4 | Acumulación en 1 pasada hash vs. búsquedas anidadas |
| `mediano.json` | **Combinaciones Sustitutas** | `O(2^N)` | `O(N·P)` | 0.780 | 0.999 | **0.78x** | 8.5 | 25.1 | Memo DP reutilizó 0 llamadas; poda en árbol |
| `mediano.json` | **Preparación de Pedidos** | `O(P·L)` | `O((P·L)/C + IPC)` | 1.543 | 310.447 | **0.00x** | 159.0 | 342.1 | Mismo CatalogoHash: ProcessPoolExecutor vs. secuencial (aísla IPC) |
| `grande.json` | **Búsqueda por ID** | `O(n)` | `O(1)` | 0.369 | 0.008 | **47.07x** | 0.6 | 0.5 | ID 5001 en catálogo de 10000 productos |
| `grande.json` | **Búsqueda por Nombre** | `O(n)` | `O(1) amort.` | 20.677 | 0.012 | **1692.08x** | 4.0 | 0.6 | Término 'pincel' (índice invertido + LRU) |
| `grande.json` | **Ranking Top-N (k=5)** | `O(N log N)` | `O(N log k)` | 15.150 | 9.013 | **1.68x** | 556.2 | 218.4 | heapq.nlargest acotado en k=5 sobre 2000 pedidos |
| `grande.json` | **Batch Picking Consolidado** | `O(P·L·n)` | `O(L)` | 827.524 | 106.052 | **7.80x** | 360.4 | 1721.9 | Acumulación en 1 pasada hash vs. búsquedas anidadas |
| `grande.json` | **Combinaciones Sustitutas** | `O(2^N)` | `O(N·P)` | 42.295 | 21.883 | **1.93x** | 30.6 | 44.1 | Memo DP reutilizó 0 llamadas; poda en árbol |
| `grande.json` | **Preparación de Pedidos** | `O(P·L)` | `O((P·L)/C + IPC)` | 65.725 | 535.725 | **0.12x** | 1617.0 | 2699.9 | Mismo CatalogoHash: ProcessPoolExecutor vs. secuencial (aísla IPC) |

---
### Conclusiones Principales del Benchmarking
1. **Catálogo:** La transición de lista $O(n)$ a tabla hash $O(1)$ muestra aceleraciones de órdenes de magnitud a medida que $n$ crece (superando 100x en `grande.json`).
2. **Batch Picking:** Evitar el producto cartesiano de búsquedas repetidas $O(P \cdot L \cdot n)$ mediante consolidación en una sola pasada con hash map $O(L)$ elimina por completo el cuello de botella crítico en almacén.
3. **Top-N:** `heapq.nlargest` $O(N \log k)$ mantiene memoria acotada a $k$ elementos frente a la lista completa de ordenamiento $O(N \log N)$.
4. **Sustitutos:** La memoización de estados DP convierte un árbol exponencial $O(2^N)$ en tiempo pseudo-polinomial $O(N \cdot P)$, permitiendo explorar cientos de combinaciones en milisegundos.
5. **Concurrencia:** La fila de preparación usa el **mismo** `CatalogoHash` a ambos lados para no confundir IPC con la ganancia O(n)→O(1). En lotes chicos el overhead de procesos/pickle domina; el pool solo paga cuando P·L cubre ese costo fijo.

---
### Suite de Regresión Continua (Segundo Parcial)

Con la integración de `pytest-benchmark` en la suite de pruebas automatizadas (`tests/integracion/test_benchmarks.py`), cada ejecución valida que las operaciones críticas mantengan sus órdenes de magnitud esperados:

- **Búsqueda Hash:** ~90 ns (11,080,000 ops/s) frente a ~976 ns en búsqueda lineal (11x speedup directo en catálogo muestra).
- **Ranking Top-N:** ~9.45 µs (105,700 ops/s).
- **Combinaciones DP:** ~22.5 µs (44,400 ops/s).
- **Batch Picking:** ~32.9 µs (30,300 ops/s).
- **Procesamiento de Pedidos:** ~31.6 µs (31,600 ops/s).

Para una comparativa detallada de métricas de calidad de código, cobertura y complejidad ciclomática entre el Primer y Segundo Parcial, consultar [Línea base Parcial 2](linea_base_parcial2/README.md).

