# Guía de exposición: Proyecto Final (Opción 6, IA)

Apuntes para estudiar la defensa oral de [docs/presentation-final/](../presentation-final/index.html). Está organizada en el mismo orden en que se presenta:

1. **Resumen del proyecto**: qué hay que tener claro antes de entrar.
2. **La animación del robot**: portada y 4 maniobras, mesa, entrega y sello.
3. **Las 11 láminas (B-01 a B-11)**: guion hablado, puntos clave, cifras y preguntas probables.
4. **Machete de cifras y preguntas difíciles.**

Las cifras salen de `contenido.js`, `datos.js` y las mediciones del 18/11/2026.

---

## 1. Resumen del proyecto

### En 30 segundos

> Agregamos al optimizador de inventario un **predictor de quiebre de stock**. Lo resolvimos de tres formas: una **regla O(1)** (punto de reorden), un **modelo de scikit-learn** (Ridge + regresión logística sobre 10 datos por producto) y una **cascada híbrida** que corre siempre la regla y enciende el modelo solo en la zona dudosa. Medimos: la regla es ~480× más rápida que el modelo; la cascada es ~7× más rápida que usar el modelo en todo y no pierde alertas fuertes. **Conclusión:** la IA no reemplaza al algoritmo eficiente, lo usa como filtro y trabaja solo donde hay duda.

### Versión ampliada (para entender el proyecto entero)

**De dónde venimos.** El sistema es el optimizador de inventario de un centro de distribución que construimos en los tres parciales. En el **P1** lo hicimos rápido (catálogo con búsqueda O(1) por hash, 718× más rápido que la búsqueda lineal). En el **P2** lo hicimos mantenible (Quality Gate, 193 tests, complejidad acotada). En el **P3** lo hicimos controlado (pipeline de CI de 7 etapas que revisa cada push). Hasta ahí el sistema respondía preguntas sobre el **presente**: cuánto stock hay, dónde está, qué alternativa ofrecer.

**Qué pedía el Final.** Dos enfoques de IA: usarla **en el desarrollo** (asistentes que generan pruebas, explican y optimizan, validando lo que proponen) e integrarla **en la aplicación** (un modelo que resuelva algo concreto, midiendo su costo). Lo que más pesa en la evaluación: **justificar cuándo conviene la IA y cuándo alcanza un algoritmo convencional**.

**El problema elegido.** Anticipar el **quiebre de stock**: avisar cuándo un producto se va a quedar sin unidades, antes de que pase. El aviso sirve si llega cuando el stock cruza el punto de reorden, no cuando ya está en cero.

**Las tres estrategias.**
- **Regla convencional O(1)** (`evaluar_heuristica_convencional`): fórmula de punto de reorden, `ROP = demanda + seguridad`. Es instantánea y explicable, pero fija: usa 3 de los 10 datos y no aprende.
- **Modelo de IA** (`ModeloPredictorIA`): cada producto se resume en **10 datos** (`ExtractorFeatures`). Dos pipelines de scikit-learn: `StandardScaler → Ridge` estima la demanda y `StandardScaler → LogisticRegression` estima la probabilidad de quiebre. Como no hay historial real, se entrena con **historial sintético** (Pareto, semilla 42) y corte cronológico 75/25. Pesa 2,6 KB y corre en local.
- **Cascada híbrida** (`_resolver_estrategia`, rama `HIBRIDA`): corre la regla siempre; si `stock ≥ máx(10, 3 × demanda)` hay holgura y responde la regla; si no, enciende el modelo. En la demo, 26 de 30 productos se resuelven sin el modelo.

**Lo que medimos.** Sin el instrumento de memoria (timeit): regla **0,47 µs**, cascada **30 µs**, modelo **226 µs** por producto. Con tracemalloc encendido los números se inflan (regla 58 µs), lo cual nos enseñó a **medir tiempo y memoria por separado**. Las 4 alertas fuertes de la demo coinciden en las tres estrategias; lo que cambia son los avisos de riesgo medio (modelo 5, cascada 1, regla 0).

**IA en el desarrollo.** Los asistentes generaron pruebas por propiedades (Hypothesis), el test de fugas de memoria, documentación y refactors. Al volver a medir todo encontramos **5 afirmaciones que no se sostenían**: la más importante, un F1 ponderado de 0,996 en un modelo que no marcaba ninguna alerta.

**Calidad.** El módulo entró por la misma aduana del P3: **235 tests**, **89 %** de cobertura, 37 tests nuevos, dependencias vigiladas por pip-audit y Dependabot.

**Autocrítica.** Datos sintéticos, regresor débil (R² 0,12), métrica engañosa y medición contaminada. Lo próximo sería entrenar con datos reales, reportar métricas por clase, mandar a la regla los productos sin historial y comparar con XGBoost/ONNX.

**El mensaje de fondo.** *Primero rápido, después mantenible, después controlado y al final, anticipando.* La IA llegó al final porque necesitaba todo lo anterior para medirse.

### Hilo conductor de las láminas

Consigna (B-01) → problema y regla clásica (B-02) → datos (B-03) → modelo (B-04) → cascada (B-05) → costo (B-06) → cuándo conviene la IA (B-07) → IA en el desarrollo (B-08) → calidad (B-09) → demo (B-10) → autocrítica (B-11).

---

## 2. La animación del robot

**Metáfora general:** la **caja** es nuestro sistema, despachado a `main` en el P3. El **brazo robótico PRD-01** es el personaje nuevo: representa el **módulo `src/ia/`**. El muelle es el centro de distribución donde el sistema llega a destino. Cada parte de la animación corresponde a algo real del código. Al hablar, decí siempre **qué pasa en pantalla y qué significa en el código**.

**Controles:**

| Tecla | Acción |
|---|---|
| `Enter` | Completa la maniobra en curso en automático (plan B si nadie la hace a mano) |
| `S` | Salta a la mesa |
| `→` / `Espacio` | Siguiente bulto o lámina |
| `←` | Lámina anterior |
| `Esc` | Vuelve a la mesa |
| `P` | Entregar la caja |
| `R` | Vuelve a la mesa desde el final (para preguntas) |
| `N` | Notas del orador |
| `T` | Cronómetro |
| `F` | Pantalla completa |
| `M` | Animaciones on/off |
| `A` | Sonido |
| `H` | Ayuda |

### Portada: el muelle a oscuras

- **En pantalla:** el muelle está apagado y el operario PRD-01 duerme (ojo apagado).
- **Qué decir:** *"Arrancamos donde terminó el Parcial 3: la caja pasó la aduana y quedó en `main`. Hoy llega a su destino, el centro de distribución para el que construimos el sistema."*
- **Acción:** `Enter` o el botón «Encender el muelle».

### Maniobra 1: «La caja llega al muelle»

- **En pantalla:**
  - Se prenden las luces y el robot se despierta.
  - En la consola aparece:
    - `MotorInventario() → PredictorDemanda()`
    - `cargando data/modelos/predictor_ia.joblib · 2.673 B`
    - `regresor: StandardScaler → Ridge(alpha=1.0)`
    - `clasificador: StandardScaler → LogisticRegression(C=1.0)`
    - `listo · estrategia por defecto: HIBRIDA`
  - Después alguien **arrastra el portón hacia arriba** con el mouse y la caja entra por la cinta.
- **Qué significa:** la consola muestra lo que pasa de verdad al crear `MotorInventario`. Instancia `PredictorDemanda` y carga el `.joblib` con los dos modelos (`_cargar_modelo_ia_si_existe()`). La estrategia por defecto es la cascada.
- **Qué decir:** *"El brazo es lo nuevo del Final: es el módulo de IA. Cuando arranca el motor, carga un modelo entrenado que pesa 2,6 KB, con un regresor y un clasificador, y queda en modo híbrido. La caja que entra es el sistema de los tres parciales."*
- **Tip:** invitá a alguien del tribunal a abrir el portón. Engancha desde el principio.

### Maniobra 2: «Antes de tocarla, lee el historial»

- **En pantalla:** el escáner del robot **sigue el mouse**. Hay que apuntar a las **tres guías** pegadas en la caja. Cada guía escaneada proyecta un holograma:
  - **P1 · Empaque:** búsqueda O(1) por hash, 718,3× más rápida.
  - **P2 · Auditoría:** 193 tests, cobertura 90 %, Quality Gate CC ≤ 12.
  - **P3 · Aduana CI:** 7 etapas, 15 controles, canal verde 7/7.

  Al completar las tres aparece «historial completo · 3/3 → se acepta la entrega».
- **Qué significa:** es la metáfora del **extractor de features** (`ExtractorFeatures.extraer_vector()`). El operario no decide solo con la foto de hoy (el stock actual): mira el **historial** y lo resume en 10 datos.
- **Qué decir:** *"Antes de tocar un producto, el modelo lee su historial. Acá el historial son nuestros tres parciales. Con cada producto del catálogo hace lo mismo con sus pedidos, y lo resume en 10 números. Los vamos a ver con productos reales en el bulto 03."*

### Maniobra 3: «La IA mueve la caja, no la reemplaza»

- **En pantalla:** hay que llevar la **ventosa** sobre la tapa y hacer clic para agarrarla (consola: `ventosa: ON · 1 bulto · 12,4 kg`). Después se lleva hasta la mesa de inspección (aparece una silueta celeste) y otro clic la apoya (`ventosa: OFF · caja en la mesa`). El robot se desplaza solo por el riel.
- **Qué significa:** la IA es **una capa más dentro de `MotorInventario`**, con dos métodos nuevos: `predecir_quiebres_stock()` y `entrenar_modelo_ia()`. Lo de adentro sigue siendo lo de los parciales: catálogo hash O(1), streaming, CI.
- **Qué decir:** *"La IA no reemplazó lo que ya teníamos: se apoya en eso. Usa el catálogo O(1) del Parcial 1 y pasa por todo el control de calidad. Y si el modelo no carga, el motor vuelve a la regla convencional."*

### Maniobra 4: «La abrimos por última vez»

- **En pantalla:** hay que **mantener apretado** sobre el punto naranja y seguir la cinta del Quality Gate con el **láser**. Una barra muestra el progreso. Al terminar, la caja se abre de golpe y salen **11 bultos** volando, que quedan flotando sobre la mesa.
- **Qué significa:** cada bulto es una lámina con su archivo de evidencia, y corresponde a las fases P4.0 a P4.6 del plan.
- **Qué decir:** *"Cortamos la cinta como con el cúter del Parcial 2. Adentro hay 11 bultos: el problema, el modelo, la cascada, las mediciones, lo que validamos y las conclusiones."* Con `Enter` («Ir a la mesa») se pasa a la mesa.

### La mesa de inspección (hub)

- **En pantalla:** los 11 bultos sobre la mesa. Al elegir uno (clic, `→` o `Espacio`), el robot **lo alcanza con la ventosa y lo acerca a cámara**, y se abre la lámina.
- **Cómo moverse:**
  - Dentro de las láminas, `→` y `←` recorren en orden.
  - `Esc` siempre vuelve a la mesa.
  - Desde la última lámina, `→` entrega la caja.
- **Qué decir:** poco. Es solo la transición. Si alguien pregunta algo puntual, desde la mesa se salta directo al bulto que corresponda.

### Entrega (`P` o `→` después de B-11)

- **En pantalla:**
  1. El robot guarda los bultos en la caja y le pega la **guía final** (destino: estante E-12).
  2. La lleva por el riel y la apoya en el estante.
  3. Después la **evalúa como a cualquier producto del catálogo**. Un láser la recorre y aparece la tarjeta:
     - `evaluar_producto(caja PEF-2026, CONVENCIONAL)`
     - `pedidos en el historial: 0`
     - `→ demanda proyectada: 0 u`
     - `→ P(quiebre) = 0,0 %`
     - `riesgo BAJO · regla O(1)`
     - `modelo: no hizo falta encenderlo`

     Estado final: **ENTREGADO**, y el robot saluda.
- **Qué significa:** es un **resumen de toda la defensa en un solo ejemplo**. Hay un caso sin historial y con holgura, y la regla O(1) alcanza: no hace falta gastar el modelo.
- **Qué decir:** *"Hasta la entrega la decidimos como decide el sistema. La caja no tiene historial de pedidos, así que la regla la resuelve en tiempo constante y el modelo ni se enciende. Ese es el criterio que defendimos toda la presentación."*

### Sello del tribunal y cierre

- **En pantalla:** botón **PUNTUAR**. El tribunal elige una nota del 1 al 10 y la sella.
  - Un **láser graba** la nota y después los nombres del equipo en la caja, en primer plano: «Entrega final · PEF 2026», los tres nombres y «fin del recorrido · P1 → P2 → P3 → Final».
  - El operario se apaga (`apagando operario PRD-01…`), se van las luces y queda un foco sobre la caja.
  - Al final aparece el **destino**: el recorrido completo P1 → P2 → P3 → `main` → estante, con las notas de cada hito.
- **Qué decir:** agradecer y ofrecerse a responder preguntas. `R` vuelve a la mesa para ir a cualquier bulto.

---

## 3. Las 11 láminas

Formato de cada una:
- **Guion:** lo que se dice en voz alta, en ~1 minuto. No hace falta memorizarlo palabra por palabra, pero sí el orden de las ideas.
- **Puntos clave:** lo que no puede faltar.
- **Transición:** la frase que conecta con la lámina siguiente.

### B-01 · Orden de trabajo: qué pide el Final

**Guion:**
> "La consigna del Final tiene dos enfoques. El primero es usar IA **en el desarrollo**: asistentes que generan pruebas, explican código y proponen optimizaciones, con una condición que la cátedra subraya: *validando siempre sus resultados*. El segundo es integrar IA **dentro de la aplicación**: una biblioteca o modelo que resuelva una funcionalidad concreta, midiendo su costo computacional.
>
> Pero lo que más pesa está en esta cita de la lámina 400: se valora *justificar cuándo la IA aporta beneficios y cuándo una solución convencional es más simple, rápida, económica o confiable*. Toda nuestra defensa responde esa pregunta.
>
> Nuestra funcionalidad concreta es **predecir quiebres de stock** con scikit-learn, la biblioteca que recomienda la lámina 387. Trabajamos en 7 fases, de P4.0 a P4.6, con una rama por fase y merge a `main`, igual que en los parciales."

**Puntos clave:**
- Los dos enfoques, y a qué bulto lleva cada uno: el 1 a B-08; el 2 a B-03 y B-06.
- La cita de la lámina 400 como eje de la defensa.
- Las fases, que se van tildando en la tabla:
  - **P4.0:** plan.
  - **P4.1:** scikit-learn y extractor.
  - **P4.2:** regla, pipeline y predictor.
  - **P4.3:** integración en el motor.
  - **P4.4:** benchmark.
  - **P4.5:** pantalla Flet.
  - **P4.6:** Sphinx y cierre.

**Transición:** *"Primero, el problema que elegimos resolver."*

**Preguntas probables:** ¿Por qué scikit-learn y no una red neuronal? → Es lo recomendado para empezar, corre en local y sin GPU, y para 10 datos tabulares un modelo lineal alcanza y es medible.

### B-02 · El problema: el quiebre de stock

**Guion:**
> "Hasta el Parcial 3 el sistema contestaba rápido sobre el presente: cuánto stock hay, dónde está, qué alternativa ofrecer. El Final agrega una pregunta sobre el futuro: **¿se va a terminar?**
>
> En el esquema, el stock baja con cada pedido. El aviso sirve si llega cuando cruza el **punto de reorden**, porque ahí todavía hay tiempo de reponer. Si llega cuando el stock ya está en cero, es tarde: hay pedidos sin atender.
>
> La respuesta clásica, sin IA, es esta fórmula. Primero estima la **demanda**: el lote medio, ajustado por la tendencia. Después suma un **colchón de seguridad**: 1,5 veces el desvío del lote. La suma es el ROP; si el stock está por debajo, alerta. La tabla muestra cómo traduce eso en probabilidad: stock cero es 100 %, si no cubre la demanda 75 a 95 %, bajo el ROP 40 a 70 %, y sobre el ROP 30 % o menos, sin alerta.
>
> Es **O(1)** y se explica en una línea. Pero es fija: usa 3 de los 10 datos que tenemos y no aprende cómo se comportó la demanda. Esa es la puerta para probar un modelo."

**Puntos clave:**
- La fórmula:
  - `demanda = μ × máx(0,2; tendencia)`
  - `seguridad = 1,5 × √σ²`, que pasa a `0,5 × demanda` si σ² = 0
  - `ROP = demanda + seguridad`
- Sin historial de pedidos: demanda 0 y no alerta.
- Código: `evaluar_heuristica_convencional()` en `src/ia/modelos.py`.

**Transición:** *"¿Cuáles son esos 10 datos?"*

**Preguntas probables:**
- ¿Por qué O(1)? → Son operaciones aritméticas sobre valores ya calculados; no recorre nada.
- ¿Por qué `máx(0,2; tendencia)`? → Para que una tendencia a la baja no anule la demanda estimada.
- ¿Por qué 1,5? → Es un factor de servicio clásico: más alto da más colchón y más alertas.

### B-03 · La etiqueta: 10 datos por producto

**Guion:**
> "Los modelos de scikit-learn no leen objetos `Producto` ni listas de pedidos: leen números. `ExtractorFeatures` resume el historial de cada producto en un vector fijo de **10 datos**, el `FeatureVector`. Es la etiqueta que lee el operario.
>
> A la derecha está qué significa cada uno. Los marcados ROP (lote medio, varianza y tendencia) son los únicos que usa la regla. El modelo usa los diez, incluidos el precio, la tasa de quiebres recientes y la cobertura.
>
> Veamos productos reales de la demo. *(Clic en Taladro)* El taladro tiene un solo pedido y 15 en stock: la regla ve holgura y dice riesgo bajo, pero el modelo lo sube a medio, 43 %, influido por el precio alto. *(Clic en Sierra)* La sierra caladora tiene stock cero: los dos coinciden en crítico. *(Clic en Amoladora)* Y la amoladora nunca se pidió: la regla dice demanda cero, pero el modelo, entrenado con historial sintético, le asigna 14,5 unidades y riesgo medio. Sin datos, **ninguno de los dos puede saberlo**. Este caso vuelve en el bulto 07."

**Puntos clave:**
- Los 10 datos, de F1 a F10: rotación, frecuencia, **lote medio**, **varianza**, stock, precio, stock/(rotación+1), tasa de quiebre reciente, **tendencia** y cobertura (999 si no hay consumo).
- Pasar el mouse sobre una fila resalta el mismo dato en la etiqueta y en la lista.
- Extraer el vector cuesta ~2,4 µs y crece con el historial.
- Opcionales:
  - Disco (id 21): ambos alertan; la regla dice Crítico y el modelo Medio.
  - Id 7: alta rotación pero 120 en stock; ambos Bajo.

**Transición:** *"¿Cómo aprende el modelo a combinar estos 10 datos?"*

**Preguntas probables:**
- ¿Por qué `+1`? → Evita dividir por cero.
- ¿Por qué 999? → Es un valor centinela para "sin consumo".
- ¿Por qué crece la extracción? → Recorre los pedidos del producto: es O(pedidos), no O(1).

### B-04 · Cómo aprende: dos modelos lineales chicos

**Guion:**
> "El JSON del catálogo es una foto: no tiene historial temporal. Para entrenar, `GeneradorHistorialSintetico` **simula ciclos de pedidos** sobre el catálogo real, con una distribución de Pareto (pocos productos concentran muchos pedidos) y semilla 42 para que sea reproducible.
>
> Cuidamos que no haya **fuga de futuro**: las 10 features se calculan con los ciclos anteriores y la etiqueta evalúa el ciclo siguiente. El corte entre entrenamiento y prueba es **cronológico**, 75/25, no aleatorio.
>
> Hay dos pipelines. Arriba, `StandardScaler` más **Ridge** estima cuántas unidades se van a pedir. Abajo, `StandardScaler` más **regresión logística** estima la probabilidad de quiebre; si supera el 50 %, alerta. Escalamos porque el precio está en miles y la tasa de quiebre entre 0 y 1: sin escalar, las magnitudes grandes dominarían los pesos.
>
> *(Botón Entrenar)* Estas son las métricas del modelo guardado. Hay que ser honestos: el **clasificador funciona**, con F1 de 0,87; el **regresor explica poco**, con R² de 0,12. Por eso las alertas dependen solo de la probabilidad, no de la demanda estimada.
>
> Elegimos modelos lineales porque corren en local, sin GPU; el archivo pesa 2,6 KB y una predicción es un producto escalar, con costo fijo por producto."

**Puntos clave:**
- Datos sintéticos (Pareto, seed 42), sin fuga, corte cronológico 75/25 y 112 muestras de prueba.
- Ridge con α = 1; LogisticRegression con C = 1 y max_iter = 300.
- Métricas: F1 0,87, precisión 0,89, recall 0,87, R² 0,12, MAE 10,6 u.
- `predictor_ia.joblib` se carga al iniciar; «Re-entrenar» reajusta en memoria.

**Transición:** *"Ya tenemos regla y modelo. ¿Cómo los combinamos?"*

**Preguntas probables:**
- ¿Qué es Ridge? → Regresión lineal con penalización L2 que reduce el sobreajuste.
- ¿Por qué un corte cronológico? → El aleatorio mezcla futuro en el entrenamiento e infla las métricas.
- ¿Por qué el R² es bajo? → La demanda sintética tiene mucho ruido y el modelo es lineal. No afecta las alertas.

### B-05 · El desviador: la cascada híbrida (escena central)

**Qué pasa en la animación de la cinta:**
1. Los **30 productos** de la demo entran por la cinta como cajas marrones con su número.
2. Llegan al **desviador** (la barra naranja). Si `stock ≥ máx(10, 3 × demanda de la regla)`, siguen derecho por el **carril rápido** (regla O(1), 0,47 µs) y se pintan con su riesgo: verde bajo, amarillo medio, rojo crítico.
3. Si no, **suben al carril del operario**. Ahí está el brazo PRD-01, que los evalúa **de a uno**: el cartel cambia de «libre» a «evaluando…» y el producto se enmarca en celeste. Después sale pintado con su riesgo.
4. Si se juntan más de 3 esperando, aparece en rojo **«cola: N esperando al modelo»**.
5. Los contadores muestran evaluados, enviados al modelo, alertas, riesgo medio y el **cómputo acumulado**, calculado con los µs medidos.

**Guion:**
> "Esta es la escena central. Arranca en **Cascada híbrida**. El desviador aplica una regla simple: si el stock es al menos el máximo entre 10 y tres veces la demanda que calculó la regla, sobra stock y no hay nada que predecir; sigue por el carril rápido. Si no, sube al operario, que es el modelo. De los 30 productos, **26 pasan por el carril rápido y solo 4 van al modelo**.
>
> *(Clic en Solo modelo)* Ahora el operario revisa los 30. Miren cómo **se forma la cola**: esa cola es el costo de poner IA en todo, y el contador de cómputo sube a varios milisegundos.
>
> *(Clic en Regla O(1))* Con la regla sola no hay cola y el cómputo es mínimo, pero tampoco aparecen avisos de riesgo medio.
>
> Lo importante: las **alertas fuertes coinciden en las tres**, 4, 4 y 4. Lo que cambia son los avisos medios: el modelo marca 5, la cascada conserva 1 y la regla ninguno. La cascada se queda con casi todo el ahorro de la regla sin perder las alertas."

**Puntos clave:**
- Orden de la demo: Cascada → Solo modelo → Regla. El botón «↻ Volver a pasar la cinta» reinicia.
- Código: `_resolver_estrategia()`, rama `HIBRIDA`, en `predictor_demanda.py:110-133`. Integración: `MotorInventario.predecir_quiebres_stock()`.
- Decir la cifra completa: no pierde alertas, pero de 5 avisos medios quedan 1.

**Transición:** *"Dijimos que el modelo cuesta más. ¿Cuánto más?"*

**Preguntas probables:**
- ¿Por qué `máx(10, …)`? → Es un piso: un producto de demanda muy baja con poco stock no debe pasar como seguro.
- ¿Por qué 3×? → Da tres lotes de cobertura; con menos que eso, la combinación de los 10 datos puede cambiar la decisión.

### B-06 · Balanza y cronómetro: el costo de cada estrategia

**Guion:**
> "Medimos el mismo código de dos formas, y esa diferencia es en sí una lección. *(Pestaña Con tracemalloc)* La tabla oficial del benchmark mide con **tracemalloc** encendido, para registrar la memoria en la misma corrida. Ahí la regla tarda 58 µs y parece solo 23 veces más rápida que el modelo.
>
> *(Pestaña Sin tracemalloc)* Pero medida sola con `timeit`, la regla tarda **0,47 µs**: casi todo lo que veíamos era el **costo de medir**. tracemalloc intercepta cada reserva de memoria y guarda su traza, y eso suma unos 50 µs por llamada. Lección de eficiencia: **tiempo y memoria se miden en corridas separadas**.
>
> Con la medición limpia, el modelo cuesta **unas 480 veces** la regla y la cascada es **7 veces más rápida** que usar el modelo en todo. Con 1.000 productos la proporción se mantiene. La escala es logarítmica porque los valores van de medio microsegundo a más de mil.
>
> En memoria: el modelo pesa 2.673 bytes en disco; el pico por corrida es de 15, 22 y 30 KB, y 200 inferencias seguidas retienen menos de 128 KB: no hay fugas."

**Puntos clave:**

| µs por producto | Regla | Cascada | Modelo |
|---|---:|---:|---:|
| Demo, oficial (tracemalloc) | 58,5 | 263,9 | 1.361,9 |
| Demo, timeit | 0,47 | 30,4 | 226,4 |
| 1.000 productos, timeit | 1,63 | 91,6 | 1.267,8 |

Las corridas varían entre un 5 y un 15 %.

**Transición:** *"Con estos números podemos responder la pregunta central."*

**Preguntas probables:** ¿Para qué usan tracemalloc si distorsiona? → Para lo que sirve: el pico real de memoria y la detección de fugas en CI. Lo que no hay que hacer es tomar el tiempo en la misma corrida.

### B-07 · ¿Cuándo conviene la IA y cuándo alcanza la regla?

**Guion:**
> "Esta es la pregunta que más pesa en la evaluación, y no la respondemos con una opinión: está **escrita en el código** de la cascada, en tres pasos.
>
> **Uno:** la regla se calcula siempre, porque cuesta medio microsegundo y nos da la demanda y una primera probabilidad. **Dos:** si el stock es al menos el máximo entre 10 y tres veces la demanda, sobra; no hay nada que predecir y responde la regla. Eso pasó con 26 de 30 productos en la demo y con 915 de 1.000 en el dataset mediano. **Tres:** solo en la zona dudosa, con el stock cerca de la demanda, donde combinar los 10 datos cambia la decisión, se enciende el modelo: 4 de 30, y 85 de 1.000.
>
> Resumido: **alcanza la regla** cuando hay que responder en tiempo real o para miles de productos, cuando el stock sobra, cuando no hay historial o cuando hay que explicar la decisión en una línea. **Conviene el modelo** cuando el stock está cerca de la demanda, la demanda varía, un quiebre cuesta caro y hay historial para aprender.
>
> Una limitación que conocemos: un producto sin pedidos y con menos de 10 unidades cae en la zona dudosa, y el modelo le responde con lo que aprendió del historial sintético, no con datos de ese producto. Es el caso de la amoladora. La mejora sería mandarlos siempre a la regla.
>
> Nuestra respuesta a la lámina 400: **la IA no reemplaza al algoritmo eficiente, lo usa como filtro y trabaja solo donde hay duda.**"

**Puntos clave:** los 3 pasos, las cifras 26/4 y 915/85, la tabla de "alcanza la regla / conviene el modelo", el caso borde y la frase final.

**Transición:** *"Eso es la IA dentro del sistema. El otro enfoque era usarla para desarrollar."*

### B-08 · Los auxiliares: IA en el desarrollo, verificada

**Guion:**
> "El primer enfoque de la consigna dice *validando siempre sus resultados*, y esta lámina es eso. Usamos asistentes para cuatro cosas:
> - **Pruebas por propiedades** con Hypothesis: genera stocks de 0 a 5.000 y datos aleatorios y verifica que la probabilidad nunca salga de 0 a 1.
> - El **test de presupuesto de memoria**: 200 inferencias seguidas con menos de 128 KB retenidos.
> - **Explicar y documentar** la API en Sphinx.
> - **Refactors** para mantener la complejidad cognitiva en 15 o menos.
>
> Pero cuando preparamos la defensa volvimos a medir todo y encontramos **cinco afirmaciones que no se sostenían** tal cual. La más importante es el F1: decíamos 0,875, pero es un **F1 ponderado**. En el dataset de 1.000 productos da 0,996 aunque el modelo **no marca ni una alerta** (la regla marca 29), porque casi todos los productos son 'sin quiebre' y esa clase domina el promedio. Es un ejemplo concreto de por qué hay que validar lo que propone la IA.
>
> El asistente escribe rápido. **La medición decide qué queda.**"

**Los 5 hallazgos (memorizar):**
1. "La regla tarda 58 µs" → sin tracemalloc son 0,47 µs. Medir tiempo y memoria por separado.
2. "Latencia sub-microsegundo", en la misma tabla → contradice la fila anterior. Una sola fuente por cifra.
3. "F1 = 0,875" → es ponderado; con 1.000 productos da 0,996 con 0 alertas. Reportar el F1 de la clase quiebre.
4. "La cascada no pierde alertas" → es cierto (4 = 4), pero de 5 avisos medios quedan 1. Decirlo con las dos cifras.
5. Umbrales de 60 % / 25 % en el resumen → el código usa 0,70 y 0,40 (`predictor_demanda.py:31-32`).

**Transición:** *"Y todo esto, ¿rompió algo de lo anterior?"*

**Preguntas probables:**
- ¿Qué es un test por propiedades? → En vez de casos fijos, se genera una gran cantidad de entradas y se verifica que una invariante se cumpla siempre.
- ¿Qué hizo la IA y qué hicieron ustedes? → Los asistentes propusieron pruebas, documentación y refactors; nosotros medimos y validamos. Eso es lo que encontró los 5 hallazgos.

### B-09 · La caja sigue pasando la aduana

**Guion:**
> "Lo que construimos en el Parcial 3 hizo su trabajo: el módulo de IA entró por la **misma aduana de 7 etapas** que revisa cada push. Corrimos la suite completa para esta defensa: **235 pruebas pasan** en 49 segundos y la **cobertura total es 89 %**, arriba del umbral de 85. Hay **37 tests nuevos**: 31 en `tests/ia/` y 6 de la pantalla.
>
> Cada archivo nuevo controla algo distinto:
> - `test_extractor_features.py`: los 10 datos y los casos sin historial.
> - `test_predictor_ia.py`: la regla, el modelo, la cascada y Hypothesis.
> - `test_integracion_motor_ia.py`: el motor con las tres estrategias.
> - `test_presupuesto_memoria_ia.py`: memoria, fugas y speedup. Este exige que la regla sea **al menos 3× más rápida** que el modelo en cada corrida de CI.
> - `test_pantalla_ia.py`: la pantalla Flet.
>
> Lo que tocó la aduana: scikit-learn y joblib quedaron declarados y vigilados por pip-audit y Dependabot, que de hecho ya abrió una rama para actualizar joblib. mypy ignora los tipos que faltan de esas librerías, pero nuestro código sigue tipado. Y el deploy de la documentación quedó solo desde `main`."

**Puntos clave:** 235 tests, 89 %, 37 nuevos (11 + 11 + 5 + 4 + 6), el test de speedup ≥ 3× y los gates (Ruff, mypy, complexipy ≤ 15, Bandit, gitleaks, pip-audit).

**Transición:** *"Ahora lo vemos funcionando en la aplicación."*

### B-10 · Demo en vivo: pantalla «Predicción IA»

**Guion (salir de la presentación a la app):**
1. `python main.py` → sección **Predicción IA**. *"Es la misma decisión que vimos en la cinta, dentro de la aplicación de escritorio."*
2. **Cascada híbrida:** *"Arriba están la latencia media en microsegundos, la memoria y las alertas activas."*
3. **Modelo IA (scikit-learn):** *"Miren cómo sube la latencia y aparecen más riesgos medios."*
4. **Heurística O(1):** *"La latencia cae a casi cero."*
5. Filtro **Crítico**: *"Esto es lo que el depósito tiene que reponer primero."*
6. **Re-entrenar Modelo**: *"Se reajusta en memoria con el catálogo cargado, sin reiniciar."*

**Plan B, sin improvisar:** la tabla de la lámina tiene los mismos resultados de la cascada, ordenados por probabilidad. En la terminal, `pytest tests/ia -v` y `python benchmarks/comparar_ia.py` muestran lo mismo.

**Transición:** *"Para cerrar, lo que salió bien, lo que no y lo que haríamos distinto."*

### B-11 · Conclusiones y autocrítica

**Guion:**
> "**Lo que rindió:**
> - La cascada: 26 de 30 productos se resuelven sin tocar el modelo.
> - El modelo entró sin romper nada: 235 tests y 89 % de cobertura.
> - Es un modelo de 2,6 KB, local, sin servicios externos.
>
> **Lo que no salió:**
> - Entrenamos con historial sintético porque no hay ventas reales.
> - El regresor de demanda explica poco, R² de 0,12.
> - El F1 ponderado hizo ver bien a un modelo que en 1.000 productos no alertó nada.
> - Medimos tiempo con tracemalloc encendido.
>
> **Qué haríamos distinto:**
> - Entrenar con el historial real del depósito.
> - Reportar precisión y recall de la clase quiebre.
> - Mandar siempre a la regla los productos sin historial.
> - Comparar con un árbol como XGBoost y exportar a ONNX para medir la inferencia, como propone la cátedra en las láminas 391 y 392.
>
> Fueron cuatro hitos con la misma caja: **primero rápida, después mantenible, después controlada y al final, anticipando**. La IA llegó al final porque necesitaba todo lo anterior para poder medirse."

Después, `P` (o `→`) para entregar la caja (ver la sección 2).

---

## 4. Machete y preguntas difíciles

### Machete de cifras

| Qué | Valor |
|---|---|
| Regla O(1), timeit | **0,47 µs** por producto |
| Modelo, timeit | **226 µs** (~**480×** la regla) |
| Cascada, timeit | **30 µs** (~**7×** más rápida que el modelo puro) |
| Con tracemalloc: regla / cascada / modelo | 58 / 264 / 1.362 µs (la regla, "solo" 23×) |
| Demo (30 productos) | **26** por carril rápido, **4** al modelo |
| Dataset mediano (1.000) | **915** rápido, **85** al modelo |
| Alertas en la demo: regla / modelo / cascada | **4 / 4 / 4** |
| Avisos de riesgo medio: regla / modelo / cascada | **0 / 5 / 1** |
| Modelo: F1 ponderado, precisión, recall | **0,87 · 0,89 · 0,87** (112 muestras) |
| Regresor: R² y MAE | **0,12** y **10,6 u** |
| Archivo del modelo | **2.673 bytes** (2,6 KB) |
| Memoria pico: regla / cascada / modelo | 15,2 / 22,2 / 29,9 KB |
| Fugas | 200 inferencias, **< 128 KB** retenidos |
| Tests y cobertura | **235** tests (49 s) y **89 %** (umbral 85 %) |
| Tests nuevos | **37** (31 de IA + 6 de UI) |
| Umbrales en el código | alerta ≥ **0,50**, medio ≥ **0,40**, crítico ≥ **0,70** |
| Desviador de la cascada | `stock ≥ máx(10, 3 × demanda)` → regla |

### Preguntas difíciles

- **"Si el regresor explica tan poco, ¿para qué está?"** → Las alertas dependen solo del clasificador; la demanda estimada es informativa. Es una limitación reconocida, atribuida al historial sintético y a un modelo lineal.
- **"¿Sus métricas valen algo con datos sintéticos?"** → Validan que el pipeline funciona y permiten comparar el costo, pero no prueban precisión en producción. Por eso lo primero que haríamos distinto es usar datos reales.
- **"¿Por qué no usar el modelo en todo si es más fino?"** → Cuesta ~480× más por producto, y en 26 de 30 productos el stock sobra: no hay nada que predecir. Las alertas fuertes son las mismas.
- **"¿Cómo saben que no hay fugas de memoria?"** → Hay un test de 200 inferencias seguidas con tracemalloc: después del GC quedan menos de 128 KB retenidos.
- **"¿Qué pasa si el archivo del modelo no está?"** → El motor sigue funcionando con la regla convencional.
- **"¿Qué parte hizo la IA y qué parte ustedes?"** → Los asistentes propusieron pruebas, documentación y refactors; nosotros medimos y validamos. Eso encontró los 5 hallazgos de B-08.

> **Ojo:** `resumen-proyecto-final.md` todavía repite cifras que B-08 corrige: 234 tests, F1 0,875 sin aclarar que es ponderado, y umbrales de 60 % / 25 %. En la defensa, usá las cifras de esta guía.
