# 1. Descripción Funcional

## 1.1. Problema que Resuelve el Sistema

En los centros de distribución y almacenes logísticos modernos, la gestión ágil del inventario y la preparación oportuna de pedidos (*order picking*) son factores determinantes para la competitividad operativa. 

A medida que el catálogo crece a decenas de miles de productos y se reciben lotes masivos de pedidos concurrentes, las implementaciones ingenuas colapsan rápidamente:
- **Búsquedas secuenciales $O(n)$** que degradan la atención de pedidos de múltiples líneas a $O(m \cdot n)$.
- **Ordenamientos completos $O(n \log n)$** para extraer un ranking acotado de apenas $k$ productos más solicitados.
- **Exploración combinatoria exponencial $O(2^n)$** para sugerir alternativas de reemplazo cuando no hay stock suficiente de un ítem.
- **Procesamiento secuencial bloqueante** que no aprovecha la arquitectura multinúcleo para validar grandes volúmenes de demanda.

El **Optimizador de Inventario y Pedidos** resuelve esta problemática implementando un motor logístico de alto rendimiento en Python, diseñado bajo una **dualidad estricta entre una versión inicial (*Baseline*) y una versión optimizada**, permitiendo contrastar analítica y empíricamente el impacto de cada decisión algorítmica.

---

## 1.2. Alcance del Sistema

El sistema cubre integralmente el ciclo operativo de un centro de distribución:

1. **Gestión de Catálogo y Búsqueda Inmediata:**
   - Indexación de productos con identificación unívoca, denominación, categoría, stock disponible y precio unitario.
   - Búsqueda en tiempo promedio constante $O(1)$ por identificador y búsqueda tokenizada amortizada por nombre mediante índices invertidos.

2. **Agrupación y Preparación Consolidada (*Batch Picking*):**
   - Consolidación de múltiples pedidos en una sola pasada $O(L)$, sumando demandas idénticas para optimizar el recorrido físico en el almacén.

3. **Ranking de Demanda (Top-N):**
   - Extracción eficiente de los $k$ productos más solicitados utilizando montículos binarios acotados (`heapq`) en tiempo $O(n \log k)$.

4. **Sugerencia Inteligente de Alternativas Sustitutas:**
   - Resolución de combinaciones de productos dentro de la misma categoría bajo restricción presupuestaria mediante **Programación Dinámica (DP) con memoización**, podando ramas redundantes y evitando la explosión combinatoria.

5. **Capa de Caching Inteligente con Invalidación Reactiva:**
   - Caché en memoria Least Recently Used (LRU) de 128 slots para consultas repetidas.
   - Protocolo de invalidación reactiva atómica que purga resultados obsoletos ante mutaciones de stock o registro de nuevos pedidos.

6. **Procesamiento Masivo y Flujos en Streaming:**
   - Procesamiento de archivos masivos en formato JSON Lines (`.jsonl`) con generadores lazy de consumo de memoria constante $O(1)$ y buffers de escritura atómicos.

7. **Interfaz de Usuario y Auditoría en Vivo:**
   - Aplicación de escritorio interactiva construida en **Flet** (motor Flutter) con 7 pantallas operativas y panel de estado en tiempo real.

---

## 1.3. Requisitos del Sistema

### Requisitos Funcionales (RF)
- **RF-01 (Carga de Datos):** El sistema debe permitir cargar datasets en formato JSON y streaming JSON Lines (`.jsonl`), validando consistencia referencial y tipado.
- **RF-02 (Consulta de Inventario):** Búsqueda por ID en tiempo constante $O(1)$ y por texto con autocompletado y coincidencia de palabras.
- **RF-03 (Consolidación de Pedidos):** Agrupación por lotes consolidando cantidades por SKU en una única pasada lineal.
- **RF-04 (Ranking Top-N):** Listado de los $k$ productos con mayor demanda acumulada.
- **RF-05 (Alternativas DP):** Cálculo de combinaciones óptimas de reemplazo ante stock insuficiente dentro del presupuesto indicado.
- **RF-06 (Conmutación Algorítmica):** La interfaz debe permitir alternar en caliente entre modo *Baseline* y modo *Optimizado* para auditar el speedup en vivo.

### Requisitos No Funcionales (RNF)
- **RNF-01 (Eficiencia Temporal):** Speedup global superior a $500\times$ en el procesamiento integral de pedidos masivos (10.000 productos y 2.000 pedidos).
- **RNF-02 (Eficiencia Espacial):** Consumo de memoria heap acotado en streaming ($< 10\text{ MB}$ para lotes de gran escala).
- **RNF-03 (Concurrencia Segura):** Aislamiento de procesos mediante `ProcessPoolExecutor`, evitando condiciones de carrera en el descuento de inventario.
- **RNF-04 (Calidad de Código):** 0 errores de sintaxis, 0 observaciones de linter (`Ruff`), complejidad cognitiva $\le 15$ (`complexipy`) y cobertura de pruebas $\ge 85\%$.
- **RNF-05 (Seguridad):** Cero vulnerabilidades críticas o altas en código fuente (`Bandit`) y dependencias (`pip-audit`), y escaneo preventivo de secretos (`Gitleaks`).
