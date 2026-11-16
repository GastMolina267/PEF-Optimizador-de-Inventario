# 6. Estrategia de Pruebas y Aseguramiento de la Calidad

## 6.1. Filosofía de Pruebas

El sistema cuenta con una **red de seguridad automatizada de 234 pruebas**, organizada modularmente por paquetes de dominio bajo el directorio `tests/`. La estrategia combina tres niveles complementarios de verificación:

```mermaid
flowchart TD
  subgraph T1 ["1. Pruebas Unitarias de Dominio e IA"]
    Unit["Aislamiento de métodos, invariantes de estado, excepciones y pipelines scikit-learn."]
  end

  subgraph T2 ["2. Property-Based Testing (Hypothesis)"]
    Hypo["Generación pseudoaleatoria masiva de escenarios para comprobar equivalencia matemática."]
  end

  subgraph T3 ["3. Pruebas de Integración, Rendimiento y Memoria"]
    Integ["Equivalencia Baseline vs Optimizado, microbenchmarks continuos y presupuesto estricto de heap tracemalloc."]
  end

  T1 --> CI["Pipeline de CI en GitHub Actions\n(Umbral mínimo de Cobertura: 85%)"]
  T2 --> CI
  T3 --> CI
```

---

## 6.2. Organización Modular de la Suite de Pruebas

| Subdirectorio de Pruebas | Casos Cubiertos | Propósito Principal |
|---|:---:|---|
| **`tests/modelos/`** | 9 | Validación de constructores, inmutabilidad, cálculo de totales e integridad de dataclasses. |
| **`tests/inventario/`** | 13 | Búsqueda por ID, coincidencia de texto, índice por categoría y cumplimiento de `CatalogoProtocol`. |
| **`tests/pedidos/`** | 20 | Batch picking consolidado, evaluación de factibilidad, combinaciones DP y procesadores concurrentes/secuenciales. |
| **`tests/ranking/`** | 4 | Selección de Top-N con montículos binarios y ordenamiento contra lista de frecuencias. |
| **`tests/cache/`** | 3 | Desalojo LRU (capacidad máxima), hit ratio e invalidación reactiva atómica por mutaciones. |
| **`tests/datos/`** | 38 | Deserialización JSON, streaming JSON Lines, buffering, validador de integridad y procesamiento en lotes. |
| **`tests/observabilidad/`** | 11 | Instrumentación de Elastic APM, decoradores `@medir`, spans internos y fallback ante ausencia de servidor. |
| **`tests/motor/`** | 10 | Fachada unificada `MotorInventario`, conmutación en caliente de estrategias baseline/optimizado. |
| **`tests/ia/`** | 31 | Inferencia de modelos scikit-learn, extracción de features, presupuesto de memoria heap (< 3 MB), ausencia de fugas y tests basados en propiedades. |
| **`tests/ui/`** | 41 | Vistas Flet, panel de estado reactivo, vista de Predicción IA con KPIs de latencia/memoria y badges accesibles. |
| **`tests/integracion/`** | 37 | Equivalencia baseline vs optimizado, microbenchmarks continuos y presupuesto de memoria heap. |
| **`tests/automations/`** | 17 | Motor de análisis AST de complejidad y generador de informes de hotspots. |

---

## 6.3. Cobertura de Código y Umbrales Estrictos

La suite se ejecuta en cada commit utilizando `pytest-cov`, configurada con soporte para medir también los procesos hijos del `ProcessPoolExecutor`:

```ini
[tool.coverage.run]
source = ["src"]
concurrency = ["multiprocessing", "thread"]
parallel = true
```

- **Cobertura Global en `src/`:** **>90%**.
- **Umbral de Bloqueo en CI:** **85%** (`--cov-fail-under=85`). Si una modificación reduce la cobertura por debajo de este valor, el pipeline rechaza el merge automáticamente.

---

## 6.4. Pruebas Basadas en Propiedades (*Property-Based Testing*)

Mediante la biblioteca **Hypothesis** (`tests/integracion/test_propiedades_hypothesis.py` y `tests/ia/test_predictor_ia.py`), se evalúa la equivalencia funcional y la validez de invariantes sobre miles de entradas generadas dinámicamente:
- **Equivalencia de Catálogo:** Para cualquier conjunto aleatorio de productos y claves de consulta, `catalogo_hash.buscar_por_id(k)` devuelve exactamente el mismo resultado que `catalogo_lineal.buscar_por_id(k)`.
- **Equivalencia de Picking:** La consolidación de líneas de demanda aleatorias produce idénticas cantidades acumuladas por SKU.
- **Equivalencia de Ranking:** El Min-Heap Top-N retorna el mismo orden y frecuencia que el ordenamiento integral.
- **Invariantes del Predictor:** Para cualquier stock entero no negativo y ventas aleatorias, las probabilidades estimadas por el clasificador se acotan estrictamente a $P \in [0.0, 1.0]$ y son monótonamente no crecientes respecto al volumen de stock remanente.

---

## 6.5. IA Aplicada al Desarrollo de Software (Testing, Invariantes y Profiling)

En cumplimiento con el eje de **IA aplicada al desarrollo de software** exigido por la cátedra, se emplearon asistentes de inteligencia artificial bajo estricta validación empírica en las siguientes áreas clave:

1. **Generación de Pruebas de Propiedades e Invariantes:**  
   Se formularon estrategias con **Hypothesis** para descubrir condiciones de borde en tensores de features de 10 dimensiones, validando que el extractor maneje nulos, historiales vacíos y ratios $0/0$ sin degradación numérica (`NaN`).
2. **Pruebas de Presupuesto y Detección de Fugas de Memoria:**  
   Diseño de arneses con `tracemalloc` (`tests/ia/test_presupuesto_memoria_ia.py`) que ejecutan bucles de 200 inferencias continuas, verificando que la tasa de crecimiento residual de memoria sea nula ($\le 0.05\text{ KB/iteración}$) y descartando acumulación indeseada de estados en las tuberías de `scikit-learn`.
3. **Optimización de Vectorización y Reducción de Latencia:**  
   Identificación asistida del cuello de botella en la inferencia producto por producto frente a la inferencia matricial vectorizada en lotes (`_regresor.predict(matriz_x)`), permitiendo una reducción drástica de tiempo en la Cascada Híbrida.
