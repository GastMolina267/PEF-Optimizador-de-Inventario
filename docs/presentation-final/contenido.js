/* ==========================================================================
   CONTENIDO — PROYECTO FINAL PEF (OPCIÓN 6)
   Los 11 bultos que salen de la caja: cada uno es una lámina con su archivo
   de evidencia. Las cifras salen de mediciones hechas sobre este repositorio
   (ver MED) y de datos.js (30 productos reales de la demo oral).
   ========================================================================== */
(function () {
  'use strict';

  const D = window.PEF4_DATOS.productos;

  /* ------------------------------------------------------------------------
     Mediciones (18/11/2026, Windows 11, Python 3.13, scikit-learn 1.9.1)
     - oficial: docs/mediciones/tabla_comparativa_ia.md (con tracemalloc activo)
     - timeit:  mejor de 5 repeticiones, sin tracemalloc, solo la decisión
                (_resolver_estrategia) con los 10 datos ya extraídos
     - modelo:  métricas guardadas en data/modelos/predictor_ia.joblib
     ------------------------------------------------------------------------ */
  const MED = {
    oficial: { conv: 58.46, ia: 1361.91, hib: 263.92, memConv: 15.2, memIa: 29.9, memHib: 22.2, conv1k: 70.63, ia1k: 1310.04, hib1k: 184.02 },
    timeit: { conv: 0.47, ia: 226.35, hib: 30.42, ext: 2.36, conv1k: 1.63, ia1k: 1267.84, hib1k: 91.64 },
    modelo: { f1: 0.871, prec: 0.887, rec: 0.866, r2: 0.123, mae: 10.56, test: 112, bytes: 2673 },
    mediano: { f1: 0.996, r2: 0.005, alertasIa: 0, alertasConv: 29, rapido: 915, ia: 85 },
    tests: 235, segundos: 49, cobertura: 89, testsIa: 31, testsUi: 6
  };

  const fmt = (n, d = 1) => Number(n).toLocaleString('es-AR', { minimumFractionDigits: d, maximumFractionDigits: d });
  const pct = (p) => fmt(p * 100, 1) + ' %';
  const RIESGO = { bajo: 'Bajo', medio: 'Medio', critico: 'Crítico' };
  const riskChip = (r) => `<span class="chip ${r === 'critico' ? 'chip-crimson' : r === 'medio' ? 'chip-amber' : 'chip-green'}">${RIESGO[r]}</span>`;

  const resumen = (() => {
    const cuenta = (k, pred) => D.filter((p) => pred(p[k])).length;
    return {
      rapido: D.filter((p) => p.hib[4] === 'rapido').length,
      alIa: D.filter((p) => p.hib[4] === 'ia').length,
      sinHistorial: D.filter((p) => p.fv[1] === 0).length,
      alertas: { conv: cuenta('conv', (r) => r[3]), ia: cuenta('ia', (r) => r[3]), hib: cuenta('hib', (r) => r[3]) },
      medios: { conv: cuenta('conv', (r) => r[2] === 'medio'), ia: cuenta('ia', (r) => r[2] === 'medio'), hib: cuenta('hib', (r) => r[2] === 'medio') }
    };
  })();

  /* ------------------------------------------------------------------------
     Íconos de cada bulto (64×64, trazo de tinta con un acento)
     ------------------------------------------------------------------------ */
  const S = (body) => `<svg viewBox="0 0 64 64" fill="none" stroke="#1B1410" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${body}</svg>`;
  const ICONOS = {
    orden: S('<rect x="14" y="10" width="36" height="46" rx="4" fill="#FFFEFB"/><rect x="24" y="6" width="16" height="9" rx="2" fill="#F2A516"/><path d="M22 28h20M22 36h20M22 44h12"/>'),
    quiebre: S('<path d="M8 52h48M12 52V16M52 52V16M12 30h40"/><rect x="16" y="20" width="10" height="10" fill="#D6AE82"/><rect x="28" y="22" width="8" height="8" fill="#D6AE82"/><path d="M40 40l8 8M48 40l-8 8" stroke="#BE123C"/>'),
    etiqueta: S('<path d="M10 30V12h18l26 26-18 18z" fill="#FFFEFB"/><circle cx="19" cy="21" r="3.5" fill="#F2A516"/><path d="M28 36l8 8M33 31l8 8"/>'),
    aprende: S('<path d="M10 50l12-14 10 8 12-18 10 6"/><circle cx="54" cy="32" r="3" fill="#F2A516"/><path d="M10 12v40h46"/>'),
    desviador: S('<path d="M6 40h22"/><path d="M28 40c8 0 10-20 20-20h10" stroke="#F2A516"/><path d="M28 40h30"/><rect x="16" y="33" width="10" height="10" fill="#D6AE82"/><path d="M52 15l6 5-6 5M52 35l6 5-6 5"/>'),
    balanza: S('<path d="M32 10v42M18 52h28M12 20h40"/><path d="M12 20l-6 14h12z" fill="#FFFEFB"/><path d="M52 20l-6 14h12z" fill="#F2A516"/><circle cx="32" cy="10" r="3"/>'),
    cuando: S('<path d="M32 58V8"/><path d="M32 14h20l6 6-6 6H32z" fill="#F2A516"/><path d="M32 30H12l-6 6 6 6h20z" fill="#FFFEFB"/>'),
    auxiliar: S('<rect x="16" y="20" width="32" height="26" rx="6" fill="#FFFEFB"/><circle cx="26" cy="33" r="4" fill="#5BD2F0"/><circle cx="38" cy="33" r="4" fill="#5BD2F0"/><path d="M32 20v-8"/><circle cx="32" cy="10" r="3" fill="#F2A516"/><path d="M22 46v8M42 46v8M10 30h6M48 30h6"/>'),
    aduana: S('<circle cx="32" cy="32" r="22" fill="#FFFEFB"/><circle cx="32" cy="32" r="15" stroke-dasharray="3 4"/><path d="M24 32l6 6 11-12" stroke="#15803D"/>'),
    demo: S('<rect x="8" y="12" width="48" height="32" rx="3" fill="#FFFEFB"/><path d="M24 52h16M32 44v8"/><path d="M14 22h14M14 28h22M14 34h10"/><rect x="40" y="20" width="10" height="16" fill="#F2A516"/>'),
    cierre: S('<rect x="10" y="22" width="44" height="32" fill="#D6AE82"/><path d="M10 22l6-10h32l6 10"/><path d="M28 22v10h8V22" fill="#F2A516"/><path d="M22 42l6 5 12-11" stroke="#15803D"/>')
  };

  /* ------------------------------------------------------------------------
     Bultos (láminas)
     ------------------------------------------------------------------------ */
  const LAMINAS = [
    /* 01 ---------------------------------------------------------------- */
    {
      icono: 'orden', sku: 'B-01', etiqueta: 'Orden de trabajo', fase: 'P4.0', tema: 'Consigna',
      titulo: 'Orden de trabajo: qué pide el Proyecto Final',
      sub: 'Dos enfoques complementarios de IA, siempre respaldados por pruebas y mediciones',
      evidencia: 'docs/final/Programacion-eficiente.pptx (láminas 386 y 400) · docs/final/planificacion-proyecto-final.md',
      html: () => `
        <div class="grid-wide fit">
          <div>
            <div class="ejes">
              <div class="eje rv" style="--i:0">
                <span class="eje-n">Enfoque 1</span>
                <h4>IA aplicada al desarrollo</h4>
                <p>Usar asistentes de IA para generar pruebas, explicar código, detectar posibles errores y proponer optimizaciones, <b>validando siempre sus resultados</b>.</p>
                <div class="goto"><button type="button" class="mini-btn" data-goto="7">Bulto 08 · Auxiliares →</button></div>
              </div>
              <div class="eje rv" style="--i:1">
                <span class="eje-n">Enfoque 2</span>
                <h4>IA integrada en la aplicación</h4>
                <p>Incorporar una biblioteca o un modelo que resuelva una funcionalidad concreta del sistema y <b>evaluar su costo computacional</b>.</p>
                <div class="goto"><button type="button" class="mini-btn" data-goto="2">Bulto 03 →</button><button type="button" class="mini-btn" data-goto="5">Bulto 06 · Costo →</button></div>
              </div>
            </div>
            <blockquote class="quote rv" style="--i:2">
              «Se valorará especialmente la capacidad de <b>justificar cuándo la IA aporta beneficios y cuándo una solución algorítmica convencional resulta más simple, rápida, económica o confiable</b>.»
              <cite>Consigna de la cátedra · lámina 400</cite>
            </blockquote>
            <p class="foot-note rv" style="--i:3">Nuestra funcionalidad concreta: <b>predecir quiebres de stock</b> en el catálogo del centro de distribución, con scikit-learn (la biblioteca recomendada para empezar en la lámina 387).</p>
          </div>
          <div class="panel rv" style="--i:1">
            <h3>Fases del Final <span class="chip chip-green" id="fase-count">0 / 7</span></h3>
            <table class="fases"><tbody>
              ${[
                ['P4.0', 'Plan y docs reorganizadas por hito', '7cfa84d'],
                ['P4.1', 'scikit-learn, tipos y extractor de 10 datos', 'b0db1d6'],
                ['P4.2', 'Regla O(1), pipeline y predictor conmutable', '3eb4da7'],
                ['P4.3', 'Integración en MotorInventario', '000e16a'],
                ['P4.4', 'Benchmark de IA y presupuesto de memoria', '62de465'],
                ['P4.5', 'Pantalla «Predicción IA» en Flet', '33525f8'],
                ['P4.6', 'Sphinx, README y cierre', '1b97f1d']
              ].map((f) => `<tr><td>${f[0]}</td><td>${f[1]}</td><td>${f[2]}</td></tr>`).join('')}
            </tbody></table>
            <p class="foot-note">Una rama por fase (<code>final/f0…f6</code>) y merge a <code>main</code>, igual que en los parciales.</p>
          </div>
        </div>`,
      init(root, api) {
        api.bindGoto(root);
        const filas = root.querySelectorAll('.fases tr');
        const cnt = root.querySelector('#fase-count');
        filas.forEach((tr, i) => api.later(api.ms(420 + i * 160), () => {
          tr.firstElementChild.innerHTML = '<span style="color:var(--sage)">✓</span> ' + tr.firstElementChild.textContent.replace('✓ ', '');
          cnt.textContent = (i + 1) + ' / 7';
        }));
      },
      notas: 'La consigna del Final tiene dos enfoques: IA en el desarrollo (asistentes, siempre validando lo que proponen) e IA dentro del sistema, con su costo medido. Lo que más pesa en la evaluación es la cita de la lámina 400: justificar cuándo conviene la IA y cuándo alcanza un algoritmo convencional. Toda la defensa responde esa pregunta. Lo hicimos en 7 fases, P4.0 a P4.6, con el mismo método de los parciales.'
    },

    /* 02 ---------------------------------------------------------------- */
    {
      icono: 'quiebre', sku: 'B-02', etiqueta: 'El problema', fase: 'P4.2', tema: 'Quiebre de stock',
      titulo: 'El problema del depósito: el quiebre de stock',
      sub: 'Hasta el P3 el sistema respondía rápido sobre el stock actual. Ahora tiene que anticipar cuándo se va a terminar',
      evidencia: 'src/ia/modelos.py · evaluar_heuristica_convencional()',
      html: () => `
        <div class="shelf-demo fit">
          <div class="panel rv" style="--i:0">
            <h3>Reaccionar o anticipar <span class="chip">esquema</span></h3>
            <figure>
              <svg viewBox="0 0 520 230" role="img" aria-label="El stock baja con cada pedido; al cruzar el punto de reorden conviene reponer; si llega a cero hay quiebre">
                <line x1="40" y1="20" x2="40" y2="190" stroke="#6B5E52"/>
                <line x1="40" y1="190" x2="510" y2="190" stroke="#6B5E52"/>
                <text x="34" y="26" text-anchor="end" font-size="11" fill="#6B5E52">stock</text>
                <text x="510" y="208" text-anchor="end" font-size="11" fill="#6B5E52">tiempo (pedidos)</text>
                <rect x="40" y="168" width="470" height="22" fill="#FFF1F3"/>
                <text x="48" y="183" font-size="11" fill="#BE123C">quiebre: stock 0, pedidos sin atender</text>
                <line x1="40" y1="118" x2="510" y2="118" stroke="#B45309" stroke-dasharray="6 5"/>
                <text x="48" y="112" font-size="11" fill="#B45309">punto de reorden (ROP)</text>
                <polyline points="40,40 100,40 100,62 160,62 160,88 220,88 220,104 270,104 270,126 330,126 330,150 390,150 390,170 440,170 440,190 510,190" fill="none" stroke="#1B1410" stroke-width="2.5"/>
                <line x1="300" y1="57" x2="273" y2="120" stroke="#B45309" stroke-width="1"/>
                <circle cx="270" cy="126" r="6" fill="#F2A516"/>
                <text x="300" y="52" font-size="11.5" font-weight="700" fill="#1B1410">acá conviene avisar</text>
                <line x1="490" y1="86" x2="443" y2="184" stroke="#BE123C" stroke-width="1"/>
                <circle cx="440" cy="190" r="6" fill="#BE123C"/>
                <text x="510" y="80" text-anchor="end" font-size="11.5" font-weight="700" fill="#BE123C">acá ya es tarde</text>
              </svg>
              <figcaption class="tl-cap">El aviso sirve si llega cuando el stock cruza el punto de reorden, no cuando ya está en cero.</figcaption>
            </figure>
          </div>
          <div class="rv" style="--i:1">
            <div class="panel">
              <h3>La regla convencional (O(1))</h3>
              <div class="formula">
                demanda = μ<sub>lote</sub> × máx(0,2; tendencia)<br>
                seguridad = <b>1,5</b> × √σ²<sub>lote</sub><br>
                ROP = demanda + seguridad
              </div>
              <table class="tbl" style="margin-top:10px">
                <thead><tr><th>Si el stock…</th><th class="r">P(quiebre)</th><th class="r">Alerta</th></tr></thead>
                <tbody>
                  <tr><td>es 0</td><td class="r">100 %</td><td class="r">sí</td></tr>
                  <tr><td>no cubre la demanda</td><td class="r">75 a 95 %</td><td class="r">sí</td></tr>
                  <tr><td>está por debajo del ROP</td><td class="r">40 a 70 %</td><td class="r">sí</td></tr>
                  <tr><td>supera el ROP</td><td class="r">≤ 30 %</td><td class="r">no</td></tr>
                </tbody>
              </table>
            </div>
            <p class="callout">Es rápida y se puede explicar en una línea. Pero es fija: usa 3 de los 10 datos que tenemos y no aprende de cómo se comportó la demanda.</p>
          </div>
        </div>`,
      notas: 'Hasta el Parcial 3 el sistema contestaba rápido sobre el presente: cuánto stock hay, dónde está, qué alternativa ofrecer. El Final agrega una pregunta sobre el futuro: ¿se va a terminar? La respuesta clásica es el punto de reorden; está implementada tal cual en evaluar_heuristica_convencional. Es O(1) y explicable. Su límite: es una fórmula fija con lote medio, varianza y tendencia; no combina el resto de la información. Esa es la puerta para probar un modelo.'
    },

    /* 03 ---------------------------------------------------------------- */
    {
      icono: 'etiqueta', sku: 'B-03', etiqueta: 'La etiqueta', fase: 'P4.1', tema: '10 datos por producto',
      titulo: 'La etiqueta: 10 datos por producto',
      sub: 'El extractor resume el historial de pedidos de cada producto en un vector fijo. Es lo que lee el operario',
      evidencia: 'src/ia/extractor_features.py · src/ia/tipos.py (FeatureVector) · data/datasets/demo_oral.json',
      html: () => `
        <div class="etq-wrap fit">
          <div class="rv" style="--i:0">
            <div class="etq-pick" id="etq-pick">
              ${[1, 5, 21, 2, 7].map((id) => { const p = D.find((x) => x.id === id); return `<button type="button" class="mini-btn" data-id="${id}">${p.n.split(' ').slice(0, 2).join(' ')}</button>`; }).join('')}
            </div>
            <div class="etiqueta" id="etiqueta"></div>
          </div>
          <div class="panel rv" style="--i:1">
            <h3>Qué significa cada dato</h3>
            <ul class="feat-list" id="feat-list">
              ${[
                ['rotacion_historica', 'unidades vendidas en total'],
                ['frecuencia_pedidos', 'en cuántos pedidos aparece'],
                ['tamano_medio_lote', 'unidades por pedido (μ)'],
                ['varianza_lote', 'qué tanto varía el lote (σ²)'],
                ['stock_actual', 'unidades en el estante'],
                ['precio_unitario', 'precio de lista'],
                ['ratio_stock_rotacion', 'stock ÷ (rotación + 1)'],
                ['tasa_quiebre_reciente', 'quiebres vistos ÷ pedidos'],
                ['tendencia_demanda', 'mitad reciente ÷ mitad antigua'],
                ['dias_cobertura_estimados', 'stock ÷ lote medio (999 = sin consumo)']
              ].map((f, i) => `<li data-f="${i}"><b>F${i + 1}</b><span><code>${f[0]}</code><br>${f[1]}</span></li>`).join('')}
            </ul>
            <p class="foot-note">Extraer los 10 datos de un producto cuesta ${fmt(MED.timeit.ext, 1)} µs en la demo: recorre sus pedidos, así que crece con el historial.</p>
            <h3 class="mt">Qué responde cada estrategia</h3>
            <div class="grid-split" id="etq-res"></div>
          </div>
        </div>`,
      init(root) {
        const etq = root.querySelector('#etiqueta');
        const res = root.querySelector('#etq-res');
        const nombres = ['rotación', 'frecuencia', 'lote medio', 'varianza', 'stock', 'precio', 'stock/rotación', 'tasa quiebre', 'tendencia', 'cobertura'];
        const pintar = (id) => {
          const p = D.find((x) => x.id === id);
          root.querySelectorAll('#etq-pick button').forEach((b) => b.classList.toggle('on', Number(b.dataset.id) === id));
          etq.innerHTML = `
            <header><b>${p.n}</b><span>SKU-${String(p.id).padStart(4, '0')} · ${p.cat}</span></header>
            <table><tbody>${p.fv.map((v, i) => `<tr data-f="${i}"><td>F${i + 1}</td><td>${nombres[i]}</td><td>${i === 5 ? '$ ' + fmt(v, 0) : fmt(v, v % 1 ? 2 : 0)}</td></tr>`).join('')}</tbody></table>
            <footer><span class="bars" aria-hidden="true"></span><span>PEF-2026</span></footer>`;
          const fila = (t, r) => `<div class="panel ${r[2] === 'critico' ? 'tint-red' : r[2] === 'medio' ? 'tint-amber' : ''}"><h3>${t} ${riskChip(r[2])}</h3><p class="small-p">Demanda <b>${fmt(r[0], 1)}</b> u · P(quiebre) <b>${pct(r[1])}</b></p></div>`;
          res.innerHTML = fila('Regla O(1)', p.conv) + fila('Modelo', p.ia);
          etq.querySelectorAll('tr').forEach((tr) => tr.addEventListener('mouseenter', () => resaltar(Number(tr.dataset.f))));
        };
        const resaltar = (i) => {
          root.querySelectorAll('[data-f]').forEach((el) => el.classList.toggle('hl', Number(el.dataset.f) === i));
        };
        root.querySelectorAll('#feat-list li').forEach((li) => li.addEventListener('mouseenter', () => resaltar(Number(li.dataset.f))));
        root.querySelectorAll('#etq-pick button').forEach((b) => b.addEventListener('click', () => pintar(Number(b.dataset.id))));
        pintar(1);
      },
      notas: 'Cada producto se resume en 10 números. Mostrar el Taladro: 1 pedido, stock 15, la regla dice riesgo bajo y el modelo dice medio. Después la Sierra Caladora, con stock 0: los dos coinciden en crítico. Y la Amoladora, que nunca se pidió: la regla dice demanda 0 y el modelo, entrenado con historial sintético, le asigna 14,5 unidades y riesgo medio. Sin datos, ninguno de los dos puede saberlo. Ese caso vuelve en el bulto 07.'
    },

    /* 04 ---------------------------------------------------------------- */
    {
      icono: 'aprende', sku: 'B-04', etiqueta: 'Cómo aprende', fase: 'P4.2', tema: 'Entrenamiento',
      titulo: 'Cómo aprende el operario: dos modelos lineales chicos',
      sub: 'Un regresor para la demanda y un clasificador para la probabilidad de quiebre, entrenados en local y guardados en 2,6 KB',
      evidencia: 'src/ia/modelos.py (ModeloPredictorIA) · src/ia/extractor_features.py (GeneradorHistorialSintetico) · data/modelos/predictor_ia.joblib',
      html: () => `
        <div class="fit" style="display:flex;flex-direction:column;gap:14px">
          <div class="panel rv" style="--i:0">
            <h3>Pipeline de scikit-learn <span class="chip chip-blue">Pipeline(StandardScaler → modelo)</span></h3>
            <div class="pipe">
              <div class="pipe-row">
                <div class="pipe-node"><code>Historial</code><span>sintético · seed 42</span></div>
                <div class="pipe-arrow">→</div>
                <div class="pipe-node"><code>10 datos</code><span>por producto y período</span></div>
                <div class="pipe-arrow">→</div>
                <div class="pipe-node"><code>StandardScaler → Ridge(alpha=1.0)</code><span>regresión lineal regularizada</span></div>
                <div class="pipe-arrow">→</div>
                <div class="pipe-node out"><code>demanda</code><span>unidades del período</span></div>
              </div>
              <div class="pipe-row">
                <div class="pipe-node"><code>Etiqueta</code><span>quiebre = demanda &gt; stock</span></div>
                <div class="pipe-arrow">→</div>
                <div class="pipe-node"><code>75 % / 25 %</code><span>entrenamiento / prueba, en orden</span></div>
                <div class="pipe-arrow">→</div>
                <div class="pipe-node"><code>StandardScaler → LogisticRegression(C=1.0)</code><span>clasificador, max_iter=300</span></div>
                <div class="pipe-arrow">→</div>
                <div class="pipe-node out"><code>P(quiebre)</code><span>0 a 1 · alerta si ≥ 0,5</span></div>
              </div>
            </div>
          </div>
          <div class="grid-split">
            <div class="panel rv" style="--i:1">
              <h3>Métricas del modelo guardado <button type="button" class="mini-btn" id="btn-train">▶ Entrenar</button></h3>
              <div class="learn-bar"><i id="learn-fill"></i></div>
              <p class="foot-note" id="learn-txt" style="margin-top:0">Historial sintético con semilla 42 · ${MED.modelo.test} muestras de prueba</p>
              <div class="metrics" style="margin-top:8px">
                <div class="metric"><span>F1 (ponderado)</span><strong data-v="${MED.modelo.f1}">0,00</strong><em>clasificador</em></div>
                <div class="metric"><span>Precisión / Recall</span><strong data-v="${MED.modelo.prec}" data-v2="${MED.modelo.rec}">0,00</strong><em>clasificador</em></div>
                <div class="metric"><span>R² · MAE</span><strong data-v="${MED.modelo.r2}" data-mae="${MED.modelo.mae}">0,00</strong><em>regresor</em></div>
              </div>
            </div>
            <div class="rv" style="--i:2">
              <div class="panel tint-dark">
                <h3>Por qué estos modelos</h3>
                <ul class="ticks small" style="color:rgba(246,239,229,.85)">
                  <li>Corren en local, sin GPU ni servicios externos.</li>
                  <li>El archivo pesa ${fmt(MED.modelo.bytes, 0)} bytes y carga al iniciar el motor.</li>
                  <li>Una predicción es un producto escalar: costo fijo por producto.</li>
                </ul>
              </div>
              <p class="callout">El clasificador funciona (F1 ${fmt(MED.modelo.f1, 2)}); el regresor de demanda explica poco (R² ${fmt(MED.modelo.r2, 2)}). Las alertas dependen solo de la probabilidad, no de la demanda estimada.</p>
            </div>
          </div>
        </div>`,
      init(root, api) {
        const fill = root.querySelector('#learn-fill');
        const txt = root.querySelector('#learn-txt');
        const nums = root.querySelectorAll('.metric strong');
        const entrenar = () => {
          fill.style.transition = 'none'; fill.style.width = '0'; void fill.offsetWidth; fill.style.transition = '';
          nums.forEach((n) => { n.textContent = '…'; });
          api.later(api.ms(60), () => { fill.style.width = '100%'; });
          let p = 0;
          const tick = () => {
            p += 1;
            txt.textContent = 'Entrenando… ' + Math.min(100, p * 4) + ' %';
            if (p < 25) api.later(api.ms(55) || 1, tick);
            else {
              txt.textContent = 'Historial sintético con semilla 42 · ' + MED.modelo.test + ' muestras de prueba';
              nums[0].textContent = fmt(nums[0].dataset.v, 2);
              nums[1].textContent = fmt(nums[1].dataset.v, 2) + ' / ' + fmt(nums[1].dataset.v2, 2);
              nums[2].textContent = fmt(nums[2].dataset.v, 2) + ' · ' + fmt(nums[2].dataset.mae, 1);
            }
          };
          tick();
        };
        root.querySelector('#btn-train').addEventListener('click', entrenar);
        api.later(api.ms(500), entrenar);
      },
      notas: 'No hay historial real de ventas, así que el generador sintético simula períodos de pedidos con semilla fija; es reproducible. La etiqueta es simple: hubo quiebre si la demanda del período superó al stock. Dos modelos lineales con escalado: Ridge para la demanda, regresión logística para la probabilidad. Ser honestos con las métricas: el clasificador anda bien, pero el regresor explica poco, R² 0,12. Por eso las alertas se deciden con la probabilidad. Si preguntan por qué no una red: la consigna pide medir costo; un modelo lineal de 2,6 KB es lo más barato que puede competir con la regla.'
    },

    /* 05 ---------------------------------------------------------------- */
    {
      icono: 'desviador', sku: 'B-05', etiqueta: 'El desviador', fase: 'P4.2', tema: 'Cascada híbrida',
      titulo: 'El desviador: la regla decide a quién mirar con el modelo',
      sub: `Los 30 productos de la demo pasan por la cinta. Elegí cómo trabaja el operario y mirá dónde se forma la cola`,
      evidencia: 'src/ia/predictor_demanda.py · _resolver_estrategia() (rama HIBRIDA, líneas 110-133)',
      html: () => `
        <div class="sorter fit">
          <div class="rv" style="--i:0">
            <div class="sorter-canvas-wrap"><canvas id="sorter" width="1080" height="400" aria-label="Simulación de la cinta con el desviador y el operario"></canvas></div>
            <p class="foot-note">Regla del desviador: si <code>stock ≥ máx(10, 3 × demanda de la regla)</code> el producto sigue por el carril rápido; si no, va al operario. Colores = riesgo calculado.</p>
          </div>
          <div class="sorter-ctrl rv" style="--i:1">
            <div class="seg" id="sorter-mode" role="group" aria-label="Estrategia">
              <button type="button" data-m="conv">Regla O(1)<small>todo por el carril rápido</small></button>
              <button type="button" data-m="ia">Solo modelo<small>el operario revisa los 30</small></button>
              <button type="button" data-m="hib" class="on">Cascada híbrida<small>el modelo solo en la zona dudosa</small></button>
            </div>
            <div class="counters">
              <div class="counter"><span>Evaluados</span><strong id="c-eval">0</strong></div>
              <div class="counter"><span>Al modelo</span><strong id="c-ia">0</strong></div>
              <div class="counter"><span>Alertas</span><strong id="c-alert">0</strong></div>
              <div class="counter"><span>Riesgo medio</span><strong id="c-medio">0</strong></div>
            </div>
            <div class="counter"><span>Cómputo medido (sin tracemalloc)</span><strong id="c-us">0 µs</strong></div>
            <button type="button" class="mini-btn" id="sorter-replay">↻ Volver a pasar la cinta</button>
          </div>
        </div>`,
      init(root, api) {
        const cv = root.querySelector('#sorter');
        const ctx = cv.getContext('2d');
        const W = cv.width;
        const H = cv.height;
        const el = (id) => root.querySelector(id);
        const COL = { bajo: '#4ADE80', medio: '#FCD34D', critico: '#FB7185' };
        const BELT_Y = 300;
        const UP_Y = 170;
        const DIV_X = 330;
        const ROB_X = 640;
        let modo = 'hib';
        let items = [];
        let t0 = 0;
        let robotBusy = null;
        let stats;

        const reset = () => {
          stats = { eval: 0, ia: 0, alert: 0, medio: 0, us: 0 };
          robotBusy = null;
          items = D.map((p, i) => {
            const r = modo === 'conv' ? p.conv : modo === 'ia' ? p.ia : p.hib;
            const ruta = modo === 'conv' ? 'rapido' : modo === 'ia' ? 'ia' : p.hib[4];
            return { p, r, ruta, x: -40 - i * 46, y: BELT_Y, st: 'belt', done: false, color: '#C49A6C' };
          });
          t0 = performance.now();
          ['#c-eval', '#c-ia', '#c-alert', '#c-medio'].forEach((s) => { el(s).textContent = '0'; });
          el('#c-us').textContent = '0 µs';
        };
        const contar = (it) => {
          stats.eval += 1;
          if (it.ruta === 'ia') stats.ia += 1;
          if (it.r[3]) stats.alert += 1;
          if (it.r[2] === 'medio') stats.medio += 1;
          stats.us += modo === 'conv' ? MED.timeit.conv : modo === 'ia' ? MED.timeit.ia : (it.ruta === 'ia' ? MED.timeit.conv + MED.timeit.ia : MED.timeit.conv);
          el('#c-eval').textContent = stats.eval;
          el('#c-ia').textContent = stats.ia;
          el('#c-alert').textContent = stats.alert;
          el('#c-medio').textContent = stats.medio;
          el('#c-us').textContent = stats.us >= 1000 ? fmt(stats.us / 1000, 2) + ' ms' : fmt(stats.us, 0) + ' µs';
        };

        const dibujarRobot = (x, y, busy, now) => {
          ctx.save();
          ctx.translate(x, y);
          ctx.fillStyle = '#2A2E35';
          ctx.fillRect(-46, 62, 92, 22);
          ctx.fillStyle = '#F2A516';
          ctx.fillRect(-46, 62, 92, 5);
          const a = busy ? Math.sin(now / 140) * 0.18 : 0;
          ctx.translate(0, 58);
          ctx.rotate(-1.15 + a);
          ctx.fillStyle = '#3A3F48';
          ctx.fillRect(0, -9, 70, 18);
          ctx.fillStyle = '#F2A516';
          ctx.fillRect(14, -6, 40, 12);
          ctx.translate(70, 0);
          ctx.rotate(1.9 - a * 1.5);
          ctx.fillStyle = '#3A3F48';
          ctx.fillRect(0, -7, 56, 14);
          ctx.translate(56, 0);
          ctx.fillStyle = busy ? '#F2A516' : '#5BD2F0';
          ctx.beginPath(); ctx.arc(0, 0, 8, 0, Math.PI * 2); ctx.fill();
          ctx.restore();
          ctx.fillStyle = 'rgba(246,239,229,.55)';
          ctx.font = '600 15px "JetBrains Mono", monospace';
          ctx.textAlign = 'center';
          ctx.fillText('PRD-01 · ' + (busy ? 'evaluando…' : 'libre'), x + 120, y + 60);
        };

        const frame = (now) => {
          ctx.clearRect(0, 0, W, H);
          // carriles
          ctx.fillStyle = '#23262C';
          ctx.fillRect(0, BELT_Y + 16, W, 16);
          ctx.fillRect(DIV_X, UP_Y + 16, W - DIV_X, 16);
          ctx.strokeStyle = '#3A3F48';
          ctx.lineWidth = 16;
          ctx.beginPath(); ctx.moveTo(DIV_X - 30, BELT_Y + 24); ctx.quadraticCurveTo(DIV_X + 10, BELT_Y + 24, DIV_X + 30, UP_Y + 24); ctx.stroke();
          ctx.font = '600 15px "JetBrains Mono", monospace';
          ctx.textAlign = 'left';
          ctx.fillStyle = 'rgba(74,222,128,.75)';
          ctx.fillText('CARRIL RÁPIDO · regla O(1) · ' + fmt(MED.timeit.conv, 2) + ' µs', DIV_X + 60, BELT_Y + 62);
          ctx.fillStyle = 'rgba(242,165,22,.85)';
          ctx.fillText('CARRIL DEL OPERARIO · modelo · ' + fmt(MED.timeit.ia, 0) + ' µs', DIV_X + 60, UP_Y + 58);
          // desviador
          ctx.fillStyle = modo === 'hib' ? '#F2A516' : '#565C67';
          ctx.fillRect(DIV_X - 6, BELT_Y - 42, 12, 42);
          ctx.fillStyle = 'rgba(246,239,229,.6)';
          ctx.textAlign = 'center';
          ctx.fillText('DESVIADOR', DIV_X, BELT_Y - 52);
          dibujarRobot(ROB_X, UP_Y - 100, !!robotBusy, now);

          const vel = 2.6;
          const enCola = items.filter((it) => it.st === 'queue');
          items.forEach((it) => {
            if (it.st === 'belt') {
              it.x += vel;
              if (it.x >= DIV_X - 20) it.st = it.ruta === 'ia' ? 'up' : 'fast';
              if (it.st === 'fast' && !it.done) { it.done = true; it.color = COL[it.r[2]]; contar(it); }
            } else if (it.st === 'fast') {
              it.x += vel * 1.6;
            } else if (it.st === 'up') {
              it.x += vel; it.y = Math.max(UP_Y, it.y - 6);
              if (it.y <= UP_Y) it.st = 'queue';
            } else if (it.st === 'queue') {
              const idx = enCola.indexOf(it);
              const objetivo = ROB_X - 30 - idx * 44;
              if (it.x < objetivo) it.x = Math.min(objetivo, it.x + vel);
              if (idx === 0 && !robotBusy && it.x >= ROB_X - 31) { robotBusy = { it, fin: now + api.ms(620) + 80 }; it.st = 'scan'; }
            } else if (it.st === 'scan') {
              if (now >= robotBusy.fin) { it.st = 'out'; it.done = true; it.color = COL[it.r[2]]; contar(it); robotBusy = null; }
            } else if (it.st === 'out') {
              it.x += vel * 1.6;
            }
            if (it.x > -40 && it.x < W + 40) {
              ctx.fillStyle = it.color;
              ctx.fillRect(it.x - 17, it.y - 12, 34, 28);
              ctx.fillStyle = 'rgba(27,20,16,.75)';
              ctx.font = '700 12px "JetBrains Mono", monospace';
              ctx.textAlign = 'center';
              ctx.fillText(String(it.p.id), it.x, it.y + 7);
              if (it.st === 'scan') {
                ctx.strokeStyle = 'rgba(91,210,240,.8)';
                ctx.lineWidth = 2;
                ctx.strokeRect(it.x - 21, it.y - 16, 42, 36);
              }
            }
          });
          if (enCola.length > 3) {
            ctx.fillStyle = '#FB7185';
            ctx.font = '700 16px "JetBrains Mono", monospace';
            ctx.textAlign = 'left';
            ctx.fillText('cola: ' + enCola.length + ' esperando al modelo', 18, UP_Y - 60);
          }
        };
        reset();
        api.raf(frame);
        root.querySelectorAll('#sorter-mode button').forEach((b) => b.addEventListener('click', () => {
          root.querySelectorAll('#sorter-mode button').forEach((x) => x.classList.toggle('on', x === b));
          modo = b.dataset.m;
          reset();
        }));
        el('#sorter-replay').addEventListener('click', reset);
      },
      notas: `Esta es la escena central. Empezar en Cascada: de los 30 productos, ${resumen.rapido} se resuelven en el carril rápido y solo ${resumen.alIa} van al operario. Después pasar a Solo modelo: el operario revisa los 30 y se forma la cola; esa cola es el costo de poner IA en todo. Con la Regla O(1) no hay cola, pero tampoco hay avisos de riesgo medio. Las alertas fuertes coinciden en las tres estrategias (${resumen.alertas.conv}, ${resumen.alertas.ia} y ${resumen.alertas.hib}); lo que cambia son los avisos medios: el modelo marca ${resumen.medios.ia}, la cascada conserva ${resumen.medios.hib}. El contador de abajo usa los microsegundos medidos sin tracemalloc.`
    },

    /* 06 ---------------------------------------------------------------- */
    {
      icono: 'balanza', sku: 'B-06', etiqueta: 'Balanza', fase: 'P4.4', tema: 'Costo computacional',
      titulo: 'Balanza y cronómetro: cuánto cuesta cada estrategia',
      sub: 'Tiempo por producto en escala logarítmica. El instrumento con el que medís también pesa',
      evidencia: 'benchmarks/comparar_ia.py · docs/mediciones/tabla_comparativa_ia.md · medición con timeit (mejor de 5)',
      html: () => `
        <div class="grid-wide fit">
          <div class="panel rv" style="--i:0">
            <h3>Microsegundos por producto · demo (30 productos)</h3>
            <div class="bench-tabs" id="bench-tabs" style="margin-bottom:12px">
              <button type="button" class="mini-btn on" data-src="timeit">Sin tracemalloc · timeit</button>
              <button type="button" class="mini-btn" data-src="oficial">Con tracemalloc · tabla oficial</button>
            </div>
            <div class="bench" id="bench">
              ${[['conv', 'Regla O(1)', 'carril rápido'], ['hib', 'Cascada', '26 rápido + 4 modelo'], ['ia', 'Solo modelo', 'los 30 al operario']].map((r) => `
                <div class="bench-row"><b>${r[1]}<small>${r[2]}</small></b><div class="bench-track"><i class="${r[0]}" data-k="${r[0]}"></i></div><span class="bench-val" data-k="${r[0]}">—</span></div>`).join('')}
              <div class="bench-row" aria-hidden="true"><span></span>
                <svg viewBox="0 0 500 24" preserveAspectRatio="none" style="width:100%;height:24px;overflow:visible">
                  ${[0.1, 1, 10, 100, 1000, 10000].map((v, i) => `<line x1="${i * 100}" y1="0" x2="${i * 100}" y2="6" stroke="#6B5E52"/><text x="${i * 100}" y="20" font-size="11" fill="#6B5E52" text-anchor="${i === 0 ? 'start' : i === 5 ? 'end' : 'middle'}">${v >= 1 ? fmt(v, 0) : '0,1'} µs</text>`).join('')}
                </svg><span></span></div>
            </div>
            <p class="callout" id="bench-msg"></p>
          </div>
          <div class="rv" style="--i:1">
            <div class="panel">
              <h3>Las dos mediciones</h3>
              <table class="tbl">
                <thead><tr><th style="text-transform:none">µs por producto</th><th class="r">Regla</th><th class="r">Cascada</th><th class="r">Modelo</th></tr></thead>
                <tbody>
                  <tr><td>Demo · oficial</td><td class="r">${fmt(MED.oficial.conv, 1)}</td><td class="r">${fmt(MED.oficial.hib, 1)}</td><td class="r">${fmt(MED.oficial.ia, 1)}</td></tr>
                  <tr><td>Demo · timeit</td><td class="r"><b>${fmt(MED.timeit.conv, 2)}</b></td><td class="r"><b>${fmt(MED.timeit.hib, 1)}</b></td><td class="r"><b>${fmt(MED.timeit.ia, 1)}</b></td></tr>
                  <tr><td>1.000 prod. · oficial</td><td class="r">${fmt(MED.oficial.conv1k, 1)}</td><td class="r">${fmt(MED.oficial.hib1k, 1)}</td><td class="r">${fmt(MED.oficial.ia1k, 1)}</td></tr>
                  <tr><td>1.000 prod. · timeit</td><td class="r">${fmt(MED.timeit.conv1k, 2)}</td><td class="r">${fmt(MED.timeit.hib1k, 1)}</td><td class="r">${fmt(MED.timeit.ia1k, 1)}</td></tr>
                </tbody>
              </table>
            </div>
            <div class="panel" style="margin-top:12px">
              <h3>Memoria</h3>
              <ul class="ticks small">
                <li>Modelo en disco: <b>${fmt(MED.modelo.bytes, 0)} bytes</b>.</li>
                <li>Pico de heap por corrida (oficial): ${fmt(MED.oficial.memConv, 1)} / ${fmt(MED.oficial.memHib, 1)} / ${fmt(MED.oficial.memIa, 1)} KB.</li>
                <li>200 inferencias seguidas retienen menos de 128 KB tras el GC (test de fugas).</li>
              </ul>
            </div>
          </div>
        </div>`,
      init(root, api) {
        const escala = (v) => Math.max(0, Math.min(100, (Math.log10(v) + 1) / 5 * 100));
        const msg = root.querySelector('#bench-msg');
        const pintar = (src) => {
          const m = MED[src];
          root.querySelectorAll('#bench-tabs button').forEach((b) => b.classList.toggle('on', b.dataset.src === src));
          root.querySelectorAll('.bench-track i').forEach((i) => { i.style.width = '0'; });
          api.later(api.ms(80) || 1, () => {
            root.querySelectorAll('.bench-track i').forEach((i) => { i.style.width = escala(m[i.dataset.k]) + '%'; });
          });
          root.querySelectorAll('.bench-val').forEach((s) => { const v = m[s.dataset.k]; s.textContent = fmt(v, v < 10 ? 2 : 1) + ' µs'; });
          const rIa = m.ia / m.conv;
          const rHib = m.ia / m.hib;
          msg.innerHTML = src === 'timeit'
            ? `Sin el instrumento, la regla es <b>${fmt(rIa, 0)}× más rápida</b> que el modelo y la cascada es <b>${fmt(rHib, 1)}× más rápida</b> que usar el modelo en todo.`
            : `Con tracemalloc activo la regla parece solo ${fmt(rIa, 1)}× más rápida: el rastreo de memoria agrega unos 50 µs por llamada y tapa el costo real de una función O(1).`;
        };
        root.querySelectorAll('#bench-tabs button').forEach((b) => b.addEventListener('click', () => pintar(b.dataset.src)));
        pintar('timeit');
      },
      notas: 'Dos mediciones del mismo código. La tabla oficial mide con tracemalloc encendido, para registrar memoria al mismo tiempo; ahí la regla tarda 58 µs. Medida sola con timeit tarda 0,47 µs: casi todo era el costo de medir. Lección de eficiencia: tiempo y memoria se miden en corridas separadas. Con la medición limpia, el modelo cuesta unas 480 veces la regla y la cascada recupera 7 veces el tiempo frente al modelo puro. Los números de 1.000 productos están para mostrar que la proporción se mantiene. Las corridas varían entre un 5 y un 15 % de una vez a otra.'
    },

    /* 07 ---------------------------------------------------------------- */
    {
      icono: 'cuando', sku: 'B-07', etiqueta: 'Cuándo conviene', fase: 'P4.4', tema: 'Justificación',
      titulo: '¿Cuándo conviene la IA y cuándo alcanza la regla?',
      sub: 'La respuesta está escrita en el código: tres pasos, y el modelo solo se enciende en el último',
      evidencia: 'src/ia/predictor_demanda.py:110-133 · docs/sphinx/secciones/04_diseno_tecnico.md',
      html: () => `
        <div class="decide fit">
          <div class="q-flow">
            <div class="q-step rv" style="--i:0"><span class="q-n">1</span><div><b>Calcular la regla O(1), siempre</b><span>Cuesta ${fmt(MED.timeit.conv, 2)} µs. Da demanda estimada y una primera probabilidad.</span></div></div>
            <div class="q-step rv" style="--i:1"><span class="q-n">2</span><div><b>¿Stock ≥ máx(10, 3 × demanda)?</b><span>Si sobra stock, no hay nada que predecir: se responde con la regla.</span>
              <div class="ans"><span class="chip chip-green">sí · ${resumen.rapido} de ${D.length} en la demo</span><span class="chip chip-green">${fmt(MED.mediano.rapido, 0)} de 1.000 en el dataset mediano</span></div></div></div>
            <div class="q-step rv" style="--i:2"><span class="q-n">3</span><div><b>Zona dudosa: se enciende el modelo</b><span>Stock cerca de la demanda, donde combinar los 10 datos cambia la decisión.</span>
              <div class="ans"><span class="chip chip-amber">${resumen.alIa} de ${D.length} en la demo</span><span class="chip chip-amber">${MED.mediano.ia} de 1.000 en el mediano</span></div></div></div>
            <p class="foot-note rv" style="--i:3">Caso borde: un producto sin pedidos y con menos de 10 unidades también cae en la zona dudosa. Ahí el modelo responde con lo que aprendió del historial sintético, no con datos de ese producto.</p>
          </div>
          <div style="display:flex;flex-direction:column;gap:12px">
            <div class="grid-split">
              <div class="panel tint-green rv" style="--i:1">
                <h3>Alcanza la regla</h3>
                <ul class="ticks small">
                  <li>Hay que responder en tiempo real o para miles de productos.</li>
                  <li>El stock sobra con holgura.</li>
                  <li>No hay historial del producto.</li>
                  <li>Hay que explicar la decisión en una línea.</li>
                </ul>
              </div>
              <div class="panel tint-amber rv" style="--i:2">
                <h3>Conviene el modelo</h3>
                <ul class="ticks small">
                  <li>El stock está cerca de la demanda esperada.</li>
                  <li>La demanda varía y una fórmula fija se equivoca.</li>
                  <li>Un quiebre cuesta caro (producto de alto valor).</li>
                  <li>Hay historial suficiente para aprender algo.</li>
                </ul>
              </div>
            </div>
            <blockquote class="quote rv" style="--i:3">La IA no reemplaza al algoritmo eficiente: <b>lo usa como filtro</b> y trabaja solo donde hay duda.<cite>Respuesta a la lámina 400 de la consigna</cite></blockquote>
          </div>
        </div>`,
      notas: `Es la pregunta que más pesa en la evaluación. No la respondemos con una opinión, sino con el código de la cascada: la regla siempre corre porque es casi gratis; si el stock sobra, ahí termina; el modelo solo se enciende en la zona dudosa. En la demo fueron ${resumen.alIa} de ${D.length}; en el dataset de 1.000 productos, 85. Mencionar el caso borde de los productos sin historial: es una limitación que conocemos, y la próxima mejora sería mandarlos siempre a la regla.`
    },

    /* 08 ---------------------------------------------------------------- */
    {
      icono: 'auxiliar', sku: 'B-08', etiqueta: 'Auxiliares', fase: 'P4.4', tema: 'IA en el desarrollo',
      titulo: 'Los auxiliares: IA en el desarrollo, con cada resultado verificado',
      sub: 'Usamos asistentes para generar pruebas, explicar y documentar. Lo que proponían pasaba por la balanza antes de quedar',
      evidencia: 'tests/ia/test_predictor_ia.py · tests/ia/test_presupuesto_memoria_ia.py · docs/final/resumen-proyecto-final.md',
      html: () => `
        <div class="grid-split fit" style="grid-template-columns:minmax(0,.8fr) minmax(0,1.2fr)">
          <div class="panel rv" style="--i:0">
            <h3>Para qué usamos asistentes</h3>
            <ul class="ticks small">
              <li><b>Pruebas por propiedades con Hypothesis:</b> stock de 0 a 5.000 y rotación, frecuencia y tendencia aleatorias; la probabilidad nunca sale de [0, 1].</li>
              <li><b>Presupuesto de memoria:</b> 200 inferencias seguidas con tracemalloc, menos de 128 KB retenidos.</li>
              <li><b>Explicar y documentar:</b> la API de <code>src/ia/</code> en Sphinx y el análisis costo-beneficio.</li>
              <li><b>Refactor guiado:</b> complejidad cognitiva ≤ 15 en todo el módulo (complexipy).</li>
            </ul>
            <p class="callout dark">El asistente escribe rápido. La medición decide qué queda.</p>
          </div>
          <div class="panel rv" style="--i:1">
            <h3>Validar siempre: lo que dijimos contra lo que medimos <span class="chip chip-crimson">5 hallazgos</span></h3>
            <table class="validar">
              <thead><tr><th>Afirmación</th><th>Lo que encontramos</th><th>Qué hacemos</th></tr></thead>
              <tbody>
                <tr><td>«La regla tarda 58 µs»</td><td>Sin tracemalloc tarda 0,47 µs; el resto era el costo de medir.</td><td>Medir tiempo y memoria por separado.</td></tr>
                <tr><td>«Latencia sub-microsegundo» (misma tabla)</td><td>Contradice la fila de 58 µs; solo es cierto sin el instrumento.</td><td>Una sola fuente por cifra.</td></tr>
                <tr><td>«F1 = 0,875»</td><td>Es F1 ponderado: con 1.000 productos da 0,996 y el modelo no marca ninguna alerta (la regla marca 29).</td><td>Reportar F1 de la clase quiebre.</td></tr>
                <tr><td>«La cascada no pierde alertas»</td><td>Cierto (${resumen.alertas.hib} = ${resumen.alertas.ia}), pero de ${resumen.medios.ia} avisos de riesgo medio quedan ${resumen.medios.hib}.</td><td>Decirlo con las dos cifras.</td></tr>
                <tr><td>Umbrales 60 % / 25 % en el resumen</td><td>El código usa 0,70 y 0,40 (<code>predictor_demanda.py:31-32</code>).</td><td>Corregir el documento.</td></tr>
              </tbody>
            </table>
          </div>
        </div>`,
      notas: 'El primer enfoque de la consigna dice «validando siempre sus resultados». Esta lámina es eso. Los asistentes nos ayudaron a escribir las pruebas de Hypothesis, el test de fugas y la documentación. Pero cuando preparamos la defensa volvimos a medir todo y encontramos cinco afirmaciones que no se sostenían tal cual. La más importante: el F1 ponderado. En el dataset de 1.000 productos da 0,996 aunque el modelo no marca ni una alerta, porque casi todos los productos son «sin quiebre». Es un ejemplo concreto de por qué hay que validar lo que propone la IA.'
    },

    /* 09 ---------------------------------------------------------------- */
    {
      icono: 'aduana', sku: 'B-09', etiqueta: 'Sigue pasando', fase: 'P4.6', tema: 'Calidad',
      titulo: 'La caja sigue pasando la aduana',
      sub: 'Sumar IA no rompió nada de lo anterior: el mismo pipeline de 7 etapas del Parcial 3 la controla en cada push',
      evidencia: 'pytest (18/11/2026, local) · .github/workflows/verify.yml · pyproject.toml',
      html: () => `
        <div class="fit" style="display:flex;flex-direction:column;gap:14px">
          <div class="grid-3">
            <div class="panel rv" style="--i:0"><h3>Pruebas</h3><div class="big-n">${MED.tests}<small>pasan</small></div><p class="small-p">Suite completa en ${MED.segundos} s, corrida en Windows para esta defensa.</p></div>
            <div class="panel rv" style="--i:1"><h3>Cobertura</h3><div class="big-n">${MED.cobertura} %<small>umbral 85 %</small></div><p class="small-p">Medida con <code>pytest --cov=src</code> sobre todo el código.</p></div>
            <div class="panel rv" style="--i:2"><h3>Nuevas</h3><div class="big-n">${MED.testsIa + MED.testsUi}<small>tests</small></div><p class="small-p">${MED.testsIa} en <code>tests/ia/</code> y ${MED.testsUi} de la pantalla en <code>tests/ui/</code>.</p></div>
          </div>
          <div class="grid-split">
            <div class="panel rv" style="--i:3">
              <h3>Qué controla cada archivo nuevo</h3>
              <table class="tbl">
                <tbody>
                  <tr><td><code>test_extractor_features.py</code></td><td>los 10 datos, casos sin historial</td><td class="r">11</td></tr>
                  <tr><td><code>test_predictor_ia.py</code></td><td>regla, modelo, cascada, Hypothesis</td><td class="r">11</td></tr>
                  <tr><td><code>test_integracion_motor_ia.py</code></td><td>el motor con las tres estrategias</td><td class="r">5</td></tr>
                  <tr><td><code>test_presupuesto_memoria_ia.py</code></td><td>memoria, fugas y speedup</td><td class="r">4</td></tr>
                  <tr><td><code>test_pantalla_ia.py</code></td><td>pantalla Flet: filtros y re-entreno</td><td class="r">6</td></tr>
                </tbody>
              </table>
            </div>
            <div class="panel rv" style="--i:4">
              <h3>Lo que tocó la aduana</h3>
              <ul class="ticks small">
                <li><code>scikit-learn</code> y <code>joblib</code> declarados en <code>pyproject.toml</code> y <code>requirements.txt</code>; quedan bajo pip-audit y Dependabot.</li>
                <li>mypy ignora los tipos faltantes de <code>sklearn</code> y <code>joblib</code>; el código propio sigue tipado.</li>
                <li>El deploy de la documentación quedó solo desde <code>main</code>, por la protección del entorno.</li>
              </ul>
              <p class="foot-note">El test de speedup exige que la regla sea al menos 3× más rápida que el modelo en cada corrida del CI.</p>
            </div>
          </div>
        </div>`,
      notas: 'Lo que construimos en el Parcial 3 hizo su trabajo: el módulo de IA entró por la misma aduana. Corrimos la suite completa para esta defensa: 235 pruebas pasan y la cobertura total es 89 %, arriba del umbral de 85. Las dependencias nuevas quedan vigiladas por pip-audit y Dependabot (de hecho Dependabot ya abrió una rama para actualizar joblib). Los 37 tests nuevos se suman a los que ya había al cerrar el Parcial 3.'
    },

    /* 10 ---------------------------------------------------------------- */
    {
      icono: 'demo', sku: 'B-10', etiqueta: 'Demo', fase: 'P4.5', tema: 'Demo en vivo',
      titulo: 'Demo en vivo: la pantalla «Predicción IA»',
      sub: 'La misma decisión, en la aplicación de escritorio. Estos son los resultados de la cascada sobre la demo',
      evidencia: 'src/ui/pantallas/prediccion_ia.py · python main.py',
      html: () => {
        const top = D.slice().sort((a, b) => b.hib[1] - a.hib[1]).slice(0, 7);
        const color = { bajo: '#4ADE80', medio: '#FCD34D', critico: '#FB7185' };
        return `
        <div class="grid-split fit" style="grid-template-columns:minmax(0,.8fr) minmax(0,1.2fr)">
          <div class="panel rv" style="--i:0">
            <h3>Guion de la demo</h3>
            <ol class="demo-steps">
              <li><span>Abrir la app con <code>python main.py</code> e ir a <b>Predicción IA</b>.</span></li>
              <li><span>Con <b>Cascada Híbrida (O(1) + IA)</b>: mirar latencia media, memoria y alertas activas.</span></li>
              <li><span>Cambiar a <b>Modelo IA (scikit-learn)</b>: comparar la latencia y los riesgos.</span></li>
              <li><span>Cambiar a <b>Heurística O(1)</b>: la latencia cae a casi cero.</span></li>
              <li><span>Filtrar <b>Crítico</b> y mostrar qué reponer primero.</span></li>
              <li><span>Pulsar <b>Re-entrenar Modelo</b>: se ajusta con el catálogo cargado.</span></li>
            </ol>
            <p class="foot-note">Si la app no abre: <code>pytest tests/ia -v</code> y <code>python benchmarks/comparar_ia.py</code> muestran lo mismo en la terminal.</p>
          </div>
          <div class="rv" style="--i:1">
            <div class="mock">
              <div class="mock-top"><i></i><i></i><i></i><span>Predicción IA · Cascada híbrida · demo_oral.json</span></div>
              <table>
                <thead><tr><th>Producto</th><th>Stock</th><th>P(quiebre)</th><th>Riesgo</th><th>Ruta</th></tr></thead>
                <tbody>${top.map((p) => `
                  <tr><td>${p.n}</td><td>${p.stock}</td><td><span class="pbar"><b style="width:${Math.round(p.hib[1] * 100)}%;background:${color[p.hib[2]]}"></b></span>${pct(p.hib[1])}</td><td><span class="risk ${p.hib[2]}"><i></i>${RIESGO[p.hib[2]]}</span></td><td>${p.hib[4] === 'ia' ? 'modelo' : 'regla'}</td></tr>`).join('')}
                </tbody>
              </table>
            </div>
            <p class="foot-note">Datos reales de <code>datos.js</code>, ordenados por probabilidad de quiebre como en la pantalla.</p>
          </div>
        </div>`;
      },
      notas: 'Salir de la presentación a la app. Guion: Cascada, después Modelo IA, después Heurística, filtro Crítico y re-entrenar. Si algo falla, no improvisar: la tabla de la derecha son los mismos resultados, y la terminal con pytest y el benchmark es el plan B.'
    },

    /* 11 ---------------------------------------------------------------- */
    {
      icono: 'cierre', sku: 'B-11', etiqueta: 'Conclusiones', fase: 'P4.6', tema: 'Cierre',
      titulo: 'Conclusiones y autocrítica',
      sub: 'Lo que rindió, lo que no y lo que haríamos distinto. Después de esto, la caja se entrega',
      evidencia: 'Todo lo anterior · docs/final/resumen-proyecto-final.md',
      html: () => `
        <div class="fit" style="display:flex;flex-direction:column;gap:14px">
          <div class="grid-3">
            <div class="panel tint-green rv" style="--i:0">
              <h3>Lo que rindió</h3>
              <ul class="ticks small">
                <li>La cascada: ${resumen.rapido} de ${D.length} productos se resuelven sin tocar el modelo.</li>
                <li>El modelo entró al sistema sin romper nada: ${MED.tests} tests, ${MED.cobertura} %.</li>
                <li>Un modelo de 2,6 KB, local, sin servicios externos.</li>
              </ul>
            </div>
            <div class="panel tint-red rv" style="--i:1">
              <h3>Lo que no salió</h3>
              <ul class="ticks small cross">
                <li>Entrenamos con historial sintético: no hay ventas reales.</li>
                <li>El regresor de demanda explica poco (R² ${fmt(MED.modelo.r2, 2)}).</li>
                <li>El F1 ponderado hizo ver bien a un modelo que en 1.000 productos no alertó nada.</li>
                <li>Medimos tiempo con tracemalloc encendido.</li>
              </ul>
            </div>
            <div class="panel tint-blue rv" style="--i:2">
              <h3>Qué haríamos distinto</h3>
              <ul class="ticks small warn">
                <li>Entrenar con el historial real del depósito.</li>
                <li>Reportar precisión y recall de la clase quiebre.</li>
                <li>Mandar a la regla los productos sin historial.</li>
                <li>Comparar con un árbol (XGBoost) y exportar a ONNX para medir inferencia.</li>
              </ul>
            </div>
          </div>
          <blockquote class="quote rv" style="--i:3">Cuatro hitos con la misma caja: <b>primero rápido, después mantenible, después controlado y al final, anticipando</b>. La IA llegó al final porque necesitaba todo lo anterior para medirse.</blockquote>
        </div>`,
      notas: 'Cerrar con autocrítica concreta. Lo que rindió: la cascada y la integración limpia. Lo que no: los datos sintéticos, el R² bajo, el F1 ponderado y la medición con tracemalloc. Qué haríamos distinto: datos reales, métricas por clase, mandar los productos sin historial a la regla y probar XGBoost y ONNX, que la cátedra propone en las láminas 391 y 392. Después, presionar P para entregar la caja.'
    }
  ];

  window.PEF4_CONTENIDO = { LAMINAS, ICONOS, MED, resumen };
})();
