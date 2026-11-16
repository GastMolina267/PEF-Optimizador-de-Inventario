# Resumen del Proyecto Final: Inteligencia Artificial

**Materia:** Programación Eficiente — Opción 6 (Universidad Blas Pascal, 2026)  
**Equipo:** Edgar Karpowicz, Gastón Molina, Tomás Molina  
**Repositorio:** [github.com/GastMolina267/PEF-Optimizador-de-Inventario](https://github.com/GastMolina267/PEF-Optimizador-de-Inventario)  

---

## 💡 En Pocas Palabras (TL;DR)

> [!IMPORTANT]
> **¿Qué se hizo en este hito final?**
> Se implementó un **Predictor Inteligente de Demanda y Quiebre de Stock** para el centro de distribución, cumpliendo con el **doble enfoque de IA** exigido por la cátedra:
> 1. **IA aplicada al desarrollo:** Usamos asistentes de IA para diseñar pruebas con **Hypothesis**, auditar presupuestos de memoria heap con **tracemalloc** (descartando fugas en 200 iteraciones) y optimizar la vectorización de código.
> 2. **IA integrada en la aplicación:** Creamos el subsistema `src/ia/` con **`scikit-learn`** (regresión `Ridge` y `LogisticRegression`), y lo enfrentamos contra una **heurística matemática $O(1)$** y una **Cascada Híbrida**.

### El Resultado Clave en 3 Números

* ⚡ **La Heurística $O(1)$ es 23.3 veces más rápida:** Tarda **58 microsegundos** y consume 0 KB adicionales de heap. Es perfecta para el 80% de los productos con stock abundante.
* 🎯 **La IA pura aporta precisión en casos difíciles:** Tarda **1.36 milisegundos** y predice quiebres con un $F_1\text{-score}$ de **0.875**, detectando tendencias no lineales que la fórmula matemática no ve.
* 🚀 **La Cascada Híbrida une lo mejor de ambos mundos:** Filtra los productos seguros en $O(1)$ y solo activa la IA en productos en zona de riesgo. **Acelera la inferencia 5.2x** (>75% ahorro de tiempo) sin perder ninguna alerta.

---

## 1. ¿Qué Exigía la Cátedra y Cómo se Resolvió?

La consigna oficial (páginas 356+ de la presentación de la materia) requería dos ejes complementarios con justificación empírica:

```mermaid
flowchart TD
    Req["Consigna de la Cátedra (PEF 2026)"] --> Eje1["Eje 1: IA en el Desarrollo de Software"]
    Req --> Eje2["Eje 2: IA Integrada en la Aplicación"]

    Eje1 --> T1["Pruebas automáticas con Hypothesis"]
    Eje1 --> T2["Presupuesto heap tracemalloc (0 fugas)"]
    Eje1 --> T3["Refactorización y complejidad cognitiva <= 15"]

    Eje2 --> M1["Pipeline scikit-learn (Ridge + LogReg)"]
    Eje2 --> M2["Enfrentamiento empírico vs Heurística O(1)"]
    Eje2 --> M3["Nueva pantalla interactiva en Flet UI"]
```

| Requisito de Cátedra | ¿Cómo se implementó? | ¿Dónde está en el código? |
|---|---|---|
| **Generar pruebas con IA** | Pruebas de propiedades matemáticas con `Hypothesis` para verificar que las probabilidades nunca salgan de $[0.0, 1.0]$. | [tests/ia/test_predictor_ia.py](file:///c:/Users/edgar/OneDrive/Escritorio/UBP/PEF/Parcial/tests/ia/test_predictor_ia.py) |
| **Detectar errores y medir memoria** | Bucle de estrés de 200 iteraciones con `tracemalloc` comprobando retención nula de memoria ($\le 0.05\text{ KB/it}$). | [tests/ia/test_presupuesto_memoria_ia.py](file:///c:/Users/edgar/OneDrive/Escritorio/UBP/PEF/Parcial/tests/ia/test_presupuesto_memoria_ia.py) |
| **Integrar modelo de IA en el sistema** | Subsistema `src/ia/` con `scikit-learn` serializado en un archivo compacto de solo **2.6 KB** (`joblib`). | [src/ia/modelos.py](file:///c:/Users/edgar/OneDrive/Escritorio/UBP/PEF/Parcial/src/ia/modelos.py), [data/modelos/predictor_ia.joblib](file:///c:/Users/edgar/OneDrive/Escritorio/UBP/PEF/Parcial/data/modelos/predictor_ia.joblib) |
| **Evaluar el costo computacional** | Benchmark de 50 iteraciones midiendo tiempo en microsegundos y memoria heap pico por producto. | [benchmarks/comparar_ia.py](file:///c:/Users/edgar/OneDrive/Escritorio/UBP/PEF/Parcial/benchmarks/comparar_ia.py), [docs/mediciones/tabla_comparativa_ia.md](file:///c:/Users/edgar/OneDrive/Escritorio/UBP/PEF/Parcial/docs/mediciones/tabla_comparativa_ia.md) |
| **Justificar cuándo conviene usar IA** | Análisis formal de costo-beneficio: por qué no poner IA en todo y cómo la Cascada Híbrida optimiza el trade-off. | [docs/sphinx/secciones/04_diseno_tecnico.md](file:///c:/Users/edgar/OneDrive/Escritorio/UBP/PEF/Parcial/docs/sphinx/secciones/04_diseno_tecnico.md) |

---

## 2. ¿Cómo Funciona el Módulo de IA (`src/ia/`)?

El flujo de predicción sigue una arquitectura clara de 4 pasos:

1. **Extracción de Características (10 variables por producto):**  
   A partir de las ventas históricas y el stock actual, se computan 10 métricas clave: rotación total, frecuencia de compra, tamaño de lote ($\mu$), varianza ($\sigma^2$), stock remanente, precio, ratio stock/demanda, quiebres previos, tendencia temporal y días de cobertura ([src/ia/tipos.py](file:///c:/Users/edgar/OneDrive/Escritorio/UBP/PEF/Parcial/src/ia/tipos.py)).
2. **Predicción con Modelos Supervisados:**
   - **Demanda Proyectada:** Modelo lineal regularizado `Ridge` que predice cuántas unidades se venderán.
   - **Probabilidad de Quiebre:** Regresión logística calibrada `LogisticRegression` que calcula el porcentaje de riesgo $P(\text{quiebre}) \in [0\%, 100\%]$.
3. **Clasificación del Nivel de Riesgo:**
   - 🔴 **Crítico:** Stock insuficiente frente a la demanda esperada ($P > 60\%$).
   - 🟡 **Medio:** Demanda cercana al stock o alta volatilidad ($25\% \le P \le 60\%$).
   - 🟢 **Bajo:** Stock abundante que cubre con seguridad el período ($P < 25\%$).
4. **Conmutación de Estrategias ([src/ia/predictor_demanda.py](file:///c:/Users/edgar/OneDrive/Escritorio/UBP/PEF/Parcial/src/ia/predictor_demanda.py)):**  
   El motor permite cambiar en caliente entre la fórmula matemática clásica, la IA pura y la Cascada Híbrida.

---

## 3. Comparativa de Rendimiento: Los Números Reales

Las mediciones oficiales ejecutadas mediante `python benchmarks/comparar_ia.py` demostraron:

| Enfoque | ¿Cómo calcula? | Latencia por Producto | Memoria Heap Pico | Speedup vs IA | Precisión ($F_1$) | ¿Cuándo conviene usarlo? |
|---|---|---:|---:|:---:|:---:|---|
| **1. Heurística Convencional $O(1)$** | Fórmula analítica de punto de reorden ($\text{ROP}$) | **58.46 $\mu\text{s}$** | **15.2 KB** | **23.30x** | N/A | Cuando el stock sobra o se requiere procesar millones de transacciones por segundo. |
| **2. Modelo IA (`scikit-learn`)** | Pipeline supervisado con 10 variables | 1.361,91 $\mu\text{s}$ | 29.9 KB | **1.00x** | **0.875** | En productos de alto valor o con demanda estacional volátil. |
| **3. Cascada Híbrida (Recomendada)** | Filtro $O(1)$ + IA en frontera de riesgo | **263.92 $\mu\text{s}$** | **22.2 KB** | **5.16x** | **0.875** | **En producción.** Ahorra más del 75% del tiempo de cómputo sin perder ninguna alerta. |

> [!TIP]
> **La Lección de Ingeniería:**  
> La IA no reemplaza a los algoritmos eficientes; los complementa. Usar IA en el 100% del catálogo gasta 23 veces más CPU de forma innecesaria. La **arquitectura híbrida** resuelve este dilema filtrando lo obvio a velocidad $O(1)$ y reservando el cómputo de Machine Learning únicamente para los casos con riesgo real.

---

## 4. Calidad, Pruebas y Estado del Proyecto

El proyecto mantiene los estándares de calidad más exigentes del curso:

* 🧪 **234 pruebas pasando al 100%:** Incluye 31 pruebas unitarias y de estrés en `tests/ia/` y 5 pruebas de interfaz en `tests/ui/test_pantalla_ia.py`.
* 📊 **89.29% de Cobertura de Código:** Supera holgadamente el umbral de 85% fijado en el pipeline de CI.
* 🧠 **Complejidad Cognitiva $\le 15$:** Todas las funciones fueron validadas con `complexipy`.
* 🛡️ **Seguridad SAST Aprobada:** 0 vulnerabilidades en `bandit -r src/ -ll` y 0 secretos en `gitleaks`.
* 📖 **Documentación Técnica Sphinx:** Compilación limpia con 0 advertencias (`-W`) incorporando la especificación del módulo IA.
* 🟢 **CI/CD en GitHub Actions:** Todos los jobs en verde tanto en Linux (Ubuntu) como en Windows.

---

## 5. ¿Dónde se ve en la Interfaz Gráfica?

Al ejecutar `python main.py`, la aplicación de escritorio en **Flet** incluye la nueva sección **"Predicción IA"**:

1. **Dropdown de Estrategia:** Permite alternar en tiempo real entre Cascada Híbrida, Heurística $O(1)$ y Modelo IA.
2. **Tarjetas KPI Reactivas:** Muestran en vivo la latencia media en $\mu\text{s}$, el consumo de memoria heap en KB y las alertas de quiebre activas.
3. **Filtro de Riesgo:** Permite aislar rápidamente los productos con riesgo crítico para reposición urgente.
4. **Botón de Re-entrenamiento:** Permite reajustar los modelos de `scikit-learn` directamente desde la interfaz con los datos activos.

---

## 6. Guía Rápida para Probarlo

```bash
# 1. Instalar dependencias (incluye scikit-learn y joblib)
pip install -r requirements.txt

# 2. Ejecutar la comparativa de velocidad (Heurística vs IA vs Híbrida)
python benchmarks/comparar_ia.py

# 3. Correr las pruebas del módulo de IA
pytest tests/ia/ -v

# 4. Lanzar la aplicación interactiva
python main.py
```
