# 4. Diseño Técnico y Complejidad Algorítmica

## 4.1. Justificación de Estructuras de Datos

En cumplimiento con el requisito pedagógico de contrastar estructuras adecuadas frente a inadecuadas:

| Estructura | Rol en el Sistema | Operaciones Críticas | Complejidad Temporal | Justificación Técnica |
|---|---|---|:---:|---|
| **`list` (Lista Dinámica)** | Línea base (*Baseline*) del catálogo; preserva orden cronológico de pedidos. | Búsqueda por ID / texto<br>Inserción final | $O(n)$<br>$O(1)$ amort. | Ineficiente para catálogos extensos; requiere escaneo secuencial completo ítem por ítem. |
| **`dict` (Tabla Hash)** | Catálogo optimizado e índice secundario por categoría. | Búsqueda por ID<br>Inserción / Update | $O(1)$ prom.<br>$O(1)$ prom. | Acceso indexado en tiempo constante promedio con resolución de colisiones en tabla hash abierta de Python. |
| **`heapq` (Montículo Binario)** | Selección de los $k$ productos más solicitados a partir del mapa de frecuencias. | `nlargest` acotado | $O(n \log k)$ | Mantiene un min-heap de tamaño $k$. Si $k \ll n$, supera drásticamente al ordenamiento completo $O(n \log n)$. |
| **`set` (Conjunto Hash)** | Control de unicidad de IDs al cargar datasets y verificación de existencia. | Pertenencia (`item in s`) | $O(1)$ prom. | Evita búsquedas lineales repetitivas de existencia cruzada en validación de lotes. |
| **`OrderedDict`** | Almacén de la Caché de Consultas (`CacheLRU`). | Desalojo de menos recientemente usado | $O(1)$ | Mantiene orden de acceso mediante lista doblemente enlazada interna, permitiendo evicciones atómicas en $O(1)$. |

---

## 4.2. Matriz Comparativa de Complejidad Asintótica (Big-O)

La siguiente tabla resume las cotas analíticas derivadas teóricamente y validadas por el motor de análisis AST (`automations/analizar_complejidad.py`):

| Operación Crítica | Algoritmo Baseline | Algoritmo Optimizado | Cota Temporal Base | Cota Temporal Optimizada | Cota Espacial |
|---|---|---|:---:|:---:|:---:|
| **Búsqueda por ID** | Escaneo secuencial | Acceso a clave Hash | $O(n)$ | **$O(1)$** prom. | $O(1)$ adicional |
| **Búsqueda por Texto** | Recorrido lineal con `in` | Índice invertido tokenizado + LRU | $O(n)$ | **$O(1)$** amort. | $O(U)$ términos únicos |
| **Batch Picking (Agrupación)** | Recorridos cuadráticos | Acumulación hash en pasada única | $O(P \cdot L \cdot n)$ | **$O(L_{\text{total}})$** | $O(K)$ productos distintos |
| **Ranking Top-N** | `sorted(..., reverse=True)` | Min-Heap acotado (`heapq`) | $O(n \log n)$ | **$O(n \log k)$** | $O(k)$ elementos en heap |
| **Alternativas de Reemplazo** | Árbol recursivo exhaustivo | Programación Dinámica (Memoizada) | $O(2^n)$ | **$O(n \cdot P)$** | $O(n \cdot P)$ tabla DP |
| **Procesamiento de Pedidos** | Secuencial mono-hilo | Workers paralelos desacoplados | $O(P \cdot L)$ | **$O((P \cdot L)/C + \text{IPC})$** | $O(P)$ tuplas compactas |
| **Lectura de Archivos Masivos** | `json.load()` completo | Streaming generador línea a línea | $O(S)$ memoria | **$O(1)$** memoria heap | Buffer circular $1\text{ MB}$ |

*Referencias:*  
- $n$: Total de productos en catálogo.  
- $P$: Cantidad de pedidos en lote.  
- $L$: Cantidad promedio de líneas por pedido.  
- $k$: Cantidad de elementos solicitados en el ranking Top-N ($k \ll n$).  
- $C$: Cantidad de núcleos físicos/lógicos disponibles.  
- $S$: Tamaño físico del archivo de datos en disco.  

---

## 4.3. Decisiones Algorítmicas de Alto Impacto

### 1. Memoización vs. Caching Inteligente
- **Memoización (Nivel Algorítmico):** Se aplica en `src/pedidos/combinaciones.py` para resolver el subproblema de mochila bounded de alternativas sustitutas. Almacena en memoria local de la función el estado `(indice, presupuesto_restante)`, podando exponencialmente ramas equivalentes.
- **Caching Inteligente (Nivel Sistema):** Se implementa en `src/cache/cache_consultas.py` mediante una fachada `GestorCacheConsultas` con tres almacenes LRU independientes (búsqueda de texto, categorías y ranking Top-N). Se invalidan reactivamente de forma atómica ante cualquier operación de escritura (`alta_producto`, `descontar_stock`, `procesar_pedidos`).

### 2. Concurrencia y la Ley de Amdahl
La evaluación de factibilidad es CPU-bound y se paraleliza con `ProcessPoolExecutor` para eludir el GIL de CPython. Sin embargo, el descuento efectivo de stock es intrínsecamente secuencial (cada pedido debe observar el stock remanente del anterior). El procesador concurrente separa ambas etapas: los workers evalúan la demanda en paralelo y el proceso principal asigna el stock en orden cronológico, eliminando condiciones de carrera y minimizando la sobrecarga de IPC en Windows.
