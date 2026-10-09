/* ==========================================================================
   CONTENIDO DEL INFORME — SEGUNDO PARCIAL PEF (OPCIÓN 6)
   Ilustraciones de los objetos de la caja, cifras con su archivo de evidencia,
   láminas del informe y notas de orador.

   Regla: toda cifra de este archivo sale de un archivo del repositorio.
   La fuente de cada lámina se muestra en su pie ("Evidencia").
   ========================================================================== */
(function () {
  'use strict';

  const O = '#2B1E14'; // tinta de contorno

  /* ------------------------------------------------------------------------
     Utilidades
     ------------------------------------------------------------------------ */
  function esc(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  // Resaltado mínimo de Python. `marcas` = números de línea (1-based) a resaltar.
  const PY_KW = /\b(def|class|return|if|elif|else|for|in|not|is|None|True|False|with|import|from|as|yield|try|except|raise|and|or|lambda|while|pass)\b/;
  function py(src, marcas, clase) {
    const marcadas = new Set(marcas || []);
    const lineas = src.replace(/^\n/, '').replace(/\s+$/, '').split('\n');
    let enDoc = false;
    const salida = lineas.map((linea, i) => {
      let html = '';
      let resto = linea;
      if (enDoc) {
        const fin = resto.indexOf('"""');
        if (fin === -1) {
          html = '<span class="t-s">' + esc(resto) + '</span>';
          resto = '';
        } else {
          html = '<span class="t-s">' + esc(resto.slice(0, fin + 3)) + '</span>';
          resto = resto.slice(fin + 3);
          enDoc = false;
        }
      }
      const re = /(#.*$)|("""[^]*?(?:"""|$))|("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')|(@[\w.]+)|(\b\d+(?:\.\d+)?\b)|(\b[A-Za-z_]\w*\b)|(\s+|.)/g;
      let m;
      let previo = '';
      while ((m = re.exec(resto)) !== null) {
        const [tok, com, doc, str, deco, num, ident] = m;
        if (com) html += '<span class="t-c">' + esc(com) + '</span>';
        else if (doc) {
          html += '<span class="t-s">' + esc(doc) + '</span>';
          if (!(doc.length >= 6 && doc.endsWith('"""'))) enDoc = true;
        } else if (str) html += '<span class="t-s">' + esc(str) + '</span>';
        else if (deco) html += '<span class="t-d">' + esc(deco) + '</span>';
        else if (num) html += '<span class="t-n">' + esc(num) + '</span>';
        else if (ident) {
          if (PY_KW.test(ident) && ident.match(PY_KW)[0] === ident) html += '<span class="t-k">' + ident + '</span>';
          else if (previo === 'def' || previo === 'class') html += '<span class="t-f">' + ident + '</span>';
          else html += esc(ident);
          previo = ident;
          continue;
        } else html += esc(tok);
        if (!/^\s+$/.test(tok)) previo = '';
      }
      const cls = 'ln' + (marcadas.has(i + 1) ? ' ' + (clase || 'mark') : '');
      return '<span class="' + cls + '">' + (html || ' ') + '</span>';
    });
    return salida.join('');
  }

  // Recorrido automático que se detiene apenas el orador hace clic en un ítem
  function recorrido(root, api, total, mostrar, opciones) {
    const o = Object.assign({ inicio: 1200, paso: 1100, loop: false }, opciones || {});
    const btn = root.querySelector('[data-tour]');
    let activo = false;
    let token = 0;
    const pintarBtn = () => {
      if (!btn) return;
      btn.textContent = activo ? '❚❚ Pausar recorrido' : '▶ Recorrer solo';
      btn.classList.toggle('on', activo);
    };
    const correr = (desde, espera) => {
      const mio = ++token;
      activo = true;
      pintarBtn();
      let i = desde;
      const tick = () => {
        if (!root.isConnected || mio !== token) return;
        mostrar(i, true);
        i += 1;
        if (i < total) api.later(api.ms(o.paso) || o.paso, tick);
        else if (o.loop) { i = 0; api.later(api.ms(o.paso * 1.6) || o.paso, tick); }
        else { activo = false; pintarBtn(); }
      };
      api.later(api.ms(espera) || espera, tick);
    };
    const detener = () => { token++; activo = false; pintarBtn(); };
    if (btn) btn.addEventListener('click', () => { if (activo) detener(); else correr(0, 0); });
    correr(0, o.inicio);
    return { detener };
  }

  // Polígono festoneado (roseta)
  function roseta(cx, cy, rExt, rInt, puntas) {
    const pts = [];
    for (let i = 0; i < puntas * 2; i++) {
      const r = i % 2 === 0 ? rExt : rInt;
      const a = (Math.PI * i) / puntas - Math.PI / 2;
      pts.push((cx + r * Math.cos(a)).toFixed(1) + ',' + (cy + r * Math.sin(a)).toFixed(1));
    }
    return pts.join(' ');
  }

  /* ------------------------------------------------------------------------
     Ilustraciones de los objetos (viewBox 0 0 120 120)
     ------------------------------------------------------------------------ */
  const S = (body) => '<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' + body + '</svg>';
  const st = 'stroke="' + O + '" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round"';

  const ARTE = {
    remito: S(
      '<rect x="24" y="16" width="72" height="92" rx="7" fill="#A8713F" ' + st + '/>' +
      '<rect x="27" y="19" width="66" height="6" rx="3" fill="#C4935F"/>' +
      '<rect x="31" y="27" width="58" height="74" rx="2" fill="#FFFEFB" ' + st + '/>' +
      '<rect x="44" y="9" width="32" height="16" rx="5" fill="#94A3B8" ' + st + '/>' +
      '<circle cx="60" cy="14.5" r="2.6" fill="' + O + '"/>' +
      [40, 53, 66, 79].map((y) =>
        '<path d="M37 ' + y + 'l3 3 6-6" fill="none" stroke="#15803D" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"/>' +
        '<rect x="51" y="' + (y - 1.5) + '" width="31" height="3.4" rx="1.7" fill="#CBD5E1"/>'
      ).join('') +
      '<rect x="36" y="88" width="9" height="9" rx="1.5" fill="none" stroke="#94A3B8" stroke-width="2"/>' +
      '<rect x="51" y="91" width="22" height="3.4" rx="1.7" fill="#E2E8F0"/>' +
      '<g transform="rotate(-14 76 92)"><rect x="66" y="86" width="22" height="11" rx="2" fill="none" stroke="#BE123C" stroke-width="1.6"/><text x="77" y="94.5" text-anchor="middle" font-family="monospace" font-size="8" font-weight="700" fill="#BE123C">P2</text></g>'
    ),
    manual: S(
      '<path d="M30 26 L36 104 L28 106 L22 28 Z" fill="#1E293B" ' + st + '/>' +
      '<path d="M84 18 L92 21 L98 98 L91 96 Z" fill="#F1E9DA" ' + st + '/>' +
      '<path d="M88 30 L94 92 M85 26 L91 94" stroke="#D9CBB2" stroke-width="1"/>' +
      '<path d="M30 26 L84 18 L91 96 L36 104 Z" fill="#0F172A" ' + st + '/>' +
      '<path d="M40 40 L78 34" stroke="#D4A45A" stroke-width="3.2" stroke-linecap="round"/>' +
      '<path d="M41 48 L70 44" stroke="#D4A45A" stroke-width="2" stroke-linecap="round"/>' +
      '<path d="M43 82 L80 76" stroke="#334155" stroke-width="1.4"/>' +
      '<text x="58" y="70" text-anchor="middle" transform="rotate(-8 58 70)" font-family="Georgia, serif" font-size="13" font-style="italic" fill="#F59E0B">718x</text>' +
      '<g fill="#C9B79A" opacity="0.7"><circle cx="50" cy="30" r="1.4"/><circle cx="72" cy="58" r="1.1"/><circle cx="46" cy="92" r="1.6"/><circle cx="80" cy="88" r="1.2"/><circle cx="62" cy="40" r="0.9"/><ellipse cx="68" cy="94" rx="6" ry="2" opacity="0.5"/></g>'
    ),
    ruta: S(
      '<rect x="22" y="28" width="76" height="64" fill="#DBEAFE" ' + st + '/>' +
      '<path d="M22 44h76M22 60h76M22 76h76M41 28v64M60 28v64M79 28v64" stroke="#BFDBFE" stroke-width="1.2"/>' +
      '<rect x="13" y="23" width="13" height="74" rx="6.5" fill="#93C5FD" ' + st + '/>' +
      '<rect x="94" y="23" width="13" height="74" rx="6.5" fill="#93C5FD" ' + st + '/>' +
      '<path d="M32 82 C40 62 50 84 59 66 S76 48 88 38" fill="none" stroke="#1D4ED8" stroke-width="2.6" stroke-dasharray="4 4" stroke-linecap="round"/>' +
      '<circle cx="32" cy="82" r="5" fill="#C2410C" ' + st + '/>' +
      '<circle cx="59" cy="66" r="4" fill="#B45309" ' + st + '/>' +
      '<circle cx="88" cy="38" r="5" fill="#15803D" ' + st + '/>' +
      '<text x="30" y="72" font-family="monospace" font-size="8" font-weight="700" fill="#C2410C">F0</text>' +
      '<text x="76" y="54" font-family="monospace" font-size="8" font-weight="700" fill="#15803D">F9</text>'
    ),
    calidad: S(
      '<path d="M45 74 L34 108 L46 101 L53 111 L61 80 Z" fill="#166534" ' + st + '/>' +
      '<path d="M75 74 L86 108 L74 101 L67 111 L59 80 Z" fill="#15803D" ' + st + '/>' +
      '<polygon points="' + roseta(60, 52, 37, 31, 18) + '" fill="#86EFAC" ' + st + '/>' +
      '<circle cx="60" cy="52" r="25" fill="#15803D" ' + st + '/>' +
      '<circle cx="60" cy="52" r="20" fill="none" stroke="#BBF7D0" stroke-width="1.2" stroke-dasharray="2 3"/>' +
      '<path d="M48 52 l8 8 l15 -16" fill="none" stroke="#FFFFFF" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>'
    ),
    tests: S(
      '<rect x="47" y="11" width="26" height="9" rx="3" fill="#E2E8F0" ' + st + '/>' +
      '<path d="M53 20 V44 L31 88 A9 9 0 0 0 39 101 H81 A9 9 0 0 0 89 88 L67 44 V20 Z" fill="#F8FAFC" ' + st + '/>' +
      '<path d="M41 70 H79 L89 88 A9 9 0 0 1 81 101 H39 A9 9 0 0 1 31 88 Z" fill="#4ADE80" opacity="0.9"/>' +
      '<path d="M41 70 H79" stroke="#15803D" stroke-width="2"/>' +
      '<path d="M53 20 V44 L31 88 A9 9 0 0 0 39 101 H81 A9 9 0 0 0 89 88 L67 44 V20" fill="none" ' + st + '/>' +
      '<path d="M67 30h-6M67 38h-4M67 46h-6" stroke="#94A3B8" stroke-width="1.6"/>' +
      '<g fill="#FFFFFF" opacity="0.85"><circle cx="50" cy="86" r="3.2"/><circle cx="61" cy="79" r="2.2"/><circle cx="70" cy="90" r="4"/><circle cx="58" cy="60" r="1.8"/><circle cx="62" cy="52" r="1.3"/></g>' +
      '<path d="M44 56 L48 50" stroke="#FFFFFF" stroke-width="3" stroke-linecap="round" opacity="0.8"/>'
    ),
    tijera: S(
      '<g transform="rotate(-10 40 34)"><rect x="10" y="22" width="56" height="16" rx="2" fill="#FFFEFB" ' + st + '/><rect x="16" y="28" width="22" height="4" rx="2" fill="#F59E0B"/><rect x="41" y="28" width="18" height="4" rx="2" fill="#CBD5E1"/></g>' +
      '<g transform="rotate(-10 44 52)"><rect x="14" y="42" width="56" height="16" rx="2" fill="#FFFEFB" ' + st + '/><rect x="20" y="48" width="22" height="4" rx="2" fill="#F59E0B"/><rect x="45" y="48" width="18" height="4" rx="2" fill="#CBD5E1"/></g>' +
      '<path d="M57 71 L100 30 Q105 28 103 34 L63 77 Z" fill="#E2E8F0" ' + st + '/>' +
      '<path d="M60 66 L106 52 Q108 57 103 59 L65 75 Z" fill="#CBD5E1" ' + st + '/>' +
      '<path d="M49 79 L59 71 M67 88 L63 75" stroke="' + O + '" stroke-width="10" stroke-linecap="round"/>' +
      '<path d="M49 79 L59 71 M67 88 L63 75" stroke="#C2410C" stroke-width="6.5" stroke-linecap="round"/>' +
      '<circle cx="40" cy="87" r="12" fill="none" stroke="' + O + '" stroke-width="10"/>' +
      '<circle cx="40" cy="87" r="12" fill="none" stroke="#C2410C" stroke-width="6.5"/>' +
      '<circle cx="68" cy="99" r="12" fill="none" stroke="' + O + '" stroke-width="10"/>' +
      '<circle cx="68" cy="99" r="12" fill="none" stroke="#C2410C" stroke-width="6.5"/>' +
      '<circle cx="61" cy="72" r="3.6" fill="' + O + '"/>'
    ),
    lupa: S(
      '<rect x="12" y="34" width="84" height="14" rx="3" fill="#FFFEFB" ' + st + '/>' +
      '<rect x="13.5" y="35.5" width="7" height="11" fill="#15803D"/><rect x="20.5" y="35.5" width="48" height="11" fill="#1D4ED8"/><rect x="68.5" y="35.5" width="26" height="11" fill="#C2410C"/>' +
      '<rect x="12" y="58" width="84" height="14" rx="3" fill="#FFFEFB" ' + st + '/>' +
      '<rect x="13.5" y="59.5" width="17" height="11" fill="#15803D"/><rect x="30.5" y="59.5" width="47" height="11" fill="#1D4ED8"/><rect x="77.5" y="59.5" width="17" height="11" fill="#C2410C"/>' +
      '<path d="M78 74 L103 99" stroke="' + O + '" stroke-width="15" stroke-linecap="round"/>' +
      '<path d="M78 74 L103 99" stroke="#8D5F38" stroke-width="10" stroke-linecap="round"/>' +
      '<circle cx="60" cy="54" r="27" fill="rgba(255,255,255,0.32)" stroke="' + O + '" stroke-width="6"/>' +
      '<circle cx="60" cy="54" r="27" fill="none" stroke="#94A3B8" stroke-width="2.5"/>' +
      '<path d="M44 42 A20 20 0 0 1 58 34" fill="none" stroke="#FFFFFF" stroke-width="3" stroke-linecap="round"/>'
    ),
    rollo: S(
      '<path d="M30 36 H88 V100 L83 106 L78 100 L73 106 L68 100 L63 106 L58 100 L53 106 L48 100 L43 106 L38 100 L33 106 L30 102 Z" fill="#FFFEFB" ' + st + '/>' +
      [46, 56, 66, 76, 86].map((y, i) =>
        '<rect x="35" y="' + y + '" width="4" height="4" rx="1" fill="#7E22CE"/>' +
        '<rect x="42" y="' + y + '" width="' + [18, 14, 20, 12, 17][i] + '" height="4" rx="2" fill="#1D4ED8"/>' +
        '<rect x="' + (44 + [18, 14, 20, 12, 17][i]) + '" y="' + y + '" width="' + [16, 22, 12, 20, 14][i] + '" height="4" rx="2" fill="#15803D"/>'
      ).join('') +
      '<rect x="20" y="20" width="76" height="21" rx="10.5" fill="#E7DCC8" ' + st + '/>' +
      '<path d="M28 27 H84" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" opacity="0.7"/>' +
      '<ellipse cx="92" cy="30.5" rx="5.5" ry="10.5" fill="#CDBFA5" ' + st + '/>' +
      '<circle cx="92" cy="30.5" r="3" fill="#8D5F38"/>'
    ),
    monitor: S(
      '<rect x="14" y="24" width="92" height="72" rx="13" fill="#334155" ' + st + '/>' +
      '<rect x="22" y="32" width="76" height="42" rx="5" fill="#0B1220" stroke="' + O + '" stroke-width="1.6"/>' +
      '<path d="M22 46h76M22 60h76M41 32v42M60 32v42M79 32v42" stroke="#14532D" stroke-width="0.8"/>' +
      '<polyline points="24,57 40,57 45,44 51,69 56,50 60,59 64,57 97,57" fill="none" stroke="#4ADE80" stroke-width="2.8" stroke-linejoin="round" stroke-linecap="round"/>' +
      '<text x="27" y="41" font-family="monospace" font-size="7" font-weight="700" fill="#4ADE80">APM</text>' +
      '<circle cx="33" cy="85" r="4.2" fill="#C2410C" stroke="' + O + '" stroke-width="1.5"/>' +
      '<circle cx="47" cy="85" r="4.2" fill="#F59E0B" stroke="' + O + '" stroke-width="1.5"/>' +
      '<rect x="62" y="82" width="32" height="6" rx="3" fill="#64748B"/>' +
      '<rect x="40" y="96" width="40" height="8" rx="3" fill="#1E293B" ' + st + '/>'
    ),
    bloques: S(
      (function () {
        const col = ['#7E22CE', '#1D4ED8', '#B45309', '#15803D', '#C2410C', '#0F766E', '#BE123C', '#4D7C0F', '#475569'];
        const claro = ['#C4B5FD', '#93C5FD', '#FCD34D', '#86EFAC', '#FDBA74', '#5EEAD4', '#FDA4AF', '#BEF264', '#CBD5E1'];
        let s = '';
        for (let r = 0; r < 3; r++) {
          for (let c = 0; c < 3; c++) {
            const i = r * 3 + c;
            const x = 20 + c * 28;
            const y = 18 + r * 28;
            s += '<rect x="' + (x + 4) + '" y="' + (y + 5) + '" width="23" height="23" rx="4" fill="' + col[i] + '" ' + st + '/>';
            s += '<rect x="' + x + '" y="' + y + '" width="23" height="23" rx="4" fill="' + claro[i] + '" ' + st + '/>';
          }
        }
        s += '<circle cx="59.5" cy="57.5" r="4" fill="#C2410C"/>';
        return s;
      })()
    ),
    sphinx: S(
      '<path d="M14 95 C30 91 46 91 60 99 C74 91 90 91 106 95 V101 C90 97 74 97 60 105 C46 97 30 97 14 101 Z" fill="#1E3A8A" ' + st + '/>' +
      '<path d="M60 33 C46 25 30 25 16 29 V93 C30 89 46 89 60 97 Z" fill="#EFF6FF" ' + st + '/>' +
      '<path d="M60 33 C74 25 90 25 104 29 V93 C90 89 74 89 60 97 Z" fill="#FFFFFF" ' + st + '/>' +
      '<path d="M60 33 V97" stroke="' + O + '" stroke-width="2"/>' +
      '<text x="23" y="44" font-family="monospace" font-size="9" font-weight="700" fill="#1D4ED8">API</text>' +
      '<path d="M23 51h28M23 57h22M23 63h26M23 72h18M23 78h27" stroke="#93C5FD" stroke-width="2.4" stroke-linecap="round"/>' +
      '<rect x="67" y="38" width="30" height="16" rx="2" fill="#F1F5F9" stroke="#BFDBFE" stroke-width="1.2"/>' +
      '<path d="M70 43h14M70 48h20" stroke="#7E22CE" stroke-width="2" stroke-linecap="round"/>' +
      '<path d="M67 62h28M67 68h22M67 74h26M67 80h16" stroke="#CBD5E1" stroke-width="2.4" stroke-linecap="round"/>' +
      '<path d="M88 26 V48 L92 44 L96 48 V27" fill="#C2410C" ' + st + '/>'
    ),
    certificado: S(
      '<rect x="14" y="18" width="92" height="68" rx="3" fill="#FFFEFB" ' + st + '/>' +
      '<rect x="20" y="24" width="80" height="56" fill="none" stroke="#D4A45A" stroke-width="1.6"/>' +
      '<path d="M36 36h48" stroke="' + O + '" stroke-width="3.4" stroke-linecap="round"/>' +
      '<path d="M30 46h60M30 53h52M30 60h40" stroke="#CBD5E1" stroke-width="2.4" stroke-linecap="round"/>' +
      '<path d="M30 70h22" stroke="#15803D" stroke-width="2.4" stroke-linecap="round"/>' +
      '<path d="M78 84 L71 108 L79 103 L83 110 L87 88 Z" fill="#BE123C" ' + st + '/>' +
      '<path d="M90 84 L97 108 L89 103 L85 110 L81 88 Z" fill="#9F1239" ' + st + '/>' +
      '<polygon points="' + roseta(84, 78, 15, 12.5, 12) + '" fill="#F59E0B" ' + st + '/>' +
      '<circle cx="84" cy="78" r="8.5" fill="#FBBF24" stroke="#B45309" stroke-width="1.4"/>' +
      '<text x="84" y="81" text-anchor="middle" font-family="monospace" font-size="7.5" font-weight="700" fill="#7C2D12">P2</text>'
    ),
    sello: S(
      '<ellipse cx="60" cy="104" rx="32" ry="8" fill="none" stroke="#BE123C" stroke-width="2" opacity="0.55"/>' +
      '<rect x="31" y="78" width="58" height="9" rx="2" fill="#BE123C" ' + st + '/>' +
      '<rect x="27" y="60" width="66" height="19" rx="4" fill="#7C4A26" ' + st + '/>' +
      '<path d="M32 66h56" stroke="#9A6438" stroke-width="2"/>' +
      '<path d="M52 36 h16 l4 25 h-24 z" fill="#8D5F38" ' + st + '/>' +
      '<circle cx="60" cy="25" r="14" fill="#A8713F" ' + st + '/>' +
      '<path d="M52 20 A9 9 0 0 1 60 15" fill="none" stroke="#D6AE82" stroke-width="2.6" stroke-linecap="round"/>'
    )
  };

  // Herramientas que siguen al puntero
  const HERRAMIENTAS = {
    cepillo:
      '<svg viewBox="0 0 160 104" xmlns="http://www.w3.org/2000/svg">' +
      '<path d="M30 54 H130 L126 96 H34 Z" fill="#E9CF9C" stroke="' + O + '" stroke-width="3" stroke-linejoin="round"/>' +
      (function () {
        let s = '';
        for (let x = 36; x <= 124; x += 5) {
          const y2 = 92 + ((x * 7) % 5);
          s += '<path d="M' + x + ' 58 L' + (x + ((x % 3) - 1)) + ' ' + y2 + '" stroke="#C9A266" stroke-width="2" stroke-linecap="round"/>';
        }
        return s;
      })() +
      '<rect x="24" y="44" width="112" height="12" rx="4" fill="#6F4528" stroke="' + O + '" stroke-width="3"/>' +
      '<rect x="14" y="8" width="132" height="40" rx="17" fill="#A8713F" stroke="' + O + '" stroke-width="3"/>' +
      '<path d="M28 20 C60 14 96 26 132 18 M30 32 C70 26 100 38 128 30" fill="none" stroke="#8D5F38" stroke-width="2" stroke-linecap="round"/>' +
      '<circle cx="128" cy="27" r="5.5" fill="#2B1E14"/>' +
      '</svg>',
    cuter:
      '<svg viewBox="0 0 150 52" xmlns="http://www.w3.org/2000/svg">' +
      '<path d="M40 16 L4 38 L40 40 Z" fill="#E2E8F0" stroke="' + O + '" stroke-width="2.6" stroke-linejoin="round"/>' +
      '<path d="M30 22 L26 39 M20 28 L17 39" stroke="#94A3B8" stroke-width="1.6"/>' +
      '<path d="M38 10 H138 a9 9 0 0 1 9 9 V34 a9 9 0 0 1 -9 9 H38 Z" fill="#F59E0B" stroke="' + O + '" stroke-width="3" stroke-linejoin="round"/>' +
      '<rect x="62" y="5" width="22" height="10" rx="3" fill="#475569" stroke="' + O + '" stroke-width="2.4"/>' +
      '<path d="M98 18 v18 M106 18 v18 M114 18 v18 M122 18 v18 M130 18 v18" stroke="#B45309" stroke-width="2.4" stroke-linecap="round"/>' +
      '</svg>'
  };

  /* ------------------------------------------------------------------------
     Datos del Parcial 1 y del Parcial 2 (con evidencia)
     ------------------------------------------------------------------------ */
  const LB1 = 'docs/mediciones/linea_base_parcial1/';
  const LB2 = 'docs/mediciones/linea_base_parcial2/';

  const COMPARATIVA = [
    { m: 'Tests automatizados', a: 84, b: 193, fmt: (v) => String(v), mejor: 'mas', nota: '0 fallos en ambos' },
    { m: 'Cobertura de src/', a: 80, b: 90, fmt: (v) => v + ' %', mejor: 'mas', max: 100 },
    { m: 'Umbral de cobertura en CI', a: 75, b: 85, fmt: (v) => v + ' %', mejor: 'mas', max: 100 },
    { m: 'Ruff (config. del repo)', a: 19, b: 0, fmt: (v) => String(v), mejor: 'menos' },
    { m: 'Ruff PEP 8 + docstrings + CC', a: 517, b: 36, fmt: (v) => String(v), mejor: 'menos', nota: '36 = 13 D107 por estilo Google + reglas PL' },
    { m: 'Complejidad ciclomática promedio', a: 3.59, b: 2.94, fmt: (v) => String(v).replace('.', ','), mejor: 'menos', nota: 'radon, grado A en ambos' },
    { m: 'Funciones con CC grado C o peor', a: 15, b: 6, fmt: (v) => String(v), mejor: 'menos', nota: 'máximo actual: CC 12' },
    { m: 'Funciones con CC grado D o peor', a: 3, b: 0, fmt: (v) => String(v), mejor: 'menos', nota: 'eran CC 29, 30 y 29' },
    { m: 'Pares de código duplicado (pylint)', a: 8, b: 0, fmt: (v) => String(v), mejor: 'menos', nota: 'puntaje 10,00 / 10' },
    { m: 'Candidatos a código muerto (vulture)', a: 69, b: 56, fmt: (v) => String(v), mejor: 'menos', nota: 'los 56 restantes: callbacks de Flet' },
    { m: 'Páginas de documentación (Sphinx)', a: 0, b: 20, fmt: (v) => String(v), mejor: 'mas', nota: 'build con -W: 0 advertencias' }
  ];

  const FASES = [
    { f: 'F0', n: 'Plan', rama: 'p2/f0-plan', tema: 'Planificación',
      hizo: ['Plan del parcial por fases con criterio de cierre', 'Evaluación de las 5 propuestas de las automatizaciones Origin: se eligió la 1 (overhead de IPC)', 'Hallazgo del error de concurrencia con descuento de stock'],
      cierre: 'Plan acordado por el grupo' },
    { f: 'F1', n: 'Calidad', rama: 'p2/f1-calidad-sonarqube', tema: 'SonarQube, PEP 8 automático, CI',
      hizo: ['SonarQube Cloud con cobertura y reporte de ruff', 'ruff con reglas I, N, B, SIM, UP y pre-commit', 'Cobertura de procesos hijos y corrección del paso de cobertura del CI que nunca corría'],
      cierre: 'El PR muestra el análisis de Sonar' },
    { f: 'F2', n: 'Tests', rama: 'p2/f2-tests-red-seguridad', tema: 'Testing antes de refactorizar',
      hizo: ['conftest.py con fixtures compartidas', 'Hypothesis: baseline ≡ optimizado con datos aleatorios', 'Test del error de concurrencia con xfail(strict=True)'],
      cierre: 'Tests nuevos en verde, cobertura ≥ 80 %' },
    { f: 'F3', n: 'Redundancia', rama: 'p2/f3-eliminar-redundancia', tema: 'Eliminar código redundante',
      hizo: ['Núcleo único de evaluación de pedidos', 'Validador único, _crear_catalogo() y PantallaBase', 'Código muerto verificado contra los tests y Enums nuevos'],
      cierre: 'pylint sin duplicados en src/' },
    { f: 'F4', n: 'Scalene', rama: 'p2/f4-scalene-ipc', tema: 'Scalene y propuesta Origin 1',
      hizo: ['Perfil de Scalene antes y después', 'GestorPool, tuplas compactas y stock por initializer', 'Error de concurrencia corregido: se quitó el xfail'],
      cierre: 'Concurrente = secuencial en todos los casos' },
    { f: 'F5', n: 'Archivos', rama: 'p2/f5-archivos-grandes', tema: 'Batching, buffering y paralelismo',
      hizo: ['JSON Lines con lectura en streaming', 'Lotes en paralelo con stock por initializer', 'Exportación CSV con buffer y carga .jsonl en la UI'],
      cierre: 'Memoria constante y speedup > 1× en lotes' },
    { f: 'F6', n: 'APM', rama: 'p2/f6-elastic-apm', tema: 'Elastic APM',
      hizo: ['Transacciones con @medir en la fachada', 'Spans del pool y de los lotes, etiquetas para Kibana', 'Errores y logging ERROR enviados; demo_apm.py'],
      cierre: 'Traza y error provocado visibles en Kibana' },
    { f: 'F7', n: 'Refactor', rama: 'p2/f7-legibilidad-refactor', tema: 'Legibilidad, mantenibilidad, refactor',
      hizo: ['Docstrings, nombres completos y constantes con nombre', 'Complejidad cognitiva ≤ 15 y ciclomática ≤ 10 en src/', 'Protocol Catalogo, AplicacionInventario y CI endurecido'],
      cierre: 'ruff con E501, C90 y D activas: 0 hallazgos' },
    { f: 'F8', n: 'Sphinx', rama: 'p2/f8-sphinx', tema: 'Documentación con Sphinx',
      hizo: ['Sphinx + Furo + napoleon + MyST', 'Referencia de la API desde los docstrings', 'Build con -W y publicación en GitHub Pages'],
      cierre: '0 advertencias y sitio publicado' },
    { f: 'F9', n: 'Cierre', rama: 'p2/f9-cierre', tema: 'Testing final y remedición',
      hizo: ['Tests reorganizados en 11 subpaquetes por dominio', 'Umbral de CI 85 % y pytest-benchmark', 'Línea base del Parcial 2 con los mismos 9 comandos'],
      cierre: 'Tabla antes / después completa' }
  ];

  const ESTACIONES = [
    { k: 'pre', t: 'pre-commit', s: 'En la máquina de cada integrante',
      d: 'ruff check, ruff format y complexipy corren antes de cada commit, junto con chequeos de YAML, TOML, JSON y archivos grandes.', dato: 'Formateo masivo en un único commit registrado en .git-blame-ignore-revs' },
    { k: 'ruff', t: 'Análisis estático', s: 'ruff: PEP 8, imports, nombres, docstrings',
      d: 'Línea de 99 caracteres por acuerdo del grupo. En F7 se activaron E501, C90 y D, que antes rompían el CI.', dato: 'Configuración del repo: 19 → 0 hallazgos' },
    { k: 'cc', t: 'Complejidad cognitiva', s: 'complexipy ≤ 15 por función',
      d: 'El mismo umbral que la regla S3776 de SonarQube, pero corre aunque Sonar no corra.', dato: '14 funciones > 15 → 0 (la peor: main de la UI, 46)' },
    { k: 'pytest', t: 'Pruebas', s: 'pytest + cobertura, Windows y Ubuntu',
      d: '--cov-fail-under=85: un PR que baje la cobertura no entra.', dato: '193 tests · 90 % de cobertura' },
    { k: 'sonar', t: 'SonarQube Cloud', s: 'Quality Gate sobre código nuevo',
      d: 'Importa coverage.xml y el reporte de ruff. Las exclusiones están justificadas en sonar-project.properties (S2245 solo en generadores con semilla fija).', dato: 'Code smells críticos y mayores corregidos en F7' },
    { k: 'docs', t: 'Sphinx -W', s: 'Documentación → GitHub Pages',
      d: 'Las advertencias cortan el build. Si un docstring está mal formado, el PR no pasa.', dato: '0 advertencias · 20 páginas' }
  ];

  const PAQUETES = [
    { k: 'modelos', d: 'Dataclasses validadas', f: ['producto.py', 'pedido.py'], x: 'Producto, Pedido y LineaPedido validan sus datos al construirse.' },
    { k: 'inventario', d: 'Catálogos intercambiables', f: ['catalogo_lineal.py', 'catalogo_hash.py', 'protocolo.py'], x: 'CatalogoLineal (baseline) y CatalogoHash (optimizado) cumplen el Protocol Catalogo.' },
    { k: 'pedidos', d: 'Evaluación y procesamiento', f: ['evaluador.py', 'procesador_secuencial.py', 'procesador_concurrente.py', 'gestor_pool.py', 'agrupador.py', 'combinaciones.py'], x: 'Un único núcleo de evaluación compartido por el secuencial y el pool.' },
    { k: 'ranking', d: 'Top-N con heap', f: ['top_productos.py'], x: 'heapq.nlargest con memoria acotada a k.' },
    { k: 'motor', d: 'Fachada MotorInventario', f: ['motor_inventario.py'], x: 'Orquesta los subsistemas, cambia de estrategia (Enum EstrategiaMotor) e instrumenta con @medir.', centro: true },
    { k: 'cache', d: 'Caché LRU reactiva', f: ['cache_consultas.py'], x: '128 entradas e invalidación ante cambios de stock o pedidos nuevos.' },
    { k: 'datos', d: 'Carga, validación y streaming', f: ['cargador.py', 'validador.py', 'streaming.py', 'procesador_lotes_paralelo.py', 'generador_archivos.py'], x: 'JSON y JSON Lines, validador único y lotes en paralelo.' },
    { k: 'observabilidad', d: 'Elastic APM', f: ['apm.py'], x: 'Transacciones, spans, etiquetas y errores; sin servidor no hace nada.' },
    { k: 'ui', d: 'Aplicación Flet', f: ['app.py', 'tema.py', 'pantallas/ (8)', 'componentes/'], x: 'AplicacionInventario declara las pantallas en SECCIONES; todas heredan de PantallaBase.' }
  ];

  /* ------------------------------------------------------------------------
     Bloques de código mostrados en las láminas (reales del repo)
     ------------------------------------------------------------------------ */
  const COD_SEC_P1 = `
for linea in pedido.lineas:
    producto = catalogo.buscar_por_id(linea.id_producto)
    stock_disp = producto.stock if producto is not None else 0
    if stock_disp >= linea.cantidad:
        asignada = linea.cantidad
        faltante = 0
        lineas_satisfechas_count += 1
    elif stock_disp > 0:
        asignada = stock_disp
        faltante = linea.cantidad - stock_disp
    else:
        asignada = 0
        faltante = linea.cantidad`;

  const COD_CONC_P1 = `
for linea in pedido.lineas:
    stock_disp = mapa_stock.get(linea.id_producto, 0)

    if stock_disp >= linea.cantidad:
        asignada = linea.cantidad
        faltante = 0
        lineas_satisfechas_count += 1
    elif stock_disp > 0:
        asignada = stock_disp
        faltante = linea.cantidad - stock_disp
    else:
        asignada = 0
        faltante = linea.cantidad`;

  const COD_EVAL_P2 = `
def evaluar_lineas(lineas, stock_de):
    """Única implementación de la regla."""
    for id_producto, solicitada in lineas:
        disponible = stock_de(id_producto)
        if disponible >= solicitada:
            cubiertas.append(...)
        elif disponible > 0:
            faltantes.append(...)
        else:
            faltantes.append(...)

def debe_descontar(estado, politica): ...`;

  const COD_STREAM = `
with open(ruta, encoding="utf-8", buffering=tamano_buffer) as f:
    for num_linea, linea in enumerate(f, start=1):
        datos = json.loads(linea)
        yield Producto(**campos(datos))  # una línea en memoria`;

  const COD_MEDIR = `
def medir(nombre, tipo="operacion"):
    def decorador(funcion):
        @functools.wraps(funcion)
        def envoltura(*args, **kwargs):
            if _cliente is None:
                return funcion(*args, **kwargs)
            if _hay_transaccion_activa():
                with span(nombre, tipo):
                    return funcion(*args, **kwargs)
            with transaccion(nombre, tipo):
                return funcion(*args, **kwargs)
        return envoltura
    return decorador`;

  const COD_PROTOCOL = `
@runtime_checkable
class Catalogo(Protocol):
    """Operaciones que ofrece cualquier catálogo."""

    def buscar_por_id(self, id_producto: int) -> Producto | None: ...
    def buscar_por_nombre(self, texto: str) -> list[Producto]: ...
    def descontar_stock(self, id_producto: int, cantidad: int) -> bool: ...`;

  const COD_DOCSTRING = `
@medir("motor.procesar_pedidos")
def procesar_pedidos(self, pedidos=None, concurrente=False,
                     descontar_stock=False,
                     politica_descuento="solo_cubiertos"):
    """Procesa un lote de pedidos según la estrategia configurada.

    El procesamiento es secuencial salvo que se pida
    concurrente=True.

    Argumentos:
        pedidos: Pedidos a procesar.
        concurrente: Si es True, usa el ProcessPoolExecutor.
        descontar_stock: Si es True, descuenta lo asignado.
        politica_descuento: solo_cubiertos o todo_lo_posible.
    """`;

  /* ------------------------------------------------------------------------
     Láminas
     ------------------------------------------------------------------------ */
  const LAMINAS = [
    /* 01 ---------------------------------------------------------------- */
    {
      arte: 'remito', etiqueta: 'Remito', fase: 'F0', tema: 'Consigna',
      titulo: 'Remito de recepción: qué volvió en la caja',
      sub: 'El Parcial 2 no reemplaza al Parcial 1: lo recibe, lo limpia y lo vuelve a despachar auditado',
      evidencia: 'docs/Parcial-II.txt · docs/planificacion-parcial-2.md',
      html: () => `
        <div class="grid-split">
          <div class="panel rv" style="--i:0">
            <h3>Envío recibido</h3>
            <dl class="manifest">
              <div><dt>Origen</dt><dd>tag <code>parcial-1</code> · commit <code>e3230a1</code></dd></div>
              <div><dt>Contenido</dt><dd>Motor dual Baseline / Optimizado, interfaz Flet, 4 datasets, benchmarks y perfiles</dd></div>
              <div><dt>Consigna</dt><dd>«Sobre el primer parcial agregar…»</dd></div>
              <div><dt>Destino</dt><dd>rama <code>parcial-2</code> → <code>main</code> + tag <code>parcial-2</code></dd></div>
            </dl>
            <div class="route-strip" aria-hidden="true">
              <span class="rs-node kraft-node">P1</span>
              <span class="rs-line">${FASES.map((f) => '<i title="' + f.f + '"></i>').join('')}</span>
              <span class="rs-node green-node">P2</span>
            </div>
            <p class="callout">Regla de la auditoría: <b>nada del Parcial 1 se borra</b>. El baseline sigue siendo el experimento contra el que se mide todo.</p>
          </div>
          <div class="panel rv" style="--i:1">
            <h3>Temas de la consigna <span class="chip chip-green" id="remito-count">0 / 10</span></h3>
            <table class="check-tbl">
              <tbody>
                ${[
                  ['Eliminar código redundante', 'F3', 6],
                  ['Herramienta de optimización del lenguaje (Scalene)', 'F4', 7],
                  ['Herramienta general de rendimiento (Elastic APM)', 'F6', 9],
                  ['Lectura y escritura de archivos grandes', 'F5', 8],
                  ['Legibilidad y mantenibilidad (PEP 8, nombres, docstrings)', 'F1 · F7', 10],
                  ['Generador de documentación (Sphinx)', 'F8', 11],
                  ['Herramienta de análisis de calidad (SonarQube)', 'F1', 4],
                  ['Refactorización', 'F7', 10],
                  ['Testing', 'F2 · F9', 5],
                  ['Uso de algún framework (Flet · pytest · Sphinx)', 'F2 · F7 · F8', 10]
                ].map((r, i) => `
                  <tr data-goto="${r[2] - 1}" tabindex="0" style="--i:${i}">
                    <td class="ck"><span class="tick">✓</span></td>
                    <td>${r[0]}</td>
                    <td><span class="chip">${r[1]}</span></td>
                    <td class="go">ítem ${String(r[2]).padStart(2, '0')} →</td>
                  </tr>`).join('')}
              </tbody>
            </table>
          </div>
        </div>`,
      init(root, api) {
        const filas = root.querySelectorAll('tr[data-goto]');
        const contador = root.querySelector('#remito-count');
        filas.forEach((tr) => {
          const ir = () => api.goTo(Number(tr.dataset.goto));
          tr.addEventListener('click', ir);
          tr.addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.stopPropagation(); ir(); } });
        });
        let n = 0;
        filas.forEach((tr, i) => {
          api.later(api.ms(420 + i * 150), () => {
            tr.classList.add('checked');
            n += 1;
            contador.textContent = n + ' / 10';
          });
        });
      },
      notas: 'Abrimos el remito: la consigna del Parcial 2 dice «sobre el primer parcial agregar». Mostramos de dónde partimos (tag parcial-1, commit e3230a1) y que cada tema pedido tiene una fase y un ítem de este informe. Si el tribunal quiere ir directo a un tema, se hace clic en la fila. Remarcar la regla: no borramos el baseline, porque es el experimento contra el que medimos.'
    },

    /* 02 ---------------------------------------------------------------- */
    {
      arte: 'manual', etiqueta: 'Manual P1', fase: 'Línea base', tema: 'Diagnóstico',
      titulo: 'Diagnóstico de recepción: el polvo del viaje',
      sub: 'Lo que mostró la línea base del Parcial 1 al pasarle las mismas 9 herramientas que usamos al cierre',
      evidencia: LB1 + ' · docs/mediciones/tabla_comparativa.md',
      html: () => `
        <div class="grid-split diag">
          <div class="panel rv" style="--i:0">
            <h3>Lo que llegó funcionando</h3>
            <ul class="ticks">
              <li>Dualidad <b>Baseline vs. Optimizado</b> bajo la fachada <code>MotorInventario</code></li>
              <li><b>84 tests</b> en verde y CI en GitHub Actions</li>
              <li>En <code>grande.json</code>: búsqueda por nombre <b>1692×</b> y batch picking <b>7,8×</b> más rápidos</li>
              <li>Una lección pendiente: el pool de procesos perdía contra el secuencial</li>
            </ul>
            <p class="callout">El motor ya era rápido. La pregunta del Parcial 2 es otra: <b>¿se puede mantener, medir en producción y documentar?</b></p>
          </div>
          <div class="panel rv" style="--i:1">
            <h3>Deuda técnica acumulada <button type="button" class="mini-btn" id="btn-brush-all">Cepillar todo</button></h3>
            <div class="dust-grid">
              ${[
                ['19', 'hallazgos de ruff', '14 F541 · 4 F401 · 1 F841', 'F1 → 0'],
                ['517', 'observaciones PEP 8 y docstrings', '275 líneas largas · 106 sin docstring', 'F7 → 36'],
                ['8', 'pares de código duplicado', 'pylint, bloques ≥ 6 líneas', 'F3 → 0'],
                ['3', 'funciones de complejidad D', 'CC 29, 30 y 29', 'F7 → 0 (máx. CC 12)'],
                ['69', 'candidatos a código muerto', 'vulture ≥ 60 % de confianza', 'F3 → 56 (callbacks Flet)'],
                ['80 %', 'de cobertura', 'umbral del CI: 75 %', 'F9 → 90 % (umbral 85)'],
                ['0', 'páginas de documentación', 'solo Markdown suelto', 'F8 → 20 páginas Sphinx'],
                ['1', 'error de correctitud latente', 'concurrente + descontar stock', 'F2 lo reproduce · F4 lo corrige', true]
              ].map((c, i) => `
                <button type="button" class="dust-card${c[4] ? ' crit' : ''}" style="--i:${i}">
                  <span class="dc-num">${c[0]}</span>
                  <span class="dc-lbl">${c[1]}</span>
                  <span class="dc-det">${c[2]}</span>
                  <span class="dc-fix">${c[3]}</span>
                  <span class="dc-dust" aria-hidden="true"></span>
                </button>`).join('')}
            </div>
          </div>
        </div>`,
      init(root, api) {
        const cards = root.querySelectorAll('.dust-card');
        const limpiar = (c) => {
          if (c.classList.contains('clean')) return;
          c.classList.add('clean');
          const r = c.getBoundingClientRect();
          api.fx.puff(r.left + r.width / 2, r.top + r.height / 2, 18, 'light');
        };
        cards.forEach((c) => {
          c.addEventListener('click', () => limpiar(c));
          c.addEventListener('pointerenter', (e) => { if (e.buttons === 1) limpiar(c); });
        });
        root.querySelector('#btn-brush-all').addEventListener('click', () => {
          cards.forEach((c, i) => api.later(api.ms(i * 110), () => limpiar(c)));
        });
      },
      notas: 'El manual del Parcial 1 vino con polvo. Con las mismas 9 herramientas del cierre medimos la línea base: 19 hallazgos de ruff, 517 observaciones de PEP 8 y docstrings, 8 pares duplicados, 3 funciones de complejidad D, 69 candidatos a código muerto, 80 % de cobertura, nada de documentación generada y un error de correctitud que nadie había visto. Hacer clic en cada tarjeta para «cepillarla»: debajo aparece en qué fase se resolvió. El motor era rápido; el Parcial 2 trata de que sea mantenible, observable y documentado.'
    },

    /* 03 ---------------------------------------------------------------- */
    {
      arte: 'ruta', etiqueta: 'Hoja de ruta', fase: 'F0 → F9', tema: 'Método',
      titulo: 'Método: una fase, una rama, un PR',
      sub: 'Diez fases encadenadas: los tests llegan antes que el refactor y cada PR tiene que pasar CI, cobertura y Quality Gate',
      evidencia: 'docs/planificacion-parcial-2.md · historial de git (59 commits sobre parcial-1)',
      html: () => `
        <div class="tour-bar rv" style="--i:0"><span>Clic en una fase para fijarla</span><button type="button" class="mini-btn" data-tour>▶ Recorrer solo</button></div>
        <div class="timeline rv" style="--i:0">
          <div class="tl-track"><div class="tl-fill" id="tl-fill"></div></div>
          ${FASES.map((f, i) => `
            <button type="button" class="tl-node" data-i="${i}" style="--i:${i}">
              <span class="tl-dot">${f.f}</span>
              <span class="tl-name">${f.n}</span>
            </button>`).join('')}
        </div>
        <div class="grid-split method">
          <div class="panel phase-card rv" style="--i:1" id="phase-card"></div>
          <div class="rules rv" style="--i:2">
            <div class="rule"><b>Una rama por fase</b><span><code>p2/fN-nombre</code>, creada desde <code>parcial-2</code> actualizada</span></div>
            <div class="rule"><b>PR contra <code>parcial-2</code></b><span>Desde F6, PRs apilados: F6 → parcial-2, F7 → F6, F8 → F7…</span></div>
            <div class="rule"><b>Cada PR entra en verde</b><span>CI, cobertura que no baja y Quality Gate de SonarQube; trae sus propios tests</span></div>
            <div class="rule"><b>Formateo una sola vez</b><span><code>ruff format</code> en F1, en un commit aislado y registrado en <code>.git-blame-ignore-revs</code></span></div>
          </div>
        </div>`,
      init(root, api) {
        const card = root.querySelector('#phase-card');
        const nodos = root.querySelectorAll('.tl-node');
        const fill = root.querySelector('#tl-fill');
        const mostrar = (i) => {
          const f = FASES[i];
          nodos.forEach((n, j) => { n.classList.toggle('active', j === i); n.classList.toggle('done', j <= i); });
          fill.style.width = (i / (FASES.length - 1)) * 100 + '%';
          card.innerHTML = `
            <div class="pc-head"><span class="pc-f">${f.f}</span><div><strong>${f.tema}</strong><code>${f.rama}</code></div></div>
            <ul class="ticks small">${f.hizo.map((h) => '<li>' + h + '</li>').join('')}</ul>
            <p class="pc-close"><span>Criterio de cierre</span>${f.cierre}</p>`;
          card.classList.remove('flash'); void card.offsetWidth; card.classList.add('flash');
        };
        mostrar(0);
        const tour = recorrido(root, api, FASES.length, mostrar, { inicio: 1400, paso: 1300 });
        nodos.forEach((n) => n.addEventListener('click', () => { tour.detener(); mostrar(Number(n.dataset.i)); }));
      },
      notas: 'Cómo trabajamos: una rama por fase, PR contra parcial-2 y, desde F6, PRs apilados. El orden importa: F1 pone las herramientas de calidad, F2 arma la red de tests y recién ahí F3 y F7 tocan la estructura. La línea de tiempo se recorre sola una vez; un clic en una fase detiene el recorrido y la deja fija. «Recorrer solo» lo vuelve a iniciar.'
    },

    /* 04 ---------------------------------------------------------------- */
    {
      arte: 'calidad', etiqueta: 'Control de calidad', fase: 'F1 · F7', tema: 'Herramientas de calidad',
      titulo: 'Calidad continua: la misma línea de control en cada push',
      sub: 'SonarQube Cloud, ruff y complexipy deciden si un cambio entra; no depende de que alguien se acuerde de revisarlo',
      evidencia: '.github/workflows/verify.yml · sonar-project.properties · .pre-commit-config.yaml',
      html: () => `
        <div class="tour-bar rv" style="--i:0"><span>Clic en una estación para fijarla</span><button type="button" class="mini-btn" data-tour>▶ Recorrer solo</button></div>
        <div class="pipeline rv" style="--i:0">
          <div class="belt" aria-hidden="true"><span class="belt-box" id="belt-box"></span></div>
          ${ESTACIONES.map((e, i) => `
            <button type="button" class="station" data-i="${i}" style="--i:${i}">
              <span class="st-n">${i + 1}</span>
              <strong>${e.t}</strong>
              <span>${e.s}</span>
              <span class="st-led" aria-hidden="true"></span>
            </button>`).join('')}
        </div>
        <div class="grid-split q">
          <div class="panel station-detail rv" style="--i:1" id="station-detail"></div>
          <div class="panel rv" style="--i:2">
            <h3>Seguridad del pipeline (F7)</h3>
            <ul class="ticks small">
              <li>Dependencias fijadas en <code>uv.lock</code> e instaladas con <code>uv sync --locked --no-build</code></li>
              <li>Actions de terceros fijadas por SHA, no por etiqueta</li>
              <li>Permisos mínimos por job</li>
              <li>Inputs de <code>workflow_dispatch</code> validados y pasados por variables de entorno (sin inyección)</li>
            </ul>
          </div>
        </div>`,
      init(root, api) {
        const det = root.querySelector('#station-detail');
        const sts = root.querySelectorAll('.station');
        const box = root.querySelector('#belt-box');
        const mostrar = (i) => {
          const e = ESTACIONES[i];
          sts.forEach((s, j) => { s.classList.toggle('active', j === i); s.classList.toggle('lit', j <= i); });
          det.innerHTML = `<h3>${i + 1}. ${e.t}</h3><p>${e.d}</p><p class="metric-line">${e.dato}</p>`;
          const r0 = root.querySelector('.pipeline').getBoundingClientRect();
          const r = sts[i].getBoundingClientRect();
          box.style.transform = 'translateX(' + ((r.left - r0.left + r.width / 2) / api.zoom() - 11) + 'px)';
        };
        mostrar(0);
        const tour = recorrido(root, api, ESTACIONES.length, mostrar, { inicio: 900, paso: 1500 });
        sts.forEach((s) => s.addEventListener('click', () => { tour.detener(); mostrar(Number(s.dataset.i)); }));
      },
      notas: 'Cada push recorre la misma cinta: pre-commit en la máquina, ruff, complexipy con el mismo umbral que Sonar, pytest con cobertura mínima de 85 % en Windows y Ubuntu, el Quality Gate de SonarQube Cloud y el build de Sphinx con -W. Hacer clic en una estación detiene el recorrido y la deja fija para leerla; «Recorrer solo» lo reanuda. A la derecha, lo que endurecimos en F7: dependencias fijadas, actions por SHA, permisos mínimos y sin inyección en los inputs.'
    },

    /* 05 ---------------------------------------------------------------- */
    {
      arte: 'tests', etiqueta: 'Laboratorio de tests', fase: 'F2 · F9', tema: 'Testing',
      titulo: 'Testing: la red de seguridad va antes que el refactor',
      sub: 'Primero blindamos el comportamiento; después cambiamos la estructura con la suite en verde',
      evidencia: 'tests/ · ' + LB2 + 'cobertura.txt · tests/pedidos/test_procesador_concurrente.py',
      html: () => `
        <div class="grid-split tests">
          <div class="kpi-grid rv" style="--i:0">
            <div class="kpi"><span class="k-lbl">Tests</span><span class="k-from">84</span><span class="k-big" data-count="193">193</span></div>
            <div class="kpi"><span class="k-lbl">Cobertura src/</span><span class="k-from">80 %</span><span class="k-big" data-count="90" data-suf=" %">90 %</span></div>
            <div class="kpi"><span class="k-lbl">Umbral en CI</span><span class="k-from">75 %</span><span class="k-big" data-count="85" data-suf=" %">85 %</span></div>
            <div class="kpi"><span class="k-lbl">Organización</span><span class="k-from">test_etapa_*.py</span><span class="k-mid">11 subpaquetes por dominio</span></div>
            <div class="kpi"><span class="k-lbl">Hypothesis</span><span class="k-mid">Baseline ≡ Optimizado con datos aleatorios</span></div>
            <div class="kpi"><span class="k-lbl">pytest-benchmark</span><span class="k-mid">Regresión de rendimiento: hash ≈ 90 ns, lineal ≈ 1 µs</span></div>
          </div>
          <div class="panel bug-lab rv" style="--i:1">
            <h3>El error que atrapó la red <span class="chip chip-crimson">correctitud</span></h3>
            <div class="bug-setup">
              <span class="stock-chip">Producto #1 · stock <b id="bug-stock">5</b></span>
              <span>Pedido #1 pide 5</span><span>Pedido #2 pide 5</span><span><code>descontar_stock=True</code></span>
            </div>
            <div class="seg" role="tablist">
              <button type="button" class="active" data-m="p1">Concurrente · Parcial 1</button>
              <button type="button" data-m="p2">Concurrente · Parcial 2</button>
              <button type="button" data-m="seq">Secuencial (referencia)</button>
            </div>
            <div class="bug-lanes" id="bug-lanes"></div>
            <p class="bug-explain" id="bug-explain"></p>
            <ol class="lifecycle">
              <li><code>xfail(strict=True)</code><span>F2 documenta el error</span></li>
              <li>Corrección<span>F4 separa evaluar de asignar</span></li>
              <li>«xpass» rompe el CI<span>obliga a quitar la marca</span></li>
              <li class="ok">Test en verde<span>respeta el descuento</span></li>
            </ol>
          </div>
        </div>`,
      init(root, api) {
        const lanes = root.querySelector('#bug-lanes');
        const exp = root.querySelector('#bug-explain');
        const stock = root.querySelector('#bug-stock');
        const MODOS = {
          p1: { w: ['Worker A lee la foto: stock 5', 'Worker B lee la misma foto: stock 5'], r: ['CUBIERTO', 'CUBIERTO'], bad: [false, true],
            t: 'Los dos workers evaluaron contra la misma foto inicial. El segundo descuento falló en silencio (descontar_stock devolvió False), pero el pedido #2 quedó informado como cubierto.' },
          p2: { w: ['Con descuento: delega en el secuencial', 'Pedido #2 ve el stock que dejó el #1: 0'], r: ['CUBIERTO', 'IMPOSIBLE'], bad: [false, false],
            t: 'Con descontar_stock=True el procesador concurrente delega en el secuencial: cada pedido ve el stock que dejó el anterior. Sin descuento, el pool evalúa en paralelo y el resultado es idéntico.' },
          seq: { w: ['Pedido #1: stock 5 → asigna 5', 'Pedido #2: stock 0 → nada que asignar'], r: ['CUBIERTO', 'IMPOSIBLE'], bad: [false, false],
            t: 'La referencia: el procesador secuencial descuenta pedido por pedido. Es el resultado que el concurrente debe reproducir.' }
        };
        const correr = (m) => {
          const d = MODOS[m];
          root.querySelectorAll('.seg button').forEach((b) => b.classList.toggle('active', b.dataset.m === m));
          lanes.innerHTML = d.w.map((w, i) => `
            <div class="lane" style="--i:${i}">
              <span class="lane-w">${w}</span>
              <span class="lane-arrow">→</span>
              <span class="res ${d.r[i] === 'CUBIERTO' ? 'ok' : 'no'}${d.bad[i] ? ' wrong' : ''}">Pedido #${i + 1}: ${d.r[i]}${d.bad[i] ? ' ✗' : ''}</span>
            </div>`).join('');
          exp.textContent = d.t;
          exp.classList.toggle('wrong', m === 'p1');
          stock.textContent = '5';
          api.later(api.ms(700), () => { if (root.isConnected) stock.textContent = '0'; });
        };
        root.querySelectorAll('.seg button').forEach((b) => b.addEventListener('click', () => correr(b.dataset.m)));
        correr('p1');
        root.querySelectorAll('[data-count]').forEach((el) => api.countUp(el, Number(el.dataset.count), el.dataset.suf || ''));
      },
      notas: 'F2 fue la red de seguridad: fixtures compartidas, propiedades con Hypothesis que exigen que baseline y optimizado den lo mismo con datos aleatorios, y un test que reproducía el error de concurrencia marcado xfail(strict=True). Mostrar el laboratorio: con el código del Parcial 1, dos pedidos que piden 5 unidades de un producto con stock 5 salían los dos «cubiertos». En F4 se corrigió; el test pasó a xpass, el CI falló a propósito y se quitó la marca. Cierre: de 84 a 193 tests, de 80 a 90 % de cobertura y umbral 85 % en el CI.'
    },

    /* 06 ---------------------------------------------------------------- */
    {
      arte: 'tijera', etiqueta: 'Tijera', fase: 'F3', tema: 'Código redundante',
      titulo: 'Eliminar código redundante sin cambiar el comportamiento',
      sub: 'pylint encontró 8 pares duplicados en el Parcial 1; hoy encuentra 0 (10,00 / 10)',
      evidencia: 'src/pedidos/evaluador.py · ' + LB1 + 'pylint_duplicados.txt · ' + LB2 + 'pylint_duplicados.txt',
      html: () => `
        <div class="merge rv" style="--i:0" id="merge">
          <div class="code-card side">
            <div class="cc-head"><span>procesador_secuencial.py</span><span class="chip">Parcial 1</span></div>
            <pre class="code">${py(COD_SEC_P1, [4, 5, 6, 7, 8, 9, 10, 11, 12, 13], 'dup')}</pre>
          </div>
          <div class="code-card center">
            <div class="cc-head"><span>evaluador.py</span><span class="chip chip-green">Parcial 2</span></div>
            <pre class="code">${py(COD_EVAL_P2, [1, 12], 'new')}</pre>
            <button type="button" class="btn btn-accent merge-btn" id="btn-merge">✂ Extraer el núcleo común</button>
          </div>
          <div class="code-card side">
            <div class="cc-head"><span>procesador_concurrente.py</span><span class="chip">Parcial 1</span></div>
            <pre class="code">${py(COD_CONC_P1, [4, 5, 6, 7, 8, 9, 10, 11, 12, 13], 'dup')}</pre>
          </div>
        </div>
        <div class="cuts rv" style="--i:1">
          <div class="cut"><b>2 validadores</b> con las mismas reglas → un único <code>ValidadorDataset</code></div>
          <div class="cut"><b>3 métodos</b> armaban el catálogo igual → <code>MotorInventario._crear_catalogo()</code></div>
          <div class="cut"><b>6 pantallas</b> repetían la inicialización → <code>PantallaBase</code></div>
          <div class="cut"><b>Strings sueltos</b> → <code>Enum EstrategiaMotor</code> y <code>Enum PoliticaDescuento</code></div>
          <div class="cut"><b>Código muerto</b>: 14 f-strings sin variables, 4 imports y 1 variable sin uso, alias duplicado</div>
          <div class="cut keep"><b>No se borró</b>: <code>CatalogoLineal</code> ni el baseline. Son el experimento.</div>
        </div>`,
      init(root, api) {
        const merge = root.querySelector('#merge');
        const btn = root.querySelector('#btn-merge');
        btn.addEventListener('click', () => {
          if (merge.classList.contains('merged')) {
            merge.classList.remove('merged');
            btn.textContent = '✂ Extraer el núcleo común';
            return;
          }
          merge.classList.add('cutting');
          const r = btn.getBoundingClientRect();
          api.fx.sparks(r.left + r.width / 2, r.top, 22);
          api.later(api.ms(650), () => {
            merge.classList.remove('cutting');
            merge.classList.add('merged');
            btn.textContent = '↺ Ver el Parcial 1';
          });
        });
      },
      notas: 'La duplicación más grande: la regla para evaluar un pedido estaba copiada en el procesador secuencial y en el concurrente. Apretar el botón: las líneas repetidas salen de los dos archivos y quedan en evaluador.py, que es hoy la única implementación de la regla. Lo mismo con dos validadores, tres construcciones del catálogo y seis pantallas de Flet. Cada candidato de vulture se verificó contra los tests antes de borrarlo. Lo que no se borró, a propósito: CatalogoLineal y el baseline.'
    },

    /* 07 ---------------------------------------------------------------- */
    {
      arte: 'lupa', etiqueta: 'Lupa Scalene', fase: 'F4', tema: 'Herramienta de optimización',
      titulo: 'Scalene: dónde se iba realmente el tiempo',
      sub: 'Separa Python, código nativo y tiempo de sistema: el costo del pool no estaba en nuestro código, estaba en esperar y serializar',
      evidencia: 'docs/mediciones/scalene/resumen.md · docs/mediciones/archivos_grandes.md §3',
      html: () => `
        <div class="grid-split scalene">
          <div class="panel rv" style="--i:0">
            <h3>Mismo escenario, antes y después de la propuesta Origin 1</h3>
            <div class="sc-legend"><span class="lg py">Python</span><span class="lg nat">Nativo (pickle, json, dataclasses)</span><span class="lg sys">Sistema (esperas, IPC, E/S)</span></div>
            ${[['Antes (F3)', 6.8, 63.1, 28.1, 3.12], ['Después (F4)', 20.0, 57.8, 20.6, 2.58]].map((r, i) => `
              <div class="sc-row" style="--i:${i}">
                <span class="sc-name">${r[0]}<small>${String(r[4]).replace('.', ',')} s</small></span>
                <div class="sc-bar" style="--w:${(r[4] / 3.12) * 100}%">
                  <span class="sg py" style="--p:${r[1]}" title="Python ${r[1]} %">${r[1] >= 9 ? String(r[1]).replace('.', ',') + ' %' : ''}</span>
                  <span class="sg nat" style="--p:${r[2]}" title="Nativo ${r[2]} %">${String(r[2]).replace('.', ',')} %</span>
                  <span class="sg sys" style="--p:${r[3]}" title="Sistema ${r[3]} %">${String(r[3]).replace('.', ',')} %</span>
                </div>
              </div>`).join('')}
            <div class="sc-stats">
              <div><span class="k-big small-big">−17 %</span><span>tiempo total bajo Scalene</span></div>
              <div><span class="k-big small-big">28,1 → 20,6 %</span><span>tiempo de sistema</span></div>
            </div>
            <p class="foot-note">Linux · Python 3.13 · 2 núcleos · workers con fork en ambas corridas, para comparar en igualdad de condiciones.</p>
          </div>
          <div class="panel rv" style="--i:1">
            <h3>Los 5 cambios de la propuesta</h3>
            <ol class="numbered">
              <li><b>Separar evaluar de asignar:</b> los workers solo calculan; el stock se asigna en orden</li>
              <li><b>Mandar menos datos:</b> stock una vez por worker (<code>initializer</code>) y resultados como tuplas compactas</li>
              <li><b>Sin <code>sort</code> final:</b> los fragmentos son contiguos y vuelven en orden</li>
              <li><b>Umbral medido, no supuesto:</b> se eliminó el <code>P ≥ 50</code></li>
              <li><b><code>GestorPool</code>:</b> ciclo de vida explícito en lugar de variables globales</li>
            </ol>
            <div class="honest">
              <span class="h-tag">Resultado honesto</span>
              <p>Con 2.000 pedidos ya en memoria el pool sigue perdiendo: <b>5,2 ms</b> secuencial contra <b>14,0 ms</b> con pool (<b>0,37×</b>). Por eso el motor es <b>secuencial por defecto</b> y el pool quedó para los archivos grandes.</p>
            </div>
          </div>
        </div>`,
      init(root) {
        root.querySelectorAll('.sc-row').forEach((r) => r.classList.add('go'));
      },
      notas: 'Scalene distingue tiempo de Python, tiempo nativo y tiempo de sistema. En el escenario completo, antes de F4, el 28 % era sistema: el proceso principal esperando a los workers y moviendo datos por el canal IPC. Después de los cinco cambios bajó a 20,6 % y el escenario tardó 17 % menos. Ser honestos: con pedidos ya cargados en memoria el pool sigue sin compensar (0,37×). Por eso el default es secuencial y el paralelismo se reservó para archivos, que es la lámina siguiente.'
    },

    /* 08 ---------------------------------------------------------------- */
    {
      arte: 'rollo', etiqueta: 'Rollo JSONL', fase: 'F5', tema: 'Archivos grandes',
      titulo: 'Archivos grandes: streaming, lotes y buffer',
      sub: '200.000 pedidos (20,96 MB) en JSON Lines: la memoria deja de depender del tamaño del archivo',
      evidencia: 'docs/mediciones/archivos_grandes.md · src/datos/streaming.py · src/datos/procesador_lotes_paralelo.py',
      html: () => `
        <div class="files-strip rv" style="--i:0">
          <span><code>productos.jsonl</code> 5.000 · 0,66 MB</span>
          <span><code>pedidos.jsonl</code> 200.000 · 20,96 MB</span>
          <span>semilla 42 · en <code>data/generados/</code>, fuera de git</span>
          <span>mediana de 5 corridas</span>
        </div>
        <div class="grid-3 files">
          <div class="panel rv" style="--i:1">
            <h3>1 · Lectura</h3>
            <div class="mem-row"><span>Carga completa</span><div class="mem-bar"><i style="--w:100%"></i></div><b>195,59 MB</b><small>849,5 ms</small></div>
            <div class="mem-row good"><span>Streaming</span><div class="mem-bar"><i style="--w:0.52%"></i></div><b>1,02 MB</b><small>696,5 ms</small></div>
            <div class="stream-window" aria-hidden="true"><div class="stream-lines" id="stream-lines"></div><span class="sw-label">yield</span></div>
            <p class="big-delta">−99,5 % <span>de memoria pico</span></p>
          </div>
          <div class="panel rv" style="--i:2">
            <h3>2 · Lotes en paralelo</h3>
            <div class="seg small" id="lote-seg">
              ${['1.000', '5.000', '20.000', '50.000'].map((l, i) => `<button type="button" data-i="${i}"${i === 1 ? ' class="active"' : ''}>${l}</button>`).join('')}
            </div>
            <div class="lote-bars" id="lote-bars"></div>
            <p class="foot-note">Con 2 workers el máximo teórico es 2×. Cada worker parsea, valida y evalúa su lote; como máximo dos lotes en vuelo por worker.</p>
          </div>
          <div class="panel rv" style="--i:3">
            <h3>3 · Escritura con buffer</h3>
            <p class="small-p">Exportación del picking a CSV: 5.000 filas (434,9 KB).</p>
            <div class="mem-row"><span>Buffer por defecto</span><div class="mem-bar"><i style="--w:100%"></i></div><b>52,4 ms</b></div>
            <div class="mem-row good"><span>Buffer de 1 MB</span><div class="mem-bar"><i style="--w:93.3%"></i></div><b>48,9 ms</b></div>
            <p class="big-delta">−7 % <span>menos llamadas al sistema</span></p>
            <ul class="ticks small tech">
              <li><code>en_lotes()</code> propio: <code>itertools.batched</code> exige Python 3.12</li>
              <li>Validación por lote: IDs de productos en un <code>set</code> antes de recorrer los pedidos</li>
              <li>Tests con archivo vacío, línea corrupta, último lote incompleto e ID inexistente</li>
            </ul>
          </div>
        </div>`,
      init(root, api) {
        const L = [
          { s: 827.8, p: 686.9, x: '1,21×', ms: '1,68', mp: '3,05' },
          { s: 995.5, p: 654.2, x: '1,52×', ms: '3,93', mp: '8,36', best: true },
          { s: 869.5, p: 769.8, x: '1,13×', ms: '12,03', mp: '30,41' },
          { s: 987.6, p: 775.5, x: '1,27×', ms: '28,19', mp: '86,05' }
        ];
        const bars = root.querySelector('#lote-bars');
        const fmt = (v) => v.toFixed(1).replace('.', ',');
        const mostrar = (i) => {
          const d = L[i];
          root.querySelectorAll('#lote-seg button').forEach((b) => b.classList.toggle('active', Number(b.dataset.i) === i));
          bars.innerHTML = `
            <div class="mem-row"><span>Secuencial</span><div class="mem-bar"><i style="--w:${(d.s / 1000) * 100}%"></i></div><b>${fmt(d.s)} ms</b></div>
            <div class="mem-row good"><span>Paralelo</span><div class="mem-bar"><i style="--w:${(d.p / 1000) * 100}%"></i></div><b>${fmt(d.p)} ms</b></div>
            <p class="big-delta">${d.x} <span>${d.best ? 'el mejor lote medido' : 'speedup'}</span></p>
            <p class="small-p">Pico de memoria: ${d.ms} MB secuencial · ${d.mp} MB paralelo</p>`;
        };
        root.querySelectorAll('#lote-seg button').forEach((b) => b.addEventListener('click', () => mostrar(Number(b.dataset.i))));
        mostrar(1);
        // Ventana de streaming: una línea por vez
        const win = root.querySelector('#stream-lines');
        let n = 1;
        const linea = () => {
          if (!root.isConnected) return;
          const el = document.createElement('div');
          el.className = 'sl';
          el.textContent = '{"id": ' + n + ', "lineas": [[' + ((n * 37) % 5000) + ', ' + ((n % 4) + 1) + ']]}';
          win.appendChild(el);
          if (win.children.length > 4) win.removeChild(win.firstChild);
          n += 1;
          api.later(api.ms(520) || 520, linea);
        };
        linea();
      },
      notas: 'F5 generó archivos de verdad grandes: 200.000 pedidos en JSON Lines. Leer línea por línea con un generador usa 1 MB de memoria pico contra casi 196 MB de la carga completa, y además es más rápido. Con lotes, el pool por fin compensa, porque cada worker parsea, valida y evalúa: el mejor caso fue 1,52× con lotes de 5.000 (el techo con 2 workers es 2×). Elegir otro tamaño de lote para mostrar el barrido. La escritura con buffer de 1 MB bajó 7 % el tiempo de exportar el CSV.'
    },

    /* 09 ---------------------------------------------------------------- */
    {
      arte: 'monitor', etiqueta: 'Monitor APM', fase: 'F6', tema: 'Herramienta general (APM)',
      titulo: 'Observabilidad con Elastic APM',
      sub: 'Cada operación del motor es una transacción, los pasos costosos son spans y los errores llegan solos a Kibana',
      evidencia: 'src/observabilidad/apm.py · docs/observabilidad-apm.md · scripts/demo_apm.py',
      html: () => `
        <div class="grid-split apm">
          <div class="panel rv" style="--i:0">
            <div class="seg" id="apm-seg">
              <button type="button" class="active" data-m="ok">Operación normal</button>
              <button type="button" data-m="err">Dataset inválido</button>
              <button type="button" data-m="off">Sin servidor APM</button>
            </div>
            <div class="apm-view" id="apm-view"></div>
          </div>
          <div class="panel rv" style="--i:1">
            <h3>Qué se envía</h3>
            <table class="mini-tbl">
              <tr><td>Transacciones</td><td><code>@medir</code> en la fachada: cargar, buscar, top-N, procesar, lotes JSONL</td></tr>
              <tr><td>Spans</td><td><code>pool.armar_fragmentos</code>, <code>pool.evaluar</code>, <code>lotes.procesar_archivo</code></td></tr>
              <tr><td>Etiquetas</td><td>estrategia, pedidos, dataset, tamaño de lote, workers, concurrente</td></tr>
              <tr><td>Errores</td><td>Excepciones, <code>BrokenProcessPool</code> y <code>logging.error</code></td></tr>
              <tr><td>Métricas</td><td>CPU y memoria cada 30 s (psutil)</td></tr>
            </table>
            <h3 class="mt">Decisiones</h3>
            <ul class="ticks small">
              <li>El agente vive solo en el proceso principal: el costo del pool se mide desde afuera</li>
              <li><code>instrument=False</code>: no hay framework web que auto-instrumentar</li>
              <li>API key en <code>.env</code>, nunca en el repo; tests con <code>disable_send=True</code></li>
            </ul>
            <p class="cmd"><code>python -m scripts.demo_apm</code><span>actividad + un error provocado para la demo</span></p>
          </div>
        </div>`,
      init(root) {
        const view = root.querySelector('#apm-view');
        const VISTAS = {
          ok: `
            <p class="apm-cap">Esquema de una traza (los tiempos reales se muestran en Kibana durante la demo)</p>
            <div class="wf">
              <div class="wf-row tx" style="--x:0%;--w:100%"><span class="wf-name">motor.procesar_pedidos</span><span class="wf-bar"></span><span class="pill ok">success</span></div>
              <div class="wf-row sp" style="--x:2%;--w:18%"><span class="wf-name">↳ pool.armar_fragmentos</span><span class="wf-bar"></span></div>
              <div class="wf-row sp ipc" style="--x:21%;--w:76%"><span class="wf-name">↳ pool.evaluar · ipc</span><span class="wf-bar"></span></div>
            </div>
            <div class="labels">${['estrategia: optimizado', 'concurrente: true', 'pedidos: 2000', 'workers', 'fragmentos', 'cubiertos', 'parciales'].map((l) => '<span>' + l + '</span>').join('')}</div>
            <dl class="wf-legend">
              <div><dt>Transacción</dt><dd>una operación de la fachada, medida de punta a punta</dd></div>
              <div><dt>Span</dt><dd>un paso interno; si ya hay transacción abierta, la operación entra como span</dd></div>
              <div><dt>Tipo ipc</dt><dd>la espera del proceso principal mientras trabajan los workers</dd></div>
            </dl>`,
          err: `
            <p class="apm-cap">La misma operación con un dataset inválido (lo provoca <code>demo_apm</code>)</p>
            <div class="wf">
              <div class="wf-row tx fail" style="--x:0%;--w:34%"><span class="wf-name">motor.cargar_dataset</span><span class="wf-bar"></span><span class="pill bad">failure</span></div>
            </div>
            <div class="err-card"><b>ValueError</b><span>Capturado automáticamente por la transacción instrumentada; también llegan los registros de <code>logging</code> con nivel ERROR (<code>ManejadorErroresAPM</code>).</span></div>`,
          off: `
            <p class="apm-cap">Sin <code>ELASTIC_APM_SERVER_URL</code> no se crea el cliente: tests y CI corren sin enviar nada</p>
            <pre class="code">${py(COD_MEDIR, [5, 6], 'new')}</pre>`
        };
        const mostrar = (m) => {
          root.querySelectorAll('#apm-seg button').forEach((b) => b.classList.toggle('active', b.dataset.m === m));
          view.innerHTML = VISTAS[m];
          view.classList.remove('in'); void view.offsetWidth; view.classList.add('in');
        };
        root.querySelectorAll('#apm-seg button').forEach((b) => b.addEventListener('click', () => mostrar(b.dataset.m)));
        mostrar('ok');
      },
      notas: 'Elastic APM nos da la vista de producción que los benchmarks no dan. El decorador @medir convierte cada operación de la fachada en una transacción, o en un span si ya hay una transacción abierta. Los pasos del pool aparecen como spans, así en Kibana se ve cuánto es IPC. Mostrar las tres pestañas: operación normal, el error provocado con un dataset inválido y qué pasa sin servidor: el decorador llama a la función directo, así los tests y el CI no dependen de Elastic. Si hay conexión, correr python -m scripts.demo_apm y abrir Kibana. Recordar: la prueba de Elastic Cloud dura 14 días desde el 8/10.'
    },

    /* 10 ---------------------------------------------------------------- */
    {
      arte: 'bloques', etiqueta: 'Bloques', fase: 'F7', tema: 'Legibilidad y refactorización',
      titulo: 'Legibilidad, mantenibilidad y refactorización',
      sub: 'Nueve paquetes con una responsabilidad cada uno, un Protocol en lugar de herencia y ninguna función por encima de complejidad 12',
      evidencia: LB2 + 'radon_complejidad.txt · ' + LB2 + 'ruff_pep8_docstrings.txt · src/inventario/protocolo.py',
      html: () => `
        <div class="grid-split refactor">
          <div class="panel rv" style="--i:0">
            <h3>src/ en 9 paquetes <span class="hint-inline">clic para ver el contenido</span></h3>
            <div class="pkg-grid">
              ${PAQUETES.map((p, i) => `<button type="button" class="pkg${p.centro ? ' center' : ''}" data-i="${i}" style="--i:${i}"><strong>${p.k}</strong><span>${p.d}</span></button>`).join('')}
            </div>
            <div class="pkg-detail" id="pkg-detail"></div>
          </div>
          <div class="panel rv" style="--i:1">
            <h3>Antes → después</h3>
            <div class="ba-list">
              <div><span>Complejidad cognitiva &gt; 15</span><b>14 → 0</b><small>la peor: <code>main</code> de la UI, 46</small></div>
              <div><span>Funciones CC grado D</span><b>3 → 0</b><small>máximo actual: 12</small></div>
              <div><span>Funciones CC grado C o peor</span><b>15 → 6</b><small>todas entre 11 y 12</small></div>
              <div><span>ruff PEP 8 + docstrings</span><b>517 → 36</b><small>0 líneas largas, 0 sin docstring</small></div>
              <div><span>Números mágicos</span><b>73 → constantes</b><small>con nombre</small></div>
            </div>
            <div class="rename" aria-label="Ejemplos de nombres">
              <span><s>lineas_satisfechas_count</s> → <code>cantidad_lineas_satisfechas</code></span>
              <span><s>p</s>, <s>ped</s>, <s>prod</s>, <s>rl</s> → nombres completos</span>
            </div>
            <pre class="code tiny">${py(COD_PROTOCOL, [2], 'new')}</pre>
            <p class="small-p"><b>Framework Flet:</b> <code>main()</code> de 250 líneas → <code>AplicacionInventario</code> + tupla <code>SECCIONES</code> + <code>PantallaBase</code>.</p>
          </div>
        </div>`,
      init(root) {
        const det = root.querySelector('#pkg-detail');
        const pk = root.querySelectorAll('.pkg');
        const mostrar = (i) => {
          const p = PAQUETES[i];
          pk.forEach((b, j) => b.classList.toggle('active', j === i));
          det.innerHTML = `<code>src/${p.k}/</code> ${p.f.map((f) => '<span class="file">' + f + '</span>').join('')}<p>${p.x}</p>`;
        };
        pk.forEach((b) => b.addEventListener('click', () => mostrar(Number(b.dataset.i))));
        mostrar(4);
      },
      notas: 'F7 fue legibilidad y refactor con la red de F2 debajo. Nueve paquetes con una responsabilidad cada uno; motor es la fachada. CatalogoLineal y CatalogoHash no comparten clase base: cumplen el Protocol Catalogo (tipado estructural). La función más compleja del proyecto era el main de la UI de Flet, con complejidad cognitiva 46: hoy es la clase AplicacionInventario con las pantallas declaradas en una tupla. Cada refactor de lógica se verificó contra la versión anterior: 864 casos de alternativas con salida idéntica. Docstrings estilo Google en español, nombres completos y 73 números mágicos convertidos en constantes.'
    },

    /* 11 ---------------------------------------------------------------- */
    {
      arte: 'sphinx', etiqueta: 'Manual Sphinx', fase: 'F8', tema: 'Generador de documentación',
      titulo: 'Documentación generada con Sphinx',
      sub: 'Los docstrings de F7 se convierten en la referencia de la API; las guías Markdown se incluyen sin duplicarse',
      evidencia: 'docs/sphinx/conf.py · .github/workflows/verify.yml (jobs docs y deploy-docs)',
      html: () => `
        <div class="grid-split sphinx">
          <div class="flip-wrap rv" style="--i:0">
            <div class="flip" id="flip">
              <div class="flip-face front">
                <div class="cc-head"><span>src/motor/motor_inventario.py</span><span class="chip">docstring</span></div>
                <pre class="code">${py(COD_DOCSTRING, [5, 10, 11, 12, 13, 14], 'new')}</pre>
              </div>
              <div class="flip-face back">
                <div class="furo">
                  <div class="furo-side"><b>Optimizador</b><span>Guías</span><span>Mediciones</span><span class="on">API · motor</span><span>API · pedidos</span><span>API · datos</span></div>
                  <div class="furo-main">
                    <p class="furo-sig"><span class="k">procesar_pedidos</span>(<i>pedidos=None, concurrente=False, descontar_stock=False, politica_descuento='solo_cubiertos'</i>) <a>[fuente]</a></p>
                    <p>Procesa un lote de pedidos según la estrategia configurada.</p>
                    <p>El procesamiento es secuencial salvo que se pida <code>concurrente=True</code>.</p>
                    <dl><dt>Argumentos:</dt>
                      <dd><b>pedidos</b> – Pedidos a procesar.</dd>
                      <dd><b>concurrente</b> – Si es True, usa el ProcessPoolExecutor.</dd>
                      <dd><b>descontar_stock</b> – Si es True, descuenta lo asignado.</dd>
                      <dd><b>politica_descuento</b> – solo_cubiertos o todo_lo_posible.</dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>
            <button type="button" class="btn btn-accent flip-btn" id="btn-flip">⚙ Compilar con Sphinx</button>
          </div>
          <div class="panel rv" style="--i:1">
            <div class="kpi-row">
              <div class="kpi"><span class="k-big">0</span><span class="k-lbl">advertencias con <code>-W</code></span></div>
              <div class="kpi"><span class="k-big">20</span><span class="k-lbl">páginas HTML</span></div>
              <div class="kpi"><span class="k-big">9</span><span class="k-lbl">paquetes en la API</span></div>
              <div class="kpi"><span class="k-big">10</span><span class="k-lbl">guías vía MyST</span></div>
            </div>
            <div class="chips-row">${['autodoc', 'napoleon (secciones en español)', 'viewcode', 'myst-parser', 'tema Furo', 'GitHub Pages'].map((c) => '<span class="chip">' + c + '</span>').join('')}</div>
            <h3 class="mt">Decisiones</h3>
            <ul class="ticks small">
              <li><b>Envoltorios con <code>{include}</code>:</b> Sphinx no admite archivos fuera de su árbol; así los <code>.md</code> de <code>docs/</code> no se duplican</li>
              <li><b><code>autodoc_mock_imports = ["flet", …]</code>:</b> la UI se documenta sin pantalla en el CI</li>
              <li><b><code>suppress_warnings</code> selectivo:</b> <code>-W</code> solo corta por errores reales</li>
            </ul>
            <p class="cmd"><code>gastmolina267.github.io/PEF-Optimizador-de-Inventario</code><span>publicado por el CI</span></p>
          </div>
        </div>`,
      init(root, api) {
        const flip = root.querySelector('#flip');
        const btn = root.querySelector('#btn-flip');
        btn.addEventListener('click', () => {
          const on = flip.classList.toggle('flipped');
          btn.textContent = on ? '↺ Ver el docstring' : '⚙ Compilar con Sphinx';
          if (on) {
            const r = flip.getBoundingClientRect();
            api.fx.sparks(r.left + r.width / 2, r.top + r.height / 2, 26);
          }
        });
      },
      notas: 'F8 cierra el círculo de F7: los docstrings estilo Google en español los lee napoleon con secciones personalizadas (Argumentos, Retorna, Lanza) y autodoc arma la referencia de la API. Apretar «Compilar» para mostrar el mismo método como código y como página. Las guías existentes se incluyen con MyST sin copiarlas, y el CI compila con -W: una advertencia corta el build. El sitio se publica en GitHub Pages.'
    },

    /* 12 ---------------------------------------------------------------- */
    {
      arte: 'certificado', etiqueta: 'Certificado', fase: 'F9', tema: 'Comparativa',
      titulo: 'Certificado de inspección: Parcial 1 vs. Parcial 2',
      sub: 'Los mismos 9 comandos sobre el commit de cierre de cada parcial',
      evidencia: LB1 + 'README.md · ' + LB2 + 'README.md',
      html: () => `
        <div class="cert rv" style="--i:0">
          <div class="cert-toggle">
            <span>Mostrar</span>
            <div class="seg small" id="cert-seg"><button type="button" data-v="a">Parcial 1</button><button type="button" class="active" data-v="b">Parcial 2</button></div>
          </div>
          <table class="cert-tbl">
            <thead><tr><th>Métrica</th><th>Parcial 1</th><th>Parcial 2</th><th class="bar-col"></th><th>Nota</th></tr></thead>
            <tbody>
              ${COMPARATIVA.map((c, i) => `
                <tr style="--i:${i}" class="${c.mejor}">
                  <td>${c.m}</td>
                  <td class="v a">${c.fmt(c.a)}</td>
                  <td class="v b">${c.fmt(c.b)}</td>
                  <td class="bar-col"><div class="cbar" data-a="${c.a}" data-b="${c.b}" data-max="${c.max || Math.max(c.a, c.b)}"><i></i></div></td>
                  <td class="nota">${c.nota || ''}</td>
                </tr>`).join('')}
            </tbody>
          </table>
          <p class="foot-note">El código de <code>src/</code> creció de 5.375 a 7.604 líneas: más módulos, docstrings y el subsistema de archivos grandes. Más líneas, menos complejidad por función.</p>
          <div class="cert-stamp" id="cert-stamp"><span>INSPECCIONADO</span><b>PARCIAL 2</b><small>9 herramientas · 2 fotos</small></div>
        </div>`,
      init(root, api) {
        const barras = root.querySelectorAll('.cbar');
        const pintar = (v) => {
          root.querySelectorAll('#cert-seg button').forEach((b) => b.classList.toggle('active', b.dataset.v === v));
          root.querySelector('.cert').dataset.v = v;
          barras.forEach((b) => {
            const val = Number(b.dataset[v]);
            const max = Number(b.dataset.max) || 1;
            b.querySelector('i').style.width = Math.max(0.6, (val / max) * 100) + '%';
          });
        };
        root.querySelectorAll('#cert-seg button').forEach((b) => b.addEventListener('click', () => pintar(b.dataset.v)));
        pintar('a');
        api.later(api.ms(900), () => {
          if (!root.isConnected) return;
          pintar('b');
          api.later(api.ms(900), () => {
            const s = root.querySelector('#cert-stamp');
            if (!s) return;
            s.classList.add('in');
            const r = s.getBoundingClientRect();
            api.fx.puff(r.left + r.width / 2, r.top + r.height / 2, 14, 'ink');
          });
        });
      },
      notas: 'La foto final: mismos 9 comandos, mismo repositorio, dos commits. La tabla arranca mostrando el Parcial 1 y pasa sola al Parcial 2; se puede alternar con el selector. Destacar las tres que más pesan: 3 funciones de complejidad D a 0, 8 duplicados a 0 y 84 a 193 tests con 90 % de cobertura. Aclarar la honesta: src/ creció en líneas porque hay más módulos y docstrings, pero cada función es más simple.'
    },

    /* 13 ---------------------------------------------------------------- */
    {
      arte: 'sello', etiqueta: 'Sello', fase: 'Cierre', tema: 'Conclusiones',
      titulo: 'Conclusiones y autocrítica',
      sub: 'Qué rindió más, qué no salió como esperábamos y qué haríamos distinto en una tercera edición',
      evidencia: 'docs/resumen-parcial-2.md · docs/mediciones/',
      html: () => `
        <div class="grid-3 concl">
          <div class="panel tint-green rv" style="--i:0">
            <h3>Mayor impacto</h3>
            <ul class="ticks small">
              <li><b>Tests antes del refactor:</b> F3 y F7 cambiaron la estructura sin cambiar el comportamiento (864 casos de alternativas idénticos; informes iguales byte a byte)</li>
              <li><b>Streaming:</b> la memoria depende de una línea, no del archivo (−99,5 %)</li>
              <li><b>Scalene:</b> mostró que el costo del pool era sistema e IPC, no nuestro Python</li>
            </ul>
          </div>
          <div class="panel tint-amber rv" style="--i:1">
            <h3>No salió como esperábamos</h3>
            <ul class="ticks small warn">
              <li>Con pedidos en memoria el pool sigue perdiendo (0,37×): quedó secuencial por defecto</li>
              <li>Con archivos, 1,52× con 2 workers: lejos del 2× teórico</li>
              <li>vulture todavía marca 56 candidatos: callbacks de Flet, falsos positivos</li>
              <li>Elastic Cloud es una prueba de 14 días: si la defensa se corre, hay que recrearla</li>
            </ul>
          </div>
          <div class="panel tint-blue rv" style="--i:2">
            <h3>Qué haríamos diferente</h3>
            <ul class="ticks small">
              <li><b>Trazabilidad desde el día 1:</b> cada número de la presentación sale de un script con su archivo</li>
              <li><b>Medir en el sistema de la defensa:</b> Scalene corrió en Linux; la app se usa en Windows</li>
              <li><b>Memoria compartida</b> (<code>shared_memory</code>) para que el pool no serialice el stock</li>
              <li><b>SonarQube desde F0</b>, para ver la deuda antes de acumularla</li>
            </ul>
          </div>
        </div>
        <div class="repack-cta rv" style="--i:3">
          <button type="button" class="btn btn-accent btn-big" id="btn-repack">📦 Re-empaquetar y despachar el Parcial 2 <kbd>P</kbd></button>
        </div>`,
      init(root, api) {
        root.querySelector('#btn-repack').addEventListener('click', () => api.repack());
      },
      notas: 'Cierre con autocrítica. Lo que más rindió fue el orden: tests antes del refactor. Lo que no salió como esperábamos: el pool en memoria sigue sin compensar y el paralelo con archivos queda en 1,52×. Qué haríamos distinto: trazabilidad desde el día 1 (en el Parcial 1 algunas cifras de la presentación no salían de un script; en este informe cada número cita su archivo), medir en Windows, memoria compartida para el pool y SonarQube desde la fase 0. Después: re-empaquetar la caja y que el tribunal la selle.'
    }
  ];

  const NOTAS_RITUAL = {
    intro: 'Arrancamos donde terminó el Parcial 1: aquella vez empaquetamos y despachamos el manual en una caja. Hoy la recibimos. Presionar Enter o «Recibir el envío».',
    arrival: 'La caja llega igual que salió: guía del Parcial 1, cinta y la marca de PUNTUAR en la tapa. Viene con polvo: la deuda técnica del viaje.',
    clean: 'El polvo son los hallazgos de la línea base del Parcial 1 (F541, E501, duplicados, CC 30…). Pasar el cepillo con el mouse o presionar Enter para limpiarla automáticamente. Al terminar, el laboratorio de calidad sella la recepción.',
    cut: 'Pasar el cúter a lo largo de la cinta (o Enter). Al abrir aparecen los 13 elementos que vamos a inspeccionar.',
    opening: 'Sale primero el manual del Parcial 1 y después las herramientas que le sumamos en el Parcial 2.',
    hub: 'Mesa de inspección: cada objeto es un tema. Recorrer en orden con → o elegir uno con clic. Esc vuelve siempre acá.',
    repack: 'Guardamos todo, cerramos con la cinta del Quality Gate y pegamos la guía nueva sobre la del Parcial 1.',
    final: 'PUNTUAR: el tribunal elige la nota y sella la caja. R reabre la mesa para preguntas.'
  };

  window.PEF2_CONTENIDO = {
    ARTE, HERRAMIENTAS, LAMINAS, NOTAS_RITUAL, py,
    CINTA_P1: 'SEALED • UBP PEF 2026 • AUDITADO DETERMINÍSTICO • 718x',
    CINTA_P2: 'QUALITY GATE: PASSED • 193 TESTS • 90% COBERTURA • 0 DUPLICADOS',
    POLVO: ['F541 ×14', 'E501 ×275', 'CC 30', 'duplicado ×8', 'sin docstring ×106', 'vulture ×69', 'F401 ×4', 'cobertura 80%', 'CC 29', 'sin docs', 'F841', 'magic number', 'xfail?', 'main() CC 46']
  };
})();
