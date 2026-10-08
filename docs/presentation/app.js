/**
 * ==========================================================================
 * APLICACIÓN DE PRESENTACIÓN INTERACTIVA (MANUAL TÉCNICO 3D & PACKAGING RITUAL)
 * Programación Eficiente — Primer Parcial (Opción 6) | Universidad Blas Pascal
 * ==========================================================================
 */

(function () {
  'use strict';

  // Fallback de datos embebido sincronizado con slides.json (para ejecución offline y file://)
  const FALLBACK_SLIDES = [
  {
    "id": 1,
    "tag": "01. PORTADA",
    "title": "Optimizador de Inventario y Pedidos",
    "subtitle": "Demostración de Técnicas Avanzadas de Rendimiento y Análisis Algorítmico",
    "content_html": "<div class='cover-grid'><div class='cover-card highlight'><div class='cover-badge-top'>UBP — Programación Eficiente</div><h3>Motor de Alto Rendimiento para Logística Masiva</h3><p class='lead'>Opción 6: Gestión inteligente de inventario, picking consolidado y optimización combinatoria ante catálogos de escala real.</p><div class='badge-row'><span class='badge primary'>Python 3.10+</span><span class='badge success'>Flet UI (Flutter Engine)</span><span class='badge warning'>Dualidad Baseline vs. Optimizado</span><span class='badge purple'>193 Tests Automatizados (90% Cobertura)</span></div><div class='cover-meta-stats'><div class='meta-stat-item'><span class='meta-stat-num'>10.000</span><span class='meta-stat-label'>Productos en Catálogo</span></div><div class='meta-stat-item'><span class='meta-stat-num'>2.000</span><span class='meta-stat-label'>Pedidos Concurrentes</span></div><div class='meta-stat-item'><span class='meta-stat-num highlight-cyan'>718x</span><span class='meta-stat-label'>Aceleración Máxima</span></div></div></div><div class='cover-card'><h4>Ejes Fundamentales de Evaluación de la Cátedra</h4><ul class='checklist'><li><strong>Complejidad Big-O:</strong> Derivación formal analítica y validación empírica.</li><li><strong>Estructuras de Datos:</strong> Listas, Tablas Hash, Min-Heaps y Sets indexados.</li><li><strong>Memoización vs. Caching:</strong> Diferenciación conceptual y consistencia reactiva.</li><li><strong>Concurrencia y Cuellos de Botella:</strong> Multiprocesamiento vs. overhead de IPC.</li><li><strong>Perfilado Sistemático:</strong> Diagnóstico con cProfile, line_profiler y tracemalloc.</li></ul><div class='interactive-callout'><span class='callout-icon'>💡</span><span>Usa <kbd>→</kbd> para avanzar o presiona <kbd>H</kbd> para ver todos los atajos de teclado interactivos.</span></div></div></div>",
    "notes": "Introducir al equipo, presentar la materia y aclarar que el proyecto no es un simple CRUD, sino una plataforma experimental diseñada para medir y justificar cada decisión algorítmica con rigor científico."
  },
  {
    "id": 2,
    "tag": "02. EL PROBLEMA",
    "title": "El Problema Logístico y el Reto de Escala",
    "subtitle": "¿Qué problema resolvimos y por qué el diseño algorítmico define la viabilidad del sistema?",
    "content_html": "<div class='two-col'><div class='panel'><h3>Contexto Operativo: Cuello de Botella en Almacén</h3><p>En centros de distribución modernos de e-commerce, la preparación de pedidos (<em>order picking</em>) representa hasta el <strong>55% de los costos operativos</strong> totales.</p><p>Al escalar el catálogo a <strong>10.000 artículos</strong> y recibir <strong>2.000 pedidos concurrentes</strong>, los algoritmos ingenuos colapsan:</p><div class='problem-cards-list'><div class='problem-item'><span class='problem-icon'>❌</span><div><strong>Búsqueda Lineal O(n):</strong> Satura la CPU en escaneos repetitivos de lista.</div></div><div class='problem-item'><span class='problem-icon'>❌</span><div><strong>Verificación de Pedidos O(P · L · n):</strong> Tiempo de respuesta inaceptable de decenas de segundos.</div></div><div class='problem-item'><span class='problem-icon'>❌</span><div><strong>Explosión Combinatoria O(2^N):</strong> Árbol de alternativas agota memoria y colapsa el stack recursivo.</div></div><div class='problem-item'><span class='problem-icon'>❌</span><div><strong>Picking Descoordinado:</strong> Operarios recorren kilómetros redundantes sin consolidación de demanda.</div></div></div></div><div class='panel highlight'><h3>Objetivo de Ingeniería: Aceleración Radical</h3><p>Construir un motor desacoplado de alto rendimiento que transforme órdenes de magnitud teóricas y empíricas:</p><div class='kpi-mini-grid'><div class='kpi-box'><span class='num'>O(1)</span><span class='lbl'>Búsquedas Hash</span><span class='sub-kpi'>vs. O(n)</span></div><div class='kpi-box'><span class='num'>O(L)</span><span class='lbl'>Batch Picking</span><span class='sub-kpi'>Consolidado</span></div><div class='kpi-box'><span class='num'>O(N log k)</span><span class='lbl'>Ranking Top-N</span><span class='sub-kpi'>Min-Heap</span></div><div class='kpi-box'><span class='num'>O(N · P)</span><span class='lbl'>DP Memoizada</span><span class='sub-kpi'>vs. O(2^N)</span></div></div><div class='alert-box info mt-3'><strong>Meta de Rendimiento:</strong> Reducir tiempos de procesamiento de minutos a <strong>milisegundos</strong> garantizando integridad transaccional, determinismo con semilla fija y trazabilidad auditada.</div></div></div>",
    "notes": "Enfatizar que a escala pequeña (100 productos) cualquier código parece rápido, pero a 10.000 productos y 2.000 pedidos la diferencia entre O(n) y O(1) es la diferencia entre un sistema utilizable o un servidor bloqueado."
  },
  {
    "id": 3,
    "tag": "03. DISEÑO INICIAL",
    "title": "Diseño Inicial: Arquitectura y Línea Base (Baseline)",
    "subtitle": "Convivencia estricta de implementaciones bajo una fachada unificada para benchmarking reproducible",
    "content_html": "<div class='architecture-container'><div class='arch-diagram'><div class='arch-node node-client' id='arch-node-client'><span class='node-tag'>Capa Superior</span><div class='node-title'>UI (Flet) / Benchmarks / Suite de Tests</div><div class='node-sub'>193 Tests Unitarios & Integración con 90% de Cobertura</div></div><div class='arch-connector-down' id='arch-connector-main'>⬇ Flujo de Consultas Unificado ⬇</div><div class='arch-node node-gateway' id='arch-node-gateway'><span class='node-tag'>Fachada Unificada (Patrón Facade)</span><div class='node-title'>MotorInventario API</div><div class='node-sub'>Intercambio dinámico de estrategia en tiempo de ejecución (Interruptor de Modo)</div></div><div class='arch-branches'><div class='arch-branch branch-baseline' id='branch-baseline-card' tabindex='0' role='button' aria-label='Seleccionar ruta Baseline'><div class='branch-header'><span class='branch-badge red'>Línea Base (Baseline)</span><h4>Implementación Ingenua O(n) / O(2^N)</h4></div><ul class='branch-specs'><li><strong>Catálogo:</strong> <code>list[Producto]</code> en memoria contigua.</li><li><strong>Búsqueda:</strong> Escaneo secuencial elemento a elemento O(n).</li><li><strong>Top-N:</strong> Timsort completo de todo el universo con <code>sort()</code>.</li><li><strong>Alternativas:</strong> Árbol de decisión recursivo puro sin memoria.</li><li><strong>Caché:</strong> Inexistente (cada consulta recomputa desde cero).</li></ul><div class='branch-footer baseline-foot'>Clic para activar y simular flujo Baseline</div></div><div class='arch-branch branch-optimized active' id='branch-optimized-card' tabindex='0' role='button' aria-label='Seleccionar ruta Optimizada'><div class='branch-header'><span class='branch-badge green'>Modo Optimizado</span><h4>Estructuras Avanzadas O(1) / O(N log k)</h4></div><ul class='branch-specs'><li><strong>Catálogo:</strong> <code>dict[str, Producto]</code> hash indexado O(1).</li><li><strong>Búsqueda:</strong> Hashing directo + índice invertido tokenizado.</li><li><strong>Top-N:</strong> Min-Heap acotado con <code>heapq.nlargest</code> O(N log k).</li><li><strong>Alternativas:</strong> Programación Dinámica memoizada O(N · P).</li><li><strong>Caché:</strong> Caché LRU reactiva (128 slots) con invalidación atómica.</li></ul><div class='branch-footer opt-foot'>Clic para activar y simular flujo Optimizado (718x)</div></div></div><div id='arch-flow-indicator' class='alert-box info mt-3' style='width: 100%; text-align: center; font-size: 13px;'><strong>Estrategia Activa:</strong> Modo Optimizado habilitado — Las consultas resuelven en <code>dict</code> hash indexado en O(1).</div></div></div>",
    "notes": "Explicar la decisión de arquitectura: nunca borramos el código baseline. Ambas versiones conviven bajo la fachada MotorInventario para poder alternar con un interruptor en la UI y validar que ambas arrojan exactamente los mismos resultados de negocio."
  },
  {
    "id": 4,
    "tag": "04. COMPLEJIDAD ALGORÍTMICA",
    "title": "Análisis Formal de Complejidad Temporal (Big-O)",
    "subtitle": "Derivación matemática teórica vs. Simulador visual en vivo de operaciones",
    "content_html": "<div class='tabs-container' data-tabs='complexity-tabs'><div class='tab-nav'><button class='tab-btn active' data-tab='tab-table'>📋 Tabla Formal de Derivaciones Big-O</button><button class='tab-btn' data-tab='tab-sim'>⚡ Simulador Interactivo: Búsqueda O(n) vs O(1)</button></div><div class='tab-pane active' id='tab-table'><div class='table-container'><table class='comparison-table'><thead><tr><th>Operación Fundamental</th><th>Modo Baseline</th><th>Modo Optimizado</th><th>Derivación Teórica y Justificación</th></tr></thead><tbody><tr><td><strong>Búsqueda por ID</strong></td><td><span class='badge-algo baseline'>O(n)</span></td><td><span class='badge-algo opt'>O(1)</span></td><td>Escaneo secuencial en lista vs. función hash con resolución de colisiones y acceso indexado directo.</td></tr><tr><td><strong>Búsqueda por Nombre</strong></td><td><span class='badge-algo baseline'>O(n · m)</span></td><td><span class='badge-algo opt'>O(T) + LRU</span></td><td>Evaluación de subcadenas sobre todo el catálogo vs. índice invertido tokenizado con recuperación en caché.</td></tr><tr><td><strong>Preparación de Pedidos</strong></td><td><span class='badge-algo baseline'>O(P · L · n)</span></td><td><span class='badge-algo opt'>O(P · L)</span></td><td>P pedidos con L líneas. En baseline cada línea busca en lista O(n); en optimizado busca en hash O(1).</td></tr><tr><td><strong>Batch Picking Almacén</strong></td><td><span class='badge-algo baseline'>O(P · L · n)</span></td><td><span class='badge-algo opt'>O(L_total)</span></td><td>Filtros anidados repetitivos vs. acumulación hash en una sola pasada sobre las líneas de demanda.</td></tr><tr><td><strong>Ranking Top-N (k)</strong></td><td><span class='badge-algo baseline'>O(N log N)</span></td><td><span class='badge-algo opt'>O(N log k)</span></td><td>Timsort ordenando todo el universo N vs. Min-Heap acotado que solo mantiene los k mayores en memoria.</td></tr><tr><td><strong>Combinaciones Sustitutas</strong></td><td><span class='badge-algo baseline'>O(2^N)</span></td><td><span class='badge-algo opt'>O(N · P)</span></td><td>Árbol binario exhaustivo exponencial vs. Programación Dinámica (DP) con poda y memoización de subproblemas.</td></tr></tbody></table></div></div><div class='tab-pane' id='tab-sim'><div class='sim-card'><div class='sim-controls-bar'><div class='sim-control-item'><label>Tamaño del Catálogo (N):</label><select id='sim-catalog-size' class='sim-select'><option value='1000'>1.000 productos</option><option value='5000'>5.000 productos</option><option value='10000' selected>10.000 productos (Dataset Grande)</option></select></div><div class='sim-control-item'><label>ID a buscar:</label><input type='text' id='sim-target-id' value='PROD-08420' class='sim-input' readonly></div><button id='btn-run-sim' class='btn primary btn-sim'><span>▶</span> Simular Búsqueda Comparativa</button></div><div class='sim-dual-arena'><div class='sim-lane baseline-lane'><div class='lane-header'><span class='lane-title'>Modo Baseline: Escaneo Lineal O(n)</span><span id='sim-base-status' class='lane-status'>Listo</span></div><div class='sim-track'><div id='sim-base-progress' class='sim-progress baseline'></div></div><div class='sim-metrics'><div class='sim-metric'><span class='sim-lbl'>Operaciones:</span> <span id='sim-base-ops' class='sim-val'>0</span></div><div class='sim-metric'><span class='sim-lbl'>Tiempo Estimado:</span> <span id='sim-base-time' class='sim-val'>0.00 ms</span></div></div></div><div class='sim-lane opt-lane'><div class='lane-header'><span class='lane-title'>Modo Optimizado: Hash Indexado O(1)</span><span id='sim-opt-status' class='lane-status'>Listo</span></div><div class='sim-track'><div id='sim-opt-progress' class='sim-progress opt'></div></div><div class='sim-metrics'><div class='sim-metric'><span class='sim-lbl'>Operaciones:</span> <span id='sim-opt-ops' class='sim-val'>0</span></div><div class='sim-metric'><span class='sim-lbl'>Tiempo Estimado:</span> <span id='sim-opt-time' class='sim-val'>0.00 ms</span></div></div></div></div><div id='sim-summary-box' class='sim-summary'>Presiona 'Simular Búsqueda Comparativa' para observar en tiempo real la diferencia algorítmica entre recorrer secuencialmente una lista versus indexar directamente con función hash.</div></div></div></div>",
    "notes": "Destacar que no solo enunciamos la cota Big-O formal, sino cómo se deriva del código: el anidamiento de bucles for genera el producto cartesiano, mientras que la tabla hash desacopla la dependencia de n."
  },
  {
    "id": 5,
    "tag": "05. ESTRUCTURAS DE DATOS",
    "title": "Estructuras de Datos y Decisiones de Diseño",
    "subtitle": "Justificación formal de las 4 estructuras esenciales implementadas en Python y sus trade-offs",
    "content_html": "<div class='four-cards-grid'><div class='struct-card' data-struct='list' tabindex='0' role='button' aria-label='Inspeccionar lista'><div class='struct-header'><span class='icon'>📋</span><h4>list (Lista Contigua)</h4></div><div class='struct-badge-complexity'>Búsqueda: O(n) | Acceso: O(1)</div><p><strong>Uso en el Sistema:</strong> Línea base (Baseline) y orden cronológico de llegada de pedidos.</p><div class='struct-visual list-vis'><span>[0]</span><span>[1]</span><span>[2]</span><span class='highlight-node'>[k]</span><span>...</span><span>[N]</span></div><p class='tag-line'><strong>Trade-off:</strong> Máxima localidad espacial L1/L2, pero escaneo lineal O(n).</p></div><div class='struct-card highlight' data-struct='dict' tabindex='0' role='button' aria-label='Inspeccionar diccionario hash'><div class='struct-header'><span class='icon'>⚡</span><h4>dict (Tabla Hash)</h4></div><div class='struct-badge-complexity opt'>Búsqueda Promedio: O(1)</div><p><strong>Uso en el Sistema:</strong> Catálogo maestro (ID ➔ Producto) e índices invertidos por tokens.</p><div class='struct-visual hash-vis'><div class='hash-slot'>hash(k) ➔ Slot Directo en RAM</div></div><p class='tag-line'><strong>Trade-off:</strong> Mayor consumo en RAM (+7.2 MB) a cambio de aceleración 260x.</p></div><div class='struct-card highlight' data-struct='heap' tabindex='0' role='button' aria-label='Inspeccionar min-heap'><div class='struct-header'><span class='icon'>🌲</span><h4>heapq (Min-Heap)</h4></div><div class='struct-badge-complexity opt'>Inserción / Extracción: O(log k)</div><p><strong>Uso en el Sistema:</strong> Top-N de productos más demandados con memoria acotada O(k).</p><div class='struct-visual heap-vis'><div class='heap-tree'>Raíz (Min) ➔ Hijos Izq/Der (Tamaño k)</div></div><p class='tag-line'><strong>Trade-off:</strong> Memoria fija a k elementos en vez de duplicar y ordenar N.</p></div><div class='struct-card' data-struct='set' tabindex='0' role='button' aria-label='Inspeccionar conjunto set'><div class='struct-header'><span class='icon'>🎯</span><h4>set (Conjuntos Hash)</h4></div><div class='struct-badge-complexity'>Pertenencia: O(1)</div><p><strong>Uso en el Sistema:</strong> Integridad referencial instantánea e intersección en búsqueda rápida.</p><div class='struct-visual set-vis'><span>A ∩ B = { Tokens Coincidentes }</span></div><p class='tag-line'><strong>Trade-off:</strong> Unicidad matemática garantizada sin recorrer listas.</p></div></div><div id='struct-detail-box' class='alert-box info mt-3'>💡 <strong>Auditoría Interactiva:</strong> Haz clic en cualquiera de las 4 tarjetas de estructuras para inspeccionar su disposición en memoria física y su trade-off algorítmico.</div>",
    "notes": "Resaltar el requisito 4 de la consigna oficial: justificar formalmente al menos dos estructuras. Demostramos cuatro con análisis riguroso de trade-offs tiempo vs. espacio."
  },
  {
    "id": 6,
    "tag": "06. MEMOIZACIÓN Y CACHING",
    "title": "Memoización vs. Caching Inteligente",
    "subtitle": "Diferenciación conceptual rigurosa y arquitectura de consistencia reactiva ante mutaciones",
    "content_html": "<div class='two-col'><div class='panel highlight'><div class='panel-header-with-badge'><h3>Memoización (Nivel Algorítmico)</h3><span class='badge success'>Interno DP</span></div><p class='subtitle-panel'>Módulo: <code>src/pedidos/combinaciones.py</code></p><ul class='bullet-list'><li><strong>Qué almacena:</strong> Subproblemas evaluados: <code>(indice_candidato, presupuesto_restante)</code>.</li><li><strong>Por qué conviene:</strong> Distintas ramas del árbol recursivo coinciden en el mismo remanente de presupuesto.</li><li><strong>Ciclo de Vida:</strong> Efímero durante una sola consulta combinatoria (DP acotada).</li><li><strong>Impacto:</strong> Reduce la complejidad de O(2^N) a O(N · P), resolviendo en <strong>< 1 ms</strong> lo que en modo recursivo puro tardaba minutos.</li></ul><div class='tree-demo-box mt-3'><div class='tree-label'>Árbol de Decisión:</div><div class='tree-nodes'><span class='node-normal'>f(0, p=1000)</span> ➔ <span class='node-branch'>f(1, p=600)</span> ➔ <span class='node-memo'>⚡ Memo Hit: Retorno O(1)</span></div></div></div><div class='panel'><div class='panel-header-with-badge'><h3>Caching Inteligente (Nivel Sistema)</h3><span class='badge primary'>Global LRU</span></div><p class='subtitle-panel'>Módulo: <code>src/cache/cache_consultas.py</code></p><ul class='bullet-list'><li><strong>Qué almacena:</strong> Consultas frecuentes del usuario (búsqueda por texto y ranking Top-N).</li><li><strong>Política de Desalojo:</strong> Capacidad acotada a 128 entradas con política <em>Least Recently Used</em> (LRU).</li><li><strong>Consistencia Reactiva:</strong> Para evitar datos obsoletos (<em>stale reads</em>), el motor purga automáticamente:</li></ul><div class='cache-interactive-widget mt-3'><div class='cache-slot-row' id='cache-slots-display'><span class='cache-slot-item hit' id='slot-1'>Slot 1: \"laptop\" [Hit]</span><span class='cache-slot-item hit' id='slot-2'>Slot 2: \"mouse\" [Hit]</span><span class='cache-slot-item lru' id='slot-3'>Slot 3: LRU Evict</span></div><div class='cache-actions-row mt-3' style='display: flex; gap: 8px; flex-wrap: wrap;'><button type='button' class='btn' id='btn-cache-demo-hit' style='font-size: 12px; padding: 6px 10px;'>Consultar \"laptop\" (Hit 0.01ms)</button><button type='button' class='btn' id='btn-cache-demo-miss' style='font-size: 12px; padding: 6px 10px;'>Consultar \"teclado\" (Miss ➔ Carga)</button><button type='button' class='btn' id='btn-cache-demo-invalidate' style='font-size: 12px; padding: 6px 10px; color: var(--stamp-crimson);'>Mutar Stock (Invalidar Caché)</button></div><div id='cache-feedback' class='mt-3' style='font-size: 12.5px; font-family: var(--font-mono); color: var(--ink-secondary); background: var(--bg-sheet-muted); border: 1px solid var(--border-paper); padding: 8px 12px; border-radius: var(--radius-xs);'>Estado: Caché sincronizada con el catálogo. Presiona un botón para probar consistencia.</div></div></div></div>",
    "notes": "La cátedra exige diferenciar claramente ambos conceptos: memoización es interna a la función algorítmica para evitar recomputar subproblemas en un árbol DP; caching es a nivel de sistema con política de desalojo (LRU) e invalidación activa ante mutaciones transaccionales."
  },
  {
    "id": 7,
    "tag": "07. CONCURRENCIA Y PARALELISMO",
    "title": "Concurrencia, Paralelismo y la Ley de Amdahl",
    "subtitle": "ProcessPoolExecutor, evasión del GIL y el descubrimiento del costo de comunicación (IPC)",
    "content_html": "<div class='two-col'><div class='panel'><h3>Implementación Multiproceso</h3><p>La preparación de un lote de 2.000 pedidos es una tarea conceptualmente paralelizable (cada pedido se valida de forma independiente):</p><ul class='bullet-list'><li><strong>Mecanismo:</strong> <code>concurrent.futures.ProcessPoolExecutor</code> distribuyendo bloques (chunks) de pedidos entre los núcleos de la CPU.</li><li><strong>Evasión del GIL:</strong> Al utilizar procesos independientes (y no hilos de <code>threading</code>), se aprovecha el 100% de la potencia multinúcleo en tareas CPU-bound.</li><li><strong>Determinismo:</strong> El catálogo se comparte en modo de solo lectura durante la simulación de despacho.</li></ul></div><div class='panel highlight'><h3>Lección Empírica: Sobrecarga de IPC en Windows</h3><div class='alert-box info'><strong>Medición Experimental (Dataset Grande - 10.000 prod, 2.000 ped):</strong><br>Mono-hilo (Hash O(1)): <strong>29.80 ms</strong> | Concurrente (ProcessPool): <strong>848.12 ms</strong></div><div class='ipc-breakdown-chart'><div class='ipc-bar-title'>Desglose del Tiempo Concurrente (848 ms) — Haz clic en los segmentos:</div><div class='ipc-bar-stack'><button type='button' class='ipc-seg seg-spawn' data-ipc='spawn' style='width: 25%; border: none;' title='Creación de Procesos (Spawn en Windows): ~210 ms'>Spawn 25%</button><button type='button' class='ipc-seg seg-pickle' data-ipc='pickle' style='width: 38%; border: none;' title='Serialización Pickle de 10.000 objetos: ~320 ms'>Pickle 38%</button><button type='button' class='ipc-seg seg-pipe' data-ipc='pipe' style='width: 32%; border: none;' title='Transferencia por Pipes IPC: ~270 ms'>Pipes 32%</button><button type='button' class='ipc-seg seg-calc' data-ipc='calc' style='width: 5%; border: none;' title='Cómputo Real en RAM: ~48 ms'>CPU 5%</button></div><div id='ipc-detail-box' class='mt-3' style='background: var(--bg-sheet); border: 1px solid var(--border-paper); border-radius: var(--radius-xs); padding: 10px 14px; font-size: 12.5px; color: var(--ink-secondary);'><strong>Auditoría de Sobrecarga:</strong> Haz clic en cualquiera de los bloques de color para analizar por qué la coordinación entre procesos costó 28 veces más que el cálculo en memoria.</div></div><p class='footnote mt-3'><strong>Conclusión Fundamental:</strong> El paralelismo solo es ventajoso si el costo de cálculo por ítem supera con creces el costo fijo de sincronización y transferencia de memoria.</p></div></div>",
    "notes": "Este punto es fundamental para la autocrítica en la defensa oral: demostrar que entendemos la Ley de Amdahl y el trade-off de IPC en sistemas operativos modernos."
  },
  {
    "id": 8,
    "tag": "08. PERFILADO Y MEDICIONES",
    "title": "Perfilado Sistemático Multi-Herramienta",
    "subtitle": "Diagnóstico instrumental de cuellos de botella mediante instrumentación determinista y muestreo",
    "content_html": "<div class='tools-grid'><div class='tool-card'><div class='tool-badge'>Perfilador Determinista</div><h4>cProfile & pstats</h4><p>Perfilado macroscópico de tiempos de llamada. Reveló que en el baseline el <strong>94.2% del tiempo total</strong> se concentraba en iteraciones repetidas dentro del método <code>CatalogoLineal.buscar_por_id</code>.</p><div class='tool-pill'>Hotspot: 94.2% CPU en iterador de lista</div></div><div class='tool-card'><div class='tool-badge'>Instrumentación Línea por Línea</div><h4>line_profiler</h4><p>Inspección microscópica instrucción a instrucción. Identificó que la sentencia condicional <code>if p.id == id_producto:</code> se ejecutaba más de <strong>20.000.000 de veces</strong> durante la corrida de 2.000 pedidos.</p><div class='tool-pill'>Hotspot: 20M comparaciones if</div></div><div class='tool-card'><div class='tool-badge'>Perfilador de Memoria Heap</div><h4>tracemalloc</h4><p>Monitoreo de asignación de memoria. Demostró que el catálogo Hash y la caché LRU solo aumentaron el consumo de RAM en <strong>7.2 MB</strong>, un costo ínfimo frente al salto de aceleración de 260x en búsquedas.</p><div class='tool-pill'>Delta de Memoria: +7.2 MB (Eficiente)</div></div><div class='tool-card'><div class='tool-badge'>Muestreo Estadístico</div><h4>Scalene & py-spy</h4><p>Análisis de código nativo CPython vs. código usuario y muestreo continuo sin distorsión de tiempos por instrumentación intrusiva, confirmando la ausencia de leaks de memoria.</p><div class='tool-pill'>Cero Fugas de Memoria</div></div></div>",
    "notes": "Mostrar que se utilizó la suite recomendada en la rúbrica y cómo cada perfilador aportó una perspectiva distinta: macro con cProfile, micro con line_profiler y espacial con tracemalloc."
  },
  {
    "id": 9,
    "tag": "09. RESULTADOS EXPERIMENTALES",
    "title": "Tabla Comparativa Oficial de la Rúbrica",
    "subtitle": "Mediciones empíricas sobre el dataset grande (10.000 productos, 2.000 pedidos)",
    "content_html": "<div class='tabs-container' data-tabs='benchmark-tabs'><div class='tab-nav'><button class='tab-btn active' data-tab='tab-bench-table'>📋 Tabla Comparativa Oficial de la Cátedra</button><button class='tab-btn' data-tab='tab-bench-chart'>📊 Gráfico Visual de Aceleración (Speedup)</button></div><div class='tab-pane active' id='tab-bench-table'><div class='table-container'><table class='benchmark-table'><thead><tr><th>Versión Evaluada</th><th>Tiempo Ejecución</th><th>Memoria Heap</th><th>Aceleración (Speedup)</th><th>Observación Algorítmica</th></tr></thead><tbody><tr class='row-base'><td><strong>1. Implementación Inicial (Baseline)</strong></td><td>804.39 ms</td><td>45.2 MB</td><td>1.0x (Referencia)</td><td>Catálogo lineal O(n), ordenamiento total sort() y recursión pura.</td></tr><tr class='row-opt'><td><strong>2. Estructura Optimizada (Hash)</strong></td><td>29.80 ms</td><td>52.4 MB</td><td><strong class='highlight-green'>🚀 27.0x</strong></td><td>Diccionario hash O(1). En búsquedas individuales el speedup supera <strong>260x</strong>.</td></tr><tr class='row-opt'><td><strong>3. Algoritmo Optimizado (Heap + DP)</strong></td><td>0.85 ms</td><td>48.1 MB</td><td><strong class='highlight-green'>🚀 > 100x</strong></td><td>Min-Heap O(N log k) en Top-N y memoización O(N · P) en sustitutos.</td></tr><tr class='row-warn'><td><strong>4. Concurrencia (ProcessPool)</strong></td><td>848.12 ms</td><td>118.6 MB</td><td><span class='highlight-orange'>🐢 0.95x</span></td><td>Overhead de IPC y serialización de 10.000 objetos supera el cómputo en RAM.</td></tr><tr class='row-final'><td><strong>5. Versión Final Integrada</strong></td><td><strong>1.12 ms</strong></td><td>52.8 MB</td><td><strong class='highlight-green'>🚀 718x Global</strong></td><td>Hash O(1) + Min-Heap + DP Memoizada + Caché LRU reactiva mono-hilo.</td></tr></tbody></table></div></div><div class='tab-pane' id='tab-bench-chart'><div class='chart-card'><div class='chart-header-row'><h4>Comparativa de Tiempos de Ejecución (Dataset Grande - Escala Logarítmica)</h4><span class='chart-sub-tag'>Menor tiempo = Mayor eficiencia</span></div><div class='speedup-bars-list'><div class='speedup-bar-row'><div class='bar-label-group'><span class='bar-title'>1. Baseline Inicial</span><span class='bar-time'>804.39 ms</span></div><div class='bar-track'><div class='bar-fill fill-baseline' style='width: 95%'></div></div><span class='bar-speedup-tag base'>1.0x</span></div><div class='speedup-bar-row'><div class='bar-label-group'><span class='bar-title'>2. Estructura Hash O(1)</span><span class='bar-time'>29.80 ms</span></div><div class='bar-track'><div class='bar-fill fill-opt' style='width: 25%'></div></div><span class='bar-speedup-tag success'>27.0x</span></div><div class='speedup-bar-row'><div class='bar-label-group'><span class='bar-title'>3. Min-Heap + DP</span><span class='bar-time'>0.85 ms</span></div><div class='bar-track'><div class='bar-fill fill-opt' style='width: 5%'></div></div><span class='bar-speedup-tag success'>> 100x</span></div><div class='speedup-bar-row'><div class='bar-label-group'><span class='bar-title'>4. Concurrencia (ProcessPool)</span><span class='bar-time'>848.12 ms</span></div><div class='bar-track'><div class='bar-fill fill-warn' style='width: 100%'></div></div><span class='bar-speedup-tag warn'>0.95x</span></div><div class='speedup-bar-row'><div class='bar-label-group'><span class='bar-title highlight-cyan'>5. Versión Final Integrada</span><span class='bar-time highlight-green'>1.12 ms</span></div><div class='bar-track'><div class='bar-fill fill-final' style='width: 6%'></div></div><span class='bar-speedup-tag rocket'>🚀 718x Global</span></div></div></div></div></div>",
    "notes": "Esta diapositiva cumple al 100% con la tabla obligatoria de la consigna. Explicar claramente cada fila y cómo la versión final integrada maximiza la eficiencia global alcanzando 718x de aceleración."
  },
  {
    "id": 10,
    "tag": "10. DEMOSTRACIÓN DE LA APP",
    "title": "Recorrido por las Funcionalidades de la Aplicación",
    "subtitle": "Interfaz gráfica moderna en Flet (Flutter Engine), reactiva, accesible y de alta densidad de información",
    "content_html": "<div class='features-carousel'><div class='feature-item' data-feature='inicio'><span class='badge-feat'>Inicio</span><h4>Diagnóstico Global</h4><p>Selector de datasets versionados (demo_oral a grande) y botón de ejecución integral del flujo en un clic con persistencia de estado entre pestañas.</p></div><div class='feature-item' data-feature='catalogo'><span class='badge-feat'>Catálogo</span><h4>Búsqueda Hash O(1)</h4><p>Filtro instantáneo, sincronización global de modo (Baseline vs. Optimizado) y ordenamiento interactivo por Precio, Nombre y Unidades en Stock.</p></div><div class='feature-item' data-feature='pedidos'><span class='badge-feat'>Pedidos</span><h4>Auditoría Desplegable</h4><p>ExpansionTile por pedido que audita disponibilidad línea a línea, faltantes monetarios y descuento transaccional de stock.</p></div><div class='feature-item' data-feature='agrupacion'><span class='badge-feat'>Agrupación</span><h4>Batch Picking O(L)</h4><p>Consolidación de demandas en una pasada para que el operario visite cada celda de stock una sola vez sin traslados repetidos.</p></div><div class='feature-item' data-feature='topn'><span class='badge-feat'>Top-N</span><h4>Priorización Min-Heap</h4><p>Visualización con barras de demanda relativa y selección rápida mediante heapq.nlargest con memoria O(k) estrictamente acotada.</p></div><div class='feature-item' data-feature='alternativas'><span class='badge-feat'>Alternativas</span><h4>Sustitutos DP Memoizada</h4><p>Exploración de paquetes sustitutos bajo presupuesto evitando colapsos de stack recursivo en menos de 1 milisegundo.</p></div><div class='feature-item' data-feature='comparacion'><span class='badge-feat'>Comparación</span><h4>Desafío en Vivo</h4><p>Tabla dinámica de medición en tiempo real con badges de microsegundos y cálculo interactivo del Speedup empírico.</p></div></div>",
    "notes": "Pasar a la demostración en vivo de la aplicación si el tribunal lo solicita, utilizando el dataset demo_oral.json para exhibir la reactividad de la interfaz y la auditoría de pedidos."
  },
  {
    "id": 11,
    "tag": "11. CONCLUSIONES Y AUTOCRÍTICA",
    "title": "Conclusiones, Lecciones Aprendidas y Autocrítica",
    "subtitle": "Evaluación crítica exigida por la rúbrica para el cierre riguroso de la exposición oral",
    "content_html": "<div class='three-col'><div class='panel highlight'><div class='conclusion-header'><span class='conclusion-icon'>🏆</span><h3>Mayor Impacto</h3></div><ul class='bullet-list'><li><strong>Programación Dinámica:</strong> Evitó el colapso exponencial O(2^N) pasando de minutos incomputables a <strong>< 1 ms</strong> en combinaciones sustitutas.</li><li><strong>Catálogo Hash:</strong> Redujo la búsqueda de pedidos de O(P · L · n) a O(P · L), generando una aceleración de <strong>27x a 260x</strong>.</li></ul></div><div class='panel'><div class='conclusion-header'><span class='conclusion-icon'>⚠️</span><h3>Decisión Subóptima</h3></div><ul class='bullet-list'><li><strong>Paralelismo Multiproceso:</strong> Para operaciones O(1) en RAM, la serialización <code>pickle</code> e IPC en Windows anuló cualquier ventaja multinúcleo.</li><li>La optimización mono-hilo fue <strong>28 veces más rápida</strong> que el clúster multiproceso.</li></ul></div><div class='panel'><div class='conclusion-header'><span class='conclusion-icon'>🚀</span><h3>¿Qué Haríamos Diferente?</h3></div><ul class='bullet-list'><li><strong>Memoria Compartida:</strong> Emplear <code>multiprocessing.shared_memory</code> o buffers contiguos de NumPy.</li><li><strong>Extensiones Nativas:</strong> Implementar los bucles críticos en Cython/Rust para exprimir la CPU.</li><li><strong>Persistencia Indexada:</strong> SQLite en memoria con índices B-Tree para queries multivariable.</li></ul></div></div><div class='mt-3' style='text-align: center;'><button type='button' class='btn btn-primary btn-pack-slide' id='btn-pack-from-slide' style='font-size: 13.5px; padding: 10px 22px; gap: 8px;'><span>📦 Empaquetar y Despachar Presentación</span></button></div>",
    "notes": "Cerrar con autocrítica rigurosa: un buen ingeniero de software no solo sabe cuándo usar concurrencia, sino cuándo NO usarla porque la sobrecarga de coordinación supera al cómputo puro."
  }
];

  let slides = FALLBACK_SLIDES;
  let currentIndex = 0;
  let isBookClosed = true;
  let isPackaging = false;
  let timerInterval = null;
  let timerSeconds = 15 * 60; // 15 minutos oficiales
  let timerRunning = false;
  let simRunning = false;

  // Elementos DOM Principales
  const slideCounter = document.getElementById('slide-counter');
  const progressBar = document.getElementById('progress-bar');
  const selectSlide = document.getElementById('select-slide');
  const btnPrev = document.getElementById('btn-prev');
  const btnNext = document.getElementById('btn-next');
  const btnFullscreen = document.getElementById('btn-fullscreen');
  const btnNotes = document.getElementById('btn-notes');
  const btnShortcuts = document.getElementById('btn-shortcuts');
  const speakerModal = document.getElementById('speaker-modal');
  const shortcutsModal = document.getElementById('shortcuts-modal');
  const speakerText = document.getElementById('speaker-text');
  const btnCloseNotes = document.getElementById('btn-close-notes');
  const btnCloseShortcuts = document.getElementById('btn-close-shortcuts');
  const timerDisplay = document.getElementById('timer-display');
  const btnTimer = document.getElementById('btn-timer');
  const btnMotion = document.getElementById('btn-motion');
  const motionLabel = document.getElementById('motion-label');
  const slidePills = document.getElementById('slide-pills');
  const bgCanvas = document.getElementById('bg-canvas');

  // Elementos del Libro 3D y Empaquetado
  const bookCoverClosed = document.getElementById('book-cover-closed');
  const bookOpened = document.getElementById('book-opened');
  const btnOpenBook = document.getElementById('btn-open-book');
  const currentSlideCard = document.getElementById('current-slide-card');
  const stackLeft = document.getElementById('stack-left');
  const stackRight = document.getElementById('stack-right');
  const bookTurningLeaf = document.getElementById('book-turning-leaf');
  const turningMesh = document.getElementById('turning-mesh');
  const turningCastShadow = document.getElementById('turning-cast-shadow');
  const dragHandleRight = document.getElementById('drag-handle-right');
  const dragHandleLeft = document.getElementById('drag-handle-left');
  const packagingOverlay = document.getElementById('packaging-overlay');
  const packedManualBook = document.getElementById('packed-manual-book');
  const isoBox3d = document.getElementById('iso-box-3d');
  const isoBoxStage = document.getElementById('iso-box-stage');
  const btnReopenBook = document.getElementById('btn-reopen-book');
  const btnReopenHud = document.getElementById('btn-reopen-hud');
  const btnPackPresentation = document.getElementById('btn-pack-presentation');
  const packInspectHint = document.getElementById('pack-inspect-hint');
  const btnPuntuar = document.getElementById('btn-puntuar');
  const btnPuntuarHud = document.getElementById('btn-puntuar-hud');
  const btnPeelLabel = document.getElementById('btn-peel-label');
  const btnStampConfirm = document.getElementById('btn-stamp-confirm');
  const btnGradeCancel = document.getElementById('btn-grade-cancel');
  const gradeDock = document.getElementById('grade-dock');
  const gradePads = document.getElementById('grade-pads');
  const gradeSeal = document.getElementById('grade-seal');
  const gradeSealScore = document.getElementById('grade-seal-score');
  const stampPress = document.getElementById('stamp-press');
  const stampPressNote = document.getElementById('stamp-press-note');
  const MOTION_STORAGE_KEY = 'pef-presentation-force-motion';
  const reduceMotionMq = window.matchMedia('(prefers-reduced-motion: reduce)');
  const motionForced = () => document.documentElement.classList.contains('force-motion');
  const motionOff = () => reduceMotionMq.matches && !motionForced();

  function syncMotionButton() {
    if (!btnMotion) return;
    const animationsOn = !motionOff();
    btnMotion.classList.toggle('is-on', animationsOn);
    btnMotion.classList.toggle('is-off', !animationsOn);
    btnMotion.setAttribute('aria-pressed', animationsOn ? 'true' : 'false');
    if (motionLabel) {
      motionLabel.textContent = animationsOn ? 'Animaciones' : 'Sin animación';
    }
    btnMotion.title = animationsOn
      ? 'Animaciones activas. Clic para respetar la preferencia del sistema (Atajo: M)'
      : 'Windows apagó las animaciones del sistema. Clic para forzarlas en la defensa (Atajo: M)';
  }

  function setForceMotion(enabled) {
    document.documentElement.classList.toggle('force-motion', enabled);
    try {
      sessionStorage.setItem(MOTION_STORAGE_KEY, enabled ? '1' : '0');
    } catch (e) {}
    if (typeof canvasEngine !== 'undefined' && canvasEngine) {
      canvasEngine.setReducedMotion(motionOff());
    }
    syncMotionButton();
  }

  function toggleForceMotion() {
    setForceMotion(!motionForced());
  }

  // ==========================================================================
  // MOTOR CANVAS REACTIVO Y CINÉTICO (PAPER STYLE BACKGROUND ENGINE)
  // ==========================================================================
  class PaperCanvasEngine {
    constructor(canvas) {
      this.canvas = canvas;
      if (!this.canvas) return;
      this.ctx = canvas.getContext('2d');
      this.particles = [];
      this.ripples = [];
      this.slideTheme = 1;
      this.width = 0;
      this.height = 0;
      this.dpr = Math.min(window.devicePixelRatio || 1, 2);
      this.mouse = { x: -1000, y: -1000, active: false };
      this.time = 0;
      this.orbitFocus = null;
      this.looping = false;
      this.reducedMotion = motionOff();

      this.initDimensions();
      this.initParticles();
      this.initEvents();
      this.startLoop();
    }

    initDimensions() {
      this.width = window.innerWidth;
      this.height = window.innerHeight;
      this.canvas.width = this.width * this.dpr;
      this.canvas.height = this.height * this.dpr;
      this.ctx.scale(this.dpr, this.dpr);
    }

    initParticles() {
      this.particles = [];
      const count = 48;
      const palette = [
        { r: 194, g: 65, b: 12, a: 0.18 },   // Terracotta stamp
        { r: 29, g: 78, b: 216, a: 0.15 },   // Blueprint blue
        { r: 21, g: 128, b: 61, a: 0.15 },   // Sage green
        { r: 15, g: 23, b: 42, a: 0.12 }     // Archival ink
      ];

      for (let i = 0; i < count; i++) {
        const pColor = palette[i % palette.length];
        this.particles.push({
          x: Math.random() * this.width,
          y: Math.random() * this.height,
          vx: (Math.random() - 0.5) * 0.7,
          vy: (Math.random() - 0.5) * 0.7,
          size: Math.random() * 3 + 1.5,
          color: pColor,
          angle: Math.random() * Math.PI * 2,
          angularSpeed: (Math.random() - 0.5) * 0.02,
          length: Math.random() * 10 + 4,
          targetX: 0,
          targetY: 0
        });
      }
    }

    initEvents() {
      window.addEventListener('resize', () => {
        this.initDimensions();
      });

      window.addEventListener('mousemove', (e) => {
        this.mouse.x = e.clientX;
        this.mouse.y = e.clientY;
        this.mouse.active = true;
        if (Math.random() < 0.12) {
          this.addRipple(e.clientX, e.clientY, 35, 'rgba(194, 65, 12, 0.12)');
        }
      });

      window.addEventListener('mouseleave', () => {
        this.mouse.active = false;
      });
    }

    addRipple(x, y, maxRadius, strokeColor) {
      this.ripples.push({
        x: x,
        y: y,
        radius: 4,
        maxRadius: maxRadius || 80,
        alpha: 0.35,
        color: strokeColor || 'rgba(194, 65, 12, 0.2)'
      });
    }

    onSlideChange(slideIndex, direction) {
      this.slideTheme = slideIndex + 1;
      this.orbitFocus = null;

      const startX = direction === 'left' ? this.width * 0.15 : (direction === 'right' ? this.width * 0.85 : this.width * 0.5);
      this.addRipple(startX, this.height * 0.5, this.width * 0.55, 'rgba(29, 78, 216, 0.22)');

      this.particles.forEach((p, idx) => {
        if (this.slideTheme === 2) {
          p.vx = (Math.random() - 0.5) * 3.2;
          p.vy = (Math.random() - 0.5) * 3.2;
        } else if (this.slideTheme === 3) {
          const isLeft = idx % 2 === 0;
          p.targetX = isLeft ? this.width * 0.28 : this.width * 0.72;
          p.targetY = this.height * 0.65;
        } else if (this.slideTheme === 5) {
          const quad = idx % 4;
          p.targetX = (quad % 2 === 0 ? 0.25 : 0.75) * this.width;
          p.targetY = (quad < 2 ? 0.35 : 0.75) * this.height;
        } else if (this.slideTheme === 7) {
          const stream = (idx % 3);
          p.targetY = this.height * (0.3 + stream * 0.22);
          p.vx = (stream + 1) * 1.5;
          p.vy = 0;
        } else if (this.slideTheme === 9) {
          p.vx = (Math.random() * 4 + 2);
          p.vy = (Math.random() - 0.5) * 0.4;
        } else {
          p.vx = (Math.random() - 0.5) * 0.8;
          p.vy = (Math.random() - 0.5) * 0.8;
        }
      });
    }

    setOrbitFocus(branch) {
      this.orbitFocus = branch;
      const targetCenterX = branch === 'baseline' ? this.width * 0.28 : this.width * 0.72;
      const targetCenterY = this.height * 0.65;
      this.addRipple(targetCenterX, targetCenterY, 120, branch === 'baseline' ? 'rgba(225, 29, 72, 0.3)' : 'rgba(21, 128, 61, 0.3)');
    }

    update() {
      this.time += 0.016;

      for (let i = this.ripples.length - 1; i >= 0; i--) {
        const r = this.ripples[i];
        r.radius += (r.maxRadius - r.radius) * 0.07 + 0.8;
        r.alpha -= 0.008;
        if (r.alpha <= 0 || r.radius >= r.maxRadius) {
          this.ripples.splice(i, 1);
        }
      }

      this.particles.forEach((p, idx) => {
        p.angle += p.angularSpeed;

        if (this.slideTheme === 3) {
          let targetX = (idx % 2 === 0) ? this.width * 0.28 : this.width * 0.72;
          let targetY = this.height * 0.65;
          if (this.orbitFocus === 'baseline' && idx % 2 === 0) {
            p.vx += (targetX - p.x) * 0.004;
            p.vy += (targetY - p.y) * 0.004;
          } else if (this.orbitFocus === 'opt' && idx % 2 !== 0) {
            p.vx += (targetX - p.x) * 0.004;
            p.vy += (targetY - p.y) * 0.004;
          } else {
            p.vx += (targetX - p.x) * 0.001;
            p.vy += (targetY - p.y) * 0.001;
          }
          p.vx *= 0.95;
          p.vy *= 0.95;
        } else if (this.slideTheme === 5 && p.targetX && p.targetY) {
          p.vx += (p.targetX - p.x) * 0.0015;
          p.vy += (p.targetY - p.y) * 0.0015;
          p.vx *= 0.94;
          p.vy *= 0.94;
        } else if (this.slideTheme === 7 || this.slideTheme === 9) {
          if (p.x > this.width + 20) p.x = -20;
        } else {
          p.vx += Math.sin(this.time * 0.5 + idx) * 0.015;
          p.vy += Math.cos(this.time * 0.5 + idx) * 0.015;
          p.vx = Math.max(-1.2, Math.min(1.2, p.vx));
          p.vy = Math.max(-1.2, Math.min(1.2, p.vy));
        }

        if (this.mouse.active) {
          const dx = p.x - this.mouse.x;
          const dy = p.y - this.mouse.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 100 && dist > 0) {
            const force = (100 - dist) / 100 * 1.5;
            p.vx += (dx / dist) * force;
            p.vy += (dy / dist) * force;
          }
        }

        p.x += p.vx;
        p.y += p.vy;

        if (p.x < -30) p.x = this.width + 30;
        if (p.x > this.width + 30) p.x = -30;
        if (p.y < -30) p.y = this.height + 30;
        if (p.y > this.height + 30) p.y = -30;
      });
    }

    draw() {
      this.ctx.clearRect(0, 0, this.width, this.height);
      this.drawTopographicWaves();

      if (this.slideTheme === 6) {
        this.drawTreeConnections();
      }

      if (this.slideTheme === 8) {
        this.drawScannerBar();
      }

      this.ripples.forEach(r => {
        this.ctx.beginPath();
        this.ctx.arc(r.x, r.y, r.radius, 0, Math.PI * 2);
        this.ctx.strokeStyle = r.color;
        this.ctx.lineWidth = 1.5;
        this.ctx.globalAlpha = Math.max(0, r.alpha);
        this.ctx.stroke();
      });
      this.ctx.globalAlpha = 1;

      this.particles.forEach(p => {
        this.ctx.save();
        this.ctx.translate(p.x, p.y);
        this.ctx.rotate(p.angle);
        this.ctx.fillStyle = `rgba(${p.color.r}, ${p.color.g}, ${p.color.b}, ${p.color.a})`;
        this.ctx.beginPath();
        this.ctx.roundRect(-p.length / 2, -p.size / 2, p.length, p.size, 2);
        this.ctx.fill();
        this.ctx.restore();
      });
    }

    drawTopographicWaves() {
      const waveConfigs = [
        { yFactor: 0.35, amp: 28, freq: 0.0018, color: 'rgba(194, 65, 12, 0.035)', speed: 0.6 },
        { yFactor: 0.65, amp: 36, freq: 0.0014, color: 'rgba(29, 78, 216, 0.03)', speed: 0.4 },
        { yFactor: 0.88, amp: 24, freq: 0.0022, color: 'rgba(15, 23, 42, 0.025)', speed: 0.8 }
      ];

      waveConfigs.forEach(w => {
        this.ctx.beginPath();
        const baseY = this.height * w.yFactor;
        this.ctx.moveTo(0, baseY);

        for (let x = 0; x <= this.width; x += 30) {
          const offset = Math.sin(x * w.freq + this.time * w.speed) * w.amp;
          this.ctx.lineTo(x, baseY + offset);
        }

        this.ctx.strokeStyle = w.color;
        this.ctx.lineWidth = 2;
        this.ctx.stroke();
      });
    }

    drawTreeConnections() {
      this.ctx.strokeStyle = 'rgba(21, 128, 61, 0.12)';
      this.ctx.lineWidth = 1;
      for (let i = 0; i < this.particles.length; i++) {
        for (let j = i + 1; j < this.particles.length; j++) {
          const p1 = this.particles[i];
          const p2 = this.particles[j];
          const dx = p1.x - p2.x;
          const dy = p1.y - p2.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 120) {
            this.ctx.beginPath();
            this.ctx.moveTo(p1.x, p1.y);
            this.ctx.lineTo(p2.x, p2.y);
            this.ctx.stroke();
          }
        }
      }
    }

    drawScannerBar() {
      const scanX = ((this.time * 90) % (this.width + 100)) - 50;
      this.ctx.save();
      this.ctx.beginPath();
      this.ctx.moveTo(scanX, 0);
      this.ctx.lineTo(scanX, this.height);
      this.ctx.strokeStyle = 'rgba(29, 78, 216, 0.14)';
      this.ctx.lineWidth = 3;
      this.ctx.setLineDash([8, 6]);
      this.ctx.stroke();
      this.ctx.restore();
    }

    setReducedMotion(off) {
      this.reducedMotion = off;
      if (!off) this.startLoop();
    }

    startLoop() {
      if (this.reducedMotion) {
        this.looping = false;
        this.update();
        this.draw();
        return;
      }
      if (this.looping) return;
      this.looping = true;

      const loop = () => {
        if (this.reducedMotion) {
          this.looping = false;
          this.update();
          this.draw();
          return;
        }
        this.update();
        this.draw();
        requestAnimationFrame(loop);
      };
      requestAnimationFrame(loop);
    }
  }

  const canvasEngine = new PaperCanvasEngine(bgCanvas);

  // ==========================================================================
  // APERTURA Y CONTROL DEL LIBRO 3D
  // ==========================================================================
  function openBook() {
    if (!isBookClosed) return;

    if (motionOff()) {
      if (bookCoverClosed) bookCoverClosed.style.display = 'none';
      if (bookOpened) bookOpened.style.display = 'flex';
      isBookClosed = false;
      renderSlide(0, 'none', false);
      return;
    }

    if (bookOpened) {
      bookOpened.style.display = 'flex';
    }
    isBookClosed = false;
    renderSlide(0, 'none', false);

    let coverSettled = false;
    const settleCover = () => {
      if (coverSettled) return;
      coverSettled = true;
      if (bookCoverClosed) {
        bookCoverClosed.style.display = 'none';
        bookCoverClosed.classList.remove('opening');
      }
    };

    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        if (!bookCoverClosed) {
          settleCover();
          return;
        }
        bookCoverClosed.addEventListener('animationend', (ev) => {
          if (ev.target !== bookCoverClosed) return;
          settleCover();
        }, { once: true });
        bookCoverClosed.classList.add('opening');
      });
    });

    if (canvasEngine) {
      canvasEngine.addRipple(window.innerWidth * 0.4, window.innerHeight * 0.5, 400, 'rgba(194, 65, 12, 0.3)');
    }

    setTimeout(settleCover, 1250);
  }

  function updatePageStackDepth(index) {
    if (!stackLeft || !stackRight) return;
    const total = Math.max(1, slides.length - 1);
    const ratio = Math.max(0, Math.min(1, index / total));
    stackLeft.style.transform = `scaleX(${0.2 + ratio * 1.5})`;
    stackRight.style.transform = `scaleX(${0.2 + (1 - ratio) * 1.5})`;
  }

  // ==========================================================================
  // MOTOR DE PÁGINA ARTICULADA (CURL POR TIRAS + FÍSICA DE ARRASTRE)
  // ==========================================================================
  const STRIP_COUNT = 12;
  let isFlipping = false;
  let flipStrips = [];
  let flipProgress = 0;
  let flipForward = true;
  let meshReady = false;

  function easeOutQuint(t) {
    return 1 - Math.pow(1 - t, 5);
  }

  function clamp01(v) {
    return Math.max(0, Math.min(1, v));
  }

  function buildTurningMesh() {
    if (!turningMesh || meshReady) return;
    turningMesh.style.setProperty('--strip-count', String(STRIP_COUNT));
    turningMesh.innerHTML = '';
    flipStrips = [];

    let parent = turningMesh;
    for (let i = 0; i < STRIP_COUNT; i++) {
      const strip = document.createElement('div');
      strip.className = 'leaf-strip' + (i === STRIP_COUNT - 1 ? ' is-edge' : '');
      strip.style.setProperty('--strip-index', String(i));

      const front = document.createElement('div');
      front.className = 'strip-front';
      const inner = document.createElement('div');
      inner.className = 'strip-inner';
      front.appendChild(inner);

      const back = document.createElement('div');
      back.className = 'strip-back';
      back.innerHTML = `
        <div class="archive-watermark">MANUAL TÉCNICO • UBP 2026</div>
        <div class="archive-seal">AUDITADO<br>DETERMINISTA</div>
        <div class="archive-folio"></div>
      `;

      const shade = document.createElement('div');
      shade.className = 'strip-shade';

      strip.appendChild(front);
      strip.appendChild(back);
      strip.appendChild(shade);
      parent.appendChild(strip);
      flipStrips.push({ strip, inner, shade, folio: back.querySelector('.archive-folio') });
      parent = strip;
    }
    meshReady = true;
  }

  function stripDeltas(progress) {
    const curl = Math.sin(progress * Math.PI);
    const weights = [];
    for (let i = 0; i < STRIP_COUNT; i++) {
      const x = i / Math.max(1, STRIP_COUNT - 1);
      weights.push(1 + curl * 0.28 * Math.pow(x, 1.15));
    }
    const sum = weights.reduce((a, b) => a + b, 0);
    const total = progress * 180;
    return weights.map((w) => total * (w / sum));
  }

  function applyFlipProgress(progress, isForward) {
    flipProgress = progress;
    const deltas = stripDeltas(progress);
    let accum = 0;
    for (let i = 0; i < flipStrips.length; i++) {
      const deg = isForward ? -deltas[i] : deltas[i];
      flipStrips[i].strip.style.transform = `rotateY(${deg}deg)`;
      accum += deltas[i];
      const crease = Math.pow(Math.abs(Math.sin((accum * Math.PI) / 180)), 1.35);
      const highlight = Math.max(0, Math.cos((accum * Math.PI) / 180));
      flipStrips[i].shade.style.opacity = String(0.06 + crease * 0.22);
      flipStrips[i].shade.style.background = `linear-gradient(90deg,
        rgba(15,23,42,${0.04 + crease * 0.16}) 0%,
        rgba(255,255,255,${0.10 * highlight}) 50%,
        rgba(15,23,42,${0.05 + crease * 0.18}) 100%)`;
    }
    if (turningMesh) {
      const lift = Math.sin(progress * Math.PI) * 5;
      turningMesh.style.transform = `translateZ(1.5px) rotateX(${lift}deg)`;
    }
    if (turningCastShadow) {
      const shadowLift = Math.sin(progress * Math.PI);
      turningCastShadow.style.opacity = String(shadowLift * 0.4);
      turningCastShadow.style.transform = `scaleX(${0.25 + progress * 0.75})`;
    }
  }

  function sanitizeClone(root) {
    root.querySelectorAll('[id]').forEach((el) => el.removeAttribute('id'));
  }

  function paintLeafContent(html, folioText) {
    flipStrips.forEach((item) => {
      item.inner.innerHTML = `<div class="slide-card turning-clone">${html}</div>`;
      sanitizeClone(item.inner);
      if (item.folio) item.folio.textContent = folioText;
    });
  }

  function showTurningLeaf() {
    if (!bookTurningLeaf) return;
    bookTurningLeaf.classList.add('is-active');
    bookTurningLeaf.style.display = 'block';
    if (bookOpened) bookOpened.classList.add('is-flipping');
  }

  function hideTurningLeaf() {
    if (!bookTurningLeaf) return;
    bookTurningLeaf.classList.remove('is-active');
    bookTurningLeaf.style.display = 'none';
    if (bookOpened) bookOpened.classList.remove('is-flipping');
    flipStrips.forEach((item) => { item.inner.innerHTML = ''; });
    if (turningCastShadow) turningCastShadow.style.opacity = '0';
  }

  function animateProgress(from, to, duration, isForward, onDone) {
    const start = performance.now();
    const tick = (now) => {
      const t = clamp01((now - start) / duration);
      applyFlipProgress(from + (to - from) * easeOutQuint(t), isForward);
      if (t < 1) {
        requestAnimationFrame(tick);
      } else if (onDone) {
        onDone();
      }
    };
    requestAnimationFrame(tick);
  }

  function renderCardHTML(slide, index) {
    return `
      <div class="slide-header">
        <span class="slide-tag">${slide.tag || `Página ${index + 1}`}</span>
        <h2 class="slide-title">${slide.title}</h2>
        ${slide.subtitle ? `<p class="slide-subtitle">${slide.subtitle}</p>` : ''}
      </div>
      <div class="slide-body">
        ${slide.content_html}
      </div>
    `;
  }

  function updateControlsUI() {
    const currentSlide = slides[currentIndex];
    slideCounter.textContent = `${currentIndex + 1} / ${slides.length}`;
    selectSlide.value = currentIndex;
    const progressRatio = (currentIndex + 1) / slides.length;
    progressBar.style.transform = `scaleX(${progressRatio})`;

    if (slidePills) {
      const pills = slidePills.querySelectorAll('.slide-pill');
      pills.forEach((p, idx) => {
        p.classList.toggle('active', idx === currentIndex);
      });
    }

    btnPrev.disabled = (currentIndex === 0);
    btnNext.disabled = (currentIndex === slides.length - 1);

    speakerText.textContent = currentSlide.notes || "No hay notas adicionales para esta diapositiva.";
  }

  function finishFlipTo(targetIndex, direction) {
    currentIndex = targetIndex;
    updateControlsUI();
    initSlideInteractiveBehaviors(slides[currentIndex].id);
    if (canvasEngine) canvasEngine.onSlideChange(currentIndex, direction);
    updatePageStackDepth(currentIndex);
    hideTurningLeaf();
    isFlipping = false;
  }

  function flipToSlide(targetIndex, direction) {
    if (isFlipping || targetIndex === currentIndex) return;
    if (targetIndex < 0 || targetIndex >= slides.length) return;

    if (motionOff() || !bookTurningLeaf || !turningMesh) {
      renderSlide(targetIndex, direction, false);
      return;
    }

    buildTurningMesh();
    isFlipping = true;
    const isForward = targetIndex > currentIndex;
    const outgoing = slides[currentIndex];
    const incoming = slides[targetIndex];
    const dirKey = isForward ? 'right' : 'left';

    showTurningLeaf();

    if (isForward) {
      paintLeafContent(currentSlideCard.innerHTML, `ARCHIVADO • ${outgoing.tag || `Pág. ${currentIndex + 1}`}`);
      currentIndex = targetIndex;
      currentSlideCard.innerHTML = renderCardHTML(incoming, currentIndex);
      updatePageStackDepth(currentIndex);
      applyFlipProgress(0, true);
      animateProgress(0, 1, 620, true, () => finishFlipTo(targetIndex, dirKey));
    } else {
      paintLeafContent(renderCardHTML(incoming, targetIndex), `ARCHIVADO • ${outgoing.tag || `Pág. ${currentIndex + 1}`}`);
      applyFlipProgress(1, true);
      animateProgress(1, 0, 620, true, () => {
        currentSlideCard.innerHTML = renderCardHTML(incoming, targetIndex);
        finishFlipTo(targetIndex, dirKey);
      });
    }
  }

  function initDragToFlip() {
    if (!bookOpened || !bookTurningLeaf) return;
    buildTurningMesh();

    let dragging = false;
    let armed = false;
    let startX = 0;
    let lastX = 0;
    let lastT = 0;
    let velocity = 0;
    let mode = null;
    let targetIndex = -1;
    let liveProgress = 0;
    let pointerId = null;

    const beginTurn = (isForward) => {
      mode = isForward ? 'forward' : 'back';
      targetIndex = isForward ? currentIndex + 1 : currentIndex - 1;
      const outgoing = slides[currentIndex];
      showTurningLeaf();
      if (isForward) {
        paintLeafContent(currentSlideCard.innerHTML, `ARCHIVADO • ${outgoing.tag || `Pág. ${currentIndex + 1}`}`);
        currentSlideCard.innerHTML = renderCardHTML(slides[targetIndex], targetIndex);
      } else {
        paintLeafContent(renderCardHTML(slides[targetIndex], targetIndex), `ARCHIVADO • ${outgoing.tag || `Pág. ${currentIndex + 1}`}`);
      }
      applyFlipProgress(isForward ? 0 : 1, true);
      liveProgress = isForward ? 0 : 1;
    };

    const onDown = (e) => {
      if (isBookClosed || isPackaging || isFlipping || motionOff()) return;
      if (e.target.closest('button, input, select, textarea, a, .tab-btn, .tab-nav, .tabs-container, .ipc-seg, .struct-card')) return;
      dragging = true;
      armed = false;
      startX = e.clientX;
      lastX = e.clientX;
      lastT = performance.now();
      velocity = 0;
      mode = null;
      pointerId = e.pointerId;
      if (e.target.setPointerCapture) {
        try { e.target.setPointerCapture(e.pointerId); } catch (err) { /* ignore */ }
      }
    };

    const onMove = (e) => {
      if (!dragging) return;
      const now = performance.now();
      const dx = e.clientX - startX;
      const dt = Math.max(8, now - lastT);
      velocity = (e.clientX - lastX) / dt;
      lastX = e.clientX;
      lastT = now;

      if (!armed && Math.abs(dx) < 12) return;

      const canForward = currentIndex < slides.length - 1;
      const canBack = currentIndex > 0;

      if (!armed) {
        if (dx < 0 && canForward) {
          armed = true;
          isFlipping = true;
          beginTurn(true);
        } else if (dx > 0 && canBack) {
          armed = true;
          isFlipping = true;
          beginTurn(false);
        } else {
          return;
        }
      }

      const width = bookOpened.offsetWidth || 1000;
      let p;
      if (mode === 'forward') {
        p = clamp01(-dx / (width * 0.58));
      } else {
        p = clamp01(1 - dx / (width * 0.58));
      }
      liveProgress += (p - liveProgress) * 0.34;
      applyFlipProgress(liveProgress, true);
    };

    const settle = (complete) => {
      const isForward = mode === 'forward';
      const dest = complete ? (isForward ? 1 : 0) : (isForward ? 0 : 1);
      const dist = Math.abs(dest - liveProgress);
      const duration = Math.round(280 + dist * 340);
      animateProgress(liveProgress, dest, duration, true, () => {
        if (complete) {
          if (!isForward) {
            currentSlideCard.innerHTML = renderCardHTML(slides[targetIndex], targetIndex);
          }
          finishFlipTo(targetIndex, isForward ? 'right' : 'left');
        } else {
          currentSlideCard.innerHTML = renderCardHTML(slides[currentIndex], currentIndex);
          initSlideInteractiveBehaviors(slides[currentIndex].id);
          hideTurningLeaf();
          isFlipping = false;
        }
      });
    };

    let skipHandleClick = false;

    const onUp = () => {
      if (!dragging) return;
      dragging = false;
      if (!armed || mode == null) return;
      skipHandleClick = true;
      const flick = mode === 'forward' ? velocity < -0.45 : velocity > 0.45;
      const farEnough = mode === 'forward' ? liveProgress > 0.28 : liveProgress < 0.72;
      settle(flick || farEnough);
    };

    bookOpened.addEventListener('pointerdown', onDown);
    window.addEventListener('pointermove', onMove);
    window.addEventListener('pointerup', onUp);
    window.addEventListener('pointercancel', onUp);

    if (dragHandleRight) {
      dragHandleRight.addEventListener('click', (e) => {
        if (skipHandleClick) { skipHandleClick = false; e.preventDefault(); return; }
        nextSlide();
      });
    }
    if (dragHandleLeft) {
      dragHandleLeft.addEventListener('click', (e) => {
        if (skipHandleClick) { skipHandleClick = false; e.preventDefault(); return; }
        prevSlide();
      });
    }
  }

  // ==========================================================================
  // RITUAL CINEMÁTICO DE EMPAQUETADO EN CAJA KRAFT ISOMÉTRICA 3D
  // ==========================================================================
  let packTimers = [];

  const boxInspect = {
    rotX: 22,
    rotY: -34,
    panX: 0,
    panY: 0,
    scale: 1,
    ready: false,
    locked: false,
    dragging: false,
    panning: false,
    lastX: 0,
    lastY: 0,
    apply() {
      if (!isoBoxStage) return;
      isoBoxStage.style.setProperty('--rx', `${this.rotX}deg`);
      isoBoxStage.style.setProperty('--ry', `${this.rotY}deg`);
      isoBoxStage.style.setProperty('--px', `${this.panX}px`);
      isoBoxStage.style.setProperty('--py', `${this.panY}px`);
      isoBoxStage.style.setProperty('--inspect-scale', String(this.scale));
    },
    reset(rotX, rotY, scale, ready = true) {
      this.rotX = rotX;
      this.rotY = rotY;
      this.panX = 0;
      this.panY = 0;
      this.scale = scale;
      this.ready = ready;
      if (packagingOverlay) packagingOverlay.classList.toggle('is-inspecting', ready);
      this.apply();
    }
  };

  const BOX_POSE_PACK = { rx: 22, ry: -34, scale: 1 };
  const BOX_POSE_READ = { rx: 8, ry: -4, scale: 1.16 };
  const BOX_POSE_PEEL = { rx: 20, ry: -10, scale: 1.3 };
  const BOX_POSE_ZENITH = { rx: -72, ry: 8, scale: 1.48 };
  const BOX_POSE_STRIKE = { rx: -18, ry: 44, scale: 1.56 };
  const BOX_POSE_SEALED = { rx: -48, ry: -18, scale: 1.32 };
  const BOX_UI_SELECTOR = '#btn-reopen-book, #btn-reopen-hud, #btn-puntuar, #btn-puntuar-hud, #btn-peel-label, #btn-stamp-confirm, #btn-grade-cancel, .grade-pad, .grade-dock, .iso-label-hinge, .iso-shipping-label, button, a, input';

  let isGrading = false;
  let pendingGrade = null;
  let packGrade = null;

  function readingScale() {
    return window.innerWidth < 1024 ? 0.82 : BOX_POSE_READ.scale;
  }

  function peelScale() {
    return window.innerWidth < 1024 ? 0.9 : BOX_POSE_PEEL.scale;
  }

  function zenithScale() {
    return window.innerWidth < 1024 ? 1.12 : BOX_POSE_ZENITH.scale;
  }

  function setLabelPeeled(on) {
    const wasPeeled = !!(isoBox3d && isoBox3d.classList.contains('label-peeled'));
    if (isoBox3d) isoBox3d.classList.toggle('label-peeled', !!on);
    if (btnPeelLabel) {
      btnPeelLabel.setAttribute('aria-expanded', on ? 'true' : 'false');
      btnPeelLabel.textContent = on ? 'Bajar guía' : 'Levantar guía';
    }
    if (!isoBoxStage || !boxInspect.ready || isGrading) return;
    isoBoxStage.classList.remove('is-orbiting');
    if (on) {
      boxInspect.reset(BOX_POSE_PEEL.rx, BOX_POSE_PEEL.ry, peelScale(), true);
    } else if (wasPeeled) {
      boxInspect.reset(BOX_POSE_READ.rx, BOX_POSE_READ.ry, readingScale(), true);
    }
  }

  function selectPendingGrade(n) {
    pendingGrade = n;
    if (!gradePads) return;
    gradePads.querySelectorAll('.grade-pad').forEach((el) => {
      const on = Number(el.dataset.grade) === n;
      el.classList.toggle('is-selected', on);
      el.setAttribute('aria-pressed', on ? 'true' : 'false');
    });
    if (btnStampConfirm) btnStampConfirm.disabled = !n;
  }

  function buildGradePads() {
    if (!gradePads || gradePads.dataset.ready === '1') return;
    gradePads.dataset.ready = '1';
    for (let n = 1; n <= 10; n += 1) {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'grade-pad';
      btn.dataset.grade = String(n);
      btn.textContent = String(n);
      btn.setAttribute('aria-pressed', 'false');
      btn.addEventListener('click', () => selectPendingGrade(n));
      gradePads.appendChild(btn);
    }
  }

  function enterGradeMode() {
    if (isGrading) return;
    if (!isoBox3d || !isoBox3d.classList.contains('labeled')) return;
    isGrading = true;
    boxInspect.locked = true;
    setLabelPeeled(false);
    if (isoBoxStage) isoBoxStage.classList.remove('is-orbiting');
    boxInspect.reset(BOX_POSE_ZENITH.rx, BOX_POSE_ZENITH.ry, zenithScale(), true);
    boxInspect.locked = true;
    if (packagingOverlay) packagingOverlay.classList.add('is-grading');
    if (gradeDock) {
      gradeDock.hidden = false;
      gradeDock.removeAttribute('hidden');
    }
    if (packInspectHint) packInspectHint.classList.remove('is-visible');
    if (btnPuntuarHud) btnPuntuarHud.hidden = true;
    if (packGrade) {
      selectPendingGrade(packGrade);
    } else {
      selectPendingGrade(0);
      pendingGrade = null;
      if (btnStampConfirm) btnStampConfirm.disabled = true;
    }
  }

  function exitGradeMode(restoreView) {
    isGrading = false;
    boxInspect.locked = false;
    if (packagingOverlay) packagingOverlay.classList.remove('is-grading');
    if (gradeDock) gradeDock.hidden = true;
    if (restoreView && isoBoxStage) {
      isoBoxStage.classList.remove('is-orbiting');
      const pose = packGrade ? BOX_POSE_SEALED : BOX_POSE_READ;
      const scale = packGrade
        ? (window.innerWidth < 1024 ? 1.08 : BOX_POSE_SEALED.scale)
        : readingScale();
      boxInspect.reset(pose.rx, pose.ry, scale, true);
    }
    if (restoreView && packInspectHint) packInspectHint.classList.add('is-visible');
    if (btnPuntuarHud) btnPuntuarHud.hidden = false;
  }

  function pressSeal() {
    if (!pendingGrade) return;
    packGrade = pendingGrade;
    if (gradeSealScore) gradeSealScore.textContent = String(packGrade);
    document.querySelectorAll('.stamp-grade-num').forEach((el) => {
      el.textContent = String(packGrade);
    });
    if (gradeDock) gradeDock.hidden = true;
    if (packagingOverlay) packagingOverlay.classList.add('is-stamping');
    if (isoBoxStage) isoBoxStage.classList.remove('is-orbiting');
    boxInspect.reset(
      BOX_POSE_STRIKE.rx,
      BOX_POSE_STRIKE.ry,
      window.innerWidth < 1024 ? 1.18 : BOX_POSE_STRIKE.scale,
      true
    );
    boxInspect.locked = true;

    if (stampPress) {
      stampPress.hidden = false;
      stampPress.classList.remove('is-striking');
      void stampPress.offsetWidth;
      stampPress.classList.add('is-striking');
    }

    const inkAt = motionOff() ? 0 : 640;
    const doneAt = motionOff() ? 80 : 1700;

    setTimeout(() => {
      if (gradeSeal) {
        gradeSeal.hidden = false;
        gradeSeal.classList.remove('is-inked');
        void gradeSeal.offsetWidth;
        gradeSeal.classList.add('is-inked');
      }
    }, inkAt);

    setTimeout(() => {
      if (stampPress) {
        stampPress.classList.remove('is-striking');
        stampPress.hidden = true;
      }
      if (packagingOverlay) packagingOverlay.classList.remove('is-stamping');
      exitGradeMode(true);
    }, doneAt);
  }

  function initBoxRitualUI() {
    buildGradePads();
    const reopen = (e) => {
      e.preventDefault();
      e.stopPropagation();
      reopenManual();
    };
    if (btnReopenBook) btnReopenBook.addEventListener('click', reopen);
    if (btnReopenHud) btnReopenHud.addEventListener('click', reopen);
    if (btnPuntuar) btnPuntuar.addEventListener('click', (e) => {
      e.stopPropagation();
      enterGradeMode();
    });
    if (btnPuntuarHud) btnPuntuarHud.addEventListener('click', (e) => {
      e.stopPropagation();
      enterGradeMode();
    });
    if (btnPeelLabel) btnPeelLabel.addEventListener('click', (e) => {
      e.stopPropagation();
      if (isGrading || !isoBox3d || !isoBox3d.classList.contains('labeled')) return;
      setLabelPeeled(!isoBox3d.classList.contains('label-peeled'));
    });
    if (btnStampConfirm) btnStampConfirm.addEventListener('click', (e) => {
      e.stopPropagation();
      pressSeal();
    });
    if (btnGradeCancel) btnGradeCancel.addEventListener('click', (e) => {
      e.stopPropagation();
      exitGradeMode(true);
    });
  }

  function initBoxInspect() {
    if (!packagingOverlay || !isoBoxStage || packagingOverlay.dataset.inspectBound === '1') return;
    packagingOverlay.dataset.inspectBound = '1';

    const onDown = (e) => {
      if (!boxInspect.ready || boxInspect.locked || isGrading) return;
      if (e.target.closest(BOX_UI_SELECTOR)) return;
      boxInspect.dragging = true;
      boxInspect.panning = e.shiftKey || e.button === 1;
      boxInspect.lastX = e.clientX;
      boxInspect.lastY = e.clientY;
      isoBoxStage.classList.add('is-orbiting');
      if (e.currentTarget.setPointerCapture) {
        try { e.currentTarget.setPointerCapture(e.pointerId); } catch (err) { /* ignore */ }
      }
      e.preventDefault();
    };

    const onMove = (e) => {
      if (!boxInspect.dragging) return;
      const dx = e.clientX - boxInspect.lastX;
      const dy = e.clientY - boxInspect.lastY;
      boxInspect.lastX = e.clientX;
      boxInspect.lastY = e.clientY;
      if (boxInspect.panning || e.shiftKey) {
        boxInspect.panX += dx;
        boxInspect.panY += dy;
      } else {
        boxInspect.rotY += dx * 0.45;
        boxInspect.rotX = Math.max(-80, Math.min(42, boxInspect.rotX + dy * 0.38));
      }
      boxInspect.apply();
    };

    const onUp = () => {
      if (!boxInspect.dragging) return;
      boxInspect.dragging = false;
      boxInspect.panning = false;
      isoBoxStage.classList.remove('is-orbiting');
    };

    packagingOverlay.addEventListener('pointerdown', onDown);
    window.addEventListener('pointermove', onMove);
    window.addEventListener('pointerup', onUp);
    window.addEventListener('pointercancel', onUp);

    packagingOverlay.addEventListener('wheel', (e) => {
      if (!boxInspect.ready || boxInspect.locked || isGrading) return;
      e.preventDefault();
      const next = boxInspect.scale + (e.deltaY > 0 ? -0.08 : 0.08);
      boxInspect.scale = Math.max(0.55, Math.min(2.2, next));
      isoBoxStage.classList.add('is-orbiting');
      boxInspect.apply();
    }, { passive: false });

    packagingOverlay.addEventListener('dblclick', (e) => {
      if (!boxInspect.ready || boxInspect.locked || isGrading) return;
      if (e.target.closest(BOX_UI_SELECTOR)) return;
      isoBoxStage.classList.remove('is-orbiting');
      boxInspect.reset(BOX_POSE_READ.rx, BOX_POSE_READ.ry, readingScale(), true);
    });
  }

  function clearPackTimers() {
    packTimers.forEach((id) => clearTimeout(id));
    packTimers = [];
  }

  function later(ms, fn) {
    packTimers.push(setTimeout(fn, ms));
  }

  function startPackagingRitual() {
    if (isPackaging) return;
    isPackaging = true;
    clearPackTimers();
    exitGradeMode(false);
    setLabelPeeled(false);
    boxInspect.locked = false;

    if (packagingOverlay) {
      packagingOverlay.style.display = 'flex';
      packagingOverlay.setAttribute('aria-hidden', 'false');
    }
    if (isoBoxStage) {
      isoBoxStage.classList.remove('hero-angle', 'inspectable', 'is-orbiting');
      boxInspect.reset(BOX_POSE_PACK.rx, BOX_POSE_PACK.ry, BOX_POSE_PACK.scale, false);
    }
    if (packInspectHint) packInspectHint.classList.remove('is-visible');
    if (packedManualBook) packedManualBook.className = 'packed-manual-book';
    if (isoBox3d) isoBox3d.className = 'iso-box-3d';

    if (motionOff()) {
      if (packedManualBook) packedManualBook.classList.add('dropped-in');
      if (isoBox3d) isoBox3d.classList.add('closing-sides', 'closing-flaps', 'taped', 'labeled');
      if (isoBoxStage) {
        isoBoxStage.classList.add('hero-angle', 'inspectable');
        boxInspect.reset(BOX_POSE_READ.rx, BOX_POSE_READ.ry, readingScale(), true);
      }
      if (packInspectHint) packInspectHint.classList.add('is-visible');
      return;
    }

    later(180, () => {
      if (packedManualBook) packedManualBook.classList.add('dropped-in');
    });
    later(920, () => {
      if (canvasEngine) {
        canvasEngine.addRipple(window.innerWidth * 0.5, window.innerHeight * 0.46, 320, 'rgba(194, 65, 12, 0.32)');
      }
      if (isoBox3d) isoBox3d.classList.add('closing-sides');
    });
    later(1480, () => {
      if (isoBox3d) isoBox3d.classList.add('closing-flaps');
    });
    later(2080, () => {
      if (isoBox3d) isoBox3d.classList.add('taped');
      if (canvasEngine) {
        canvasEngine.addRipple(window.innerWidth * 0.5, window.innerHeight * 0.46, 200, 'rgba(180, 83, 9, 0.28)');
      }
    });
    later(2580, () => {
      if (isoBox3d) isoBox3d.classList.add('labeled');
      if (isoBoxStage) {
        isoBoxStage.classList.add('hero-angle', 'inspectable');
        boxInspect.reset(BOX_POSE_READ.rx, BOX_POSE_READ.ry, readingScale(), true);
      }
      if (packInspectHint) packInspectHint.classList.add('is-visible');
      if (canvasEngine) {
        canvasEngine.addRipple(window.innerWidth * 0.5, window.innerHeight * 0.46, 140, 'rgba(21, 128, 61, 0.28)');
      }
    });
  }

  function reopenManual() {
    clearPackTimers();
    if (packagingOverlay) {
      packagingOverlay.style.display = 'none';
      packagingOverlay.setAttribute('aria-hidden', 'true');
      packagingOverlay.classList.remove('is-inspecting', 'is-grading', 'is-stamping');
    }
    isPackaging = false;
    exitGradeMode(false);
    setLabelPeeled(false);
    boxInspect.locked = false;
    boxInspect.ready = false;
    if (packedManualBook) packedManualBook.className = 'packed-manual-book';
    if (isoBox3d) isoBox3d.className = 'iso-box-3d';
    if (isoBoxStage) {
      isoBoxStage.classList.remove('hero-angle', 'inspectable', 'is-orbiting');
      boxInspect.reset(BOX_POSE_PACK.rx, BOX_POSE_PACK.ry, BOX_POSE_PACK.scale, false);
    }
    if (packInspectHint) packInspectHint.classList.remove('is-visible');
    if (bookOpened) bookOpened.style.display = 'flex';
    if (bookCoverClosed) bookCoverClosed.style.display = 'none';
    isBookClosed = false;
    renderSlide(currentIndex, 'none', false);
  }

  // ==========================================================================
  // CARGA DE DIAPOSITIVAS Y NAVEGACIÓN
  // ==========================================================================
  async function cargarSlides() {
    try {
      const response = await fetch('slides.json');
      if (response.ok) {
        const data = await response.json();
        if (data && data.slides && data.slides.length > 0) {
          slides = data.slides;
        }
      }
    } catch (e) {
      console.warn('Usando dataset de diapositivas local por restricción CORS (file://):', e);
    }
    inicializarDropdown();
    inicializarPills();
    initDragToFlip();
    initBoxInspect();
    initBoxRitualUI();
  }

  function inicializarDropdown() {
    selectSlide.innerHTML = '';
    slides.forEach((s, idx) => {
      const opt = document.createElement('option');
      opt.value = idx;
      opt.textContent = `${s.tag || `Slide ${idx + 1}`}: ${s.title}`;
      selectSlide.appendChild(opt);
    });
  }

  function inicializarPills() {
    if (!slidePills) return;
    slidePills.innerHTML = '';
    slides.forEach((s, idx) => {
      const pill = document.createElement('button');
      pill.className = 'slide-pill' + (idx === currentIndex ? ' active' : '');
      pill.textContent = idx + 1;
      pill.title = s.tag || `Página ${idx + 1}`;
      pill.type = 'button';
      pill.setAttribute('aria-label', `Saltar a página ${idx + 1}: ${s.title}`);
      pill.addEventListener('click', () => {
        if (isBookClosed) openBook();
        const dir = idx > currentIndex ? 'right' : 'left';
        flipToSlide(idx, dir);
      });
      slidePills.appendChild(pill);
    });
  }

  function renderSlide(index, direction, usePageTurn = true) {
    if (index < 0 || index >= slides.length) return;
    if (usePageTurn && !isBookClosed && index !== currentIndex) {
      flipToSlide(index, direction);
      return;
    }

    currentIndex = index;
    const slide = slides[currentIndex];

    if (canvasEngine) {
      canvasEngine.onSlideChange(currentIndex, direction);
    }

    updatePageStackDepth(currentIndex);
    currentSlideCard.innerHTML = renderCardHTML(slide, currentIndex);
    updateControlsUI();
    initSlideInteractiveBehaviors(slide.id);
  }

  // ==========================================================================
  // COMPORTAMIENTOS INTERACTIVOS DENTRO DE LAS DIAPOSITIVAS
  // ==========================================================================
  function activateTabButton(btn) {
    if (!btn) return;
    const targetTabId = btn.getAttribute('data-tab');
    const tabsContainer = btn.closest('.tabs-container');
    if (!tabsContainer || !targetTabId) return;

    tabsContainer.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    tabsContainer.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

    btn.classList.add('active');
    const targetPane = tabsContainer.querySelector(`#${targetTabId}`);
    if (targetPane) {
      targetPane.classList.add('active');
    }
    if (targetTabId === 'tab-bench-chart') {
      animateSpeedupBars();
    }
  }

  function initSlideInteractiveBehaviors(slideId) {
    // 1. Pestañas (Tabs)
    const tabButtons = currentSlideCard.querySelectorAll('.tab-btn');
    tabButtons.forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        activateTabButton(btn);
      });
    });

    // 2. Diapositiva 03: Inspección de Arquitectura Dual
    if (slideId === 3) {
      const branchBase = document.getElementById('branch-baseline-card');
      const branchOpt = document.getElementById('branch-optimized-card');
      const flowMsg = document.getElementById('arch-flow-indicator');

      if (branchBase && branchOpt && flowMsg) {
        branchBase.addEventListener('click', () => {
          branchBase.classList.add('active');
          branchOpt.classList.remove('active');
          flowMsg.className = 'alert-box alert-base mt-3';
          flowMsg.style.borderColor = 'var(--stamp-crimson)';
          flowMsg.style.background = 'var(--stamp-crimson-bg)';
          flowMsg.innerHTML = "<strong>Ruta Baseline Activa:</strong> La fachada <code>MotorInventario</code> delega a <code>CatalogoLineal</code> en memoria contigua O(n). Sin indexación previa ni caching.";
          if (canvasEngine) canvasEngine.setOrbitFocus('baseline');
        });

        branchOpt.addEventListener('click', () => {
          branchOpt.classList.add('active');
          branchBase.classList.remove('active');
          flowMsg.className = 'alert-box info mt-3';
          flowMsg.style.borderColor = 'var(--stamp-sage)';
          flowMsg.style.background = 'var(--stamp-sage-bg)';
          flowMsg.innerHTML = "<strong>Ruta Optimizada Activa:</strong> La fachada delega a <code>dict</code> hash indexado O(1), min-heaps acotados y caché LRU reactiva con aceleración global de 718x.";
          if (canvasEngine) canvasEngine.setOrbitFocus('opt');
        });
      }
    }

    // 3. Diapositiva 04: Simulador Interactivo O(n) vs O(1)
    if (slideId === 4) {
      const btnRunSim = document.getElementById('btn-run-sim');
      const catalogSelect = document.getElementById('sim-catalog-size');
      const targetInput = document.getElementById('sim-target-id');

      if (catalogSelect && targetInput) {
        catalogSelect.addEventListener('change', () => {
          const n = parseInt(catalogSelect.value, 10);
          const targetIndex = Math.floor(n * 0.842);
          targetInput.value = `PROD-${targetIndex.toString().padStart(5, '0')}`;
          resetSimUI();
        });
      }

      if (btnRunSim) {
        btnRunSim.addEventListener('click', runSearchSimulation);
      }
    }

    // 4. Diapositiva 05: Inspector Interactivo de Estructuras
    if (slideId === 5) {
      const structCards = currentSlideCard.querySelectorAll('.struct-card');
      const detailBox = document.getElementById('struct-detail-box');
      const structData = {
        'list': "<strong>list en Python:</strong> Arreglo contiguo de punteros en C (<code>PyListObject</code>). Acceso indexado <code>O(1)</code> directo pero búsqueda lineal secuencial <code>O(n)</code>.",
        'dict': "<strong>dict en Python:</strong> Tabla hash compacta indexada en tiempo constante <code>O(1)</code> con resolución cuadrática de colisiones y aceleración 260x.",
        'heap': "<strong>heapq (Min-Heap):</strong> Árbol binario implícito con memoria acotada a <code>k</code> elementos, inserción <code>O(log k)</code> y cero necesidad de ordenar todo el universo.",
        'set': "<strong>set en Python:</strong> Conjunto hash puro sin punteros a valores. Verificación de pertenencia e intersección multi-criterio en <code>O(1)</code>."
      };

      structCards.forEach(card => {
        card.addEventListener('click', () => {
          structCards.forEach(c => c.style.outline = 'none');
          card.style.outline = '2px solid var(--stamp-terracotta)';
          const st = card.getAttribute('data-struct');
          if (detailBox && structData[st]) {
            detailBox.innerHTML = `🔬 ${structData[st]}`;
          }
        });
      });
    }

    // 5. Diapositiva 06: Demostración de Cache LRU
    if (slideId === 6) {
      const btnHit = document.getElementById('btn-cache-demo-hit');
      const btnMiss = document.getElementById('btn-cache-demo-miss');
      const btnInvalidate = document.getElementById('btn-cache-demo-invalidate');
      const slot1 = document.getElementById('slot-1');
      const slot2 = document.getElementById('slot-2');
      const slot3 = document.getElementById('slot-3');
      const feedback = document.getElementById('cache-feedback');

      if (btnHit && slot1 && feedback) {
        btnHit.addEventListener('click', () => {
          slot1.style.background = 'var(--stamp-sage-bg)';
          slot1.style.borderColor = 'var(--stamp-sage)';
          feedback.innerHTML = "⚡ <strong>CACHE HIT (0.01 ms):</strong> 'laptop' recuperado instantáneamente desde la tabla LRU en RAM.";
        });
      }

      if (btnMiss && slot3 && feedback) {
        btnMiss.addEventListener('click', () => {
          slot3.textContent = 'Slot 3: "teclado" [Nuevo]';
          slot3.style.background = 'var(--stamp-blueprint-bg)';
          slot3.style.borderColor = 'var(--stamp-blueprint)';
          feedback.innerHTML = "📥 <strong>CACHE MISS (28 ms):</strong> Se computó la búsqueda y se guardó en el slot más antiguo desocupado (LRU).";
        });
      }

      if (btnInvalidate && feedback) {
        btnInvalidate.addEventListener('click', () => {
          if (slot1) slot1.textContent = 'Slot 1: [Vacío]';
          if (slot2) slot2.textContent = 'Slot 2: [Vacío]';
          if (slot3) slot3.textContent = 'Slot 3: [Vacío]';
          [slot1, slot2, slot3].forEach(s => {
            if (s) {
              s.style.background = 'var(--stamp-crimson-bg)';
              s.style.borderColor = 'var(--stamp-crimson-border)';
            }
          });
          feedback.innerHTML = "🛡️ <strong>INVALIDACIÓN REACTIVA ATÓMICA:</strong> Stock mutado por despacho de pedidos. Purgado atómico para prevenir lecturas obsoletas.";
        });
      }
    }

    // 6. Diapositiva 07: Auditoría IPC
    if (slideId === 7) {
      const ipcButtons = currentSlideCard.querySelectorAll('.ipc-seg');
      const ipcDetail = document.getElementById('ipc-detail-box');
      const explanations = {
        'spawn': "<strong>Spawn en Windows (25% - ~210 ms):</strong> Creación pesada de nuevos ejecutables de Python con importación completa de DLLs.",
        'pickle': "<strong>Serialización Pickle (38% - ~320 ms):</strong> Conversión a bytes de 10.000 productos y 2.000 órdenes para cruzarlas entre procesos.",
        'pipe': "<strong>Tuberías IPC del OS (32% - ~270 ms):</strong> Transferencia por pipes y sincronización del kernel de Windows.",
        'calc': "<strong>Cómputo en RAM (5% - ~48 ms):</strong> Validación real en memoria, demostrando la Ley de Amdahl."
      };

      ipcButtons.forEach(btn => {
        btn.addEventListener('click', () => {
          const key = btn.getAttribute('data-ipc');
          if (ipcDetail && explanations[key]) {
            ipcDetail.innerHTML = explanations[key];
          }
        });
      });
    }

    // 8. Diapositiva 10: Características de la App
    if (slideId === 10) {
      const featureItems = currentSlideCard.querySelectorAll('.feature-item');
      featureItems.forEach(item => {
        item.addEventListener('click', () => {
          featureItems.forEach(i => i.classList.remove('active'));
          item.classList.add('active');
        });
      });
    }

    // 9. Diapositiva 11: Botón de Empaquetado
    if (slideId === 11) {
      const btnPackSlide = document.getElementById('btn-pack-from-slide');
      if (btnPackSlide) {
        btnPackSlide.addEventListener('click', startPackagingRitual);
      }
    }
  }

  // ==========================================================================
  // MOTOR DEL SIMULADOR DE BÚSQUEDA (SLIDE 04)
  // ==========================================================================
  function resetSimUI() {
    const baseProgress = document.getElementById('sim-base-progress');
    const optProgress = document.getElementById('sim-opt-progress');
    const baseOps = document.getElementById('sim-base-ops');
    const optOps = document.getElementById('sim-opt-ops');
    const baseTime = document.getElementById('sim-base-time');
    const optTime = document.getElementById('sim-opt-time');
    const baseStatus = document.getElementById('sim-base-status');
    const optStatus = document.getElementById('sim-opt-status');
    const summaryBox = document.getElementById('sim-summary-box');

    if (baseProgress) baseProgress.style.transform = 'scaleX(0)';
    if (optProgress) optProgress.style.transform = 'scaleX(0)';
    if (baseOps) baseOps.textContent = '0';
    if (optOps) optOps.textContent = '0';
    if (baseTime) baseTime.textContent = '0.00 ms';
    if (optTime) optTime.textContent = '0.00 ms';
    if (baseStatus) { baseStatus.textContent = 'Listo'; baseStatus.className = 'lane-status'; }
    if (optStatus) { optStatus.textContent = 'Listo'; optStatus.className = 'lane-status'; }
    if (summaryBox) {
      summaryBox.innerHTML = "Presiona 'Simular Búsqueda Comparativa' para observar en tiempo real la diferencia algorítmica entre recorrer secuencialmente una lista versus indexar directamente con función hash.";
    }
  }

  function runSearchSimulation() {
    if (simRunning) return;
    simRunning = true;

    const btnRun = document.getElementById('btn-run-sim');
    if (btnRun) btnRun.disabled = true;

    const catalogSelect = document.getElementById('sim-catalog-size');
    const n = catalogSelect ? parseInt(catalogSelect.value, 10) : 10000;
    const targetIdx = Math.floor(n * 0.842);

    const baseProgress = document.getElementById('sim-base-progress');
    const optProgress = document.getElementById('sim-opt-progress');
    const baseOps = document.getElementById('sim-base-ops');
    const optOps = document.getElementById('sim-opt-ops');
    const baseTime = document.getElementById('sim-base-time');
    const optTime = document.getElementById('sim-opt-time');
    const baseStatus = document.getElementById('sim-base-status');
    const optStatus = document.getElementById('sim-opt-status');
    const summaryBox = document.getElementById('sim-summary-box');

    if (optStatus) { optStatus.textContent = 'Cálculo Hash Directo O(1)'; optStatus.className = 'lane-status completed'; }
    if (optProgress) optProgress.style.transform = 'scaleX(1)';
    if (optOps) optOps.textContent = '1 operación';
    if (optTime) optTime.textContent = '0.001 ms';

    if (baseStatus) { baseStatus.textContent = 'Escaneando lista secuencialmente...'; baseStatus.className = 'lane-status running'; }
    let currentStep = 0;
    const totalSteps = 40;
    const stepIncrement = Math.floor(targetIdx / totalSteps);
    const intervalMs = 25;

    const scanInterval = setInterval(() => {
      currentStep++;
      const currentOps = Math.min(targetIdx, currentStep * stepIncrement);
      const ratio = currentOps / n;

      if (baseProgress) baseProgress.style.transform = `scaleX(${ratio})`;
      if (baseOps) baseOps.textContent = `${currentOps.toLocaleString('es-AR')} ops`;
      const simulatedMs = (currentOps * 0.00005).toFixed(2);
      if (baseTime) baseTime.textContent = `${simulatedMs} ms`;

      if (currentStep >= totalSteps) {
        clearInterval(scanInterval);
        if (baseOps) baseOps.textContent = `${targetIdx.toLocaleString('es-AR')} ops`;
        if (baseTime) baseTime.textContent = `${(targetIdx * 0.00005).toFixed(2)} ms`;
        if (baseStatus) { baseStatus.textContent = `Encontrado en pos. ${targetIdx.toLocaleString('es-AR')}`; baseStatus.className = 'lane-status completed'; }

        const speedup = Math.round(targetIdx / 1);
        if (summaryBox) {
          summaryBox.innerHTML = `<strong>Resultado Demostrado:</strong> El escaneo lineal Baseline recorrió secuencialmente <strong>${targetIdx.toLocaleString('es-AR')} elementos</strong> en memoria, mientras que la tabla Hash Optimizada saltó al registro en <strong>1 sola operación indexada</strong> (aceleración teórica de <strong>${speedup.toLocaleString('es-AR')}x</strong> en esta búsqueda).`;
        }

        simRunning = false;
        if (btnRun) btnRun.disabled = false;
      }
    }, intervalMs);
  }

  function animateSpeedupBars() {
    const fills = currentSlideCard.querySelectorAll('.bar-fill');
    fills.forEach((fill) => {
      fill.classList.remove('is-grown');
      fill.style.transform = 'scaleX(0)';
    });
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        fills.forEach((fill) => {
          fill.style.transform = '';
          fill.classList.add('is-grown');
        });
      });
    });
  }

  // ==========================================================================
  // NAVEGACIÓN Y CONTROLADORES
  // ==========================================================================
  function nextSlide() {
    if (isBookClosed) {
      openBook();
      return;
    }
    if (currentIndex < slides.length - 1) {
      flipToSlide(currentIndex + 1, 'right');
    }
  }

  function prevSlide() {
    if (currentIndex > 0) {
      flipToSlide(currentIndex - 1, 'left');
    }
  }

  function toggleFullscreen() {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(err => {
        console.warn(`Error al intentar pantalla completa: ${err.message}`);
      });
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
    }
  }

  function toggleNotes() {
    speakerModal.classList.toggle('active');
  }

  function toggleShortcuts() {
    shortcutsModal.classList.toggle('active');
  }

  // Cronómetro de Exposición
  function formatTime(totalSeconds) {
    const mins = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }

  function toggleTimer() {
    if (timerRunning) {
      clearInterval(timerInterval);
      timerRunning = false;
      btnTimer.classList.remove('running');
      btnTimer.title = "Iniciar cronómetro (Atajo: T)";
    } else {
      timerRunning = true;
      btnTimer.classList.add('running');
      btnTimer.title = "Pausar cronómetro (Atajo: T)";
      timerInterval = setInterval(() => {
        if (timerSeconds > 0) {
          timerSeconds--;
          timerDisplay.textContent = formatTime(timerSeconds);

          if (timerSeconds <= 60) {
            btnTimer.classList.remove('warning');
            btnTimer.classList.add('danger');
          } else if (timerSeconds <= 180) {
            btnTimer.classList.add('warning');
          }
        } else {
          clearInterval(timerInterval);
          timerRunning = false;
          btnTimer.classList.remove('running');
          btnTimer.classList.remove('warning');
          btnTimer.classList.add('danger');
        }
      }, 1000);
    }
  }

  // Event Listeners de Controles UI
  if (btnOpenBook) btnOpenBook.addEventListener('click', openBook);
  if (bookCoverClosed) bookCoverClosed.addEventListener('click', openBook);
  if (btnPackPresentation) btnPackPresentation.addEventListener('click', startPackagingRitual);

  btnNext.addEventListener('click', nextSlide);
  btnPrev.addEventListener('click', prevSlide);
  selectSlide.addEventListener('change', (e) => {
    if (isBookClosed) openBook();
    const targetIdx = parseInt(e.target.value, 10);
    const dir = targetIdx > currentIndex ? 'right' : 'left';
    renderSlide(targetIdx, dir);
  });
  btnFullscreen.addEventListener('click', toggleFullscreen);
  btnNotes.addEventListener('click', toggleNotes);
  btnCloseNotes.addEventListener('click', toggleNotes);
  btnShortcuts.addEventListener('click', toggleShortcuts);
  btnCloseShortcuts.addEventListener('click', toggleShortcuts);
  btnTimer.addEventListener('click', toggleTimer);
  if (btnMotion) btnMotion.addEventListener('click', toggleForceMotion);
  syncMotionButton();

  // Delegación global de pestañas (Tabs)
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('.tab-btn');
    if (!btn) return;
    activateTabButton(btn);
  });

  // Atajos de Teclado
  window.addEventListener('keydown', (e) => {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT' || e.target.tagName === 'TEXTAREA') {
      return;
    }

    switch (e.key) {
      case 'ArrowRight':
      case ' ':
      case 'PageDown':
        e.preventDefault();
        nextSlide();
        break;
      case 'ArrowLeft':
      case 'PageUp':
        e.preventDefault();
        prevSlide();
        break;
      case 'p':
      case 'P':
        e.preventDefault();
        startPackagingRitual();
        break;
      case 'f':
      case 'F':
        e.preventDefault();
        toggleFullscreen();
        break;
      case 'n':
      case 'N':
        e.preventDefault();
        toggleNotes();
        break;
      case 'h':
      case 'H':
      case '?':
        e.preventDefault();
        toggleShortcuts();
        break;
      case 't':
      case 'T':
        e.preventDefault();
        toggleTimer();
        break;
      case 'm':
      case 'M':
        e.preventDefault();
        toggleForceMotion();
        break;
      case 'Escape':
        speakerModal.classList.remove('active');
        shortcutsModal.classList.remove('active');
        if (isPackaging) reopenManual();
        break;
      case 'Home':
        e.preventDefault();
        if (isBookClosed) openBook();
        renderSlide(0, 'left');
        break;
      case 'End':
        e.preventDefault();
        if (isBookClosed) openBook();
        renderSlide(slides.length - 1, 'right');
        break;
      default:
        if (e.key >= '1' && e.key <= '9') {
          const targetIndex = parseInt(e.key, 10) - 1;
          if (targetIndex < slides.length) {
            if (isBookClosed) openBook();
            const dir = targetIndex > currentIndex ? 'right' : 'left';
            renderSlide(targetIndex, dir);
          }
        }
        break;
    }
  });

  // Inicialización
  cargarSlides();
})();
