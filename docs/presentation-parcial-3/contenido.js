/* ==========================================================================
   CONTENIDO DEL INFORME DE ADUANA — TERCER PARCIAL PEF (OPCIÓN 6)
   La caja que se re-despachó al final del Parcial 2 pasa por el control
   aduanero de Integración Continua: 7 puestos = 7 etapas del pipeline.

   Regla: toda cifra sale del repositorio (tag parcial-3) o de correr sus
   controles. Las mediciones locales se marcan como tales.
   ========================================================================== */
(function () {
  'use strict';

  const O = '#2B1E14';
  const st = 'stroke="' + O + '" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round"';
  const S = (b) => '<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' + b + '</svg>';

  function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }

  // Recorrido automático que se detiene apenas el orador hace clic en un ítem
  function recorrido(root, api, total, mostrar, opciones) {
    const o = Object.assign({ inicio: 1200, paso: 1300 }, opciones || {});
    const btn = root.querySelector('[data-tour]');
    let activo = false;
    let token = 0;
    const pintar = () => {
      if (!btn) return;
      btn.textContent = activo ? '❚❚ Pausar recorrido' : '▶ Recorrer solo';
      btn.classList.toggle('on', activo);
    };
    const correr = (desde, espera) => {
      const mio = ++token;
      activo = true;
      pintar();
      let i = desde;
      const tick = () => {
        if (!root.isConnected || mio !== token) return;
        mostrar(i);
        i += 1;
        if (i < total) api.later(api.ms(o.paso) || o.paso, tick);
        else { activo = false; pintar(); }
      };
      api.later(api.ms(espera) || espera, tick);
    };
    const detener = () => { token++; activo = false; pintar(); };
    if (btn) btn.addEventListener('click', () => { if (activo) detener(); else correr(0, 0); });
    correr(0, o.inicio);
    return { detener };
  }

  /* ------------------------------------------------------------------------
     Objetos de la oficina de aduana (viewBox 0 0 120 120)
     ------------------------------------------------------------------------ */
  const ARTE = {
    declaracion: S(
      '<rect x="24" y="16" width="72" height="92" rx="7" fill="#A8713F" ' + st + '/>' +
      '<rect x="31" y="27" width="58" height="74" rx="2" fill="#FFFEFB" ' + st + '/>' +
      '<rect x="44" y="9" width="32" height="16" rx="5" fill="#94A3B8" ' + st + '/>' +
      '<circle cx="60" cy="14.5" r="2.6" fill="' + O + '"/>' +
      '<rect x="37" y="34" width="46" height="7" rx="1.5" fill="#1D4ED8"/>' +
      '<text x="60" y="39.6" text-anchor="middle" font-family="monospace" font-size="5.6" font-weight="700" fill="#FFF">DECLARACIÓN P3</text>' +
      [50, 61, 72].map((y) => '<path d="M37 ' + y + 'l3 3 6-6" fill="none" stroke="#15803D" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"/><rect x="51" y="' + (y - 1.5) + '" width="31" height="3.4" rx="1.7" fill="#CBD5E1"/>').join('') +
      '<g transform="rotate(-12 72 88)"><circle cx="72" cy="88" r="11" fill="none" stroke="#BE123C" stroke-width="2"/><circle cx="72" cy="88" r="7.5" fill="none" stroke="#BE123C" stroke-width="1"/><text x="72" y="90.5" text-anchor="middle" font-family="monospace" font-size="6.5" font-weight="800" fill="#BE123C">CI</text></g>'
    ),
    planilla: S(
      '<rect x="16" y="20" width="88" height="80" rx="4" fill="#FFFEFB" ' + st + '/>' +
      '<rect x="16" y="20" width="88" height="14" rx="4" fill="#1E293B"/>' +
      '<path d="M16 34h88M16 47h88M16 60h88M16 73h88M16 86h88M44 34v66M64 34v66M84 34v66" stroke="#CBD5E1" stroke-width="1.3"/>' +
      (function () {
        let s = '';
        const marcas = [[1, 1, 1], [1, 1, 1], [1, 2, 1], [1, 1, 1], [1, 1, 3]];
        for (let r = 0; r < 5; r++) {
          for (let c = 0; c < 3; c++) {
            const x = 54 + c * 20;
            const y = 40.5 + r * 13;
            const m = marcas[r][c];
            if (m === 1) s += '<path d="M' + (x - 4) + ' ' + y + 'l2.6 2.6 5-5" fill="none" stroke="#15803D" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>';
            else if (m === 2) s += '<circle cx="' + x + '" cy="' + y + '" r="3" fill="#F59E0B"/>';
            else s += '<path d="M' + (x - 3) + ' ' + (y - 3) + 'l6 6M' + (x + 3) + ' ' + (y - 3) + 'l-6 6" stroke="#BE123C" stroke-width="2.4" stroke-linecap="round"/>';
          }
          s += '<rect x="21" y="' + (39 + r * 13) + '" width="18" height="3" rx="1.5" fill="#94A3B8"/>';
        }
        return s;
      })() +
      '<rect x="22" y="25" width="30" height="4" rx="2" fill="#FDBA74"/>'
    ),
    cinta: S(
      '<rect x="10" y="64" width="100" height="18" rx="9" fill="#334155" ' + st + '/>' +
      [22, 41, 60, 79, 98].map((x) => '<circle cx="' + x + '" cy="73" r="5.5" fill="#94A3B8" stroke="' + O + '" stroke-width="1.6"/><circle cx="' + x + '" cy="73" r="1.6" fill="' + O + '"/>').join('') +
      '<path d="M18 92 v12 M102 92 v12 M14 104 h12 M94 104 h12" stroke="' + O + '" stroke-width="3" stroke-linecap="round"/>' +
      '<rect x="40" y="36" width="36" height="28" rx="2" fill="#C49A6C" ' + st + '/>' +
      '<rect x="40" y="46" width="36" height="6" fill="#7FB77E"/>' +
      '<path d="M86 50 h16 m-6 -6 l6 6 -6 6" fill="none" stroke="#C2410C" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>' +
      '<path d="M14 46 h14" stroke="#94A3B8" stroke-width="3" stroke-linecap="round" stroke-dasharray="3 5"/>'
    ),
    rayosx: S(
      '<rect x="12" y="18" width="96" height="70" rx="8" fill="#1E293B" ' + st + '/>' +
      '<rect x="20" y="26" width="80" height="54" rx="4" fill="#082F49" stroke="#0EA5E9" stroke-width="1.4"/>' +
      '<rect x="36" y="38" width="48" height="32" rx="1" fill="none" stroke="#7DD3FC" stroke-width="2"/>' +
      '<rect x="42" y="44" width="14" height="18" rx="1" fill="#38BDF8" opacity="0.55"/>' +
      '<circle cx="66" cy="50" r="6" fill="#38BDF8" opacity="0.5"/>' +
      '<rect x="62" y="58" width="16" height="7" rx="1" fill="#38BDF8" opacity="0.45"/>' +
      '<path d="M20 52 h80" stroke="#F0F9FF" stroke-width="1.6" opacity="0.85"/>' +
      '<rect x="44" y="88" width="32" height="8" rx="2" fill="#475569" ' + st + '/>' +
      '<rect x="34" y="96" width="52" height="7" rx="3" fill="#334155" ' + st + '/>'
    ),
    perro: S(
      '<path d="M30 70 Q28 52 46 50 H78 Q92 50 92 64 V74 Q92 80 86 80 H40 Q30 80 30 70Z" fill="#B7793F" ' + st + '/>' +
      '<path d="M30 62 Q16 56 14 44" fill="none" stroke="' + O + '" stroke-width="5" stroke-linecap="round"/>' +
      '<path d="M30 62 Q16 56 14 44" fill="none" stroke="#B7793F" stroke-width="2.6" stroke-linecap="round"/>' +
      '<path d="M40 80 v16 M50 80 v16 M74 80 v16 M84 80 v16" stroke="' + O + '" stroke-width="7" stroke-linecap="round"/>' +
      '<path d="M40 80 v16 M50 80 v16 M74 80 v16 M84 80 v16" stroke="#9A622F" stroke-width="4.4" stroke-linecap="round"/>' +
      '<path d="M78 46 Q80 32 94 32 Q104 32 106 44 L110 54 Q111 60 104 60 H92 Q82 60 78 52Z" fill="#B7793F" ' + st + '/>' +
      '<path d="M88 34 Q80 40 84 56 Q90 50 92 36Z" fill="#6F4528" ' + st + '/>' +
      '<circle cx="98" cy="42" r="2.4" fill="' + O + '"/>' +
      '<circle cx="109" cy="54" r="3.2" fill="' + O + '"/>' +
      '<rect x="74" y="52" width="10" height="5" rx="2" fill="#C2410C" ' + st + '/>' +
      '<path d="M112 64 q4 2 2 6 M115 58 q5 1 4 6" fill="none" stroke="#94A3B8" stroke-width="1.8" stroke-linecap="round"/>' +
      '<rect x="44" y="56" width="26" height="12" rx="2" fill="#FFF7ED" ' + st + '/>' +
      '<text x="57" y="64.5" text-anchor="middle" font-family="monospace" font-size="6" font-weight="800" fill="#C2410C">K-9</text>'
    ),
    semaforo: S(
      '<rect x="40" y="10" width="40" height="88" rx="10" fill="#1E293B" ' + st + '/>' +
      '<circle cx="60" cy="28" r="10" fill="#4C0519" stroke="' + O + '" stroke-width="1.6"/>' +
      '<circle cx="60" cy="54" r="10" fill="#451A03" stroke="' + O + '" stroke-width="1.6"/>' +
      '<circle cx="60" cy="80" r="10" fill="#22C55E" stroke="' + O + '" stroke-width="1.6"/>' +
      '<circle cx="56" cy="76" r="3" fill="#DCFCE7"/>' +
      '<rect x="56" y="98" width="8" height="14" fill="#475569" ' + st + '/>' +
      '<path d="M30 24h10M30 50h10M30 76h10M80 24h10M80 50h10M80 76h10" stroke="#475569" stroke-width="4" stroke-linecap="round"/>'
    ),
    muestras: S(
      '<rect x="14" y="70" width="92" height="14" rx="3" fill="#A8713F" ' + st + '/>' +
      '<rect x="18" y="84" width="8" height="18" fill="#8D5F38" ' + st + '/><rect x="94" y="84" width="8" height="18" fill="#8D5F38" ' + st + '/>' +
      [30, 52, 74, 96].map((x, i) =>
        '<path d="M' + (x - 6) + ' 24 V80 a6 6 0 0 0 12 0 V24" fill="#F8FAFC" ' + st + '/>' +
        '<path d="M' + (x - 6) + ' ' + (50 + i * 4) + ' V80 a6 6 0 0 0 12 0 V' + (50 + i * 4) + ' Z" fill="' + ['#4ADE80', '#4ADE80', '#86EFAC', '#4ADE80'][i] + '"/>' +
        '<rect x="' + (x - 8) + '" y="20" width="16" height="6" rx="2" fill="#CBD5E1" ' + st + '/>'
      ).join('') +
      '<circle cx="88" cy="22" r="11" fill="#15803D" ' + st + '/><path d="M83 22 l3.5 3.5 7-7" fill="none" stroke="#FFF" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>'
    ),
    balanza: S(
      '<rect x="14" y="72" width="92" height="28" rx="6" fill="#475569" ' + st + '/>' +
      '<rect x="20" y="62" width="80" height="12" rx="3" fill="#CBD5E1" ' + st + '/>' +
      '<rect x="40" y="79" width="40" height="14" rx="2" fill="#052E16" stroke="' + O + '" stroke-width="1.6"/>' +
      '<text x="60" y="89.5" text-anchor="middle" font-family="monospace" font-size="9" font-weight="700" fill="#4ADE80">1.0 MB</text>' +
      '<rect x="40" y="38" width="40" height="24" rx="2" fill="#C49A6C" ' + st + '/><rect x="40" y="46" width="40" height="5" fill="#7FB77E"/>' +
      '<circle cx="92" cy="30" r="13" fill="#FFFEFB" ' + st + '/><path d="M92 30 V22 M92 30 l6 4" stroke="#C2410C" stroke-width="2.4" stroke-linecap="round"/>' +
      '<rect x="88" y="13" width="8" height="5" rx="1.5" fill="#94A3B8" ' + st + '/>'
    ),
    manifiesto: S(
      '<rect x="22" y="14" width="70" height="92" rx="4" fill="#FFFEFB" ' + st + '/>' +
      ['#C2410C', '#B45309', '#15803D', '#0F766E', '#1D4ED8', '#7E22CE', '#BE123C', '#475569', '#4D7C0F'].map((c, i) =>
        '<rect x="90" y="' + (18 + i * 9.6) + '" width="12" height="7.6" rx="2" fill="' + c + '" stroke="' + O + '" stroke-width="1.2"/>').join('') +
      '<rect x="30" y="22" width="50" height="7" rx="2" fill="#1E293B"/>' +
      '<text x="55" y="27.6" text-anchor="middle" font-family="monospace" font-size="5.4" font-weight="800" fill="#FDBA74">MANIFIESTO</text>' +
      [38, 48, 58, 68, 78, 88].map((y, i) => '<text x="30" y="' + (y + 2.4) + '" font-family="monospace" font-size="6" font-weight="800" fill="#1D4ED8">' + (i + 1) + '</text><rect x="37" y="' + y + '" width="' + [40, 32, 44, 28, 38, 34][i] + '" height="3.2" rx="1.6" fill="#CBD5E1"/>').join('')
    ),
    terminal: S(
      '<rect x="18" y="22" width="84" height="58" rx="5" fill="#334155" ' + st + '/>' +
      '<rect x="24" y="28" width="72" height="46" rx="2" fill="#0B1220"/>' +
      '<path d="M30 38 l5 4 -5 4" fill="none" stroke="#4ADE80" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>' +
      '<rect x="39" y="40" width="30" height="3.4" rx="1.7" fill="#E2E8F0"/>' +
      '<rect x="30" y="50" width="44" height="3.4" rx="1.7" fill="#4ADE80"/>' +
      '<rect x="30" y="58" width="36" height="3.4" rx="1.7" fill="#4ADE80"/>' +
      '<rect x="30" y="66" width="8" height="4" fill="#F8FAFC"/>' +
      '<path d="M10 82 H110 L104 94 H16 Z" fill="#94A3B8" ' + st + '/>' +
      '<rect x="50" y="85" width="20" height="3" rx="1.5" fill="#64748B"/>'
    ),
    contrabando: S(
      '<path d="M30 46 Q30 32 44 32 H76 Q90 32 90 46" fill="none" stroke="' + O + '" stroke-width="7" stroke-linecap="round"/>' +
      '<path d="M30 46 Q30 32 44 32 H76 Q90 32 90 46" fill="none" stroke="#6F4528" stroke-width="4" stroke-linecap="round"/>' +
      '<rect x="14" y="44" width="92" height="58" rx="8" fill="#8D5F38" ' + st + '/>' +
      '<rect x="14" y="62" width="92" height="22" fill="#5C3A22" ' + st + '/>' +
      '<g transform="rotate(-18 60 73)"><circle cx="46" cy="73" r="6.5" fill="none" stroke="#FCD34D" stroke-width="3"/><path d="M52 73 H74 M68 73 v5 M72 73 v4" stroke="#FCD34D" stroke-width="3" stroke-linecap="round"/></g>' +
      '<path d="M86 12 L106 46 H66 Z" fill="#BE123C" ' + st + '/>' +
      '<path d="M86 24 V35" stroke="#FFF" stroke-width="3.4" stroke-linecap="round"/><circle cx="86" cy="40.5" r="2" fill="#FFF"/>'
    ),
    liberado: S(
      '<g transform="rotate(-10 60 96)"><rect x="24" y="86" width="72" height="20" rx="3" fill="none" stroke="#15803D" stroke-width="2.6" opacity="0.75"/><text x="60" y="100" text-anchor="middle" font-family="monospace" font-size="10" font-weight="800" fill="#15803D" opacity="0.8">LIBERADO</text></g>' +
      '<rect x="31" y="62" width="58" height="9" rx="2" fill="#15803D" ' + st + '/>' +
      '<rect x="27" y="44" width="66" height="19" rx="4" fill="#7C4A26" ' + st + '/>' +
      '<path d="M52 20 h16 l4 25 h-24 z" fill="#8D5F38" ' + st + '/>' +
      '<circle cx="60" cy="14" r="11" fill="#A8713F" ' + st + '/>'
    )
  };

  // Siluetas del contenido real de la caja (lo que se ve con rayos X)
  const SILUETAS = ['remito', 'manual', 'ruta', 'calidad', 'tests', 'tijera', 'lupa', 'rollo', 'monitor', 'bloques', 'sphinx', 'certificado', 'sello'];

  /* ------------------------------------------------------------------------
     Los 7 puestos de la aduana (= 7 etapas del pipeline)
     Resultados obtenidos corriendo los controles sobre el tag parcial-3.
     ------------------------------------------------------------------------ */
  const PUESTOS = [
    { n: 'Ingreso', e: 'Etapa 1 · Integración del código', fx: 'ticket',
      c: [
        ['Disparadores', 'push · pull_request · workflow_dispatch', 'en cada cambio'],
        ['Checkout', 'actions/checkout', 'repositorio descargado'],
        ['Revisión', 'PR contra dev / main', 'nada entra sin pasar la cinta']
      ] },
    { n: 'Precintos', e: 'Etapa 2 · Preparación del entorno', fx: 'precinto',
      c: [
        ['Python', 'actions/setup-python', '3.14 en el runner'],
        ['Dependencias', 'uv sync --locked --no-build', 'versiones fijadas en uv.lock'],
        ['Instalador', 'astral-sh/setup-uv', 'fijado por SHA']
      ] },
    { n: 'Rayos X y perro detector', e: 'Etapa 3 · Calidad estática y secretos', fx: 'rayos',
      c: [
        ['Sintaxis', 'python -m compileall -q …', 'sin errores'],
        ['Estilo', 'ruff check .', 'All checks passed!'],
        ['Formato', 'ruff format --check .', '110 files already formatted'],
        ['Complejidad', 'complexipy … --max-complexity-allowed 15', '0 funciones > 15'],
        ['Tipado', 'mypy src/', '0 errores en 43 archivos'],
        ['Código inseguro', 'bandit -r src/ -ll', 'No issues identified · 6.485 líneas'],
        ['Secretos', 'gitleaks (acción)', 'sin hallazgos fuera del allowlist']
      ] },
    { n: 'Inspección de muestras', e: 'Etapa 4 · Pruebas y cobertura', fx: 'muestras',
      c: [
        ['Pruebas', 'pytest tests/', '198 passed'],
        ['Cobertura', '--cov-fail-under=85', '90 % (2.532 sentencias)'],
        ['Plataformas', 'matriz Ubuntu + Windows', 'misma suite en ambos'],
        ['Reporte', '--junitxml', 'JUnit XML como artefacto']
      ] },
    { n: 'Proveedores y manifiesto', e: 'Etapa 5 · Dependencias y documentación', fx: 'manifiesto',
      c: [
        ['Dependencias', 'pip-audit -r requirements*.txt', 'No known vulnerabilities found'],
        ['Parches', 'Dependabot (pip + actions)', 'revisión semanal'],
        ['Documentación', 'sphinx-build -W -b html', '0 advertencias · 37 páginas'],
        ['Enlaces', 'sphinx-build -b linkcheck', 'enlaces externos validados']
      ] },
    { n: 'Balanza y cronómetro', e: 'Etapa 6 · Rendimiento y memoria', fx: 'balanza',
      c: [
        ['Streaming JSONL', 'tracemalloc', 'pico 1,03 MB · límite 10 MB'],
        ['Catálogo hash', 'tracemalloc', '0,59 MB · límite 3 MB'],
        ['Picking', 'tracemalloc', '0,09 MB · límite 5 MB'],
        ['Benchmarks', 'pytest-benchmark --benchmark-json', 'hash 71 ns · lineal 1.214 ns'],
        ['Profiling', 'python -m benchmarks.comparar', 'smoke OK']
      ] },
    { n: 'Semáforo', e: 'Etapa 7 · Resultado y reportes', fx: 'semaforo',
      c: [
        ['Seguridad', 'upload-sarif (Bandit)', 'GitHub Security'],
        ['Calidad', 'SonarQube Cloud', 'Quality Gate'],
        ['Publicación', 'deploy-pages', 'documentación en GitHub Pages'],
        ['Dictamen', 'todos los jobs en verde', 'LIBERADO · canal verde']
      ] }
  ];

  /* ------------------------------------------------------------------------
     Matriz de controles (sección 2.2 y 3.1 de la consigna) tal como está hoy
     ------------------------------------------------------------------------ */
  const MATRIZ = [
    { c: 'Sintaxis', h: 'compileall', r: 'consola', x: 'error de sintaxis', t: 'det', e: 3, cmd: 'python -m compileall -q src automations benchmarks tests scripts main.py' },
    { c: 'Análisis estático', h: 'Ruff', r: 'consola · JSON para Sonar', x: 'cualquier violación activa', t: 'det', e: 3, cmd: 'ruff check .' },
    { c: 'Formato', h: 'ruff format', r: 'diff', x: 'archivo sin formatear', t: 'det', e: 3, cmd: 'ruff format --check .' },
    { c: 'Complejidad', h: 'complexipy · Radon', r: 'consola', x: 'función con complejidad cognitiva > 15', t: 'det', e: 3, cmd: 'complexipy src automations benchmarks scripts main.py --max-complexity-allowed 15 --failed' },
    { c: 'Tipado', h: 'mypy', r: 'consola', x: '≥ 1 error en src/ (UI excluida)', t: 'det', e: 3, cmd: 'mypy src/' },
    { c: 'Código inseguro', h: 'Bandit', r: 'SARIF · consola', x: 'severidad Media o Alta (-ll)', t: 'det', e: 3, cmd: 'bandit -r src/ -f sarif -o bandit-report.sarif -ll' },
    { c: 'Secretos', h: 'Gitleaks', r: 'consola de la acción', x: 'secreto fuera del allowlist', t: 'det', e: 3, cmd: 'gitleaks detect --source . --verbose' },
    { c: 'Pruebas', h: 'pytest', r: 'JUnit XML', x: '≥ 1 prueba falla', t: 'det', e: 4, cmd: 'pytest tests/ -v --junitxml=pytest-report.xml' },
    { c: 'Cobertura', h: 'pytest-cov', r: 'coverage.xml', x: 'menos de 85 %', t: 'det', e: 4, cmd: 'pytest tests/ --cov=src --cov-report=xml:coverage.xml --cov-fail-under=85' },
    { c: 'Dependencias', h: 'pip-audit · Dependabot', r: 'JSON · consola · PRs', x: 'vulnerabilidad conocida', t: 'det', e: 5, cmd: 'pip-audit -r requirements.txt -r requirements-dev.txt --format json -o pip-audit-report.json' },
    { c: 'Documentación', h: 'Sphinx -W', r: 'HTML', x: 'cualquier advertencia', t: 'det', e: 5, cmd: 'sphinx-build -W -b html docs/sphinx docs/sphinx/_build/html' },
    { c: 'Enlaces', h: 'Sphinx linkcheck', r: 'output.json', x: 'enlace roto', t: 'red', e: 5, cmd: 'sphinx-build -b linkcheck docs/sphinx docs/sphinx/_build/linkcheck' },
    { c: 'Memoria', h: 'tracemalloc (tests)', r: 'log de pytest', x: 'pico sobre el límite de cada prueba', t: 'tol', e: 6, cmd: 'pytest tests/integracion/test_presupuesto_memoria.py -v' },
    { c: 'Benchmark', h: 'pytest-benchmark', r: 'benchmark-report.json', x: 'speedup hash < 3× (aserción en la suite)', t: 'tol', e: 6, cmd: 'pytest tests/integracion/test_benchmarks.py --benchmark-only --benchmark-json=benchmark-report.json' },
    { c: 'Profiling', h: 'cProfile · Scalene (smoke)', r: 'consola · docs/mediciones', x: 'el script de perfilado falla', t: 'det', e: 6, cmd: 'python -m benchmarks.comparar' }
  ];

  const JOBS = [
    { k: 'fast', t: 'fast-checks', e: 'Etapas 1–3', d: 'Calidad estática, tipado y SAST', col: 0, needs: [],
      pasos: ['checkout', 'Python 3.14 + uv sync --locked', 'compileall', 'ruff check · ruff format', 'complexipy ≤ 15', 'mypy src/', 'bandit (SARIF)', 'gitleaks', 'artefacto SARIF'] },
    { k: 'tests', t: 'test-suite', e: 'Etapa 4', d: 'Pruebas · Ubuntu y Windows', col: 1, needs: ['fast'],
      pasos: ['pytest con --cov-fail-under=85', 'coverage.xml (Ubuntu)', 'JUnit XML por sistema'] },
    { k: 'deps', t: 'deps-and-docs', e: 'Etapa 5', d: 'Dependencias y documentación', col: 1, needs: ['fast'],
      pasos: ['pip-audit (JSON)', 'motor AST de complejidad', 'integridad de datasets', 'presentación P1 (11 slides)', 'sphinx-build -W', 'sphinx linkcheck', 'artefacto de Pages'] },
    { k: 'perf', t: 'performance-and-memory', e: 'Etapa 6', d: 'Rendimiento y memoria', col: 2, needs: ['tests'],
      pasos: ['presupuesto de memoria (tracemalloc)', 'pytest-benchmark → JSON', 'smoke de profiling'] },
    { k: 'sonar', t: 'sonarqube', e: 'Etapa 7', d: 'SonarQube Cloud', col: 2, needs: ['tests'],
      pasos: ['descarga coverage.xml', 'reporte de ruff', 'Quality Gate'] },
    { k: 'sarif', t: 'sarif-upload', e: 'Etapa 7', d: 'Reportes a GitHub Security', col: 2, needs: ['fast', 'deps'],
      pasos: ['descarga el SARIF de Bandit', 'codeql-action/upload-sarif'] },
    { k: 'pages', t: 'deploy-docs', e: 'Etapa 7', d: 'Publicación en GitHub Pages', col: 2, needs: ['deps'],
      pasos: ['solo en push a main / dev', 'deploy-pages'] }
  ];

  const SECCIONES = [
    ['Descripción funcional', 'Problema que resuelve, alcance y requisitos del sistema'],
    ['Arquitectura', 'Principios de diseño, diagrama de componentes, módulos y responsabilidades'],
    ['Instalación y ejecución', 'Requisitos, uv o pip, cómo correr la app, perfiles, tests y empaquetado'],
    ['Diseño técnico', 'Estructuras de datos, matriz Big-O y decisiones algorítmicas'],
    ['API y contratos', 'Referencia generada con autodoc desde los docstrings (entradas, salidas, excepciones)'],
    ['Pruebas', 'Filosofía, organización por dominio, cobertura y property-based testing'],
    ['Rendimiento', 'Profiling multi-herramienta, tabla comparativa, microbenchmarks y autocrítica de IPC'],
    ['Seguridad', 'Enfoque SAST + SCA + secretos, severidades, falsos positivos y parches'],
    ['Mantenimiento', 'Flujo de contribución, reproducción local de los 13 controles y fallos típicos del CI']
  ];

  const TERMINAL = [
    ['uv sync --locked --extra dev --extra docs', ['Resolved · Audited · entorno idéntico a uv.lock']],
    ['python -m compileall -q src automations benchmarks tests scripts main.py', ['(sin salida: 0 errores de sintaxis)']],
    ['ruff check .', ['All checks passed!']],
    ['ruff format --check .', ['110 files already formatted']],
    ['complexipy src automations benchmarks scripts main.py --max-complexity-allowed 15 --failed', ['No functions were found with complexity greater than 15.']],
    ['mypy src/', ['Success: no issues found in 43 source files']],
    ['bandit -r src/ -ll', ['No issues identified.', 'Total lines of code: 6485 · issues skipped (#nosec B311): 2']],
    ['gitleaks detect --source . --verbose', ['(se corre en el CI con gitleaks-action y .gitleaks.toml)']],
    ['pytest tests/ --cov=src --cov-fail-under=85', ['TOTAL   2532   263   90%', '198 passed']],
    ['pytest tests/integracion/test_presupuesto_memoria.py -v', ['4 passed']],
    ['pytest tests/integracion/test_benchmarks.py --benchmark-only', ['6 passed, 1 skipped']],
    ['pip-audit -r requirements.txt -r requirements-dev.txt', ['No known vulnerabilities found']],
    ['sphinx-build -W -b html docs/sphinx docs/sphinx/_build/html', ['build succeeded.']]
  ];

  const CONTRABANDO = [
    { k: 'token', t: 'Un token pegado en el código', e: 2, h: 'Gitleaks', out: 'Finding:  AWS_KEY = "AKIA••••••••EXAMPLE"\nRuleID:   aws-access-token\nleaks found: 1' },
    { k: 'cc', t: 'Una función con 20 ramas anidadas', e: 2, h: 'complexipy', out: 'procesar_todo   src/motor/ejemplo.py   20   FAILED\n1 function exceeded the max complexity (15)' },
    { k: 'tipo', t: 'Un id de producto pasado como texto', e: 2, h: 'mypy', out: 'error: Argument 1 to "buscar_por_id" has incompatible type "str";\nexpected "int"  [arg-type]\nFound 1 error in 1 file' },
    { k: 'eval', t: 'Un eval() sobre datos del archivo', e: 2, h: 'Bandit', out: '>> Issue: [B307:blacklist] Use of possibly insecure function -\n   consider using safer ast.literal_eval.\n   Severity: Medium   Confidence: High' },
    { k: 'test', t: 'Un cambio que rompe una regla de negocio', e: 3, h: 'pytest', out: 'FAILED tests/pedidos/test_evaluador.py::... - AssertionError\n1 failed, 197 passed' },
    { k: 'lineal', t: 'Volver a buscar recorriendo la lista', e: 3, h: 'pytest (aserción de speedup)', out: 'AssertionError: Alerta de regresión algorítmica: el speedup del\ncatálogo hash (1.02x) no alcanzó el umbral mínimo aceptable de 3.0x' },
    { k: 'cov', t: 'Código nuevo sin ningún test', e: 3, h: 'pytest-cov', out: 'FAIL Required test coverage of 85% not reached.\nTotal coverage: 82.40%' },
    { k: 'dep', t: 'Una dependencia con vulnerabilidad conocida', e: 4, h: 'pip-audit', out: 'Found 1 known vulnerability in 1 package\nName           Version ID\n-------------- ------- -------------\npaquete-ejemplo 1.0.0  PYSEC-XXXX-XX' },
    { k: 'doc', t: 'Un docstring mal indentado', e: 4, h: 'Sphinx -W', out: 'WARNING: Unexpected indentation.\nbuild finished with problems, 1 warning\n(with warnings treated as errors).' },
    { k: 'mem', t: 'Cargar el JSONL entero en una lista', e: 5, h: 'tracemalloc', out: 'AssertionError: Regresión de memoria en streaming: consumo de\n13.40 MB supera el límite de 10.0 MB.' }
  ];

  const ETAPAS_CORTAS = ['Ingreso', 'Entorno', 'Estática', 'Pruebas', 'Deps + docs', 'Rendimiento', 'Resultado'];

  /* ------------------------------------------------------------------------
     Láminas
     ------------------------------------------------------------------------ */
  const LAMINAS = [
    /* 01 ---------------------------------------------------------------- */
    {
      arte: 'declaracion', etiqueta: 'Declaración', fase: 'P3.0', tema: 'Consigna',
      titulo: 'Declaración de aduana: qué pide el Parcial 3',
      sub: 'La caja ya funciona (P1) y es mantenible (P2). Ahora no puede llegar a main sin pasar un control automático, documentado y reproducible',
      evidencia: 'docs/Parcial-3.docx · docs/planificacion-parcial-3.md',
      html: () => `
        <div class="grid-split">
          <div class="consigna rv" style="--i:0">
            <div class="cons-block"><span class="cb-n">1</span><div><b>Documentación externa</b><p>Las 9 secciones obligatorias y cómo correr en local los mismos controles del CI.</p></div><button type="button" class="mini-btn" data-goto="8">ítem 09 →</button></div>
            <div class="cons-block"><span class="cb-n">2</span><div><b>CI con matriz de controles</b><p>Cada control con herramienta, comando reproducible, reporte y criterio de rechazo, organizado en etapas por costo.</p></div><button type="button" class="mini-btn" data-goto="1">ítem 02 →</button></div>
            <div class="cons-block"><span class="cb-n">3</span><div><b>Seguridad</b><p>Código, dependencias y secretos; reportes JSON o SARIF; política de bloqueo por severidad y falsos positivos documentados.</p></div><button type="button" class="mini-btn" data-goto="4">ítem 05 →</button></div>
          </div>
          <div class="panel rv" style="--i:1">
            <h3>Fases del Parcial 3 <span class="chip chip-green" id="fase-count">0 / 7</span></h3>
            <table class="check-tbl">
              <tbody>
                ${[
                  ['P3.0', 'Plan y especificación de políticas', 'c3906b0', 0],
                  ['P3.1', 'Seguridad: Bandit, pip-audit, Gitleaks, Dependabot', '0d70982', 4],
                  ['P3.2', 'Tipado estático con mypy', '297df3d', 3],
                  ['P3.3', 'Presupuestos de memoria y aserción de rendimiento', '43ee2bf', 7],
                  ['P3.4', 'Pipeline en 7 etapas y SARIF', '837c321', 2],
                  ['P3.5', 'Sphinx en 9 secciones y linkcheck', '94db233', 8],
                  ['P3.6', 'Cierre y tag parcial-3', '81444b6', 11]
                ].map((r, i) => `
                  <tr data-goto="${r[3]}" tabindex="0">
                    <td class="ck"><span class="tick">✓</span></td>
                    <td><b>${r[0]}</b> ${r[1]}</td>
                    <td><code>${r[2]}</code></td>
                    <td class="go">→</td>
                  </tr>`).join('')}
              </tbody>
            </table>
            <p class="foot-note">Rama base <code>dev</code>, una rama por fase (<code>p3/fN-…</code>) y merge a <code>main</code> con el tag <code>parcial-3</code>.</p>
          </div>
        </div>`,
      init(root, api) {
        root.querySelectorAll('[data-goto]').forEach((el) => {
          const ir = () => api.goTo(Number(el.dataset.goto));
          el.addEventListener('click', ir);
          el.addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.stopPropagation(); ir(); } });
        });
        const filas = root.querySelectorAll('tr[data-goto]');
        const cnt = root.querySelector('#fase-count');
        filas.forEach((tr, i) => api.later(api.ms(400 + i * 170), () => { tr.classList.add('checked'); cnt.textContent = (i + 1) + ' / 7'; }));
      },
      notas: 'La consigna del Parcial 3 tiene tres bloques: documentación externa con 9 secciones, un CI con una matriz de controles donde cada control tiene herramienta, comando, reporte y criterio de rechazo, y una capa de seguridad con política por severidad. Lo resolvimos en 7 fases, como en los parciales anteriores, y quedó en main con el tag parcial-3. La metáfora: la caja ya no se puede despachar a mano; cada cambio pasa por la aduana.'
    },

    /* 02 ---------------------------------------------------------------- */
    {
      arte: 'planilla', etiqueta: 'Matriz', fase: 'P3.4', tema: 'Matriz de controles',
      titulo: 'Matriz de controles: herramienta, reporte y criterio de rechazo',
      sub: '15 controles cubren las 11 categorías de la consigna. Clic en una fila para ver el comando reproducible',
      evidencia: '.github/workflows/verify.yml · docs/planificacion-parcial-3.md §3',
      html: () => `
        <div class="matriz rv" style="--i:0">
          <div class="mx-filter" id="mx-filter">
            <span>Etapa</span>
            <button type="button" class="active" data-e="0">Todas</button>
            ${[3, 4, 5, 6].map((e) => `<button type="button" data-e="${e}">${e} · ${ETAPAS_CORTAS[e - 1]}</button>`).join('')}
            <span class="mx-legend"><i class="tp det"></i>determinista <i class="tp tol"></i>con tolerancia <i class="tp red"></i>depende de la red</span>
          </div>
          <table class="mx-tbl">
            <thead><tr><th>Control</th><th>Herramienta</th><th>Reporte</th><th>Se rechaza si…</th><th>Etapa</th></tr></thead>
            <tbody>
              ${MATRIZ.map((m, i) => `
                <tr data-i="${i}" data-e="${m.e}" style="--i:${i}">
                  <td><i class="tp ${m.t}"></i><b>${m.c}</b></td>
                  <td>${m.h}</td>
                  <td class="mono">${m.r}</td>
                  <td>${m.x}</td>
                  <td class="mono">${m.e}</td>
                </tr>`).join('')}
            </tbody>
          </table>
          <div class="mx-cmd" id="mx-cmd"><span class="prompt">$</span><code id="mx-cmd-txt">elegí un control</code></div>
        </div>`,
      init(root) {
        const filas = root.querySelectorAll('.mx-tbl tbody tr');
        const txt = root.querySelector('#mx-cmd-txt');
        filas.forEach((tr) => tr.addEventListener('click', () => {
          filas.forEach((f) => f.classList.toggle('on', f === tr));
          txt.textContent = MATRIZ[Number(tr.dataset.i)].cmd;
          const box = root.querySelector('#mx-cmd');
          box.classList.remove('flash'); void box.offsetWidth; box.classList.add('flash');
        }));
        root.querySelectorAll('#mx-filter button').forEach((b) => b.addEventListener('click', () => {
          root.querySelectorAll('#mx-filter button').forEach((x) => x.classList.toggle('active', x === b));
          const e = Number(b.dataset.e);
          filas.forEach((f) => f.classList.toggle('dim', e !== 0 && Number(f.dataset.e) !== e));
        }));
        filas[1].click();
      },
      notas: 'Esta es la parte central que pide la cátedra. Cada fila tiene herramienta, reporte y condición de rechazo; el clic muestra el comando exacto que corre el CI. Distinguir: casi todos los controles son deterministas; memoria y benchmark tienen tolerancia porque dependen del entorno; linkcheck depende de la red. Si preguntan por la regresión de benchmarks: hoy se rechaza si el hash pierde el speedup de 3× frente a la lista; el JSON de pytest-benchmark queda como artefacto, todavía sin comparación automática contra una línea base.'
    },

    /* 03 ---------------------------------------------------------------- */
    {
      arte: 'cinta', etiqueta: 'Cinta', fase: 'P3.4', tema: 'Diseño del pipeline',
      titulo: 'Diseño del pipeline: primero lo barato, después lo caro',
      sub: '7 jobs de GitHub Actions. Si falla algo estático, no se gastan minutos en pruebas ni en mediciones',
      evidencia: '.github/workflows/verify.yml (needs entre jobs)',
      html: () => `
        <div class="dag-wrap rv" style="--i:0">
          <div class="tour-bar"><span>Clic en un job para ver sus pasos</span><button type="button" class="mini-btn" data-tour>▶ Recorrer solo</button></div>
          <div class="dag" id="dag">
            <svg class="dag-lines" id="dag-lines" aria-hidden="true"></svg>
            ${[0, 1, 2].map((col) => `
              <div class="dag-col">
                <span class="dag-col-t">${['Barato y rápido', 'Con la caja limpia', 'Mediciones y publicación'][col]}</span>
                ${JOBS.filter((j) => j.col === col).map((j) => `
                  <button type="button" class="job" data-k="${j.k}">
                    <span class="job-e">${j.e}</span>
                    <strong>${j.t}</strong>
                    <span>${j.d}</span>
                  </button>`).join('')}
              </div>`).join('')}
          </div>
          <div class="panel job-detail" id="job-detail"></div>
        </div>`,
      init(root, api) {
        const svg = root.querySelector('#dag-lines');
        const dag = root.querySelector('#dag');
        const btns = root.querySelectorAll('.job');
        const det = root.querySelector('#job-detail');
        const dibujar = () => {
          const z = api.zoom();
          const r0 = dag.getBoundingClientRect();
          svg.setAttribute('width', r0.width / z);
          svg.setAttribute('height', r0.height / z);
          let paths = '';
          JOBS.forEach((j) => j.needs.forEach((n) => {
            const a = root.querySelector('.job[data-k="' + n + '"]').getBoundingClientRect();
            const b = root.querySelector('.job[data-k="' + j.k + '"]').getBoundingClientRect();
            const x1 = (a.right - r0.left) / z;
            const y1 = (a.top + a.height / 2 - r0.top) / z;
            const x2 = (b.left - r0.left) / z;
            const y2 = (b.top + b.height / 2 - r0.top) / z;
            const mx = (x1 + x2) / 2;
            paths += '<path data-from="' + n + '" data-to="' + j.k + '" d="M' + x1 + ' ' + y1 + ' C' + mx + ' ' + y1 + ' ' + mx + ' ' + y2 + ' ' + x2 + ' ' + y2 + '"/>';
          }));
          svg.innerHTML = paths;
        };
        const mostrar = (i) => {
          const j = JOBS[i];
          btns.forEach((b) => b.classList.toggle('active', b.dataset.k === j.k));
          svg.querySelectorAll('path').forEach((p) => p.classList.toggle('hot', p.dataset.to === j.k));
          det.innerHTML = `<h3>${j.t} <span class="chip">${j.e}</span></h3>
            <p class="small-p">${j.needs.length ? 'Necesita: ' + j.needs.map((n) => '<code>' + JOBS.find((x) => x.k === n).t + '</code>').join(' y ') : 'Arranca primero, en cada push y pull request'}</p>
            <ol class="steps">${j.pasos.map((p) => '<li>' + p + '</li>').join('')}</ol>`;
        };
        [60, 700, 1300].forEach((t) => api.later(t, dibujar));
        window.addEventListener('resize', () => { if (root.isConnected) dibujar(); });
        const tour = recorrido(root, api, JOBS.length, mostrar, { inicio: 900, paso: 1700 });
        btns.forEach((b) => b.addEventListener('click', () => { tour.detener(); mostrar(JOBS.findIndex((j) => j.k === b.dataset.k)); }));
        mostrar(0);
      },
      notas: 'El pipeline sigue la sugerencia de la cátedra: etapas de menor a mayor costo. fast-checks agrupa las etapas 1 a 3 (sintaxis, estilo, complejidad, tipado, Bandit y Gitleaks): falla en segundos si algo está mal. Recién con eso en verde corren en paralelo las pruebas en Ubuntu y Windows y la auditoría de dependencias con la documentación. Las mediciones de memoria y benchmarks van al final porque son las más caras y las más sensibles al entorno. La etapa 7 publica: SARIF a GitHub Security, SonarQube y GitHub Pages.'
    },

    /* 04 ---------------------------------------------------------------- */
    {
      arte: 'rayosx', etiqueta: 'Rayos X', fase: 'P3.2', tema: 'Calidad estática y tipado',
      titulo: 'Rayos X: lo que se ve sin ejecutar el código',
      sub: 'Sintaxis, estilo, formato, complejidad y tipos se revisan en segundos, antes de correr una sola prueba',
      evidencia: 'pyproject.toml ([tool.ruff], [tool.complexipy], [tool.mypy]) · ejecución local sobre parcial-3',
      html: () => `
        <div class="grid-split xray-s">
          <div class="xray-grid rv" style="--i:0">
            ${[
              ['compileall', 'Sintaxis', '0 errores'],
              ['ruff check', 'Estilo y convenciones', 'All checks passed!'],
              ['ruff format', 'Formato PEP 8', '110 archivos ok'],
              ['complexipy', 'Complejidad ≤ 15', '0 funciones'],
              ['mypy src/', 'Tipos y contratos', '0 errores · 43 archivos'],
              ['Radon', 'Complejidad ciclomática', 'en docs/mediciones']
            ].map((c, i) => `<div class="xg" style="--i:${i}"><span class="xg-t">${c[0]}</span><b>${c[2]}</b><span>${c[1]}</span></div>`).join('')}
          </div>
          <div class="panel rv" style="--i:1">
            <h3>Qué cambió con mypy (P3.2)</h3>
            <pre class="code">${C_DIFF}</pre>
            <pre class="code tiny">${C_MYPY}</pre>
            <p class="honest-line"><b>Dicho con precisión:</b> exige firmas tipadas (<code>disallow_untyped_defs</code>) y revisa el cuerpo de todas las funciones, pero no es <code>strict = true</code> y la interfaz Flet (<code>src.ui.*</code>) queda excluida.</p>
          </div>
        </div>`,
      init() {},
      notas: 'Etapa 3, la más barata. compileall, ruff, el formato y complexipy ya venían del Parcial 2; lo nuevo es mypy. En P3.2 se tiparon las firmas que faltaban, por ejemplo __iter__ de los catálogos, y mypy pasa sin errores en 43 archivos. Ser precisos si preguntan: no es el modo strict completo y la interfaz Flet está excluida, porque Flet no trae tipos completos.'
    },

    /* 05 ---------------------------------------------------------------- */
    {
      arte: 'perro', etiqueta: 'Perro detector', fase: 'P3.1', tema: 'Seguridad',
      titulo: 'Seguridad: código, secretos y proveedores',
      sub: 'Tres análisis complementarios: Bandit mira nuestro código, Gitleaks busca credenciales y pip-audit revisa a los proveedores',
      evidencia: 'pyproject.toml [tool.bandit] · .gitleaks.toml · .github/dependabot.yml · docs/seguridad-politica.md',
      html: () => `
        <div class="grid-3 sec3">
          <div class="panel sec rv" style="--i:0">
            <span class="sec-k">SAST · código propio</span>
            <h4>Bandit</h4>
            <p class="sec-big">0 hallazgos</p>
            <p class="small-p">6.485 líneas de <code>src/</code> analizadas. 2 excepciones marcadas con <code>nosec B311</code>: <code>random.Random(seed)</code> para datasets sintéticos, no para criptografía.</p>
            <p class="sec-rep">Reporte: SARIF → GitHub Security + consola</p>
          </div>
          <div class="panel sec rv" style="--i:1">
            <span class="sec-k">Secretos · historial y árbol</span>
            <h4>Gitleaks</h4>
            <p class="sec-big">Antes del merge</p>
            <p class="small-p">Corre en <code>fast-checks</code> con <code>.gitleaks.toml</code>: el allowlist cubre fixtures de tests, datasets sintéticos y mediciones; los tokens de prueba siguen patrones explícitos (<code>dummy_api_key_…</code>).</p>
            <p class="sec-rep">Reporte: consola de la acción</p>
          </div>
          <div class="panel sec rv" style="--i:2">
            <span class="sec-k">SCA · dependencias</span>
            <h4>pip-audit + Dependabot</h4>
            <p class="sec-big">0 vulnerabilidades</p>
            <p class="small-p">pip-audit contrasta los requirements con PyPI / OSV. Dependabot revisa <code>pip</code> y <code>github-actions</code> cada semana: el 28/10 ya abrió 5 PRs de actualización.</p>
            <p class="sec-rep">Reporte: JSON como artefacto + consola</p>
          </div>
        </div>
        <div class="sniff rv" style="--i:3" aria-hidden="true">
          <span class="sniff-dog">${''}</span>
          <span class="sniff-trail"></span>
        </div>`,
      init(root, api) {
        const dog = root.querySelector('.sniff-dog');
        dog.innerHTML = ARTE.perro;
        api.later(api.ms(300), () => root.querySelector('.sniff').classList.add('go'));
      },
      notas: 'Los tres requisitos de seguridad de la consigna: analizar el código, analizar las dependencias y detectar secretos. Bandit es SAST: lee el árbol sintáctico de nuestro código; hoy da 0 hallazgos y las dos excepciones están justificadas y registradas. Gitleaks busca credenciales. pip-audit compara las dependencias contra bases de vulnerabilidades conocidas y Dependabot propone las actualizaciones. Diferencia clave que suele preguntar la cátedra: Bandit mira nuestro código, pip-audit mira el código de terceros.'
    },

    /* 06 ---------------------------------------------------------------- */
    {
      arte: 'semaforo', etiqueta: 'Semáforo', fase: 'P3.1', tema: 'Política por severidad',
      titulo: 'Política por severidad: los canales de la aduana',
      sub: 'No toda alerta frena la caja. La política define qué bloquea, qué se revisa y qué solo se registra',
      evidencia: 'docs/seguridad-politica.md §3 y §5',
      html: () => `
        <div class="grid-split pol">
          <div class="canales rv" style="--i:0">
            <div class="light-col" aria-hidden="true"><i class="l r"></i><i class="l a"></i><i class="l v"></i></div>
            <div class="canal-list">
              ${[
                ['rojo', 'Crítica', 'CVSS 9,0 – 10', 'Bloqueo inmediato: el build falla', 'Hotfix inmediato', 'Ejecución remota, credenciales activas expuestas'],
                ['rojo', 'Alta', 'CVSS 7,0 – 8,9', 'Bloqueo inmediato: el build falla', 'Máximo 48 h', 'Vulnerabilidad explotable en una dependencia activa'],
                ['naranja', 'Media', 'CVSS 4,0 – 6,9', 'Advertencia con revisión documentada', 'Dentro de la entrega', 'Configuración subóptima, dependencia solo de desarrollo'],
                ['verde', 'Baja / Info', 'CVSS 0,1 – 3,9', 'Se registra y pasa', 'Mantenimiento', 'random no criptográfico, buenas prácticas']
              ].map((c, i) => `<button type="button" class="canal ${c[0]}" data-i="${i}"><b>${c[1]}</b><span>${c[3]}</span><small>${c[2]} · ${c[4]}</small><em>${c[5]}</em></button>`).join('')}
            </div>
          </div>
          <div class="panel rv" style="--i:1">
            <h3>Registro de falsos positivos</h3>
            <table class="mini-tbl">
              <tr><td>Bandit B311</td><td><code>generador_archivos.py:45</code> · <code>random.Random(seed)</code>: datasets sintéticos con semilla fija</td></tr>
              <tr><td>Bandit B311</td><td><code>generador_archivos.py:69</code> · misma justificación para pedidos sintéticos</td></tr>
              <tr><td>Gitleaks</td><td><code>tests/observabilidad/test_apm.py</code>: tokens de prueba del cliente APM</td></tr>
            </table>
            <p class="small-p"><b>Regla:</b> nunca se desactiva una regla de forma global; la excepción va en la línea (<code># nosec: B311</code>) o en el allowlist, y siempre se registra con su justificación.</p>
            <p class="honest-line"><b>Pendiente de alinear:</b> en el CI, Bandit corre con <code>-ll</code> y rechaza desde severidad Media, y pip-audit rechaza cualquier vulnerabilidad conocida. Hoy el pipeline es más estricto que la política.</p>
          </div>
        </div>`,
      init(root) {
        const cs = root.querySelectorAll('.canal');
        const lights = root.querySelectorAll('.light-col .l');
        const sel = (i) => {
          cs.forEach((c, j) => c.classList.toggle('active', i === j));
          const color = cs[i].classList.contains('rojo') ? 0 : cs[i].classList.contains('naranja') ? 1 : 2;
          lights.forEach((l, j) => l.classList.toggle('on', j === color));
        };
        cs.forEach((c, i) => c.addEventListener('click', () => sel(i)));
        sel(3);
      },
      notas: 'La consigna no exige que toda alerta rechace, sino una política explícita y verificable. La nuestra usa CVSS: crítica y alta bloquean el build, media es advertencia con revisión documentada y baja se registra. Mostrar el registro de falsos positivos: dos usos de random con semilla para datos sintéticos y tokens de prueba. Autocrítica honesta: hoy el pipeline es más estricto que la política (Bandit corta desde media y pip-audit corta ante cualquier vulnerabilidad); falta alinear la configuración con el documento.'
    },

    /* 07 ---------------------------------------------------------------- */
    {
      arte: 'muestras', etiqueta: 'Muestras', fase: 'P3.3', tema: 'Pruebas y cobertura',
      titulo: 'Inspección de muestras: pruebas y cobertura',
      sub: 'La misma suite corre en Ubuntu y en Windows; si una prueba falla o la cobertura baja de 85 %, la caja no pasa',
      evidencia: 'tests/ · ejecución local sobre parcial-3 (Linux, Python 3.13) · verify.yml job test-suite',
      html: () => `
        <div class="grid-split tests3">
          <div class="cov-wrap rv" style="--i:0">
            <div class="ring" id="ring"><svg viewBox="0 0 120 120"><circle class="ring-bg" cx="60" cy="60" r="50"/><circle class="ring-thr" cx="60" cy="60" r="50"/><circle class="ring-fg" id="ring-fg" cx="60" cy="60" r="50"/></svg>
              <div class="ring-c"><b id="ring-n">0 %</b><span>cobertura de src/</span></div></div>
            <p class="small-p ring-note">Umbral del CI: <b>85 %</b> (marca naranja). 2.532 sentencias, 263 sin cubrir.</p>
          </div>
          <div class="panel rv" style="--i:1">
            <div class="kpi-row three">
              <div class="kpi"><span class="k-lbl">Pruebas</span><span class="k-big" id="t-n">0</span><span class="k-mid">198 passed · 0 failed</span></div>
              <div class="kpi"><span class="k-lbl">Plataformas</span><span class="k-big">2</span><span class="k-mid">Ubuntu y Windows</span></div>
              <div class="kpi"><span class="k-lbl">Reporte</span><span class="k-big small-big">JUnit</span><span class="k-mid">XML por sistema</span></div>
            </div>
            <h3 class="mt">Lo que se sumó en el Parcial 3</h3>
            <ul class="ticks small">
              <li><b>4 pruebas de presupuesto de memoria</b> con <code>tracemalloc</code>: streaming, catálogo hash, caché LRU y picking</li>
              <li><b>1 aserción de rendimiento</b>: el catálogo hash tiene que ser al menos 3× más rápido que la lista</li>
              <li>Reporte JUnit XML y <code>coverage.xml</code> como artefactos de cada corrida</li>
            </ul>
            <p class="foot-note">De 84 pruebas (P1) a 193 (P2) y 198 (P3).</p>
          </div>
        </div>`,
      init(root, api) {
        const fg = root.querySelector('#ring-fg');
        const n = root.querySelector('#ring-n');
        api.later(api.ms(300), () => { fg.style.strokeDashoffset = String(314.16 * (1 - 0.9)); });
        api.countUp(n, 90, ' %');
        api.countUp(root.querySelector('#t-n'), 198, '');
      },
      notas: 'Etapa 4. La suite tiene 198 pruebas y corre en Ubuntu y Windows; cobertura 90 % con umbral de rechazo 85 %. En el Parcial 3 se sumaron cinco pruebas que no miran correctitud sino eficiencia: cuatro presupuestos de memoria y una aserción de que el hash sigue siendo al menos 3 veces más rápido que la lista. Las cifras las verificamos corriendo la suite sobre el tag parcial-3.'
    },

    /* 08 ---------------------------------------------------------------- */
    {
      arte: 'balanza', etiqueta: 'Balanza', fase: 'P3.3', tema: 'Rendimiento y memoria',
      titulo: 'Balanza y cronómetro: memoria y tiempo con tolerancia',
      sub: 'A diferencia de las pruebas funcionales, estas mediciones varían según la máquina: se controlan con límites holgados y repetición',
      evidencia: 'tests/integracion/test_presupuesto_memoria.py · tests/integracion/test_benchmarks.py · medición local Linux, Python 3.13',
      html: () => `
        <div class="grid-split perf3">
          <div class="panel rv" style="--i:0">
            <h3>Presupuestos de memoria (pico medido vs. límite)</h3>
            ${[
              ['Streaming JSONL (1.000 + 2.000)', 1.03, 10],
              ['Catálogo hash (1.000 productos)', 0.59, 3],
              ['Caché LRU tras 2.000 consultas', 0.02, 2],
              ['Picking consolidado', 0.09, 5]
            ].map((m, i) => `
              <div class="budget" style="--i:${i}">
                <span>${m[0]}</span>
                <div class="b-bar"><i style="--w:${(m[1] / m[2]) * 100}%"></i><em>límite ${String(m[2]).replace('.', ',')} MB</em></div>
                <b>${String(m[1]).replace('.', ',')} MB</b>
              </div>`).join('')}
            <p class="foot-note">Los límites dejan margen para runners distintos; un cambio que cargue el archivo entero en memoria los rompe.</p>
          </div>
          <div class="panel rv" style="--i:1">
            <h3>Microbenchmarks (mediana)</h3>
            <table class="mini-tbl bench">
              ${[
                ['Búsqueda hash por id', '71 ns'],
                ['Búsqueda lineal por id', '1.214 ns'],
                ['Top-N con heap', '12,0 µs'],
                ['Combinaciones con DP', '24,2 µs'],
                ['Batch picking', '29,7 µs'],
                ['Procesamiento de pedidos', '35,8 µs']
              ].map((b) => `<tr><td>${b[0]}</td><td class="mono">${b[1]}</td></tr>`).join('')}
            </table>
            <div class="speed-guard"><b>≥ 3×</b><span>aserción en la suite: si el hash deja de ganarle a la lista por 3 veces, la prueba falla. Hoy: <b>17×</b>.</span></div>
            <p class="honest-line"><b>Pendiente:</b> el JSON de pytest-benchmark queda como artefacto, pero todavía no se compara automáticamente contra una línea base.</p>
          </div>
        </div>`,
      init() {},
      notas: 'Etapa 6, la más cara y la más ruidosa. La consigna pide distinguir: las pruebas funcionales son deterministas, pero tiempo y memoria varían según el runner, entonces se usan límites con margen. Los cuatro presupuestos de memoria muestran el pico medido contra el límite. En tiempos, la protección actual es la aserción de speedup: si alguien vuelve a una búsqueda lineal, falla. Ser honestos: la comparación automática contra una línea base de pytest-benchmark está pendiente.'
    },

    /* 09 ---------------------------------------------------------------- */
    {
      arte: 'manifiesto', etiqueta: 'Manifiesto', fase: 'P3.5', tema: 'Documentación externa',
      titulo: 'Manifiesto de carga: la documentación externa en 9 secciones',
      sub: 'Sphinx + Furo publicado en GitHub Pages. Se compila en cada push con -W y se validan los enlaces',
      evidencia: 'docs/sphinx/index.rst · docs/sphinx/secciones/ · verify.yml (deps-and-docs, deploy-docs)',
      html: () => `
        <div class="grid-split docs3">
          <div class="panel rv" style="--i:0">
            <h3>Las 9 secciones de la consigna <span class="hint-inline">clic para ver el contenido</span></h3>
            <div class="sec-list">
              ${SECCIONES.map((s, i) => `<button type="button" class="sec-tab" data-i="${i}" style="--i:${i}"><span>${i + 1}</span>${s[0]}</button>`).join('')}
            </div>
            <div class="sec-detail" id="sec-detail"></div>
          </div>
          <div class="panel rv" style="--i:1">
            <div class="kpi-row">
              <div class="kpi"><span class="k-big">9</span><span class="k-lbl">secciones</span></div>
              <div class="kpi"><span class="k-big">0</span><span class="k-lbl">advertencias -W</span></div>
              <div class="kpi"><span class="k-big">37</span><span class="k-lbl">páginas HTML</span></div>
              <div class="kpi"><span class="k-big">13</span><span class="k-lbl">controles en local</span></div>
            </div>
            <ul class="ticks small mt">
              <li><b>Lugar compartido y con control de acceso:</b> el repositorio de GitHub; se publica sola en GitHub Pages</li>
              <li><b>Siempre actualizada:</b> la API sale de los docstrings (autodoc) y las guías se incluyen con MyST sin copiarse</li>
              <li><b>Requisito adicional:</b> la sección 9 explica cómo correr en local los mismos controles del CI</li>
              <li><b>Enlaces:</b> <code>sphinx-build -b linkcheck</code> en la etapa 5</li>
            </ul>
          </div>
        </div>`,
      init(root) {
        const tabs = root.querySelectorAll('.sec-tab');
        const det = root.querySelector('#sec-detail');
        const sel = (i) => {
          tabs.forEach((t, j) => t.classList.toggle('active', i === j));
          det.innerHTML = '<b>' + (i + 1) + '. ' + SECCIONES[i][0] + '</b><p>' + SECCIONES[i][1] + '</p>';
        };
        tabs.forEach((t, i) => t.addEventListener('click', () => sel(i)));
        sel(8);
      },
      notas: 'La consigna pide una herramienta de documentación externa con 9 secciones mínimas. Usamos Sphinx con Furo, que ya teníamos del Parcial 2, reorganizado en esas 9 secciones y publicado en GitHub Pages. Está en un lugar compartido con control de acceso (el repositorio) y se mantiene actualizada porque el CI la compila en cada push con -W. El requisito adicional, correr en local los mismos controles, está en la sección 9 y es la lámina siguiente.'
    },

    /* 10 ---------------------------------------------------------------- */
    {
      arte: 'terminal', etiqueta: 'Terminal', fase: 'P3.5', tema: 'Reproducción local',
      titulo: 'Los mismos controles, en la máquina de cada integrante',
      sub: 'La sección 9 de la documentación lista 13 comandos equivalentes al CI. Las salidas son las que obtuvimos al correrlos',
      evidencia: 'docs/sphinx/secciones/09_mantenimiento.md · ejecución local sobre parcial-3',
      html: () => `
        <div class="term rv" style="--i:0">
          <div class="term-bar"><i></i><i></i><i></i><span>PEF-Optimizador-de-Inventario — reproducción local</span><button type="button" class="mini-btn" id="btn-run-local">▶ Ejecutar los 13 controles</button></div>
          <div class="term-body" id="term-body"><p class="t-dim"># Presioná «Ejecutar» para correr la suite local.</p></div>
        </div>`,
      init(root, api) {
        const bodyT = root.querySelector('#term-body');
        const btn = root.querySelector('#btn-run-local');
        let corriendo = false;
        btn.addEventListener('click', async () => {
          if (corriendo) return;
          corriendo = true;
          bodyT.innerHTML = '';
          for (let i = 0; i < TERMINAL.length; i++) {
            if (!root.isConnected) return;
            const [cmd, out] = TERMINAL[i];
            const p = document.createElement('p');
            p.className = 't-cmd';
            p.innerHTML = '<span class="t-n">' + String(i + 1).padStart(2, '0') + '</span><span class="t-p">$</span> <span class="t-type"></span>';
            bodyT.appendChild(p);
            const tt = p.querySelector('.t-type');
            const pasos = api.ms(1) ? Math.ceil(cmd.length / 4) : 1;
            for (let k = 1; k <= pasos; k++) {
              tt.textContent = cmd.slice(0, Math.ceil((cmd.length * k) / pasos));
              await new Promise((r) => setTimeout(r, api.ms(14)));
            }
            out.forEach((o) => {
              const q = document.createElement('p');
              q.className = 't-out' + (/passed|All checks|No issues|Success|No known|succeeded|already|No functions|90%/.test(o) ? ' ok' : '');
              q.textContent = o;
              bodyT.appendChild(q);
            });
            bodyT.scrollTop = bodyT.scrollHeight;
            await new Promise((r) => setTimeout(r, api.ms(260)));
          }
          const f = document.createElement('p');
          f.className = 't-out ok big';
          f.textContent = '✓ 13 / 13 controles en verde · listo para abrir el pull request';
          bodyT.appendChild(f);
          bodyT.scrollTop = bodyT.scrollHeight;
          corriendo = false;
        });
      },
      notas: 'Requisito adicional de la consigna: poder correr en local los mismos controles que corre el CI. Presionar «Ejecutar»: son los 13 comandos de la sección 9 con las salidas reales que obtuvimos al correrlos sobre el tag parcial-3. Gitleaks se corre en el CI con su acción oficial; en local se necesita el binario de gitleaks instalado.'
    },

    /* 11 ---------------------------------------------------------------- */
    {
      arte: 'contrabando', etiqueta: 'Contrabando', fase: 'P3.4', tema: '¿Qué pasa si un control falla?',
      titulo: 'Contrabando: ¿qué pasa si un control falla?',
      sub: 'Elegí qué esconder en la caja y mirá en qué puesto la frenan. Es la tabla 3.1 de la consigna, en vivo',
      evidencia: 'docs/Parcial-3.docx §3.1 · salidas ilustrativas con el formato real de cada herramienta',
      html: () => `
        <div class="grid-split contra">
          <div class="panel rv" style="--i:0">
            <h3>Esconder en la caja…</h3>
            <div class="contra-list">
              ${CONTRABANDO.map((c, i) => `<button type="button" class="contra-opt" data-i="${i}">${c.t}<small>${c.h}</small></button>`).join('')}
              <button type="button" class="contra-opt clean" data-i="-1">Nada: un cambio limpio<small>todos los controles</small></button>
            </div>
          </div>
          <div class="panel rv" style="--i:1">
            <div class="mini-line" id="mini-line">
              ${ETAPAS_CORTAS.map((e, i) => `<div class="ml-st" data-i="${i}"><span class="ml-dot">${i + 1}</span><span class="ml-n">${e}</span></div>`).join('')}
              <span class="ml-box" id="ml-box"></span>
            </div>
            <div class="verdict" id="verdict"><p class="t-dim">Elegí un contrabando para correr el pipeline.</p></div>
          </div>
        </div>`,
      init(root, api) {
        const sts = root.querySelectorAll('.ml-st');
        const box = root.querySelector('#ml-box');
        const ver = root.querySelector('#verdict');
        const line = root.querySelector('#mini-line');
        let token = 0;
        const posicion = (i) => {
          const z = api.zoom();
          const r0 = line.getBoundingClientRect();
          const r = sts[i].querySelector('.ml-dot').getBoundingClientRect();
          box.style.transform = 'translateX(' + ((r.left - r0.left + r.width / 2) / z - 13) + 'px)';
        };
        const correr = async (idx) => {
          const mio = ++token;
          const c = idx >= 0 ? CONTRABANDO[idx] : null;
          const tope = c ? c.e : 7;
          root.querySelectorAll('.contra-opt').forEach((b) => b.classList.toggle('active', Number(b.dataset.i) === idx));
          sts.forEach((s) => s.classList.remove('ok', 'bad', 'run'));
          box.className = 'ml-box';
          ver.innerHTML = '<p class="t-dim">Corriendo el pipeline…</p>';
          for (let i = 0; i < 7; i++) {
            if (mio !== token || !root.isConnected) return;
            posicion(i);
            sts[i].classList.add('run');
            await new Promise((r) => setTimeout(r, api.ms(520) || 30));
            if (mio !== token) return;
            sts[i].classList.remove('run');
            if (c && i === tope) {
              sts[i].classList.add('bad');
              box.classList.add('bad');
              ver.innerHTML = `<div class="v-head bad"><b>RECHAZADO</b> en la etapa ${i + 1} · ${ETAPAS_CORTAS[i]} · <code>${c.h}</code></div>
                <pre class="v-out">${esc(c.out)}</pre>
                <p class="small-p">La caja se desvía al canal rojo: el PR no se puede fusionar hasta corregirlo. Las etapas siguientes ni se ejecutan.</p>`;
              const r = sts[i].getBoundingClientRect();
              api.fx.puff(r.left + r.width / 2, r.top + 10, 16, 'ink');
              return;
            }
            sts[i].classList.add('ok');
          }
          box.classList.add('ok');
          ver.innerHTML = '<div class="v-head ok"><b>LIBERADO</b> · canal verde · los 7 puestos en verde</div><p class="small-p">El cambio se puede fusionar a <code>main</code>.</p>';
        };
        root.querySelectorAll('.contra-opt').forEach((b) => b.addEventListener('click', () => correr(Number(b.dataset.i))));
        [80, 900].forEach((t) => api.later(t, () => { if (!line.querySelector('.ml-st.ok, .ml-st.bad, .ml-st.run')) posicion(0); }));
      },
      notas: 'La consigna, en la sección 3.1, pregunta qué debe ocurrir si un control falla. Lo mostramos en vivo: elegir un contrabando y ver en qué puesto frenan la caja y con qué mensaje. Un token lo frena Gitleaks en la etapa 3; un test roto o volver a la búsqueda lineal lo frena pytest en la etapa 4; una dependencia vulnerable, pip-audit en la 5; cargar el archivo entero en memoria, el presupuesto de tracemalloc en la 6. Los mensajes son ilustrativos pero tienen el formato real de cada herramienta. Punto importante: al fallar una etapa, las más caras ni se ejecutan.'
    },

    /* 12 ---------------------------------------------------------------- */
    {
      arte: 'liberado', etiqueta: 'Sello', fase: 'P3.6', tema: 'Conclusiones',
      titulo: 'Conclusiones y autocrítica',
      sub: 'Qué ganamos con la aduana automática y qué todavía no hace lo que dice el plan',
      evidencia: 'docs/planificacion-parcial-3.md · .github/workflows/verify.yml · docs/seguridad-politica.md',
      html: () => `
        <div class="grid-3 concl">
          <div class="panel tint-green rv" style="--i:0">
            <h3>Lo que ganamos</h3>
            <ul class="ticks small">
              <li><b>Nada entra sin pasar la cinta:</b> 15 controles con criterio de rechazo explícito</li>
              <li><b>Falla rápido y barato:</b> lo estático corta en segundos, antes de medir</li>
              <li><b>Seguridad en tres capas</b> con reportes SARIF y JSON, y una política escrita</li>
              <li><b>Documentación viva:</b> 9 secciones compiladas y publicadas en cada push</li>
            </ul>
          </div>
          <div class="panel tint-amber rv" style="--i:1">
            <h3>Lo que falta ajustar</h3>
            <ul class="ticks small warn">
              <li>Los benchmarks no se comparan todavía contra una línea base</li>
              <li>El CI es más estricto que la política: Bandit corta desde Media y pip-audit ante cualquier hallazgo</li>
              <li>pip-audit revisa los <code>requirements</code> con rangos, no las versiones de <code>uv.lock</code></li>
              <li>mypy excluye la interfaz y las acciones nuevas no están fijadas por SHA</li>
            </ul>
          </div>
          <div class="panel tint-blue rv" style="--i:2">
            <h3>Qué haríamos después</h3>
            <ul class="ticks small">
              <li><code>--benchmark-compare-fail</code> contra una línea base guardada en el repo</li>
              <li>Auditar la exportación de <code>uv.lock</code> y filtrar por severidad</li>
              <li>Gitleaks también en pre-commit y con reporte SARIF</li>
              <li>Fijar por SHA las acciones nuevas y aceptar los PRs de Dependabot</li>
            </ul>
          </div>
        </div>
        <div class="repack-cta rv" style="--i:3">
          <button type="button" class="btn btn-accent btn-big" id="btn-despachar">🚚 Despachar la caja a main <kbd>P</kbd></button>
        </div>`,
      init(root, api) {
        root.querySelector('#btn-despachar').addEventListener('click', () => api.despachar());
      },
      notas: 'Cierre. Lo que ganamos: ningún cambio llega a main sin pasar 15 controles con criterio de rechazo, ordenados para fallar rápido; seguridad en tres capas con política escrita; y documentación que se compila y publica sola. Lo que falta, dicho por nosotros antes de que lo pregunten: comparar benchmarks contra una línea base, alinear la configuración de Bandit y pip-audit con la política, auditar uv.lock y fijar por SHA las acciones nuevas. Después: despachar la caja a main y que el tribunal la selle.'
    }
  ];

  const C_DIFF_SRC = [
    ['-', 'def __iter__(self):'],
    ['+', 'def __iter__(self) -> Iterator[Producto]:'],
    [' ', ''],
    ['-', 'def _armar_fragmentos(catalogo, pedidos, workers):'],
    ['+', 'def _armar_fragmentos(catalogo: Catalogo, pedidos: Sequence[Pedido],'],
    ['+', '                      workers: int) -> list[FragmentoCompacto]:']
  ];
  var C_DIFF = C_DIFF_SRC.map((l) => '<span class="ln ' + (l[0] === '+' ? 'new' : l[0] === '-' ? 'del' : '') + '">' + (l[0] === ' ' ? '  ' : l[0] + ' ') + esc(l[1]) + '</span>').join('');
  var C_MYPY = ['[tool.mypy]', 'python_version = "3.10"', 'disallow_untyped_defs = true', 'check_untyped_defs = true', 'warn_return_any = true', '', '[[tool.mypy.overrides]]  # flet, elasticapm, src.ui.*', 'ignore_errors = true'].map((l) => '<span class="ln' + (l.startsWith('ignore') ? ' mark' : '') + '">' + (esc(l) || ' ') + '</span>').join('');

  const NOTAS_RITUAL = {
    intro: 'Empezamos donde terminó el Parcial 2: la caja quedó re-despachada con la cinta verde del Quality Gate y el sello del tribunal. Ahora, para llegar a main, tiene que pasar la aduana de Integración Continua. Enter para presentarla.',
    aduana: 'Cada puesto es una etapa del pipeline. Enter avanza al puesto siguiente; A corre la cinta completa. El panel de la derecha muestra el control, el comando y el resultado real.',
    hub: 'Oficina de aduana: cada objeto es un tema del informe. → recorre en orden; un clic abre uno; Esc vuelve acá.',
    despacho: 'La caja sale por la puerta de main con el sello de libre circulación.',
    final: 'PUNTUAR: el tribunal elige la nota y sella la caja. La caja cruza el arco de salida y llega a su destino: main, el depósito de producción, con el tag parcial-3. El recorrido resume los tres parciales: empaque (P1), auditoría (P2) y aduana (P3). R vuelve a la oficina para preguntas.'
  };

  window.PEF3_CONTENIDO = { ARTE, LAMINAS, PUESTOS, SILUETAS, NOTAS_RITUAL, ETAPAS_CORTAS, CINTA_P2: 'QUALITY GATE: PASSED • 193 TESTS • 90% COBERTURA • 0 DUPLICADOS' };
})();
