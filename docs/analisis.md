# Análisis de Complejidad, Perfilado y Optimización

Este documento constituye el informe técnico fundamental del **Parcial I de Programación Eficiente (Opción 6: Optimizador de Inventario y Pedidos)**. Contiene la derivación formal de cotas asintóticas de complejidad temporal y espacial, la justificación de las estructuras de datos seleccionadas, la discusión teórica de memoización, caching y concurrencia, y el análisis exhaustivo de las mediciones empíricas recopiladas.

---

## 1. Contexto del Problema y Diagnóstico Inicial

En centros de distribución y logística masiva de *e-commerce*, los catálogos crecen de miles a cientos de miles de artículos (`SKUs`), mientras los lotes de pedidos entrantes demandan procesamiento continuo.

El diseño ingenuo (*baseline*) adolece de tres fallas arquitectónicas severas:
1. **Catálogo basado en listas:** Cualquier consulta de existencia o precio requiere un escaneo secuencial exhaustivo de la lista de productos ($O(n)$).
2. **Batch Picking anidado:** Agrupar los artículos solicitados por múltiples pedidos para los operarios de almacén genera un producto cartesiano cuadrático ($O(P \cdot L \cdot n)$), donde cada línea de cada pedido vuelve a recorrer la lista completa.
3. **Exploración combinatoria sin poda:** Para pedidos con faltante de stock, la búsqueda de combinaciones sustitutas dentro del presupuesto explora un árbol binario completo de decisión, incurriendo en tiempo exponencial ($O(2^N)$).

---

## 2. Derivación Formal de Complejidad Temporal y Espacial

A continuación se detalla la deducción matemática de las cotas asintóticas en notación Big-O para el mejor, promedio y peor caso de cada componente del sistema.

### 2.1 Búsqueda en Catálogo de Productos

Sea $n$ la cantidad total de productos en catálogo y $m$ la longitud promedio del nombre del producto.

| Operación | Versión | Mejor Caso | Caso Promedio | Peor Caso | Complejidad Espacial |
|---|---|:---:|:---:|:---:|:---:|
| **Búsqueda por ID** | Baseline (`CatalogoLineal`) | $\Omega(1)$ (primer elemento) | $\Theta(n)$ | $O(n)$ (ausente o al final) | $O(1)$ aux. |
| **Búsqueda por ID** | Optimizado (`CatalogoHash`) | $\Omega(1)$ | $\Theta(1)$ | $O(n)$ (colisión patológica) | $O(n)$ aux. |
| **Búsqueda por Nombre** | Baseline (`CatalogoLineal`) | $\Omega(n \cdot m)$ | $\Theta(n \cdot m)$ | $O(n \cdot m)$ | $O(k)$ aux. |
| **Búsqueda por Nombre** | Optimizado (`CatalogoHash`) | $\Omega(1)$ (en caché) | $\Theta(k)$ | $O(n)$ | $O(n \cdot m)$ aux. |

#### Derivación matemática:
- **Catálogo Lineal:**  
  La búsqueda secuencial evalúa la condición `producto.id == id_producto` recorriendo un array contiguo de punteros. El número de comparaciones promedio para un elemento presente es:
  $$\mathbb{E}[C] = \frac{1}{n} \sum_{i=1}^{n} i = \frac{n + 1}{2} \in \Theta(n)$$
  Si el elemento no existe, se efectúan exactamente $n$ comparaciones ($O(n)$).

- **Catálogo Hash:**  
  Utiliza la tabla hash nativa de CPython implementada mediante sondeo perturbado (*perturbed open addressing*) con factor de carga acotado ($\alpha \le \frac{2}{3}$). El costo esperado de sondeo exitoso es:
  $$\mathbb{E}[\text{sondeo}] \approx 1 + \frac{\alpha}{2(1 - \alpha)} = 1 + \frac{2/3}{2/3} = 2 \in O(1)$$
  Para la búsqueda por texto, el índice invertido descompone el catálogo en un vocabulario de palabras normalizadas; la consulta recupera el conjunto precomputado de IDs en tiempo $O(1)$ promedio, requiriendo únicamente $O(k)$ para instanciar la lista de resultados (donde $k$ es el número de coincidencias, $k \ll n$).

---

### 2.2 Ranking de Productos Más Solicitados (Top-N)

Sea $N$ la cantidad de productos con demanda acumulada positiva ($N \le n$) y $k$ la cantidad de artículos a exhibir en el ranking ($k \ll N$).

| Versión | Algoritmo | Tiempo Mejor Caso | Tiempo Promedio | Tiempo Peor Caso | Espacio Auxiliar |
|---|---|:---:|:---:|:---:|:---:|
| **Baseline** | Timsort global (`sorted()`) | $\Omega(N)$ | $\Theta(N \log N)$ | $O(N \log N)$ | $O(N)$ |
| **Optimizado** | Min-Heap (`heapq.nlargest`) | $\Omega(N)$ | $\Theta(N \log k)$ | $O(N \log k)$ | $O(k)$ |

#### Derivación matemática:
- **Baseline (Timsort):**  
  Construye una lista completa de $N$ pares `(producto, demanda)` y aplica Timsort. La relación de recurrencia de división y fusión genera:
  $$T(N) = 2\,T(N/2) + \Theta(N) \implies T(N) \in \Theta(N \log N)$$
  Requiere además $O(N)$ espacio auxiliar para retener la lista intermedia antes de extraer los $k$ primeros elementos.

- **Optimizado (Min-Heap de tamaño fijo $k$):**  
  1. Se construye un min-heap inicial con los primeros $k$ elementos en tiempo $O(k)$.
  2. Para los restantes $(N - k)$ elementos, cada elemento se compara con la raíz del heap (el mínimo de los top-k actuales).
  3. Si es mayor, se reemplaza la raíz mediante `heapreplace`, lo que toma a lo sumo $\lfloor \log_2 k \rfloor$ comparaciones de rebalanceo (sift-down).
  
  Costo temporal total:
  $$T(N, k) = O(k) + (N - k) \cdot O(\log k) = O(N \log k)$$
  
  Cuando $k$ es pequeño y constante (por ejemplo $k = 5$ o $k = 10$), $\log k$ es una constante insignificante ($\log_2 5 \approx 2.32$), por lo que:
  $$T(N, k) \in O(N)$$
  El ahorro espacial es crítico: solo se retienen $k$ referencias en memoria heap en lugar de los $N$ registros completos.

---

### 2.3 Agrupación de Pedidos para Batch Picking Consolidado

Sea $P$ el número total de pedidos en el lote y $L$ el número promedio de líneas por pedido. El número total de líneas a consolidar es $|L_{\text{total}}| = P \cdot L$.

| Versión | Algoritmo | Complejidad Temporal | Complejidad Espacial |
|---|---|:---:|:---:|
| **Baseline** | Recorrido anidado con búsqueda lineal | $O(P \cdot L \cdot n)$ | $O(U)$ |
| **Optimizado** | Consolidación en 1 pasada con acumulador Hash | $O(P \cdot L) = O(|L_{\text{total}}|)$ | $O(U)$ |

#### Derivación matemática:
- **Baseline:** Por cada uno de los $P$ pedidos y por cada una de sus $L$ líneas, se invoca `catalogo_lineal.buscar_por_id()`, que efectúa en promedio $n/2$ operaciones:
  $$T_{\text{base}} = \sum_{p=1}^{P} \sum_{l=1}^{L} \Theta(n) = \Theta(P \cdot L \cdot n)$$
  Para un escenario mediano ($P = 200, L = 5, n = 1.000$), se realizan del orden de $1.000.000$ de operaciones.

- **Optimizado:**  
  En una única pasada lineal sobre las líneas de pedidos, se agrega la demanda acumulada en un diccionario hash indexado por `id_producto` ($O(1)$ por inserción/acumulación). Finalizada la pasada, se resuelve el producto desde `CatalogoHash` en $O(1)$ por producto único $U$ ($U \le n$):
  $$T_{\text{opt}} = O(P \cdot L) + O(U) \in O(P \cdot L)$$
  La complejidad se desacopla completamente del tamaño del catálogo $n$.

---

### 2.4 Búsqueda de Alternativas y Combinaciones Sustitutas

Sea $N$ el número de productos candidatos en la misma categoría del artículo agotado y $P$ el presupuesto máximo disponible expresado en centavos enteros ($P \in \mathbb{N}$).

| Versión | Algoritmo | Complejidad Temporal | Complejidad Espacial |
|---|---|:---:|:---:|
| **Baseline** | Árbol recursivo exhaustivo | $O(2^N)$ | $O(N)$ (pila de llamadas) |
| **Optimizado** | Programación Dinámica con Memoización | $O(N \cdot P)$ | $O(N \cdot P)$ (tabla de memoización) |

#### Derivación matemática:
- **Baseline (Fuerza bruta recursiva):**  
  Cada producto candidato $i \in \{1, \dots, N\}$ presenta una decisión binaria: incluirlo o excluirlo de la combinación. El árbol de recurrencia tiene profundidad $N$ y un total de nodos dado por:
  $$\sum_{i=0}^{N} \binom{N}{i} = 2^N$$
  Para $N = 30$, $2^{30} \approx 1.07 \times 10^9$ llamadas, lo cual es inabordable en tiempo real.

- **Optimizado (Programación Dinámica Top-Down con Memoización):**  
  El subproblema queda unívocamente definido por la tupla de estado:
  $$\text{Estado} = (i, p)$$
  donde $i \in [0, N]$ es el índice del candidato bajo evaluación y $p \in [0, P]$ es el presupuesto restante.
  
  El espacio de estados discretos es a lo sumo:
  $$|\mathcal{S}| = (N + 1) \times (P + 1) \in O(N \cdot P)$$
  Al memoizar los resultados de cada estado en una tabla hash, ningún estado $(i, p)$ se evalúa más de una vez. La transición de cada estado realiza trabajo $O(1)$ (combinar las listas de combinaciones retornadas acotadas a un límite superior $M$).
  Por tanto:
  $$T(N, P) \in O(N \cdot P)$$
  Esto transforma un problema de complejidad exponencial en uno de tiempo **pseudo-polinomial**.

---

### 2.5 Preparación y Validación de Pedidos

| Versión | Modelo de Ejecución | Complejidad Temporal | Complejidad Espacial |
|---|---|:---:|:---:|
| **Secuencial** | Mono-hilo en hilo principal | $O(P \cdot L)$ | $O(P \cdot L)$ |
| **Concurrente** | Multi-proceso (`ProcessPoolExecutor`) | $O\left(\frac{P \cdot L}{C}\right) + O(C_{\text{IPC}})$ | $O(P \cdot L + C \cdot \text{chunk})$ |

donde $C$ es la cantidad de núcleos CPU disponibles y $C_{\text{IPC}}$ es el costo de serialización/deserialización (Pickling) entre procesos.

---

## 3. Justificación de Algoritmos y Estructuras de Datos

### 3.1 Tabla Hash con Índices Invertidos (`CatalogoHash`)
- **Por qué no listas:** Una lista requiere un recorrido de punteros secuencial en memoria heap; a medida que el catálogo crece de $1.000$ a $10.000$ artículos, la latencia de búsqueda pasa de milisegundos a décimas de segundo, multiplicada por cada línea de pedido.
- **Por qué índices invertidos:** Para las búsquedas parciales de texto, buscar subcadenas con `in` sobre la lista completa cuesta $O(n \cdot m)$. El índice invertido indexa palabras normalizadas (minúsculas, sin acentos), mapeando cada término directamente a un `set[int]` de IDs en $O(1)$.

### 3.2 Min-Heap para Top-N (`heapq.nlargest`)
- **Por qué no `sorted()`:** Ordenar todo el catálogo para mostrar únicamente los 5 productos más demandados realiza trabajo innecesario sobre el 99.9% de los productos restantes. Timsort reordena la lista completa en $O(N \log N)$; `heapq.nlargest` filtra dinámicamente conservando un heap invertido de $k$ elementos con costo $O(N \log k)$ y huella de memoria minúscula.

### 3.3 Programación Dinámica para Combinaciones Sustitutas
- **Por qué no recursión pura:** Los árboles de decisión combinatoria reevalúan los mismos estados de saldo restante decenas de miles de veces en diferentes ramas. La memoización almacena la tupla `(indice, presupuesto_restante)` cortando inmediatamente la exploración de ramas redundantes.

---

## 4. Memoización vs. Caching

Una de las distinciones fundamentales evaluadas en la materia radica en no confundir la **memoización algorítmica** con el **caching de consultas**:

| Dimensión | Memoización (Programación Dinámica) | Caching de Consultas (GestorCacheConsultas) |
|---|---|---|
| **Ámbito** | Interno al algoritmo de optimización (`BuscadorAlternativas`). | Periférico a las llamadas del usuario y la UI (`MotorInventario`). |
| **Determinismo** | Estrictamente determinista: para una entrada $(i, p)$, la salida es matemática e invariante. | Dependiente del estado del inventario; puede quedar obsoleto si el stock muta. |
| **Ciclo de vida** | Efímero (se crea para una ejecución o se preserva mientras el catálogo no cambie). | Persistente entre múltiples pantallas y acciones del usuario. |
| **Política de desalojo** | Sin desalojo durante la corrida del subproblema (almacena el grafo de estados completo). | Política estricta **LRU (Least Recently Used)** con capacidad máxima fija $O(C)$. |
| **Protocolo de invalidación** | No requiere invalidación durante la llamada recursiva. | **Invalidación reactiva:** ante una mutación de stock o nuevo lote de pedidos, se purgan selectivamente las claves afectadas. |

### Demostración del Protocolo de Invalidación Reactiva
Cuando un pedido se procesa con descuento de inventario:
1. Se muta el atributo `stock` del producto.
2. `MotorInventario` invoca automáticamente:
   - `_cache.invalidar_por_mutacion_stock()`: limpia las búsquedas de texto y filtros por categoría, asegurando que ninguna pantalla devuelva productos con existencias obsoletas.
   - `_cache.invalidar_por_nuevos_pedidos()`: purga el Top-N previamente calculado.

---

## 5. Concurrencia y Paralelismo: El GIL y el Overhead de IPC

### El Global Interpreter Lock (GIL) de CPython
En Python, el GIL es un mecanismo de sincronización que restringe la ejecución de bytecode a un único hilo nativo por proceso. En tareas intensivas de cómputo (CPU-bound) como la validación masiva de cientos de pedidos con múltiples líneas de inventario:
- `threading` o `ThreadPoolExecutor` **no logran aceleración real**: los hilos compiten por el GIL, alternando ejecución y generando sobrecosto por cambios de contexto (*context switching*).
- La solución requerida es **multi-procesamiento** (`ProcessPoolExecutor`), que genera procesos independientes del sistema operativo, cada uno con su propio intérprete de Python, su propio espacio de memoria y su propio GIL.

### Análisis del Punto de Inflexión (*Break-Even Point*) y Overhead de IPC
El multi-procesamiento introduce un costo fijo no despreciable:
1. **Creación de procesos:** `_winapi.CreateProcess` en Windows.
2. **Serialización IPC (Pickling):** La serialización binaria de lotes de pedidos y su envío por tuberías o colas inter-proceso.
3. **Sincronización:** `_winapi.WaitForSingleObject`.

#### Evidencia empírica obtenida en benchmarking:
La corrida original contrastaba `CatalogoLineal` secuencial contra `CatalogoHash` + `ProcessPoolExecutor`, de modo que el speedup de `grande.json` (**1.95x**) mezclaba búsqueda $O(n)$ con paralelismo. Re-medición con el **mismo** `CatalogoHash` en ambos lados (aísla IPC):

- **`demo_oral.json` (8 pedidos):**  
  - Secuencial (hash): **0.093 ms**
  - Concurrente: **7.608 ms** (Speedup **0.01x**)
  - *Diagnóstico:* El costo de crear procesos y serializar el snapshot supera el cómputo de 8 pedidos.
- **`grande.json` (2.000 pedidos, 10.000 productos):**  
  - Secuencial (hash): **21.275 ms**
  - Concurrente: **73.583 ms** (Speedup **0.29x**)
  - *Diagnóstico:* Con catálogo $O(1)$, preparar 2.000 pedidos es tan barato (~21 ms) que el pool **no paga**. El 1.95x previo se debía sobre todo a dejar de recorrer la lista, no a los núcleos extra. El pool solo se justifica con más trabajo por pedido (p. ej. combinaciones DP) o lotes claramente mayores.

---

## 6. Evidencia Empírica: Tabla Comparativa Oficial

Las siguientes mediciones fueron registradas automáticamente mediante `time.perf_counter()` y `tracemalloc` ejecutando `python -m benchmarks.comparar` sobre los datasets oficiales:

| Dataset | Operación | Complejidad Base | Complejidad Opt | Tiempo Base (ms) | Tiempo Opt (ms) | Speedup | Memoria Base (KB) | Memoria Opt (KB) | Observaciones |
|---|---|:---:|:---:|---:|---:|:---:|---:|---:|---|
| `demo_oral.json` | **Búsqueda por ID** | `O(n)` | `O(1)` | 0.003 | 0.002 | **1.99x** | 0.6 | 0.6 | ID 16 en catálogo de 30 productos |
| `demo_oral.json` | **Búsqueda por Nombre** | `O(n)` | `O(1) amort.` | 0.030 | 0.003 | **8.60x** | 1.2 | 0.6 | Término 'pincel' (índice invertido + LRU) |
| `demo_oral.json` | **Ranking Top-N (k=5)** | `O(N log N)` | `O(N log k)` | 0.044 | 0.066 | **0.67x** | 4.7 | 3.6 | heapq.nlargest acotado en k=5 sobre 8 pedidos |
| `demo_oral.json` | **Batch Picking Consolidado** | `O(P·L·n)` | `O(L)` | 0.029 | 0.151 | **0.19x** | 1.9 | 8.2 | Acumulación en 1 pasada hash vs. búsquedas anidadas |
| `demo_oral.json` | **Combinaciones Sustitutas** | `O(2^N)` | `O(N·P)` | 0.291 | 0.393 | **0.74x** | 5.9 | 9.4 | Poda en árbol combinatorio |
| `demo_oral.json` | **Preparación de Pedidos** | `O(P·L)` | `O((P·L)/C + IPC)` | 0.093 | 7.608 | **0.01x** | 6.6 | 61.4 | Mismo CatalogoHash: aísla IPC |
| `pequeno.json` | **Búsqueda por ID** | `O(n)` | `O(1)` | 0.004 | 0.002 | **2.27x** | 0.6 | 0.6 | ID 51 en catálogo de 100 productos |
| `pequeno.json` | **Búsqueda por Nombre** | `O(n)` | `O(1) amort.` | 0.261 | 0.009 | **29.16x** | 1.4 | 0.6 | Índice invertido + LRU |
| `pequeno.json` | **Ranking Top-N (k=5)** | `O(N log N)` | `O(N log k)` | 0.104 | 0.171 | **0.61x** | 7.0 | 4.4 | 20 pedidos |
| `pequeno.json` | **Batch Picking Consolidado** | `O(P·L·n)` | `O(L)` | 0.081 | 1.081 | **0.07x** | 3.2 | 15.4 | Hash map consolidado |
| `pequeno.json` | **Combinaciones Sustitutas** | `O(2^N)` | `O(N·P)` | 0.911 | 1.348 | **0.68x** | 6.8 | 13.4 | DP memoizada |
| `pequeno.json` | **Preparación de Pedidos** | `O(P·L)` | `O((P·L)/C + IPC)` | 0.220 | 6.592 | **0.03x** | 14.2 | 72.0 | Mismo CatalogoHash: aísla IPC |
| `mediano.json` | **Búsqueda por ID** | `O(n)` | `O(1)` | 0.016 | 0.001 | **12.28x** | 0.6 | 0.6 | ID 501 en catálogo de 1000 productos |
| `mediano.json` | **Búsqueda por Nombre** | `O(n)` | `O(1) amort.` | 0.857 | 0.003 | **261.97x** | 1.6 | 0.6 | 261x más rápido con caché |
| `mediano.json` | **Ranking Top-N (k=5)** | `O(N log N)` | `O(N log k)` | 0.421 | 0.364 | **1.16x** | 58.5 | 16.4 | Ahorro sustancial de memoria |
| `mediano.json` | **Batch Picking Consolidado** | `O(P·L·n)` | `O(L)` | 4.201 | 3.227 | **1.30x** | 23.0 | 167.6 | Inicio de ventaja de consolidación |
| `mediano.json` | **Combinaciones Sustitutas** | `O(2^N)` | `O(N·P)` | 1.603 | 2.516 | **0.64x** | 9.5 | 25.2 | Poda en árbol combinatorio |
| `mediano.json` | **Preparación de Pedidos** | `O(P·L)` | `O((P·L)/C + IPC)` | 2.011 | 12.349 | **0.16x** | 159.0 | 324.7 | Mismo CatalogoHash: aísla IPC |
| `grande.json` | **Búsqueda por ID** | `O(n)` | `O(1)` | 0.383 | 0.005 | **75.26x** | 0.6 | 0.6 | ID 5001 en 10.000 productos |
| `grande.json` | **Búsqueda por Nombre** | `O(n)` | `O(1) amort.` | 26.430 | 0.010 | **2627.23x** | 4.0 | 0.6 | **2627x de aceleración** con hash invertido |
| `grande.json` | **Ranking Top-N (k=5)** | `O(N log N)` | `O(N log k)` | 19.003 | 10.821 | **1.76x** | 604.7 | 218.9 | **63% de ahorro de memoria** en heap |
| `grande.json` | **Batch Picking Consolidado** | `O(P·L·n)` | `O(L)` | 1241.727 | 117.607 | **10.56x** | 360.5 | 1722.0 | **10.5x más rápido** evitando recorridos |
| `grande.json` | **Combinaciones Sustitutas** | `O(2^N)` | `O(N·P)` | 36.246 | 35.551 | **1.02x** | 31.7 | 44.2 | Evita explosión combinatorial |
| `grande.json` | **Preparación de Pedidos** | `O(P·L)` | `O((P·L)/C + IPC)` | 21.275 | 73.583 | **0.29x** | 1617.0 | 3181.7 | Mismo CatalogoHash: el pool no paga a esta escala |

---

## 7. Diagnóstico de Hotspots con Evidencia de Profiling

### 7.1 Evidencia de `cProfile`
El informe en `docs/mediciones/cprofile_resumen.txt` demuestra que en la ejecución optimizada:
- El cuello de botella en tiempo propio (`tottime`) en datasets grandes se desplaza a las llamadas de sistema de Windows para crear y coordinar procesos:
  - `{built-in method _winapi.CreateProcess}` (0.364 s acumulado).
  - `{built-in method _winapi.WaitForSingleObject}` (0.354 s acumulado).
- Esto valida teóricamente la hipótesis de que las operaciones de dominio de Python ($O(1)$) se volvieron tan rápidas que la mayor latencia restante proviene del sistema operativo.

### 7.2 Evidencia de `line_profiler`
El informe en `docs/mediciones/line_profiler_resumen.txt` expone el comportamiento instrucción a instrucción:
- En `CatalogoLineal.buscar_por_id`:
  - Se registraron **197.850 iteraciones (Hits)** en el bucle `for producto in self._productos:`, consumiendo el **99.7% del tiempo total** de la función.
- En `CatalogoHash.buscar_por_id`:
  - La línea `return self._productos_por_id.get(id_producto)` insume únicamente **5.0 microsegundos por ejecución (Per Hit)** de manera constante.

### 7.3 Evidencia de `memory_profiler` y `tracemalloc`
El informe en `docs/mediciones/memoria_resumen.txt` certifica los trade-offs espaciales:
- En `grande.json`:
  - `CatalogoLineal`: 83.59 KB.
  - `CatalogoHash`: 5.339,00 KB (~5.2 MB) debido a la redundancia calculada para los índices de categoría y de palabras.
  - **Min-Heap vs Sort:** `sorted` requirió un pico de **603.25 KB**, mientras que `heapq.nlargest` requirió únicamente **216.20 KB**, logrando un **ahorro de 387.05 KB** en memoria activa.
  - **Caché LRU:** Permanece acotada en **~10.27 KB** y se reduce a **1.13 KB** tras la invalidación reactiva.

---

## 8. Guía de Respuestas para la Defensa Oral (10-15 min)

1. **¿Dónde estaba el cuello de botella original?**  
   En la búsqueda lineal en catálogo repetida en cada pedido y en la consolidación de batch picking, que generaban una complejidad algorítmica cuadrática $O(P \cdot L \cdot n)$, colapsando el sistema ante $10.000$ productos.
2. **¿Qué optimización generó el mayor impacto marginal?**  
   El reemplazo de la lista de productos por la tabla hash con índice invertido y caché LRU, logrando un **speedup de hasta 2.627x** en búsquedas textuales.
3. **¿La solución escala si el catálogo crece 10x (100.000 productos)?**  
   Sí: la búsqueda hash permanece en $O(1)$, el batch picking en $O(L)$, y el Top-N en $O(N \log k)$. La única limitación es el consumo de memoria del índice invertido, que escalaría de 5 MB a ~50 MB, perfectamente manejable en RAM moderna.
4. **¿Qué trade-offs se asumieron y qué se haría diferente?**  
   Se asumió un trade-off clásico de **tiempo por memoria**: se invirtieron ~5 MB adicionales en índices hash para eliminar los bucles $O(n)$. Para futuras iteraciones, en datasets masivos se reemplazaría la serialización de procesos de `ProcessPoolExecutor` por memoria compartida (`multiprocessing.shared_memory`) para erradicar el overhead de IPC.

## 9. Refresco automático de complejidad (Origin)

Esta sección la regenera la **Automatización 1** en cada push. El análisis formal del grupo está en las secciones 2 a 5; este bloque solo refleja el recorrido AST del commit actual.

<!-- ORIGIN-AUTO-COMPLEJIDAD:INICIO -->

<!-- Bloque generado por la automatización Origin 1 (análisis de complejidad). -->
<!-- No editar a mano: se regenera con `python -m automations.ejecutar --complejidad`. -->
<!-- El comentario del grupo (secciones 1-8) permanece intacto por encima de este bloque. -->

**Commit analizado:** `a393b1b` · **Generado:** 2026-09-08 02:06 UTC

Criterio: se recorrió el AST de cada función fundamental. Las cotas salen de
bucles, accesos hash, recursión, `heapq`, memoización y `ProcessPoolExecutor`
observados en el cuerpo. No se analizan UI Flet, tests ni wrappers.

| Operación | Función | Mejor | Promedio | Peor | Espacio | Evidencia AST |
|---|---|:---:|:---:|:---:|:---:|---|
| Búsqueda por identificador (baseline) | `CatalogoLineal.buscar_por_id` (L39–47) | Ω(1) | Θ(n) | O(n) | O(1) aux. | bucles×1 |
| Búsqueda por nombre (baseline) | `CatalogoLineal.buscar_por_nombre` (L49–59) | Ω(n · m) | Θ(n · m) | O(n · m) | O(k) aux. | bucles×1 |
| Alta de producto (baseline) | `CatalogoLineal.agregar` (L27–37) | Ω(n) | Θ(n) | O(n) | O(1) aux. | bucles×1 |
| Búsqueda por identificador (optimizado) | `CatalogoHash.buscar_por_id` (L69–74) | Ω(1) | Θ(1) | O(n) (colisión patológica) | O(1) aux. | hash |
| Búsqueda por nombre (optimizado) | `CatalogoHash.buscar_por_nombre` (L76–114) | Ω(1) | Θ(k) | O(n) (fallback lineal) | O(k) aux. | bucles×1, hash |
| Alta de producto (optimizado) | `CatalogoHash.agregar` (L48–67) | Ω(1) | Θ(1) | O(n) (colisión patológica) | O(1) aux. | hash |
| Agrupación / batch picking | `agrupar_pedidos_batch` (L70–117) | Ω(L) | Θ(L + U) | O(L + U log U) | O(U) | bucles×2, hash, sorted, buscar_por_id |
| Top-N más solicitados (baseline) | `calcular_top_solicitados_lineal` (L15–55) | Ω(L + N) | Θ(L + N log N) | O(L + N log N) | O(N) | bucles×2, hash, sorted, buscar_por_id |
| Top-N más solicitados (optimizado) | `calcular_top_solicitados_heap` (L58–99) | Ω(L + N) | Θ(L + N log k) | O(L + N log k) | O(N + k) | bucles×2, hash, heapq, buscar_por_id |
| Combinaciones sustitutas (baseline) | `BuscadorAlternativas._resolver_recursivo_puro` (L170–209) | Ω(N) | Θ(2^N) | O(2^N) | O(N) (pila de llamadas) | bucles×1, recursión |
| Combinaciones sustitutas (optimizado) | `BuscadorAlternativas._resolver_dp_memo` (L211–256) | Ω(1) (hit de memo) | Θ(N · P) | O(N · P) | O(N · P) (tabla de estados) | bucles×1, hash, recursión, memo |
| Preparación de pedidos (secuencial) | `procesar_pedidos_secuencial` (L19–121) | Ω(P · L) | Θ(P · L · T_búsqueda) | O(P · L · T_búsqueda) | O(P · L) | bucles×2, buscar_por_id |
| Preparación de pedidos (concurrente) | `procesar_pedidos_concurrente` (L118–216) | O(P · L) | O((P · L)/C + C_IPC) | O(P · L + C_IPC) | O(P · L + C · chunk) | bucles×2, hash, sorted, ProcessPool |
| Consulta de caché LRU | `CacheLRU.obtener` (L61–68) | Ω(1) | Θ(1) | O(n) (colisión patológica) | O(1) aux. | hash |
| Escritura de caché LRU | `CacheLRU.guardar` (L70–78) | Ω(1) | Θ(1) | O(n) (colisión patológica) | O(1) aux. | hash |
| Invalidación reactiva por stock | `GestorCacheConsultas.invalidar_por_mutacion_stock` (L136–142) | Ω(1) | Θ(1) | O(1) | O(1) | cuerpo trivial |

### Derivación por función (automática)

#### `CatalogoLineal.buscar_por_id`

- **Archivo:** `src/inventario/catalogo_lineal.py` líneas 39–47
- **Técnica:** Recorrido lineal sobre lista
- **Cotas:** mejor Ω(1) · promedio Θ(n) · peor O(n)
- **Justificación (del cuerpo, no inventada):** El AST muestra un `for` sobre `self._productos` (profundidad 1) y no hay tabla hash de ids. Cada consulta compara contra hasta n productos. Comentario del grupo (docstring): O(n) en el peor y caso promedio. O(1) si está al inicio.

#### `CatalogoLineal.buscar_por_nombre`

- **Archivo:** `src/inventario/catalogo_lineal.py` líneas 49–59
- **Técnica:** Recorrido lineal + subcadena
- **Cotas:** mejor Ω(n · m) · promedio Θ(n · m) · peor O(n · m)
- **Justificación (del cuerpo, no inventada):** El AST muestra un `for` sobre `self._productos` (profundidad 1) y no hay tabla hash de ids. Cada consulta compara contra hasta n productos; la prueba de subcadena añade un factor m (longitud media del nombre). Comentario del grupo (docstring): O(n * L), donde n es la cantidad de productos y L la longitud media del texto.

#### `CatalogoLineal.agregar`

- **Archivo:** `src/inventario/catalogo_lineal.py` líneas 27–37
- **Técnica:** Verificación de unicidad en lista
- **Cotas:** mejor Ω(n) · promedio Θ(n) · peor O(n)
- **Justificación (del cuerpo, no inventada):** El AST muestra un `for` sobre `self._productos` (profundidad 1) y no hay tabla hash de ids. Cada consulta compara contra hasta n productos. Comentario del grupo (docstring): O(n) debido a la verificación de unicidad en la lista.

#### `CatalogoHash.buscar_por_id`

- **Archivo:** `src/inventario/catalogo_hash.py` líneas 69–74
- **Técnica:** Tabla hash por id
- **Cotas:** mejor Ω(1) · promedio Θ(1) · peor O(n) (colisión patológica)
- **Justificación (del cuerpo, no inventada):** No hay bucles sobre el catálogo. El cuerpo resuelve la consulta con acceso hash (self._productos_por_id.get). Con factor de carga acotado el costo esperado es constante; el peor caso teórico de una tabla hash degenerada es O(n). Comentario del grupo (docstring): O(1) promedio y en el mejor caso.

#### `CatalogoHash.buscar_por_nombre`

- **Archivo:** `src/inventario/catalogo_hash.py` líneas 76–114
- **Técnica:** Índice invertido + verificación de subcadena
- **Cotas:** mejor Ω(1) · promedio Θ(k) · peor O(n) (fallback lineal)
- **Justificación (del cuerpo, no inventada):** Hay accesos a índices hash y un bucle acotado (palabras de la consulta o verificación de k candidatos; profundidad 1). El caso típico es O(k) con k ≪ n; si el índice no filtra, el fallback recorre el universo y vuelve a O(n).

#### `CatalogoHash.agregar`

- **Archivo:** `src/inventario/catalogo_hash.py` líneas 48–67
- **Técnica:** Inserción hash + índices secundarios
- **Cotas:** mejor Ω(1) · promedio Θ(1) · peor O(n) (colisión patológica)
- **Justificación (del cuerpo, no inventada):** No hay bucles sobre el catálogo. El cuerpo resuelve la consulta con acceso hash (in self._productos_por_id, self._productos_por_id, self._indice_categoria). Con factor de carga acotado el costo esperado es constante; el peor caso teórico de una tabla hash degenerada es O(n). Comentario del grupo (docstring): O(1) promedio para inserción en hash tables.

#### `agrupar_pedidos_batch`

- **Archivo:** `src/pedidos/agrupador.py` líneas 70–117
- **Técnica:** Acumulador hash en una pasada
- **Cotas:** mejor Ω(L) · promedio Θ(L + U) · peor O(L + U log U)
- **Justificación (del cuerpo, no inventada):** Doble bucle sobre pedidos y líneas con acumulación en un diccionario hash (inserción/actualización O(1) promedio por línea). La cota se desacopla del tamaño del catálogo n. Tras la pasada se ordenan los U productos únicos (O(U log U)). Comentario del grupo (docstring): O(L + P_dist), donde L es la sumatoria de todas las líneas

#### `calcular_top_solicitados_lineal`

- **Archivo:** `src/ranking/top_productos.py` líneas 15–55
- **Técnica:** Ordenamiento total de frecuencias
- **Cotas:** mejor Ω(L + N) · promedio Θ(L + N log N) · peor O(L + N log N)
- **Justificación (del cuerpo, no inventada):** Tras acumular frecuencias en un diccionario (O(L)), el cuerpo llama a `sorted` sobre las N claves. Timsort impone Θ(N log N) comparaciones; después se recortan los primeros k elementos. Comentario del grupo (docstring): O(L + N log N + k * T_busqueda).

#### `calcular_top_solicitados_heap`

- **Archivo:** `src/ranking/top_productos.py` líneas 58–99
- **Técnica:** Montículo acotado heapq.nlargest
- **Cotas:** mejor Ω(L + N) · promedio Θ(L + N log k) · peor O(L + N log k)
- **Justificación (del cuerpo, no inventada):** Se recorren las líneas de pedidos para armar un mapa de frecuencias (una pasada O(L)) y luego se invoca `heapq.nlargest`. Un min-heap de tamaño `k` hace un sift-down O(log k) por cada una de las N claves, de modo que la selección es O(N log k) y no O(N log N). Comentario del grupo (docstring): O(L + N log k + k * T_busqueda).

#### `BuscadorAlternativas._resolver_recursivo_puro`

- **Archivo:** `src/pedidos/combinaciones.py` líneas 170–209
- **Técnica:** Árbol recursivo exhaustivo
- **Cotas:** mejor Ω(N) · promedio Θ(2^N) · peor O(2^N)
- **Justificación (del cuerpo, no inventada):** Hay recursión sobre el índice del candidato y no se observa tabla de memoización. Cada elemento admite incluirlo o excluirlo, lo que genera un árbol de decisión de hasta 2^N hojas. El docstring del grupo coincide con esta derivación.

#### `BuscadorAlternativas._resolver_dp_memo`

- **Archivo:** `src/pedidos/combinaciones.py` líneas 211–256
- **Técnica:** Programación dinámica con memoización
- **Cotas:** mejor Ω(1) (hit de memo) · promedio Θ(N · P) · peor O(N · P)
- **Justificación (del cuerpo, no inventada):** La función se llama a sí misma y consulta `_memo_cache` indexado por `(indice, presupuesto_restante)`. Cada estado se resuelve a lo sumo una vez; el espacio de estados es el producto de candidatos `N` por el presupuesto discretizado `P`, de ahí la cota pseudo-polinomial O(N · P).

#### `procesar_pedidos_secuencial`

- **Archivo:** `src/pedidos/procesador_secuencial.py` líneas 19–121
- **Técnica:** Mono-hilo, una búsqueda por línea
- **Cotas:** mejor Ω(P · L) · promedio Θ(P · L · T_búsqueda) · peor O(P · L · T_búsqueda)
- **Justificación (del cuerpo, no inventada):** Hay un `for` sobre pedidos y otro anidado sobre líneas, y cada línea invoca `buscar_por_id`. La cota se descompone: T_búsqueda = O(n) si el catálogo es lineal y O(1) promedio si es hash. Por eso el baseline escala a O(P · L · n) y el optimizado a O(P · L). Comentario del grupo (docstring): O(P * M * N), donde P es la cantidad de pedidos, M la cantidad promedio de líneas

#### `procesar_pedidos_concurrente`

- **Archivo:** `src/pedidos/procesador_concurrente.py` líneas 118–216
- **Técnica:** ProcessPoolExecutor + snapshot de stock
- **Cotas:** mejor O(P · L) · promedio O((P · L)/C + C_IPC) · peor O(P · L + C_IPC)
- **Justificación (del cuerpo, no inventada):** El cuerpo instancia `ProcessPoolExecutor` y parte el lote en fragmentos. El trabajo útil por pedido es lineal en sus líneas; el término `C_IPC` aparece porque cada worker recibe un snapshot serializado del stock. Con pocos pedidos el overhead de creación de procesos domina; con muchos el costo se reparte entre `C` núcleos.

#### `CacheLRU.obtener`

- **Archivo:** `src/cache/cache_consultas.py` líneas 61–68
- **Técnica:** Acceso hash + política LRU
- **Cotas:** mejor Ω(1) · promedio Θ(1) · peor O(n) (colisión patológica)
- **Justificación (del cuerpo, no inventada):** No hay bucles sobre el catálogo. El cuerpo resuelve la consulta con acceso hash (in self._almacen, self._almacen). Con factor de carga acotado el costo esperado es constante; el peor caso teórico de una tabla hash degenerada es O(n).

#### `CacheLRU.guardar`

- **Archivo:** `src/cache/cache_consultas.py` líneas 70–78
- **Técnica:** Inserción hash + desalojo del menos reciente
- **Cotas:** mejor Ω(1) · promedio Θ(1) · peor O(n) (colisión patológica)
- **Justificación (del cuerpo, no inventada):** No hay bucles sobre el catálogo. El cuerpo resuelve la consulta con acceso hash (in self._almacen, self._almacen). Con factor de carga acotado el costo esperado es constante; el peor caso teórico de una tabla hash degenerada es O(n).

#### `GestorCacheConsultas.invalidar_por_mutacion_stock`

- **Archivo:** `src/cache/cache_consultas.py` líneas 136–142
- **Técnica:** Purga de búsquedas y categorías
- **Cotas:** mejor Ω(1) · promedio Θ(1) · peor O(1)
- **Justificación (del cuerpo, no inventada):** El cuerpo no recorre colecciones del dominio ni dispara recursión: son asignaciones, purgas de caché o accesos puntuales.

### Qué no hace esta automatización

- No reescribe el motor ni aplica optimizaciones.
- No sustituye la derivación formal del grupo (secciones 2–5): la complementa.
- Si una función nueva del motor no aparece, hay que agregarla a
  `automations/inventario_funciones.py`.

<!-- ORIGIN-AUTO-COMPLEJIDAD:FIN -->
