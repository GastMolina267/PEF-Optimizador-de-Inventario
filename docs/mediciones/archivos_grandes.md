# Archivos grandes: streaming, buffering y paralelismo

Generado por `python -m benchmarks.perfilar_archivos_grandes`. No editar a mano: volver
a correr el script para actualizar los números.

## Entorno y datos

- **Sistema:** Linux 6.18.44-fc-v80 · Python 3.13.16 · 2 núcleos lógicos · 2 workers.
- **Archivos generados** (semilla 42, en `data/generados/`, fuera de git):
  `productos.jsonl` con 5,000 productos (0.66 MB) y
  `pedidos.jsonl` con 200,000 pedidos (20.96 MB).
- **Metodología:** cada tiempo es la mediana de 5 corridas con el pool ya
  creado. Tiempo y memoria se miden en corridas separadas, porque `tracemalloc` frena al
  proceso principal pero no a los workers y eso inflaba el speedup del paralelo. La memoria
  es el pico del proceso principal (no incluye los workers).

## 1. Lectura: carga completa vs streaming

| Estrategia | Tiempo (ms) | Pico de memoria (MB) |
|---|---:|---:|
| Carga completa (`json.loads` de todas las líneas a una lista) | 849.5 | 195.59 |
| Streaming (`leer_pedidos_streaming_jsonl`) | 696.5 | 1.02 |

El streaming usa un **99.5 % menos de memoria pico**: la memoria depende del tamaño de una línea, no del tamaño del archivo. Además fue más rápido, porque no tiene que hacer crecer una lista gigante.

## 2. Procesamiento por lotes: secuencial vs paralelo

Cada lote se parsea, valida y evalúa con la misma función en ambas versiones. La versión
paralela manda el stock una sola vez por worker (initializer) y mantiene como máximo dos
lotes en vuelo por worker, así que su memoria no crece con el archivo.

| Lote (líneas) | Secuencial (ms) | Paralelo (ms) | Speedup | Pico secuencial (MB) | Pico paralelo (MB) |
|---:|---:|---:|---:|---:|---:|
| 1,000 | 827.8 | 686.9 | **1.21×** | 1.68 | 3.05 |
| 5,000 | 995.5 | 654.2 | **1.52×** | 3.93 | 8.36 |
| 20,000 | 869.5 | 769.8 | **1.13×** | 12.03 | 30.41 |
| 50,000 | 987.6 | 775.5 | **1.27×** | 28.19 | 86.05 |

El paralelo superó al secuencial con lotes de 1,000, 5,000, 20,000, 50,000 líneas. El mejor resultado fue **1.52×** con lotes de 5,000. Con 2 workers el máximo teórico es 2×. La memoria del proceso principal crece con el tamaño de lote (hay hasta dos lotes por worker en vuelo), no con el tamaño del archivo.

## 3. Pedidos ya cargados en memoria (`grande.json`)

| Pedidos | Secuencial (ms) | Pool de procesos (ms) | Speedup |
|---:|---:|---:|---:|
| 2,000 | 5.2 | 14.0 | **0.37×** |

Evaluar un pedido en memoria es un lookup O(1) por línea, más barato que serializarlo hacia
un worker. Por eso `MotorInventario.procesar_pedidos` es secuencial por defecto y el pool
queda como opción explícita. Con archivos (sección 2) el balance cambia porque cada worker
además parsea y valida JSON.

## 4. Exportación a CSV con buffer

| Buffer | Tiempo (ms) |
|---|---:|
| Por defecto de Python | 52.4 |
| Explícito de 1 MB | 48.9 |

Se exportaron 5,000 filas (434.9 KB). El buffer de 1 MB fue un 7 % más rápido: agrupa las escrituras en menos llamadas al sistema operativo.
