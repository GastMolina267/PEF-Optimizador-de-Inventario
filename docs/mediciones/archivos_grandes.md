# Medición de Archivos Grandes: Streaming, Buffering y Paralelismo (Fase F5)

Este documento documenta las mediciones de rendimiento de la **Fase F5** (Programación Eficiente - Segundo Parcial), demostrando el comportamiento de la arquitectura de streaming, el buffering explícito de I/O y el procesamiento paralelo por lotes (chunking) frente a archivos masivos en formato JSON Lines (`.jsonl`).

---

## 1. Contexto y Parámetros del Experimento

- **Entorno:** Python en Windows (Arquitectura multicore).
- **Archivos de prueba generados:**
  - `productos.jsonl`: **5,000** productos (0.66 MB).
  - `pedidos.jsonl`: **25,000** pedidos (2.63 MB).
- **Generación determinista:** Semilla fija (`seed=42`) sin trackeo en Git (`data/generados/` ignorado por `.gitignore`).

---

## 2. Experimento 1: Monolítico en Memoria vs. Streaming Línea por Línea

Se evaluó el consumo de memoria RAM pico y tiempo de lectura comparando la carga monolítica tradicional (`json.load` acumulando estructuras en listas de objetos) contra el generador lazy en streaming (`leer_pedidos_streaming_jsonl`).

| Estrategia | Tiempo de Lectura | Memoria Pico (RAM) | Memoria Final Retenida | Comportamiento |
|---|---|---|---|---|
| **Monolítico (`json.load`)** | 258.3 ms | 24.65 MB | 24.52 MB | $O(N)$ lineal con el tamaño del archivo |
| **Streaming (`.jsonl` lazy)** | 369.6 ms | 1.03 MB | 0.00 MB | $O(1)$ constante (buffer acotado) |

> **Hallazgo:** El generador de streaming logra un **ahorro de memoria pico del 95.8%**, garantizando que el sistema pueda procesar archivos de escala arbitraria sin agotar la memoria física del equipo.

---

## 3. Experimento 2: Barrido de Tamaños de Lote (Break-Even Secuencial vs. Paralelo)

Cada worker de proceso independiente deserializa, valida la existencia de IDs y evalúa la cobertura de demanda. Se varió el tamaño de lote ($B$) para determinar el punto óptimo donde el cómputo CPU supera el costo de serialización/IPC de Windows.

| Tamaño de Lote ($B$) | Secuencial (Tiempo) | Secuencial (Pico RAM) | Paralelo (Tiempo) | Paralelo (Pico RAM) | Speedup ($T_{sec} / T_{par}$) |
|---|---|---|---|---|---|
| 1,000 | 359.1 ms | 2.04 MB | 360.7 ms | 13.03 MB | **1.00×** |
| 5,000 | 402.9 ms | 6.02 MB | 103.3 ms | 13.75 MB | **3.90×** |
| 10,000 | 411.0 ms | 11.01 MB | 123.3 ms | 14.96 MB | **3.33×** |
| 25,000 | 1020.6 ms | 15.38 MB | 570.2 ms | 20.47 MB | **1.79×** |

### Conclusiones del Paralelismo:
1. **Compensación del IPC:** A diferencia de la evaluación individual sobre objetos preexistentes en memoria (donde el IPC no compensaba por la simplicidad de la búsqueda $O(1)$), en archivos `.jsonl` el lote incluye **parsing JSON**, **validación de integridad** y **evaluación algorítmica**.
2. **Break-Even:** A partir de lotes de **5.000 pedidos**, el paralelismo supera consistentemente a la versión secuencial con un **speedup mayor a 1.0×**, alcanzando su mejor desempeño en lotes entre **5.000 y 10.000 pedidos**.
3. **Control de Memoria:** El uso de tuplas compactas para devolver resultados y el despacho mediante generadores asegura que la memoria de ambos enfoques se mantenga contenida durante todo el ciclo.

---

## 4. Experimento 3: Exportación con Buffering Explícito (1 MB) a CSV

Se evaluó la exportación del reporte consolidado de picking hacia CSV (`exportar_picking_csv_con_buffer`):
- **Registros consolidados exportados:** 3,190 filas.
- **Tamaño del archivo:** 268.0 KB.
- **Tiempo de serialización y escritura con buffer de 1 MB:** 252.72 ms.
- **Pico de memoria asignada:** 1.15 MB.

El buffer de 1 MB (`1 << 20 bytes`) minimiza las llamadas al sistema operativo (`write()` syscalls), agrupando los bytes en memoria antes de transferirlos al disco.
