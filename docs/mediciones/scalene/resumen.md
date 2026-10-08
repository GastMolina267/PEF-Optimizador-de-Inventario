# Scalene: antes y después de la propuesta Origin 1

Generado por `python -m benchmarks.resumir_scalene`. No editar a mano.

- **Antes:** código al cierre de F3 (commit `823bb18`), antes de los cambios de IPC.
- **Después:** código actual.
- **Escenario:** `benchmarks/perfilar_scalene.py` (búsquedas, picking, Top-N, alternativas y
  30 vueltas de procesamiento secuencial y con pool sobre `grande.json`).
- **Entorno:** Linux, Python 3.13, 2 núcleos. Workers creados con fork en ambas corridas (en la de después, con PEF_MP_START_METHOD=fork) para comparar en igualdad de condiciones

## Resultado global

| Métrica | Antes | Después |
|---|---:|---:|
| Tiempo total bajo Scalene (s) | 3.12 | 2.58 |
| Pico de memoria (MB) | 16.7 | 17.1 |
| Tiempo en Python (% del total) | 6.8 | 20.0 |
| Tiempo en código nativo (% del total) | 63.1 | 57.8 |
| Tiempo de sistema: esperas, IPC, E/S (% del total) | 28.1 | 20.6 |

El escenario completo tardó un **17 % menos** después de los cambios.

## Dónde se va el tiempo, por función

Porcentaje del tiempo total de cada corrida (Python · nativo · sistema). "—" indica menos
de 1 %.

| Función | Antes | Después |
|---|---|---|
| `src/pedidos/procesador_concurrente.py · procesar_pedidos_concurrente` | 48.1 % (py 1 · nat 23 · sis 24) | — |
| `src/pedidos/procesador_concurrente.py · _evaluar_en_pool` | — | 21.6 % (py 0 · nat 9 · sis 13) |
| `src/pedidos/evaluador.py · _armar_resultado` | — | 12.5 % (py 0 · nat 11 · sis 1) |
| `<exec@dataclasses.py:498> · __create_fn__.<locals>.__init__` | 6.8 % (py 2 · nat 5 · sis 0) | 12.0 % (py 6 · nat 3 · sis 3) |
| `src/datos/cargador.py · cargar_dataset_json` | 10.3 % (py 0 · nat 9 · sis 2) | 8.8 % (py 0 · nat 8 · sis 1) |
| `src/pedidos/procesador_concurrente.py · _armar_fragmentos` | — | 10.2 % (py 4 · nat 5 · sis 1) |
| `src/modelos/producto.py · Producto.__post_init__` | — | 6.4 % (py 1 · nat 5 · sis 1) |
| `src/inventario/catalogo_hash.py · CatalogoHash.buscar_por_id` | 5.3 % (py 0 · nat 5 · sis 0) | 3.8 % (py 0 · nat 4 · sis 0) |
| `src/inventario/catalogo_hash.py · CatalogoHash._indexar_nombre` | 5.0 % (py 0 · nat 4 · sis 1) | 4.9 % (py 0 · nat 5 · sis 0) |
| `src/pedidos/agrupador.py · agrupar_pedidos_batch` | 4.5 % (py 1 · nat 4 · sis 0) | 3.3 % (py 2 · nat 1 · sis 0) |
| `src/datos/validador.py · ValidadorDataset.validar_diccionario` | 4.4 % (py 0 · nat 4 · sis 1) | — |
| `src/pedidos/evaluador.py · _consultar_stock` | 3.9 % (py 1 · nat 2 · sis 1) | — |

## Cómo leerlo

- **Tiempo de sistema** en las funciones del pool es el proceso principal esperando a los
  workers y moviendo datos por el canal IPC. Es el costo que ataca la propuesta Origin 1.
- **Nativo** incluye `pickle` y `json` (implementados en C) y la creación de dataclasses.
- Los porcentajes son relativos a cada corrida. Para comparar entre corridas, usar el
  tiempo total de la primera tabla.
