# Guía de exposición: Proyecto Final (Opción 6, IA)

Apuntes para estudiar la defensa oral de [docs/presentation-final/](../presentation-final/index.html). Para cada bulto (B-01 a B-11) hay: **la idea**, **qué decir**, **cifras a memorizar** y **preguntas probables**. Las cifras salen de `contenido.js` (mediciones del 18/11/2026).

---

## Resumen en 30 segundos

> Agregamos al optimizador de inventario un **predictor de quiebre de stock**. Lo resolvimos de tres formas: una **regla O(1)** (punto de reorden), un **modelo de scikit-learn** (Ridge + regresión logística sobre 10 datos por producto) y una **cascada híbrida** que corre siempre la regla y solo enciende el modelo en la zona dudosa. Medimos: la regla es ~480× más rápida que el modelo; la cascada es ~7× más rápida que usar el modelo en todo y no pierde alertas fuertes. **Conclusión:** la IA no reemplaza al algoritmo eficiente, lo usa como filtro y trabaja solo donde hay duda.

## Hilo conductor

1. **Consigna** (B-01) → 2. **Problema** y solución clásica (B-02) → 3. **Datos** (B-03) → 4. **Modelo** (B-04) → 5. **Cascada** (B-05) → 6. **Costo** (B-06) → 7. **Cuándo conviene IA** (B-07) → 8. **IA en el desarrollo** (B-08) → 9. **Calidad** (B-09) → 10. **Demo** (B-10) → 11. **Autocrítica** (B-11).

La pregunta que atraviesa toda la defensa (lámina 400 de la consigna): **¿cuándo aporta la IA y cuándo alcanza una solución convencional más simple, rápida, barata o confiable?**

## Machete de cifras

| Qué | Valor |
|---|---|
| Regla O(1), timeit | **0,47 µs** por producto |
| Modelo, timeit | **226 µs** (~**480×** la regla) |
| Cascada, timeit | **30 µs** (~**7×** más rápida que el modelo puro) |
| Regla / cascada / modelo con tracemalloc (tabla oficial) | 58 / 264 / 1.362 µs (regla "solo" 23×) |
| Demo (30 productos) | **26** por carril rápido, **4** al modelo |
| Dataset mediano (1.000) | **915** rápido, **85** al modelo |
| Alertas en la demo (regla / modelo / cascada) | **4 / 4 / 4** |
| Avisos de riesgo medio (regla / modelo / cascada) | **0 / 5 / 1** |
| Modelo: F1 ponderado · precisión · recall | **0,87 · 0,89 · 0,87** (112 muestras de prueba) |
| Regresor: R² · MAE | **0,12 · 10,6 u** (explica poco) |
| Archivo del modelo | **2.673 bytes** (2,6 KB) |
| Memoria pico (regla / cascada / modelo) | 15,2 / 22,2 / 29,9 KB |
| Fugas | 200 inferencias, **< 128 KB** retenidos |
| Tests · cobertura | **235** pasan en 49 s · **89 %** (umbral 85 %) |
| Tests nuevos | **37** (31 en `tests/ia/` + 6 de UI) |
| Umbrales de riesgo (código) | alerta ≥ **0,50** · medio ≥ **0,40** · crítico ≥ **0,70** |

---

## B-01 · Orden de trabajo: qué pide el Final

**La idea:** la consigna tiene dos enfoques de IA y un criterio de evaluación central.

**Qué decir:**
- **Enfoque 1, IA en el desarrollo:** asistentes para generar pruebas, explicar código, detectar errores y optimizar, *validando siempre lo que proponen* (→ B-08).
- **Enfoque 2, IA en la aplicación:** una biblioteca o modelo que resuelva una funcionalidad concreta, *midiendo su costo* (→ B-03 a B-06).
- Lo que más pesa (lámina 400): **justificar cuándo conviene la IA y cuándo alcanza un algoritmo convencional**. Toda la defensa responde esto.
- Nuestra funcionalidad: **predecir quiebres de stock** con scikit-learn (la biblioteca que recomienda la lámina 387).
- Método: 7 fases (P4.0 a P4.6), una rama por fase (`final/f0…f6`) y merge a `main`, igual que en los parciales.

**Preguntas probables:** ¿Por qué scikit-learn y no una red neuronal? → Es lo recomendado para empezar, corre en local, sin GPU, y modelos lineales alcanzan para 10 datos tabulares.

---

## B-02 · El problema: el quiebre de stock

**La idea:** hasta el P3 el sistema respondía sobre el presente (cuánto hay, dónde). Ahora debe anticipar el futuro: ¿se va a terminar?

**Qué decir:**
- El aviso sirve si llega **cuando el stock cruza el punto de reorden (ROP)**, no cuando ya está en cero.
- La solución clásica, sin IA, es `evaluar_heuristica_convencional()` en `src/ia/modelos.py`:
  - `demanda = μ_lote × máx(0,2; tendencia)` → cuánto se espera vender.
  - `seguridad = 1,5 × √σ²_lote` → colchón por variabilidad (si σ² = 0, usa 0,5 × demanda).
  - `ROP = demanda + seguridad` → si el stock baja de acá, alerta.
- Bandas: stock 0 → 100 %; no cubre la demanda → 75–95 %; bajo el ROP → 40–70 %; sobre el ROP → ≤ 30 % (sin alerta).
- Sin historial de pedidos → demanda 0, no alerta.
- **Fortaleza:** O(1) y explicable en una línea. **Límite:** fórmula fija, usa 3 de los 10 datos y no aprende. Esa es la puerta para probar un modelo.

**Preguntas probables:** ¿Por qué es O(1)? → Son operaciones aritméticas sobre valores ya calculados; no recorre nada. ¿Por qué el `máx(0,2; tendencia)`? → Para que una tendencia a la baja no anule la demanda.

---

## B-03 · La etiqueta: 10 datos por producto

**La idea:** scikit-learn no lee objetos `Producto`; `ExtractorFeatures` resume cada SKU en un `FeatureVector` de 10 números.

**Los 10 datos (F1–F10):** rotación histórica, frecuencia de pedidos, **lote medio (μ)**, **varianza del lote (σ²)**, stock actual, precio, ratio stock/(rotación+1), tasa de quiebre reciente, **tendencia** (mitad reciente ÷ mitad antigua), días de cobertura (stock ÷ lote; 999 si no hay consumo). Los tres en negrita son los que usa la regla.

**Qué decir (mostrar en vivo):**
- **Taladro:** 1 pedido, stock 15 → la regla dice Bajo, el modelo Medio (43 %), influido por el precio alto.
- **Sierra caladora:** stock 0 → ambos Crítico y alerta.
- **Amoladora:** nunca se pidió → la regla dice demanda 0 (Bajo); el modelo proyecta 14,5 u (Medio) por lo que aprendió del historial sintético. **Sin datos, ninguno puede saberlo** (vuelve en B-07).
- Extraer los 10 datos cuesta ~2,4 µs y crece con el historial (recorre los pedidos).

**Preguntas probables:** ¿Por qué `+1` en el ratio? → Evita dividir por cero. ¿Por qué 999 de cobertura? → Valor centinela para "sin consumo".

---

## B-04 · Cómo aprende: dos modelos lineales chicos

**La idea:** un regresor para la demanda y un clasificador para la probabilidad de quiebre, entrenados en local.

**Qué decir:**
- El JSON es una foto sin historial temporal, así que `GeneradorHistorialSintetico` **simula ciclos de pedidos** (distribución **Pareto**, `seed=42`) sobre el catálogo real.
- **Sin fuga de futuro:** las features se calculan con ciclos anteriores y la etiqueta evalúa el ciclo siguiente. Corte **cronológico 75/25**.
- Dos pipelines: `StandardScaler → Ridge(α=1)` (demanda) y `StandardScaler → LogisticRegression(C=1, max_iter=300)` (P(quiebre), alerta ≥ 50 %).
- **¿Por qué StandardScaler?** El precio está en miles y la tasa de quiebre en 0–1; escalar evita que las magnitudes grandes dominen los pesos.
- Se guarda en `predictor_ia.joblib` (2,6 KB), se carga al iniciar; "Re-entrenar" reajusta en memoria.
- **Honestidad con las métricas:** el clasificador funciona (F1 0,87); el regresor explica poco (R² 0,12). **Las alertas dependen solo de la probabilidad**, no de la demanda estimada.

**Preguntas probables:** ¿Por qué corte cronológico y no aleatorio? → Un corte aleatorio mezcla futuro en el entrenamiento y infla las métricas. ¿Qué es Ridge? → Regresión lineal con penalización L2 que reduce el sobreajuste. ¿Por qué modelos lineales? → Predicción = un producto escalar: costo fijo, sin GPU, archivo mínimo.

---

## B-05 · El desviador: la cascada híbrida (escena central)

**La idea:** la regla decide a qué productos mirar con el modelo.

**Qué decir:**
- Regla del desviador (`_resolver_estrategia()`, rama `HIBRIDA`, `predictor_demanda.py:110-133`): si **stock ≥ máx(10, 3 × demanda de la regla)**, el producto sigue por el carril rápido; si no, va al modelo.
- Mostrar en este orden:
  1. **Cascada:** de 30 productos, **26** carril rápido y **4** al modelo.
  2. **Solo modelo:** los 30 van al operario y **se forma cola**. Esa cola es el costo de poner IA en todo.
  3. **Regla O(1):** no hay cola, pero tampoco avisos de riesgo medio.
- Las **alertas fuertes coinciden** en las tres (4, 4 y 4). Lo que cambia son los **avisos medios**: modelo 5, cascada 1, regla 0.
- El contador usa los µs medidos sin tracemalloc.

**Preguntas probables:** ¿Por qué `máx(10, …)`? → Piso mínimo para que un producto de demanda muy baja con poco stock no pase como "seguro". ¿La cascada pierde algo? → No pierde alertas, pero sí 4 de los 5 avisos de riesgo medio (decirlo con las dos cifras).

---

## B-06 · Balanza y cronómetro: el costo de cada estrategia

**La idea:** el instrumento con el que medís también pesa.

**Qué decir:**
- **Dos mediciones del mismo código:**
  - Tabla oficial (`benchmarks/comparar_ia.py`) con **tracemalloc** encendido para registrar memoria: regla 58 µs, cascada 264 µs, modelo 1.362 µs.
  - Con **timeit** (mejor de 5, sin tracemalloc): regla **0,47 µs**, cascada **30 µs**, modelo **226 µs**.
- Casi todo lo que medía la regla era el costo de medir (~50 µs por llamada de tracemalloc).
- **Lección de eficiencia:** tiempo y memoria se miden en corridas separadas.
- Con medición limpia: el modelo cuesta **~480×** la regla y la cascada es **~7×** más rápida que el modelo puro. Con 1.000 productos la proporción se mantiene.
- Memoria: modelo 2.673 bytes en disco; pico 15 / 22 / 30 KB; 200 inferencias retienen < 128 KB (sin fugas).
- Variabilidad entre corridas: 5–15 %.

**Preguntas probables:** ¿Para qué sirve tracemalloc? → Rastrea el heap de Python para medir el pico de memoria y detectar fugas; intercepta cada reserva y por eso suma tiempo. ¿Por qué el gráfico es logarítmico? → Las cifras van de 0,5 a más de 1.000 µs.

---

## B-07 · ¿Cuándo conviene la IA y cuándo alcanza la regla?

**La idea:** es la pregunta que más pesa, y la respuesta está escrita en el código, no en una opinión.

**Qué decir (los 3 pasos):**
1. **Calcular la regla siempre:** cuesta 0,47 µs.
2. **¿Stock ≥ máx(10, 3 × demanda)?** Si sobra stock, no hay nada que predecir: responde la regla (26/30 en la demo, 915/1.000 en el mediano).
3. **Zona dudosa → modelo:** stock cerca de la demanda, donde combinar los 10 datos cambia la decisión (4/30; 85/1.000).

| Alcanza la regla | Conviene el modelo |
|---|---|
| Tiempo real o miles de productos | Stock cerca de la demanda esperada |
| Stock con holgura | Demanda variable, la fórmula fija se equivoca |
| Sin historial del producto | Un quiebre cuesta caro (alto valor) |
| Hay que explicar la decisión en una línea | Hay historial suficiente para aprender |

- **Caso borde (limitación conocida):** un producto sin pedidos y con < 10 unidades cae en la zona dudosa, y el modelo responde con lo aprendido del historial sintético. Mejora propuesta: mandarlos siempre a la regla.
- **Frase de cierre:** *"La IA no reemplaza al algoritmo eficiente: lo usa como filtro y trabaja solo donde hay duda."*

---

## B-08 · Los auxiliares: IA en el desarrollo, verificada

**La idea:** el enfoque 1 dice "validando siempre sus resultados". Esta lámina es eso.

**Para qué usamos asistentes:**
- Pruebas por propiedades con **Hypothesis** (stock 0–5.000, datos aleatorios): la probabilidad nunca sale de [0, 1].
- **Presupuesto de memoria:** 200 inferencias con tracemalloc, < 128 KB retenidos.
- Explicar y documentar la API de `src/ia/` en Sphinx.
- Refactor guiado: complejidad cognitiva ≤ 15 (complexipy).

**Los 5 hallazgos al validar (memorizar):**
1. "La regla tarda 58 µs" → sin tracemalloc son 0,47 µs. Medir tiempo y memoria por separado.
2. "Latencia sub-microsegundo" en la misma tabla → contradice la fila anterior. Una sola fuente por cifra.
3. "F1 = 0,875" → es **F1 ponderado**: con 1.000 productos da 0,996 aunque el modelo **no marca ninguna alerta** (la regla marca 29), porque casi todos son "sin quiebre". Reportar F1 de la clase quiebre.
4. "La cascada no pierde alertas" → cierto (4 = 4), pero de 5 avisos medios quedan 1. Decirlo con las dos cifras.
5. Umbrales 60 % / 25 % en el resumen → el código usa **0,70 y 0,40** (`predictor_demanda.py:31-32`).

**Frase:** *"El asistente escribe rápido. La medición decide qué queda."*

**Preguntas probables:** ¿Qué es un test por propiedades? → En vez de casos fijos, Hypothesis genera cientos de entradas aleatorias y verifica que una invariante se cumpla siempre. ¿Por qué engaña el F1 ponderado? → Pondera por cantidad de muestras de cada clase; si la clase "sin quiebre" domina, tapa el mal desempeño en la clase que importa.

---

## B-09 · La caja sigue pasando la aduana

**La idea:** sumar IA no rompió nada; el mismo pipeline de 7 etapas del P3 lo controla en cada push.

**Qué decir:**
- **235 tests** pasan (49 s, Windows), **89 %** de cobertura (umbral 85 %), **37 tests nuevos**.
- Archivos nuevos: `test_extractor_features.py` (11), `test_predictor_ia.py` (11, incluye Hypothesis), `test_integracion_motor_ia.py` (5), `test_presupuesto_memoria_ia.py` (4), `test_pantalla_ia.py` (6).
- `scikit-learn` y `joblib` declarados en `pyproject.toml` y `requirements.txt`, vigilados por **pip-audit** y **Dependabot** (que ya abrió una rama para actualizar joblib).
- mypy ignora los tipos faltantes de sklearn/joblib; el código propio sigue tipado.
- El test de speedup exige que la regla sea **al menos 3×** más rápida que el modelo en cada corrida de CI.
- Otros gates: Ruff, Mypy, Complexipy (≤ 15), Bandit, gitleaks, deploy de docs solo desde `main`.

---

## B-10 · Demo en vivo: pantalla "Predicción IA"

**Guion (no improvisar):**
1. `python main.py` → **Predicción IA**.
2. **Cascada híbrida:** mirar latencia media, memoria y alertas.
3. **Modelo IA:** comparar latencia y riesgos.
4. **Heurística O(1):** la latencia cae a casi cero.
5. Filtrar **Crítico**: qué reponer primero.
6. **Re-entrenar Modelo:** se ajusta con el catálogo cargado.

**Plan B:** si la app falla, la tabla de la lámina tiene los mismos resultados; en terminal, `pytest tests/ia -v` y `python benchmarks/comparar_ia.py`.

---

## B-11 · Conclusiones y autocrítica

| Lo que rindió | Lo que no salió | Qué haríamos distinto |
|---|---|---|
| Cascada: 26/30 sin tocar el modelo | Historial **sintético**, sin ventas reales | Entrenar con historial real |
| Integración limpia: 235 tests, 89 % | Regresor con R² 0,12 | Reportar precisión/recall de la clase quiebre |
| Modelo de 2,6 KB, local | F1 ponderado engañoso (0 alertas en 1.000) | Productos sin historial → siempre a la regla |
| | Medimos tiempo con tracemalloc encendido | Comparar con XGBoost y exportar a ONNX (láminas 391–392) |

**Frase final:** *"Cuatro hitos con la misma caja: primero rápido, después mantenible, después controlado y al final, anticipando. La IA llegó al final porque necesitaba todo lo anterior para medirse."* Después, presionar **P** para "entregar la caja".

---

## Preguntas difíciles que conviene tener preparadas

- **"Si el regresor explica tan poco, ¿para qué está?"** → Las alertas dependen solo del clasificador; la demanda estimada es informativa. Es una limitación que reconocemos y atribuimos al historial sintético.
- **"¿Sus métricas valen algo con datos sintéticos?"** → Validan que el pipeline funciona y sirven para comparar costo, no para afirmar precisión en producción. Por eso el primer "haríamos distinto" es usar datos reales.
- **"¿Por qué no usar el modelo en todo si es más fino?"** → Cuesta ~480× más por producto y en el 87 % de la demo (26/30) el stock sobra: no hay nada que predecir.
- **"¿Cómo saben que no hay fugas de memoria?"** → Test de 200 inferencias seguidas con tracemalloc: después del GC quedan < 128 KB retenidos.
- **"¿Qué parte hizo la IA y qué parte ustedes?"** → Los asistentes propusieron pruebas, documentación y refactors; nosotros medimos y validamos, y eso detectó los 5 hallazgos de B-08.

> **Ojo:** `resumen-proyecto-final.md` todavía repite algunas cifras corregidas en B-08 (234 tests, F1 0,875 sin aclarar que es ponderado, umbrales 60 % / 25 %). En la defensa usar las cifras de esta guía.
