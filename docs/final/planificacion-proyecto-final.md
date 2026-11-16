# Planificación del Proyecto Final: Integración de Inteligencia Artificial en el Optimizador de Inventario

**Materia:** Programación Eficiente — Opción 6 (*Universidad Blas Pascal, 2026*)  
**Proyecto:** Optimizador de Inventario y Preparación de Pedidos en Escala Masiva  
**Equipo de Desarrollo:** Edgar Karpowicz, Gastón Molina, Tomás Molina  
**Documento Base del Enunciado:** `docs/final/Programacion-eficiente.pptx` (Diapositivas 356 a 401)  
**Punto de Partida:** Tag `parcial-3` / Rama `dev`  

---

## 1. Introducción y Enfoque Académico

El Proyecto Final representa la culminación integral del sistema desarrollado a lo largo de la materia. Tras haber construido una arquitectura algorítmica de alto rendimiento (Parcial 1), haberla refactorizado, perfilado y dotado de observabilidad (Parcial 2), y haber establecido una infraestructura de Integración Continua con rigurosos controles de calidad y seguridad (Parcial 3), la etapa final aborda la **incorporación metódica y justificada de la Inteligencia Artificial**.

De acuerdo con las directivas oficiales de la cátedra (diapositivas 386 y 400), el proyecto final debe estructurarse obligatoriamente bajo **dos enfoques complementarios**:

1. **IA aplicada al desarrollo de software:** Utilizar asistentes y herramientas de IA para generar pruebas automáticas, documentar código, detectar fallos y proponer optimizaciones, **validando siempre sus resultados de forma empírica**.
2. **IA integrada en la aplicación:** Incorporar una biblioteca o modelo de IA que resuelva una funcionalidad concreta del sistema y **evaluar rigurosamente su costo computacional**.

> [!IMPORTANT]
> **Criterio de Evaluación Rector (Slide 400):**  
> *"La integración de IA deberá demostrar una utilidad concreta y estar respaldada por pruebas y mediciones. Se valorará especialmente la capacidad de justificar cuándo la IA aporta beneficios y cuándo una solución algorítmica convencional resulta más simple, rápida, económica o confiable."*

---

## 2. Definición Funcional del Módulo de IA: Predicción Inteligente de Demanda y Quiebre de Stock

Para dar respuesta a los requerimientos del dominio logístico, se selecciona la **Opción A: Predictor Inteligente de Demanda y Quiebre de Stock (*Stockout*)**:

### 2.1. El Problema en Centros de Distribución
En la operación de un almacén o centro de fulfillment (ej. Mercado Libre, Amazon), el inventario disponible de cada SKU es finito y dinámico. Al procesar lotes masivos de pedidos concurrentes, un porcentaje significativo de órdenes no puede satisfacerse íntegramente debido a que determinados productos críticos sufren **quiebres de stock (*stockouts*)**.

Hasta el Parcial 3, el sistema es puramente **reactivo**: procesa el lote y, si no hay stock suficiente, marca la línea como "imposible" o "parcial". El objetivo de la IA es volver al sistema **proactivo**: anticipar qué productos tienen alta probabilidad de agotarse en el siguiente turno o lote de pedidos, y estimar cuántas unidades adicionales se demandarán, permitiendo disparar alertas de reabastecimiento antes de que el pedido falle.

### 2.2. Tareas del Modelo de IA
1. **Clasificación Supervisada de Riesgo de Quiebre:** Predice para cada producto si entrará en quiebre de stock en el próximo ciclo ($\hat{y} \in \{\text{Seguro}, \text{Riesgo Moderado}, \text{Quiebre Inminente}\}$).
2. **Regresión Supervisada de Demanda:** Estima la cantidad numérica de unidades que serán solicitadas en el siguiente lote ($\hat{D}_i \in \mathbb{R}^+$).

### 2.3. Biblioteca Seleccionada: `scikit-learn`
Tal como recomienda la cátedra en la Diapositiva 387:
- **`scikit-learn`** es la biblioteca idónea para problemas tabulares y aprendizaje automático supervisado en ingeniería de software.
- Permite entrenar y serializar modelos ligeros (`RandomForestClassifier`, `RidgeClassifier`, `RandomForestRegressor`, `Ridge`) de forma **100% local**, sin requerir tarjetas gráficas (GPU) ni descargas de gigabytes de pesos en la nube.
- Garantiza compilación y ejecución determinista y reproducible en los runners de GitHub Actions (Ubuntu y Windows) sin timeouts.

---

## 3. El Enfrentamiento Algorítmico: Solución Convencional vs. Solución con IA

Fieles al espíritu de la materia y a la dualidad *Baseline vs. Optimizado*, el sistema implementará **dos estrategias intercambiables bajo la misma fachada (`PredictorDemanda`)**:

```
                          ┌─────────────────────────────────────┐
                          │     Fachada: PredictorDemanda       │
                          └──────────────────┬──────────────────┘
                                             │
                     ┌───────────────────────┴───────────────────────┐
                     ▼                                               ▼
     ┌───────────────────────────────┐               ┌───────────────────────────────┐
     │    Estrategia Convencional    │               │       Estrategia con IA       │
     │      (Heurística O(1))        │               │         (scikit-learn)        │
     ├───────────────────────────────┤               ├───────────────────────────────┤
     │ • Regla de Punto de Reorden   │               │ • Random Forest / Ridge       │
     │ • StockActual < μ + k·σ       │               │ • Pipeline con StandardScaler │
     │ • Latencia: ~15 a 50 ns       │               │ • Latencia: ~0.15 a 0.50 ms   │
     │ • Memoria extra: 0 MB         │               │ • Memoria extra: ~1.5 MB      │
     │ • Cero dependencias           │               │ • Multivariable no lineal     │
     └───────────────────────────────┘               └───────────────────────────────┘
```

### 3.1. Estrategia A — Solución Algorítmica Convencional ($O(1)$)
- **Mecanismo:** Heurística clásica de control de inventarios basada en punto de reorden determinista:
  $$\text{UmbralAlerta} = \mu_{\text{demanda}} + Z \cdot \sigma_{\text{demanda}}$$
  Donde $\mu$ y $\sigma$ se extraen en tiempo constante $O(1)$ desde el acumulador hash de frecuencias históricas.
- **Complejidad Temporal:** $O(1)$ por producto evaluado.
- **Latencia:** $\approx 15 \text{ a } 50 \text{ nanosegundos}$.
- **Consumo de Memoria:** $0 \text{ MB}$ de sobrecarga.
- **Cuándo es superior:** Para validaciones transaccionales en tiempo real durante el despacho a máxima velocidad en mono-hilo, donde cada microsegundo cuenta y la demanda es estable.

### 3.2. Estrategia B — Solución con Inteligencia Artificial (`scikit-learn`)
- **Mecanismo:** Pipeline de aprendizaje automático que extrae un vector de características multidimensional por producto:
  - Rotación histórica (cantidad de pedidos previos que incluyeron el SKU).
  - Varianza en el tamaño de lote solicitado.
  - Precio unitario y categoría del producto.
  - Stock actual remanente y relación stock / rotación.
  - Ratio de pedidos con falta de stock en el pasado reciente.
- **Complejidad Temporal:** $O(T \cdot d)$ donde $T$ es el número de árboles y $d$ la profundidad máxima.
- **Latencia:** $\approx 0.15 \text{ a } 0.50 \text{ milisegundos}$ ($\approx 10.000\times$ más lenta que la fórmula aritmética).
- **Consumo de Memoria:** $\approx 1.2 \text{ a } 2.5 \text{ MB}$ de memoria heap (medida con `tracemalloc`) para la estructura del modelo entrenado.
- **Cuándo es superior:** En la planificación estratégica de aprovisionamiento por lotes y en catálogos con demanda dinámica o correlacionada, donde la heurística simple sufre de subestimación de quiebres (*falsos negativos* costosos).

### 3.3. Estrategia Híbrida en Cascada (*Best Engineering Practice*)
El motor ofrecerá además un modo híbrido inteligente:
1. Filtro rápido $O(1)$: Si el stock actual supera ampliamente el umbral holgado (ej. $> 5\times$ la demanda máxima observada), se descarta riesgo en $\approx 20\text{ ns}$.
2. Inferencia focalizada con IA: Solo los productos que caen en la "zona de incertidumbre" se evalúan mediante el modelo de `scikit-learn`, reduciendo el tiempo global de cómputo en un $\approx 85\%$.

---

## 4. Enfoque 1: IA Aplicada al Ciclo de Vida del Software

Para satisfacer el requerimiento de *«utilizar asistentes de IA para generar pruebas, explicar código, detectar posibles errores y proponer optimizaciones, validando siempre sus resultados»*, se formalizarán cuatro ejes de evidencia:

1. **Generación de Pruebas Asistida:**
   - Creación de casos de prueba guiados por propiedades con `Hypothesis` (mencionada explícitamente en la Diapositiva 378 de la cátedra) para verificar invariantes del predictor (ej. la probabilidad estimada siempre $\in [0, 1]$, la demanda predicha $\ge 0$).
   - Generación de casos límite (*edge cases*): catálogo vacío, productos con varianza cero, lotes con un solo ítem.
2. **Detección Estática de Errores y Seguridad:**
   - Auditoría asistida de tipos estáticos (`mypy`) en el módulo de IA, garantizando firmas explícitas para arrays de NumPy y DataFrames sin comprometer la velocidad.
3. **Propuestas de Optimización vs. Validación Empírica Obligatoria:**
   - Se documentará formalmente el proceso científico de validación: toda propuesta generada por el asistente de IA (ej. vectorización masiva, poda de árboles en Random Forest, paralelismo de inferencia) se perfila con `cProfile`, `tracemalloc` y `pytest-benchmark`.
   - Se preservará el análisis autocrítico del caso del IPC en Windows como precedente metodológico donde la medición refutó la recomendación teórica del asistente.

---

## 5. Arquitectura del Software (Nuevo Subsistema `src/ia/`)

El nuevo subsistema de IA se integrará con alta cohesión y bajo acoplamiento respetando la arquitectura hexagonal del proyecto:

```text
src/
├── ia/
│   ├── __init__.py
│   ├── extractor_features.py       # Transforma Producto y Pedido en matrices de features
│   ├── modelos.py                  # Definición, entrenamiento y serialización de modelos scikit-learn
│   ├── predictor_demanda.py        # Fachada conmutadora (convencional vs ia vs hibrida)
│   └── metricas_ia.py              # Telemetría: tiempo de inferencia, memoria tracemalloc y métricas ML
├── motor/
│   └── motor_inventario.py         # Fachada que expone predecir_quiebres_stock()
└── ui/
    └── pantallas/
        └── prediccion_ia.py        # Nueva vista en Flet con comparador interactivo
```

---

## 6. Plan de Fases de Implementación (Proyecto Final)

Seguiremos la metodología de trabajo rigurosa y trazable consolidada en los parciales anteriores:

| Fase | Rama | Objetivo y Entregables Principales | Criterio de Cierre | Estado |
|---|---|---|---|:---:|
| **P4.0** | `final/f0-plan-y-organizacion-docs` | Elaboración del plan integral del proyecto final y reestructuración ordenada de `docs/` en `parcial-1/`, `parcial-2/`, `parcial-3/` y `final/`. | Documento aprobado, árbol ordenado, Sphinx compila con 0 warnings (`-W`). | ✅ Completado |
| **P4.1** | `final/f1-dataset-y-features` | Incorporación de `scikit-learn` a `pyproject.toml` y `uv.lock`. Implementación de `src/ia/extractor_features.py` con generación determinista de historiales sintéticos de demanda. | Generación reproducible de matrices de features con tipos verificados por Mypy. | ✅ Completado |
| **P4.2** | `final/f2-modelos-predictor` | Implementación de la heurística convencional ($O(1)$) y del modelo de `scikit-learn` en `src/ia/predictor_demanda.py`. Persistencia y carga del modelo. | Modelos entrenables y ejecutables localmente con precisión cuantificada. | ✅ Completado |
| **P4.3** | `final/f3-integracion-motor-tests` | Integración del predictor en `MotorInventario`. Creación de la suite de pruebas unitarias y de propiedades (`tests/ia/test_predictor_ia.py`). | 100% de tests pasando en pytest, cobertura de código $\ge 85\%$. | ⏳ Pendiente |
| **P4.4** | `final/f4-benchmarks-y-memoria` | Suite de benchmarking comparativo (latencia convencional vs IA vs híbrida) y test de presupuesto de memoria heap con `tracemalloc` (`test_presupuesto_memoria_ia.py`). | Tabla comparativa oficial completa, aserción de no regresión y memoria acotada. | ⏳ Pendiente |
| **P4.5** | `final/f5-interfaz-flet` | Construcción de la pantalla interactiva `PantallaPrediccionIA` en Flet con sliders de umbral, selector de estrategia, KPIs de tiempo/memoria y visualización de alertas. | Interfaz accesible, fluida y responsive integrada en la navegación principal. | ⏳ Pendiente |
| **P4.6** | `final/f6-docs-presentacion-cierre` | Documentación técnica en Sphinx (sección de IA en las 9 secciones), actualización de la presentación interactiva (`docs/presentation-final/`), merge a `main` y tag `final`. | CI en verde (Ubuntu/Windows), documentación publicada en Pages y release listo. | ⏳ Pendiente |

---

## 7. Matriz Comparativa Oficial de Rendimiento y Memoria (Estimación y Diseño de Ensayo)

Siguiendo el estándar de evaluación del proyecto, las mediciones empíricas completarán la siguiente tabla oficial para la defensa final:

| Estrategia de Predicción | Complejidad Big-O | Latencia Media (Inferencia) | Memoria Heap (`tracemalloc`) | Precisión / Acierto (F1 / MAE) | Justificación de Ingeniería |
|---|:---:|:---:|:---:|:---:|---|
| **1. Heurística Convencional** | $O(1)$ | $\approx 25 \text{ ns}$ | $< 0.01 \text{ MB}$ | Aceptable en demanda estable | Óptima para validación online masiva a alta velocidad. |
| **2. Modelo IA (`scikit-learn`)** | $O(T \cdot d)$ | $\approx 0.25 \text{ ms}$ | $\approx 1.50 \text{ MB}$ | Alta en demanda compleja | Justificada para compras y reabastecimiento estratégico. |
| **3. Estrategia Híbrida en Cascada** | $O(1)$ amort. | $\approx 0.04 \text{ ms}$ | $\approx 1.50 \text{ MB}$ | Idéntica a la IA | El mejor compromiso entre velocidad y poder predictivo. |

---

## 8. Guía de Ejecución y Reproducción Local del Módulo de IA

Una vez implementado, cualquier evaluador podrá reproducir los ensayos mediante la suite estándar de comandos:

```bash
# 1. Sincronizar el entorno con uv incluyendo scikit-learn
uv sync --locked --extra dev --extra docs

# 2. Entrenar y evaluar el modelo de IA localmente
python -m src.ia.entrenador

# 3. Ejecutar los tests unitarios y de propiedades del módulo de IA
pytest tests/ia/ -v

# 4. Verificar el presupuesto de memoria heap del modelo (tracemalloc)
pytest tests/ia/test_presupuesto_memoria_ia.py -v

# 5. Ejecutar la comparativa de latencia (convencional vs IA)
python -m benchmarks.comparar_ia

# 6. Lanzar la aplicación interactiva de escritorio
python main.py
```
