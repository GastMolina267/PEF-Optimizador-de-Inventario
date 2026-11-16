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

---

## 4.4. Confrontación de Paradigmas: Heurística Convencional $O(1)$ vs. Pipeline con IA vs. Cascada Híbrida

En cumplimiento con el requisito central del proyecto final (*"demostrar una utilidad concreta y estar respaldada por pruebas y mediciones, justificando cuándo la IA aporta beneficios y cuándo una solución algorítmica convencional resulta más simple, rápida, económica o confiable"*), se comparan tres paradigmas:

### 1. Heurística Convencional Analítica ($O(1)$)
- **Mecanismo:** Regla aritmética basada en punto de reorden clásico:
  $$\text{ROP} = \mu_{\text{demanda}} \cdot L + z \cdot \sigma_{\text{demanda}} \cdot \sqrt{L}$$
- **Complejidad Temporal:** $O(1)$ estricto (4 operaciones aritméticas escalares).
- **Latencia Medida:** $\approx 58.5\ \mu\text{s}$ por producto (**23.3x más rápida** que el modelo supervisado).
- **Consumo de Memoria:** $0.0\text{ KB}$ de heap adicional (sin asignaciones dinámicas ni objetos de estimador).
- **Cuándo es Superior:** Catálogos con cientos de miles de SKUs de demanda estable, microservicios de altísima concurrencia o entornos embebidos/edge donde el cómputo debe mantenerse en microsegundos y el overhead de dependencias de ML (`numpy`, `scipy`, `scikit-learn`) es inaceptable.

### 2. Modelo Supervisado con IA (`scikit-learn`)
- **Mecanismo:** Vector de características de 10 dimensiones (medias móviles a 3 y 7 periodos, desvío estándar, ratio demanda/stock, tendencia, penetración y precio unitario) procesado mediante un pipeline doble:
  - **Regresor `Ridge`:** Predicción continua de demanda futura en unidades.
  - **Clasificador `LogisticRegression`:** Estimación de probabilidad calibrada de quiebre de stock $P(\text{quiebre}) \in [0.0, 1.0]$.
- **Complejidad Temporal:** $O(d)$ donde $d=10$ dimensiones, sumado al overhead de serialización y llamadas internas en C/Cython.
- **Latencia Medida:** $\approx 1.361,9\ \mu\text{s}$ por producto.
- **Consumo de Memoria:** $29.9\text{ KB}$ pico de heap en inferencia batch y artefacto compacto de $2.6\text{ KB}$ en disco (`joblib`).
- **Cuándo es Superior:** Productos críticos de alto valor, estacionalidad no lineal, correlación multivariada entre precio y volatilidad de demanda, o cuando el negocio requiere cuantificar el nivel de certeza antes de disparar compras costosas.

### 3. Cascada Híbrida Reactiva (Compromiso Óptimo de Ingeniería)
- **Mecanismo:** Arquitectura en dos fases inspirada en los clasificadores en cascada de Viola-Jones:
  1. *Filtro Rápido $O(1)$:* Si el stock actual supera holgadamente el punto de reorden ($\text{stock} > 2.5 \cdot \text{ROP}$), se etiqueta inmediatamente como `Riesgo.BAJO` sin invocar el pipeline de IA.
  2. *Inferencia Especializada:* Si el producto se encuentra en la zona de incertidumbre ($\text{stock} \le 2.5 \cdot \text{ROP}$), se activa la inferencia completa con `scikit-learn`.
- **Latencia Medida:** $\approx 263.9\ \mu\text{s}$ por producto (**5.2x más rápida** que la inferencia pura de IA, con un ahorro de tiempo $> 75\%$).
- **Garantía Operativa:** Detecta el 100% de los quiebres reales con una fracción del costo computacional.
