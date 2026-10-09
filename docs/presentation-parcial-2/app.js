/* ==========================================================================
   PRESENTACIÓN INTERACTIVA — SEGUNDO PARCIAL PEF (OPCIÓN 6)
   Ritual: recibir la caja del Parcial 1 → cepillar el polvo → cortar la cinta →
   abrir → inspeccionar los 13 elementos → re-empaquetar → sellar.
   ========================================================================== */
(function () {
  'use strict';

  const C = window.PEF2_CONTENIDO;
  const $ = (s, r) => (r || document).querySelector(s);
  const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
  const html = document.documentElement;
  const body = document.body;

  /* ------------------------------------------------------------------------
     Movimiento (Windows suele apagar las animaciones del sistema)
     ------------------------------------------------------------------------ */
  const MOTION_KEY = 'pef2-force-motion';
  const reduceMq = window.matchMedia('(prefers-reduced-motion: reduce)');
  const motionOff = () => reduceMq.matches && !html.classList.contains('force-motion');
  const ms = (v) => (motionOff() ? 0 : v);
  const sleep = (t) => new Promise((r) => setTimeout(r, t));

  function syncMotionButton() {
    const on = !motionOff();
    $('#motion-label').textContent = on ? 'Animaciones' : 'Sin animaciones';
    $('#btn-motion').classList.toggle('is-off', !on);
  }
  function toggleMotion() {
    const forced = html.classList.toggle('force-motion');
    try { sessionStorage.setItem(MOTION_KEY, forced ? '1' : '0'); } catch (e) { /* sin storage */ }
    syncMotionButton();
  }

  /* ------------------------------------------------------------------------
     Estado
     ------------------------------------------------------------------------ */
  let state = 'intro';
  let current = 0;
  const visited = new Set();
  const STEP_OF = { intro: null, arrival: 'arrival', clean: 'clean', cut: 'cut', opening: 'cut', hub: 'hub', slides: 'hub', repack: 'hub', final: 'hub' };
  const STEP_ORDER = ['arrival', 'clean', 'cut', 'hub'];

  function setState(s) {
    state = s;
    body.className = body.className.replace(/\bstate-\S+/g, '').trim() + ' state-' + s;
    body.classList.toggle('theme-light', s === 'slides');
    body.classList.toggle('theme-dark', s !== 'slides');
    const step = STEP_OF[s];
    const idx = STEP_ORDER.indexOf(step);
    $$('#ritual-steps li').forEach((li, i) => {
      li.classList.toggle('active', i === idx);
      li.classList.toggle('done', idx > -1 && i < idx);
    });
    $('#brand-sub').textContent = s === 'slides'
      ? 'Informe de inspección — Segundo Parcial (Opción 6)'
      : 'Recepción y Auditoría de Calidad — Segundo Parcial (Opción 6)';
    refreshNotes();
  }

  /* ------------------------------------------------------------------------
     FX: polvo, chispas y motas de luz
     ------------------------------------------------------------------------ */
  const fx = (function () {
    const cv = $('#fx-canvas');
    const ctx = cv.getContext('2d');
    let W = 0;
    let H = 0;
    let dpr = 1;
    const parts = [];
    const motes = [];
    const hooks = [];

    function resize() {
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      W = window.innerWidth;
      H = window.innerHeight;
      cv.width = W * dpr;
      cv.height = H * dpr;
      cv.style.width = W + 'px';
      cv.style.height = H + 'px';
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    resize();
    window.addEventListener('resize', resize);

    for (let i = 0; i < 46; i++) {
      motes.push({ x: Math.random(), y: Math.random(), r: 0.6 + Math.random() * 1.8, v: 0.00004 + Math.random() * 0.00012, p: Math.random() * Math.PI * 2 });
    }

    const PAL = {
      dust: ['140,124,104', '176,160,138', '98,86,72', '200,186,166'],
      light: ['150,135,115', '190,176,156', '120,108,92'],
      ink: ['190,18,60', '159,18,57', '225,29,72'],
      spark: ['252,211,77', '245,158,11', '255,247,237', '253,186,116']
    };

    function puff(x, y, n, kind) {
      if (motionOff()) return;
      const pal = PAL[kind || 'dust'];
      for (let i = 0; i < n; i++) {
        const a = Math.random() * Math.PI * 2;
        const sp = 0.4 + Math.random() * (kind === 'ink' ? 2.2 : 1.6);
        parts.push({
          x, y,
          vx: Math.cos(a) * sp,
          vy: Math.sin(a) * sp - (kind === 'ink' ? 0 : 0.6),
          g: kind === 'ink' ? 0.05 : 0.025,
          life: 0,
          max: 40 + Math.random() * 50,
          r: kind === 'ink' ? 1 + Math.random() * 2.2 : 1.2 + Math.random() * 3.4,
          c: pal[(Math.random() * pal.length) | 0],
          soft: kind !== 'ink'
        });
      }
    }
    function sparks(x, y, n) {
      if (motionOff()) return;
      for (let i = 0; i < n; i++) {
        const a = -Math.PI / 2 + (Math.random() - 0.5) * Math.PI * 1.4;
        const sp = 1.5 + Math.random() * 3.8;
        parts.push({ x, y, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp, g: 0.06, life: 0, max: 30 + Math.random() * 40, r: 1 + Math.random() * 1.8, c: PAL.spark[(Math.random() * 4) | 0], spark: true });
      }
    }
    function brushDust(x, y, vx, vy) {
      if (motionOff()) return;
      parts.push({ x, y, vx: -vx * 0.08 + (Math.random() - 0.5) * 1.4, vy: -Math.random() * 1.2, g: 0.045, life: 0, max: 50 + Math.random() * 40, r: 1 + Math.random() * 2.6, c: PAL.dust[(Math.random() * 4) | 0], soft: true });
    }

    function loop() {
      ctx.clearRect(0, 0, W, H);
      hooks.forEach((h) => h());
      // motas en el haz de luz (solo en escenas oscuras)
      if (body.classList.contains('theme-dark') && !motionOff()) {
        for (const m of motes) {
          m.y -= m.v * 16;
          m.p += 0.01;
          if (m.y < -0.05) { m.y = 1.05; m.x = Math.random(); }
          const x = (0.3 + m.x * 0.4) * W + Math.sin(m.p) * 12;
          const y = m.y * H;
          const fall = 1 - Math.min(1, Math.abs(x - W / 2) / (W * 0.22));
          ctx.fillStyle = 'rgba(255,226,180,' + (0.06 + fall * 0.22).toFixed(3) + ')';
          ctx.beginPath(); ctx.arc(x, y, m.r, 0, Math.PI * 2); ctx.fill();
        }
      }
      for (let i = parts.length - 1; i >= 0; i--) {
        const p = parts[i];
        p.life += 1;
        p.vx *= 0.985;
        p.vy = p.vy * 0.985 + p.g;
        p.x += p.vx;
        p.y += p.vy;
        const t = p.life / p.max;
        if (t >= 1) { parts.splice(i, 1); continue; }
        const a = (1 - t) * (p.spark ? 1 : 0.75);
        if (p.soft) {
          const r = p.r * (1 + t * 2.2);
          const g = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, r);
          g.addColorStop(0, 'rgba(' + p.c + ',' + a.toFixed(3) + ')');
          g.addColorStop(1, 'rgba(' + p.c + ',0)');
          ctx.fillStyle = g;
          ctx.beginPath(); ctx.arc(p.x, p.y, r, 0, Math.PI * 2); ctx.fill();
        } else {
          ctx.fillStyle = 'rgba(' + p.c + ',' + a.toFixed(3) + ')';
          ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2); ctx.fill();
        }
      }
      requestAnimationFrame(loop);
    }
    requestAnimationFrame(loop);
    return { puff, sparks, brushDust, hook: (f) => hooks.push(f) };
  })();

  /* ------------------------------------------------------------------------
     Caja 3D: poses, geometría de pantalla
     ------------------------------------------------------------------------ */
  const rig = $('#rig');
  const boxEl = $('#box');
  const POSES = {
    intro: { rx: -22, ry: -30, s: 1.0, ty: 20 },
    clean: { rx: -24, ry: -22, s: 1.12, ty: 10 },
    cut: { rx: -60, ry: -6, s: 1.1, ty: 40 },
    opening: { rx: -50, ry: -16, s: 0.98, ty: 50 },
    hub: { rx: -50, ry: -20, s: 0.6, ty: 34 },
    label: { rx: -12, ry: -12, s: 1.12, ty: 0 },
    final: { rx: -32, ry: -32, s: 0.95, ty: 20 },
    stamp: { rx: -64, ry: -4, s: 1.16, ty: 50 }
  };
  let pose = Object.assign({}, POSES.intro);

  function viewScale() {
    return Math.max(0.55, Math.min(1, window.innerHeight / 880, window.innerWidth / 1380));
  }
  function setPose(p, instant) {
    pose = Object.assign({ tx: 0, ty: 0 }, p);
    if (instant) rig.classList.add('no-trans');
    rig.style.setProperty('--rx', pose.rx + 'deg');
    rig.style.setProperty('--ry', pose.ry + 'deg');
    rig.style.setProperty('--s', (pose.s * viewScale()).toFixed(3));
    rig.style.setProperty('--tx', (pose.tx || 0) + 'px');
    rig.style.setProperty('--ty', (pose.ty || 0) * viewScale() + 'px');
    if (instant) { void rig.offsetWidth; rig.classList.remove('no-trans'); }
  }

  // Esquinas en pantalla de un elemento plano dentro de la escena 3D
  function cornersOf(el, w, h) {
    const pts = [[0, 0], [w, 0], [w, h], [0, h]];
    return pts.map(([x, y]) => {
      const m = document.createElement('i');
      m.style.cssText = 'position:absolute;left:' + (x - 1) + 'px;top:' + (y - 1) + 'px;width:2px;height:2px;pointer-events:none';
      el.appendChild(m);
      const r = m.getBoundingClientRect();
      m.remove();
      return [r.left + 1, r.top + 1];
    });
  }
  function bilerp(c, u, v) {
    const x = (1 - u) * (1 - v) * c[0][0] + u * (1 - v) * c[1][0] + u * v * c[2][0] + (1 - u) * v * c[3][0];
    const y = (1 - u) * (1 - v) * c[0][1] + u * (1 - v) * c[1][1] + u * v * c[2][1] + (1 - u) * v * c[3][1];
    return [x, y];
  }
  function mouthPoint() {
    const r = $('#mouth-marker').getBoundingClientRect();
    return [r.left + r.width / 2, r.top + r.height / 2];
  }
  function boxScreenRect() {
    return $('.f-front').getBoundingClientRect();
  }

  // Luz que sale de la boca de la caja
  const glow = $('#mouth-glow');
  let glowOn = false;
  fx.hook(() => {
    if (!glowOn) return;
    const [x, y] = mouthPoint();
    glow.style.transform = 'translate(' + (x - 300) + 'px,' + (y - 300) + 'px)';
  });
  function setGlow(on, dim) {
    glowOn = on;
    glow.classList.toggle('on', on);
    glow.classList.toggle('dim', !!dim);
  }

  /* ------------------------------------------------------------------------
     Solapas y cinta
     ------------------------------------------------------------------------ */
  const FLAPS = {
    front: $('#flap-front'), back: $('#flap-back'), left: $('#flap-left'), right: $('#flap-right')
  };
  function setFlap(k, deg, delay, dur) {
    const f = FLAPS[k];
    f.style.transitionDelay = (delay || 0) + 'ms';
    f.style.transitionDuration = (dur === undefined ? 900 : dur) + 'ms';
    f.style.setProperty('--a', deg + 'deg');
  }
  function openFlaps(instant) {
    const d = instant ? 0 : 1;
    setFlap('front', -128, 80 * d, 1000 * d);
    setFlap('back', -128, 220 * d, 1000 * d);
    setFlap('left', -112, 520 * d, 850 * d);
    setFlap('right', -112, 620 * d, 850 * d);
    boxEl.classList.add('is-open');
  }
  function closeFlaps() {
    setFlap('left', 90, 0, 650);
    setFlap('right', 90, 120, 650);
    setFlap('back', 90, 420, 800);
    setFlap('front', 90, 560, 800);
    setTimeout(() => { if (state === 'repack') boxEl.classList.remove('is-open'); }, ms(1400));
  }
  function setTapeText(t) {
    $$('[data-tape-text]').forEach((el) => {
      el.textContent = (t + '   •   ').repeat(3);
    });
  }

  /* ------------------------------------------------------------------------
     Polvo (deuda técnica) y cepillo
     ------------------------------------------------------------------------ */
  const dust = [];
  function rng(seed) {
    let a = seed >>> 0;
    return function () {
      a = (a + 0x6d2b79f5) >>> 0;
      let t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function paintDust(d, seed) {
    const { ctx, w, h } = d;
    const R = rng(seed);
    ctx.globalCompositeOperation = 'source-over';
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = 'rgba(122,108,92,0.58)';
    ctx.fillRect(0, 0, w, h);
    // más polvo hacia los bordes
    const g = ctx.createRadialGradient(w / 2, h / 2, Math.min(w, h) * 0.2, w / 2, h / 2, Math.max(w, h) * 0.75);
    g.addColorStop(0, 'rgba(90,78,64,0)');
    g.addColorStop(1, 'rgba(84,72,58,0.42)');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, w, h);
    for (let i = 0; i < 46; i++) {
      const x = R() * w;
      const y = R() * h;
      const r = 16 + R() * 80;
      const light = R() > 0.55;
      const gg = ctx.createRadialGradient(x, y, 0, x, y, r);
      gg.addColorStop(0, light ? 'rgba(186,172,152,0.30)' : 'rgba(70,58,46,0.26)');
      gg.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = gg;
      ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill();
    }
    for (let i = 0; i < (w * h) / 55; i++) {
      ctx.fillStyle = R() > 0.5 ? 'rgba(58,48,38,' + (0.25 + R() * 0.4).toFixed(2) + ')' : 'rgba(214,202,184,' + (0.2 + R() * 0.35).toFixed(2) + ')';
      ctx.fillRect(R() * w, R() * h, 0.6 + R() * 1.6, 0.6 + R() * 1.6);
    }
    ctx.strokeStyle = 'rgba(66,56,46,0.45)';
    ctx.lineWidth = 0.8;
    for (let i = 0; i < 22; i++) {
      const x = R() * w;
      const y = R() * h;
      ctx.beginPath();
      ctx.moveTo(x, y);
      ctx.quadraticCurveTo(x + (R() - 0.5) * 30, y + (R() - 0.5) * 30, x + (R() - 0.5) * 50, y + (R() - 0.5) * 40);
      ctx.stroke();
    }
    // palabras de deuda técnica marcadas en la mugre
    const words = C.POLVO;
    const n = d.face === 'top' ? 5 : d.face === 'front' ? 4 : 2;
    for (let i = 0; i < n; i++) {
      const word = words[(seed * 3 + i * 5) % words.length];
      ctx.save();
      ctx.translate(w * (0.14 + R() * 0.62), h * (0.18 + R() * 0.66));
      ctx.rotate((R() - 0.5) * 0.5);
      ctx.font = '700 ' + (15 + R() * 8).toFixed(0) + 'px "JetBrains Mono", Consolas, monospace';
      ctx.fillStyle = 'rgba(48,36,26,0.55)';
      ctx.fillText(word, 0, 0);
      ctx.restore();
    }
  }
  // Sello de cerdas para borrar el polvo (se dibuja con destination-out)
  const bristle = (function () {
    const c = document.createElement('canvas');
    c.width = 96; c.height = 44;
    const x = c.getContext('2d');
    for (let i = 0; i < 220; i++) {
      const a = Math.random() * Math.PI * 2;
      const rr = Math.sqrt(Math.random());
      const px = 48 + Math.cos(a) * rr * 44;
      const py = 22 + Math.sin(a) * rr * 18;
      x.fillStyle = 'rgba(0,0,0,' + (0.25 + Math.random() * 0.5).toFixed(2) + ')';
      x.beginPath(); x.arc(px, py, 1.5 + Math.random() * 3.2, 0, Math.PI * 2); x.fill();
    }
    return c;
  })();
  function scrub(d, x0, y0, x1, y1, power) {
    const ctx = d.ctx;
    ctx.globalCompositeOperation = 'destination-out';
    const dist = Math.hypot(x1 - x0, y1 - y0);
    const steps = Math.max(1, Math.ceil(dist / 5));
    for (let i = 0; i <= steps; i++) {
      const t = i / steps;
      const x = x0 + (x1 - x0) * t;
      const y = y0 + (y1 - y0) * t;
      ctx.globalAlpha = (power || 0.22) * (0.7 + Math.random() * 0.6);
      ctx.drawImage(bristle, x - 48 + (Math.random() - 0.5) * 6, y - 22 + (Math.random() - 0.5) * 6);
    }
    ctx.globalAlpha = 1;
  }
  function setupDust() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    $$('canvas.dust').forEach((cv, i) => {
      const host = cv.parentElement;
      const w = host.offsetWidth;
      const h = host.offsetHeight;
      cv.width = Math.round(w * dpr);
      cv.height = Math.round(h * dpr);
      const ctx = cv.getContext('2d', { willReadFrequently: true });
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const d = { cv, ctx, w, h, dpr, face: cv.dataset.face, count: cv.dataset.count === '1', host };
      paintDust(d, 11 + i * 7);
      dust.push(d);
    });
  }
  function dustLeft(d) {
    const img = d.ctx.getImageData(0, 0, d.cv.width, d.cv.height).data;
    let n = 0;
    const step = 9;
    for (let y = 0; y < d.cv.height; y += step) {
      for (let x = 0; x < d.cv.width; x += step) {
        if (img[(y * d.cv.width + x) * 4 + 3] > 60) n++;
      }
    }
    return n;
  }
  let dustBase = 0;
  function cleanedFraction() {
    let n = 0;
    dust.forEach((d) => { if (d.count) n += dustLeft(d); });
    return dustBase ? 1 - n / dustBase : 0;
  }

  /* ------------------------------------------------------------------------
     Cursor de herramienta (cepillo / cúter)
     ------------------------------------------------------------------------ */
  const tool = $('#tool-cursor');
  let toolKind = null;
  let toolPos = [0, 0];
  let toolAngle = 0;
  const TOOL = {
    cepillo: { w: 150, h: 98, hx: 75, hy: 90, base: -14 },
    cuter: { w: 128, h: 44, hx: 3, hy: 32, base: -8 }
  };
  function setTool(kind) {
    toolKind = kind;
    tool.innerHTML = kind ? C.HERRAMIENTAS[kind] : '';
    tool.classList.toggle('on', !!kind);
    if (kind) {
      const t = TOOL[kind];
      tool.style.width = t.w + 'px';
      tool.style.height = t.h + 'px';
      tool.style.transformOrigin = t.hx + 'px ' + t.hy + 'px';
    }
  }
  function placeTool(x, y, extraAngle) {
    if (!toolKind) return;
    const t = TOOL[toolKind];
    toolPos = [x, y];
    tool.style.transform = 'translate(' + (x - t.hx) + 'px,' + (y - t.hy) + 'px) rotate(' + (t.base + (extraAngle || 0)) + 'deg)';
  }

  /* ------------------------------------------------------------------------
     Pistas de cada etapa
     ------------------------------------------------------------------------ */
  function hint(text, meter) {
    $('#hint-main').innerHTML = text;
    $('#hint-meter').hidden = !meter;
    $('#stage-hint').classList.toggle('show', !!text);
  }
  function setMeter(f) {
    $('#hint-meter-fill').style.width = Math.round(Math.min(1, Math.max(0, f)) * 100) + '%';
  }

  /* ------------------------------------------------------------------------
     Etapa 1: recepción
     ------------------------------------------------------------------------ */
  async function receive() {
    if (state !== 'intro') return;
    setState('arrival');
    $('#intro-card').classList.add('gone');
    boxEl.classList.add('arrived');
    const shadow = $('#floor-shadow');
    if (!motionOff()) {
      const drop = boxEl.animate([
        { transform: 'translateY(-900px) rotateZ(-6deg) rotateX(8deg)', offset: 0 },
        { transform: 'translateY(0px) rotateZ(0deg) rotateX(0deg)', offset: 0.6, easing: 'cubic-bezier(.2,0,.6,1)' },
        { transform: 'translateY(-34px) rotateZ(1.2deg)', offset: 0.76, easing: 'cubic-bezier(.3,0,.6,1)' },
        { transform: 'translateY(0px) rotateZ(0deg)', offset: 0.88, easing: 'cubic-bezier(.4,0,1,1)' },
        { transform: 'translateY(-6px)', offset: 0.94 },
        { transform: 'translateY(0px)', offset: 1 }
      ], { duration: 1500, easing: 'cubic-bezier(.55,0,1,.45)' });
      shadow.animate([
        { opacity: 0, transform: shadow.style.transform + ' scale(.3)' },
        { opacity: 1, offset: 0.6 },
        { opacity: 0.7, offset: 0.76 },
        { opacity: 1 }
      ], { duration: 1500 });
      await sleep(900);
      landingPuff();
      shake();
      await drop.finished.catch(() => {});
    }
    hint('Llegó la caja del <b>Parcial 1</b>: guía, cinta y la marca de <em>PUNTUAR</em> en la tapa. Viene con el polvo del viaje.', false);
    await sleep(ms(1700));
    if (state === 'arrival') enterClean();
  }
  function landingPuff() {
    const r = boxScreenRect();
    for (let i = 0; i < 9; i++) fx.puff(r.left + (r.width * i) / 8, r.bottom, 7, 'dust');
  }
  function shake() {
    if (motionOff()) return;
    $('#scene3d').animate([
      { transform: 'translate(0,0)' }, { transform: 'translate(-3px,2px)' }, { transform: 'translate(3px,-1px)' },
      { transform: 'translate(-2px,1px)' }, { transform: 'translate(0,0)' }
    ], { duration: 260 });
  }

  /* ------------------------------------------------------------------------
     Etapa 2: limpieza con cepillo
     ------------------------------------------------------------------------ */
  let brushing = false;
  let cleanTimer = null;
  let cleaningDone = false;
  const lastPt = new Map();
  let lastClient = null;
  let travel = 0;

  function enterClean() {
    setState('clean');
    setPose(POSES.clean);
    setTool('cepillo');
    placeTool(window.innerWidth * 0.72, window.innerHeight * 0.7);
    hint('<b>Cepillá la caja:</b> mantené apretado y arrastrá sobre la tapa, el frente y el costado. El polvo es la deuda técnica del Parcial 1.', true);
    setMeter(0);
    dustBase = 0;
    dust.forEach((d) => { if (d.count) dustBase += dustLeft(d); });
    clearInterval(cleanTimer);
    cleanTimer = setInterval(() => {
      if (state !== 'clean' || cleaningDone) return;
      const f = cleanedFraction();
      setMeter(f / 0.68);
      if (f >= 0.68) finishCleaning();
    }, 280);
  }

  dust.length = 0;
  function bindDustEvents() {
    dust.forEach((d) => {
      d.cv.addEventListener('pointermove', (e) => {
        if (state !== 'clean' || !brushing || cleaningDone) return;
        const p = [e.offsetX, e.offsetY];
        const last = lastPt.get(d) || p;
        scrub(d, last[0], last[1], p[0], p[1]);
        lastPt.set(d, p);
      });
      d.cv.addEventListener('pointerleave', () => lastPt.delete(d));
    });
  }
  window.addEventListener('pointerdown', (e) => {
    if (state === 'clean' && !e.target.closest('button')) {
      brushing = true;
      tool.classList.add('pressing');
    }
  });
  window.addEventListener('pointerup', () => {
    brushing = false;
    cutting = false;
    lastPt.clear();
    tool.classList.remove('pressing');
  });
  window.addEventListener('pointermove', (e) => {
    if (!toolKind || autoRunning) return;
    let ang = 0;
    if (lastClient) {
      const vx = e.clientX - lastClient[0];
      const vy = e.clientY - lastClient[1];
      ang = Math.max(-14, Math.min(14, vx * 0.6));
      if (brushing && state === 'clean') {
        travel += Math.hypot(vx, vy);
        if (travel > 12 && e.target.classList && e.target.classList.contains('dust')) {
          travel = 0;
          fx.brushDust(e.clientX, e.clientY, vx, vy);
          fx.brushDust(e.clientX + 20, e.clientY + 4, vx, vy);
        }
      }
    }
    lastClient = [e.clientX, e.clientY];
    placeTool(e.clientX, e.clientY, ang);
  });

  let autoRunning = false;
  async function autoBrush() {
    if (state !== 'clean' || autoRunning || cleaningDone) return;
    autoRunning = true;
    const targets = dust.filter((d) => d.count);
    for (const d of targets) {
      if (cleaningDone) break;
      const corners = cornersOf(d.host, d.w, d.h);
      const rows = Math.ceil(d.h / 24) + 1;
      const path = [];
      for (let r = 0; r < rows; r++) {
        const y = Math.min(d.h, r * 24);
        path.push(r % 2 === 0 ? [-20, y] : [d.w + 20, y]);
        path.push(r % 2 === 0 ? [d.w + 20, y] : [-20, y]);
      }
      const dur = ms(820);
      if (!dur) {
        for (let i = 1; i < path.length; i++) scrub(d, path[i - 1][0], path[i - 1][1], path[i][0], path[i][1], 1);
        continue;
      }
      const segs = [];
      let total = 0;
      for (let i = 1; i < path.length; i++) {
        const L = Math.hypot(path[i][0] - path[i - 1][0], path[i][1] - path[i - 1][1]);
        segs.push({ a: path[i - 1], b: path[i], L, s: total });
        total += L;
      }
      await new Promise((res) => {
        const t0 = performance.now();
        let done = 0;
        const step = (now) => {
          const t = Math.min(1, (now - t0) / dur);
          const target = t * total;
          while (done < target) {
            const pos = Math.min(target, done + 10);
            const seg = segs.find((s) => pos >= s.s && pos <= s.s + s.L) || segs[segs.length - 1];
            const k = (pos - seg.s) / seg.L;
            const k0 = Math.max(0, (done - seg.s) / seg.L);
            const x0 = seg.a[0] + (seg.b[0] - seg.a[0]) * k0;
            const y0 = seg.a[1] + (seg.b[1] - seg.a[1]) * k0;
            const x1 = seg.a[0] + (seg.b[0] - seg.a[0]) * k;
            const y1 = seg.a[1] + (seg.b[1] - seg.a[1]) * k;
            scrub(d, x0, y0, x1, y1, 0.55);
            done = pos;
            if (Math.random() < 0.25) {
              const [sx, sy] = bilerp(corners, Math.max(0, Math.min(1, x1 / d.w)), Math.max(0, Math.min(1, y1 / d.h)));
              fx.brushDust(sx, sy, (seg.b[0] - seg.a[0]) > 0 ? 6 : -6, 0);
            }
          }
          const seg = segs.find((s) => target >= s.s && target <= s.s + s.L) || segs[segs.length - 1];
          const k = (target - seg.s) / seg.L;
          const lx = seg.a[0] + (seg.b[0] - seg.a[0]) * k;
          const ly = seg.a[1] + (seg.b[1] - seg.a[1]) * k;
          const [sx, sy] = bilerp(corners, Math.max(0, Math.min(1, lx / d.w)), Math.max(0, Math.min(1, ly / d.h)));
          placeTool(sx, sy, (seg.b[0] - seg.a[0]) > 0 ? 10 : -10);
          if (t < 1 && state === 'clean') requestAnimationFrame(step);
          else res();
        };
        requestAnimationFrame(step);
      });
    }
    autoRunning = false;
    if (state === 'clean') finishCleaning();
  }

  async function finishCleaning() {
    if (cleaningDone) return;
    cleaningDone = true;
    clearInterval(cleanTimer);
    setMeter(1);
    dust.forEach((d) => d.cv.classList.add('gone'));
    const r = boxScreenRect();
    for (let i = 0; i < 14; i++) fx.puff(r.left + Math.random() * r.width, r.top - 40 + Math.random() * (r.height + 40), 6, 'dust');
    hint('Superficie limpia. El laboratorio de calidad sella la recepción…', false);
    await sleep(ms(700));
    $('#recv-stamp').classList.add('in');
    const s = $('#recv-stamp').getBoundingClientRect();
    fx.puff(s.left + s.width / 2, s.top + s.height / 2, 16, 'ink');
    shake();
    await sleep(ms(1300) || 300);
    if (state === 'clean') enterCut();
  }

  /* ------------------------------------------------------------------------
     Etapa 3: cortar la cinta y abrir
     ------------------------------------------------------------------------ */
  const tapeEl = $('#tape-whole');
  const cutLine = $('#cut-line');
  let cutting = false;
  let cutMin = null;
  let cutMax = null;
  let cutDone = false;

  function enterCut() {
    setState('cut');
    setPose(POSES.cut);
    setTool('cuter');
    hint('<b>Cortá la cinta:</b> apretá sobre la cinta y deslizá el cúter de punta a punta.', true);
    setMeter(0);
  }
  function drawCut() {
    const w = tapeEl.offsetWidth;
    cutLine.style.left = cutMin + 'px';
    cutLine.style.width = Math.max(0, cutMax - cutMin) + 'px';
    const f = (cutMax - cutMin) / w;
    setMeter(f / 0.9);
    if (f >= 0.9) finishCut();
  }
  tapeEl.addEventListener('pointerdown', (e) => {
    if (state !== 'cut' || cutDone) return;
    cutting = true;
    if (cutMin === null) { cutMin = e.offsetX; cutMax = e.offsetX; }
  });
  tapeEl.addEventListener('pointermove', (e) => {
    if (state !== 'cut' || !cutting || cutDone) return;
    const x = e.offsetX;
    if (cutMin === null) { cutMin = x; cutMax = x; }
    const before = cutMax - cutMin;
    cutMin = Math.min(cutMin, x);
    cutMax = Math.max(cutMax, x);
    if (cutMax - cutMin > before + 6) fx.sparks(e.clientX, e.clientY, 2);
    drawCut();
  });
  async function autoCut() {
    if (state !== 'cut' || autoRunning || cutDone) return;
    autoRunning = true;
    const w = tapeEl.offsetWidth;
    const h = tapeEl.offsetHeight;
    const corners = cornersOf(tapeEl, w, h);
    cutMin = 0;
    const dur = ms(1100);
    const t0 = performance.now();
    await new Promise((res) => {
      const step = (now) => {
        const t = dur ? Math.min(1, (now - t0) / dur) : 1;
        cutMax = w * t;
        const [sx, sy] = bilerp(corners, t, 0.5);
        placeTool(sx, sy, 0);
        if (Math.random() < 0.5) fx.sparks(sx, sy, 1);
        drawCut();
        if (t < 1 && !cutDone) requestAnimationFrame(step); else res();
      };
      requestAnimationFrame(step);
    });
    autoRunning = false;
  }
  async function finishCut() {
    if (cutDone) return;
    cutDone = true;
    cutting = false;
    setMeter(1);
    setTool(null);
    hint('', false);
    boxEl.classList.add('tape-split');
    await sleep(ms(260));
    setState('opening');
    setPose(POSES.opening);
    openFlaps(false);
    await sleep(ms(500));
    setGlow(true);
    const [mx, my] = mouthPoint();
    fx.sparks(mx, my, 40);
    await sleep(ms(1100) || 200);
    await emergeItems(false);
    enterHub();
  }

  /* ------------------------------------------------------------------------
     Objetos de la caja: salida y mesa de inspección
     ------------------------------------------------------------------------ */
  const layer = $('#items-layer');
  const items = [];
  const ITEM_W = 112;
  const ITEM_H = 132;

  function buildItems() {
    C.LAMINAS.forEach((l, i) => {
      const el = document.createElement('button');
      el.type = 'button';
      el.className = 'item';
      el.dataset.i = i;
      el.setAttribute('aria-label', 'Ítem ' + (i + 1) + ': ' + l.titulo);
      el.innerHTML =
        '<span class="item-art">' + C.ARTE[l.arte] + '</span>' +
        '<span class="item-tag" style="--tilt:' + (((i * 37) % 7) - 3) + 'deg"><b>' + String(i + 1).padStart(2, '0') + '</b>' + l.etiqueta + '<em class="item-check">✓</em></span>';
      el.addEventListener('click', () => { if (state === 'hub') openSlide(i, { fromItem: true }); });
      layer.appendChild(el);
      items.push(el);
    });
  }
  function ringSlot(i) {
    const W = window.innerWidth;
    const H = window.innerHeight;
    const cx = W / 2;
    const cy = H * 0.515;
    const rx = Math.min(W * 0.41, 640);
    const ry = Math.min(H * 0.3, 290);
    const n = C.LAMINAS.length;
    const a = -Math.PI / 2 + (i / n) * Math.PI * 2;
    return [cx + rx * Math.cos(a), cy + ry * Math.sin(a)];
  }
  function placeAt(el, x, y, rot, sc) {
    el.style.transform = 'translate(' + (x - ITEM_W / 2) + 'px,' + (y - ITEM_H / 2) + 'px) rotate(' + (rot || 0) + 'deg) scale(' + (sc || 1) + ')';
  }
  function layoutRing() {
    items.forEach((el, i) => {
      const [x, y] = ringSlot(i);
      placeAt(el, x, y, ((i * 53) % 9) - 4);
    });
  }

  async function flyOut(el, i, mx, my, hold) {
    const [tx, ty] = ringSlot(i);
    const rot = ((i * 53) % 9) - 4;
    const from = 'translate(' + (mx - ITEM_W / 2) + 'px,' + (my - ITEM_H / 2) + 'px) scale(.3)';
    const up = 'translate(' + (mx - ITEM_W / 2) + 'px,' + (my - ITEM_H / 2 - (hold ? 200 : 150)) + 'px) scale(' + (hold ? 2.1 : 0.8) + ') rotate(' + (rot * 2) + 'deg)';
    const to = 'translate(' + (tx - ITEM_W / 2) + 'px,' + (ty - ITEM_H / 2) + 'px) rotate(' + rot + 'deg) scale(1)';
    el.classList.add('flying');
    if (motionOff()) {
      el.style.transform = to;
      el.style.opacity = 1;
      el.classList.remove('flying');
      return;
    }
    const kf = hold
      ? [
          { transform: from, clipPath: 'inset(0 0 100% 0)', opacity: 0 },
          { transform: up, clipPath: 'inset(0 0 0% 0)', opacity: 1, offset: 0.25, easing: 'cubic-bezier(.2,.8,.2,1)' },
          { transform: up, clipPath: 'inset(0 0 0% 0)', opacity: 1, offset: 0.62, easing: 'cubic-bezier(.5,0,.2,1)' },
          { transform: to, clipPath: 'inset(0 0 0% 0)', opacity: 1 }
        ]
      : [
          { transform: from, clipPath: 'inset(0 0 100% 0)', opacity: 0 },
          { transform: up, clipPath: 'inset(0 0 0% 0)', opacity: 1, offset: 0.32, easing: 'cubic-bezier(.3,.7,.3,1)' },
          { transform: to, clipPath: 'inset(0 0 0% 0)', opacity: 1 }
        ];
    const a = el.animate(kf, { duration: hold ? 2600 : 1150, easing: 'cubic-bezier(.2,.7,.2,1)', fill: 'forwards' });
    if (hold) {
      const cap = $('#hold-caption') || Object.assign(document.createElement('p'), { id: 'hold-caption', className: 'hold-caption' });
      cap.innerHTML = 'Primero sale lo que despachamos: <b>el Manual Técnico del Parcial 1</b>';
      $('#box-scene').appendChild(cap);
      cap.style.left = mx + 'px';
      cap.style.top = (my - 390) + 'px';
      requestAnimationFrame(() => cap.classList.add('in'));
      setTimeout(() => cap.classList.remove('in'), 1500);
    }
    await a.finished.catch(() => {});
    el.style.transform = to;
    el.style.opacity = 1;
    a.cancel();
    el.classList.remove('flying');
    fx.puff(tx, ty + 46, 6, 'dust');
  }
  async function emergeItems(fast) {
    layer.classList.add('show');
    const [mx, my] = mouthPoint();
    const order = [1, 0].concat(C.LAMINAS.map((_, i) => i).filter((i) => i > 1));
    const proms = [];
    let t = 0;
    order.forEach((i, k) => {
      const hold = !fast && k === 0;
      const delay = fast ? k * 70 : (k === 0 ? 0 : 1500 + (k - 1) * 150);
      t = Math.max(t, delay);
      proms.push(sleep(ms(delay)).then(() => {
        fx.sparks(mx, my, 6);
        return flyOut(items[i], i, mx, my, hold);
      }));
    });
    await Promise.all(proms);
  }
  async function flyIn(el, i, mx, my) {
    const cur = getComputedStyle(el).transform;
    const up = 'translate(' + (mx - ITEM_W / 2) + 'px,' + (my - ITEM_H / 2 - 140) + 'px) scale(.8)';
    const to = 'translate(' + (mx - ITEM_W / 2) + 'px,' + (my - ITEM_H / 2) + 'px) scale(.3)';
    if (motionOff()) { el.style.opacity = 0; return; }
    const a = el.animate([
      { transform: cur, clipPath: 'inset(0 0 0% 0)', opacity: 1 },
      { transform: up, clipPath: 'inset(0 0 0% 0)', opacity: 1, offset: 0.6 },
      { transform: to, clipPath: 'inset(0 0 100% 0)', opacity: 0.6 }
    ], { duration: 900, easing: 'cubic-bezier(.5,0,.3,1)', fill: 'forwards' });
    await a.finished.catch(() => {});
    el.style.opacity = 0;
    a.cancel();
  }

  function enterHub() {
    setState('hub');
    setPose(POSES.hub);
    setGlow(true, true);
    layer.classList.add('show');
    $('#hub-hud').hidden = false;
    $('#final-hud').hidden = true;
    hint('', false);
    setTool(null);
    items.forEach((el) => { el.style.opacity = 1; });
    layoutRing();
  }

  // Saltar el ritual (por si algo falla en vivo)
  function skipToHub() {
    if (['hub', 'slides', 'repack', 'final'].includes(state)) return;
    autoRunning = false;
    cleaningDone = true;
    cutDone = true;
    clearInterval(cleanTimer);
    $('#intro-card').classList.add('gone');
    boxEl.classList.add('arrived', 'tape-split');
    boxEl.getAnimations().forEach((a) => a.cancel());
    dust.forEach((d) => d.cv.classList.add('gone'));
    $('#recv-stamp').classList.add('in');
    openFlaps(true);
    setPose(POSES.hub, true);
    setGlow(true, true);
    items.forEach((el) => el.getAnimations().forEach((a) => a.cancel()));
    enterHub();
  }

  /* ------------------------------------------------------------------------
     Informe (láminas)
     ------------------------------------------------------------------------ */
  const desk = $('#desk');
  const scene2d = $('#slides-scene');
  const boxScene = $('#box-scene');
  let slideTimers = [];
  let sheetEl = null;

  function slideLater(t, fn) { slideTimers.push(setTimeout(fn, t)); }
  function clearSlideTimers() { slideTimers.forEach(clearTimeout); slideTimers = []; }

  function countUp(el, target, suf) {
    if (motionOff()) { el.textContent = target + suf; return; }
    const t0 = performance.now();
    const dur = 900;
    const step = (now) => {
      const t = Math.min(1, (now - t0) / dur);
      const e = 1 - Math.pow(1 - t, 3);
      el.textContent = Math.round(target * e) + suf;
      if (t < 1 && el.isConnected) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }

  // Ajusta el contenido para que llene la hoja sin desbordar (proyectores de 768 a 1080 px)
  function fitSheet(sheet) {
    if (!sheet) return;
    const bodyEl = sheet.querySelector('.sheet-body');
    const fit = sheet.querySelector('.fit');
    if (!bodyEl || !fit) return;
    const cs = getComputedStyle(bodyEl);
    const avail = bodyEl.clientHeight - parseFloat(cs.paddingTop) - parseFloat(cs.paddingBottom);
    let z = 1;
    fit.style.zoom = 1;
    for (let k = 0; k < 4; k++) {
      const h = fit.getBoundingClientRect().height;
      if (!h) break;
      const nz = Math.max(0.74, Math.min(1.24, z * (avail * 0.98) / h));
      if (Math.abs(nz - z) < 0.01) break;
      z = nz;
      fit.style.zoom = z.toFixed(3);
    }
    sheet.dataset.zoom = z.toFixed(3);
  }

  const api = {
    zoom: () => (sheetEl ? Number(sheetEl.dataset.zoom) || 1 : 1),
    goTo: (i) => openSlide(i),
    later: (t, fn) => slideLater(t, fn),
    ms,
    fx,
    countUp,
    repack: () => repack()
  };

  function buildDock() {
    const strip = $('#dock-strip');
    C.LAMINAS.forEach((l, i) => {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'dock-item';
      b.title = String(i + 1).padStart(2, '0') + ' · ' + l.titulo;
      b.innerHTML = C.ARTE[l.arte] + '<span>' + (i + 1) + '</span>';
      b.addEventListener('click', () => openSlide(i));
      strip.appendChild(b);
    });
  }
  function syncDock() {
    $$('.dock-item').forEach((b, i) => {
      b.classList.toggle('active', i === current);
      b.classList.toggle('seen', visited.has(i));
    });
    $('#btn-prev').disabled = current === 0;
    $('#btn-next').disabled = current === C.LAMINAS.length - 1;
    items.forEach((el, i) => el.classList.toggle('seen', visited.has(i)));
  }

  function renderSheet(i) {
    const l = C.LAMINAS[i];
    const n = C.LAMINAS.length;
    const a = document.createElement('article');
    a.className = 'sheet';
    a.innerHTML = `
      <header class="sheet-head">
        <div class="plate"><span class="plate-art">${C.ARTE[l.arte]}</span></div>
        <div class="sheet-titles">
          <p class="tagline">Ítem ${String(i + 1).padStart(2, '0')} / ${n} · ${l.fase} · ${l.tema}</p>
          <h2>${l.titulo}</h2>
          <p class="sheet-sub">${l.sub}</p>
        </div>
        <div class="sheet-meta">
          <span class="doc-ref">INF-P2-${String(i + 1).padStart(2, '0')}</span>
          <span class="verif">Verificado</span>
        </div>
      </header>
      <div class="sheet-body"><div class="fit">${l.html()}</div></div>
      <footer class="sheet-foot"><span>Evidencia: <code>${l.evidencia}</code></span><span>${l.etiqueta}</span></footer>`;
    return a;
  }

  async function openSlide(i, opts) {
    opts = opts || {};
    if (i < 0 || i >= C.LAMINAS.length) return;
    if (state === 'repack' || state === 'final' || state === 'opening') return;
    const fromHub = state !== 'slides';
    const dir = i >= current ? 1 : -1;
    clearSlideTimers();
    current = i;
    visited.add(i);
    const nuevo = renderSheet(i);
    const viejo = sheetEl;
    sheetEl = nuevo;

    if (fromHub) {
      setState('slides');
      scene2d.hidden = false;
      desk.innerHTML = '';
      desk.appendChild(nuevo);
      nuevo.classList.add('enter-up');
      requestAnimationFrame(() => { scene2d.classList.add('show'); boxScene.classList.add('away'); });
      // el objeto vuela desde la mesa hasta la placa del informe
      const src = items[i].querySelector('.item-art');
      const plate = nuevo.querySelector('.plate-art');
      if (src && plate && !motionOff()) {
        plate.style.opacity = 0;
        const r0 = src.getBoundingClientRect();
        await sleep(30);
        const r1 = plate.getBoundingClientRect();
        const fly = document.createElement('div');
        fly.className = 'flyer';
        fly.innerHTML = C.ARTE[C.LAMINAS[i].arte];
        fly.style.left = r0.left + 'px';
        fly.style.top = r0.top + 'px';
        fly.style.width = r0.width + 'px';
        fly.style.height = r0.height + 'px';
        body.appendChild(fly);
        const dx = r1.left - r0.left;
        const dy = r1.top - r0.top;
        const sc = r1.width / r0.width;
        const an = fly.animate([
          { transform: 'translate(0,0) scale(1) rotate(0deg)' },
          { transform: 'translate(' + dx * 0.5 + 'px,' + (dy * 0.5 - 60) + 'px) scale(' + (1 + sc) / 1.6 + ') rotate(-8deg)', offset: 0.5 },
          { transform: 'translate(' + dx + 'px,' + dy + 'px) scale(' + sc + ') rotate(0deg)' }
        ], { duration: 820, easing: 'cubic-bezier(.4,0,.2,1)', fill: 'forwards' });
        await an.finished.catch(() => {});
        plate.style.opacity = 1;
        plate.classList.add('pop');
        fly.remove();
      }
    } else {
      desk.appendChild(nuevo);
      nuevo.classList.add(dir > 0 ? 'enter-right' : 'enter-left');
      if (viejo) {
        viejo.classList.remove('enter-right', 'enter-left', 'enter-up');
        viejo.classList.add(dir > 0 ? 'leave-left' : 'leave-right');
        setTimeout(() => viejo.remove(), ms(650) || 0);
      }
      nuevo.querySelector('.plate-art').classList.add('pop');
    }
    try { C.LAMINAS[i].init(nuevo.querySelector('.fit'), api); } catch (err) { console.error(err); }
    fitSheet(nuevo);
    syncDock();
    refreshNotes();
  }

  function goHub() {
    if (state !== 'slides') return;
    clearSlideTimers();
    scene2d.classList.remove('show');
    boxScene.classList.remove('away');
    setTimeout(() => { if (state !== 'slides') scene2d.hidden = true; }, ms(600) || 0);
    enterHub();
    syncDock();
  }

  /* ------------------------------------------------------------------------
     Cierre: re-empaquetar, guía nueva y sello del tribunal
     ------------------------------------------------------------------------ */
  let repacked = false;
  async function repack() {
    if (state === 'slides') {
      goHub();
      await sleep(ms(700) || 50);
    }
    if (state !== 'hub') return;
    setState('repack');
    $('#hub-hud').hidden = true;
    hint('Guardamos todo en la caja…', false);
    const [mx, my] = mouthPoint();
    const order = C.LAMINAS.map((_, i) => i).reverse();
    await Promise.all(order.map((i, k) => sleep(ms(k * 90)).then(() => flyIn(items[i], i, mx, my))));
    layer.classList.remove('show');
    setGlow(false);
    setPose(POSES.opening);
    await sleep(ms(300));
    closeFlaps();
    await sleep(ms(1500) || 100);
    // cinta nueva del Quality Gate
    setTapeText(C.CINTA_P2);
    boxEl.classList.remove('tape-split');
    tapeEl.classList.remove('unroll');
    void tapeEl.offsetWidth;
    tapeEl.classList.add('p2', 'unroll');
    cutLine.style.width = '0px';
    setPose(POSES.cut);
    hint('Cinta nueva: <b>Quality Gate aprobado</b>.', false);
    await sleep(ms(1500) || 100);
    // guía nueva sobre la del Parcial 1
    setPose(POSES.label);
    await sleep(ms(1000));
    $('#label-p2').classList.add('on');
    $('#front-batch').textContent = 'EXPEDICIÓN: PEF-2026-PARCIAL-2';
    await sleep(ms(260));
    const r = $('#label-p2').getBoundingClientRect();
    fx.puff(r.left + r.width / 2, r.bottom, 18, 'dust');
    shake();
    await sleep(ms(1400) || 100);
    repacked = true;
    enterFinal();
  }
  function enterFinal() {
    setState('final');
    setPose(POSES.final);
    hint('', false);
    $('#final-hud').hidden = false;
    $('#grade-dock').hidden = true;
  }

  let pendingGrade = null;
  function buildGradePads() {
    const pads = $('#grade-pads');
    for (let n = 1; n <= 10; n++) {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'grade-pad';
      b.textContent = n;
      b.addEventListener('click', () => {
        pendingGrade = n;
        $$('.grade-pad').forEach((x) => x.classList.toggle('on', Number(x.textContent) === n));
        $('#btn-seal').disabled = false;
      });
      pads.appendChild(b);
    }
  }
  async function sealBox() {
    if (!pendingGrade) return;
    $('#grade-dock').hidden = true;
    $('#final-hud').classList.add('stamping');
    setPose(POSES.stamp);
    await sleep(ms(1200) || 60);
    const seal = $('#seal-p2');
    $('#seal-p2-score').textContent = pendingGrade;
    seal.hidden = false;
    seal.classList.remove('in');
    const r = seal.getBoundingClientRect();
    const cx = r.left + r.width / 2;
    const cy = r.top + r.height / 2;
    const st = $('#rubber-stamp');
    st.innerHTML = C.ARTE.sello;
    if (!motionOff()) {
      st.classList.add('on');
      const a = st.animate([
        { transform: 'translate(' + (cx - 90) + 'px,' + (cy - 520) + 'px) scale(1.15) rotate(-6deg)', opacity: 0, easing: 'cubic-bezier(.2,.7,.3,1)' },
        { transform: 'translate(' + (cx - 90) + 'px,' + (cy - 260) + 'px) scale(1.1) rotate(-3deg)', opacity: 1, offset: 0.45, easing: 'cubic-bezier(.7,0,1,.7)' },
        { transform: 'translate(' + (cx - 90) + 'px,' + (cy - 156) + 'px) scale(.96) rotate(0deg)', opacity: 1, offset: 0.62, easing: 'linear' },
        { transform: 'translate(' + (cx - 90) + 'px,' + (cy - 156) + 'px) scale(.96) rotate(0deg)', opacity: 1, offset: 0.74, easing: 'cubic-bezier(.4,0,.2,1)' },
        { transform: 'translate(' + (cx - 40) + 'px,' + (cy - 560) + 'px) scale(1.1) rotate(8deg)', opacity: 0 }
      ], { duration: 1900, easing: 'linear' });
      await sleep(1180);
      seal.classList.add('in');
      fx.puff(cx, cy, 26, 'ink');
      shake();
      await a.finished.catch(() => {});
      st.classList.remove('on');
    } else {
      seal.classList.add('in');
    }
    $('#final-msg').innerHTML = 'Sellado por el tribunal · <b>nota ' + pendingGrade + '</b> · EXPEDICIÓN PEF-2026-PARCIAL-2';
    $('#final-hud').classList.remove('stamping');
    await sleep(ms(700));
    setPose(POSES.final);
  }

  async function reopen() {
    if (state !== 'final') return;
    setState('opening');
    $('#final-hud').hidden = true;
    setPose(POSES.opening);
    tapeEl.classList.remove('unroll');
    boxEl.classList.add('tape-split');
    fx.sparks(...mouthPoint(), 20);
    openFlaps(false);
    await sleep(ms(700));
    setGlow(true);
    items.forEach((el) => { el.style.opacity = 0; });
    await emergeItems(true);
    enterHub();
  }

  // Rotar la caja con el mouse en el cierre
  (function () {
    let drag = null;
    boxScene.addEventListener('pointerdown', (e) => {
      if (state !== 'final' || e.target.closest('button, .grade-dock')) return;
      drag = { x: e.clientX, y: e.clientY, rx: pose.rx, ry: pose.ry };
      rig.classList.add('no-trans');
    });
    window.addEventListener('pointermove', (e) => {
      if (!drag) return;
      const p = Object.assign({}, pose, {
        ry: drag.ry + (e.clientX - drag.x) * 0.35,
        rx: Math.max(-80, Math.min(10, drag.rx - (e.clientY - drag.y) * 0.3))
      });
      rig.style.setProperty('--rx', p.rx + 'deg');
      rig.style.setProperty('--ry', p.ry + 'deg');
      pose = p;
    });
    window.addEventListener('pointerup', () => {
      if (!drag) return;
      drag = null;
      rig.classList.remove('no-trans');
    });
  })();

  /* ------------------------------------------------------------------------
     Barra: cronómetro, notas, ayuda, pantalla completa
     ------------------------------------------------------------------------ */
  let timerLeft = 15 * 60;
  let timerId = null;
  function fmtTime(s) {
    const m = Math.floor(Math.abs(s) / 60);
    const r = Math.abs(s) % 60;
    return (s < 0 ? '−' : '') + String(m).padStart(2, '0') + ':' + String(r).padStart(2, '0');
  }
  function toggleTimer() {
    const b = $('#btn-timer');
    if (timerId) {
      clearInterval(timerId);
      timerId = null;
      b.classList.remove('running');
      return;
    }
    b.classList.add('running');
    timerId = setInterval(() => {
      timerLeft -= 1;
      $('#timer-display').textContent = fmtTime(timerLeft);
      b.classList.toggle('warn', timerLeft <= 120 && timerLeft > 0);
      b.classList.toggle('over', timerLeft <= 0);
    }, 1000);
  }
  function refreshNotes() {
    const nb = $('#notes-body');
    if (!nb) return;
    if (state === 'slides') {
      const l = C.LAMINAS[current];
      nb.innerHTML = '<p class="notes-k">Ítem ' + String(current + 1).padStart(2, '0') + ' · ' + l.etiqueta + '</p><p>' + l.notas + '</p>';
    } else {
      const k = state === 'final' ? 'final' : state;
      nb.innerHTML = '<p class="notes-k">Ritual · ' + k + '</p><p>' + (C.NOTAS_RITUAL[k] || '') + '</p>';
    }
  }
  function toggleNotes() { $('#notes-panel').hidden = !$('#notes-panel').hidden; refreshNotes(); }
  function toggleHelp(force) {
    const m = $('#help-modal');
    m.hidden = force === undefined ? !m.hidden : !force;
  }
  function toggleFull() {
    if (!document.fullscreenElement) document.documentElement.requestFullscreen().catch(() => {});
    else document.exitFullscreen().catch(() => {});
  }

  /* ------------------------------------------------------------------------
     Teclado
     ------------------------------------------------------------------------ */
  document.addEventListener('keydown', (e) => {
    if (e.target.matches && e.target.matches('input, textarea, select')) return;
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    const k = e.key;
    if (!$('#help-modal').hidden) {
      if (k === 'Escape' || k === 'h' || k === 'H' || k === '?') toggleHelp(false);
      return;
    }
    if (k === 'h' || k === 'H' || k === '?') { toggleHelp(true); return; }
    if (k === 't' || k === 'T') { toggleTimer(); return; }
    if (k === 'n' || k === 'N') { toggleNotes(); return; }
    if (k === 'm' || k === 'M') { toggleMotion(); return; }
    if (k === 'f' || k === 'F') { toggleFull(); return; }
    if (k === 's' || k === 'S') { skipToHub(); return; }

    const avanzar = k === 'Enter' || k === 'ArrowRight' || k === ' ' || k === 'PageDown';
    switch (state) {
      case 'intro':
        if (avanzar) { e.preventDefault(); receive(); }
        break;
      case 'clean':
        if (avanzar) { e.preventDefault(); autoBrush(); }
        break;
      case 'cut':
        if (avanzar) { e.preventDefault(); autoCut(); }
        break;
      case 'hub':
        if (avanzar) { e.preventDefault(); openSlide(visited.size ? current : 0, { fromItem: true }); }
        else if (k === 'p' || k === 'P') repack();
        else if (/^[1-9]$/.test(k)) openSlide(Number(k) - 1, { fromItem: true });
        break;
      case 'slides':
        if (k === 'ArrowRight' || k === ' ' || k === 'PageDown') { e.preventDefault(); openSlide(Math.min(C.LAMINAS.length - 1, current + 1)); }
        else if (k === 'ArrowLeft' || k === 'PageUp') { e.preventDefault(); openSlide(Math.max(0, current - 1)); }
        else if (k === 'Home') openSlide(0);
        else if (k === 'End') openSlide(C.LAMINAS.length - 1);
        else if (k === 'Escape' || k === '0') goHub();
        else if (k === 'p' || k === 'P') repack();
        else if (/^[1-9]$/.test(k)) openSlide(Number(k) - 1);
        break;
      case 'final':
        if (k === 'r' || k === 'R') reopen();
        else if (k === 'Enter' && $('#grade-dock').hidden) $('#btn-puntuar').click();
        break;
      default:
        break;
    }
  });

  /* ------------------------------------------------------------------------
     Botones
     ------------------------------------------------------------------------ */
  $('#btn-receive').addEventListener('click', receive);
  $('#btn-auto').addEventListener('click', () => { if (state === 'clean') autoBrush(); else if (state === 'cut') autoCut(); });
  $('#btn-skip').addEventListener('click', skipToHub);
  $('#btn-start').addEventListener('click', () => openSlide(visited.size ? current : 0, { fromItem: true }));
  $('#btn-repack-hub').addEventListener('click', repack);
  $('#btn-prev').addEventListener('click', () => openSlide(current - 1));
  $('#btn-next').addEventListener('click', () => openSlide(current + 1));
  $('#btn-hub').addEventListener('click', goHub);
  $('#btn-notes').addEventListener('click', toggleNotes);
  $('#btn-notes-close').addEventListener('click', toggleNotes);
  $('#btn-full').addEventListener('click', toggleFull);
  $('#btn-help').addEventListener('click', () => toggleHelp(true));
  $('#btn-help-close').addEventListener('click', () => toggleHelp(false));
  $('#help-modal').addEventListener('click', (e) => { if (e.target.id === 'help-modal') toggleHelp(false); });
  $('#btn-timer').addEventListener('click', toggleTimer);
  $('#btn-motion').addEventListener('click', toggleMotion);
  $('#btn-puntuar').addEventListener('click', () => { if (state === 'final') { $('#grade-dock').hidden = false; setPose(POSES.label); } });
  $('#btn-grade-cancel').addEventListener('click', () => { $('#grade-dock').hidden = true; setPose(POSES.final); });
  $('#btn-seal').addEventListener('click', sealBox);
  $('#btn-reopen').addEventListener('click', reopen);

  window.addEventListener('resize', () => {
    setPose(pose, true);
    if (state === 'hub' || state === 'slides') layoutRing();
    if (state === 'slides') fitSheet(sheetEl);
  });

  /* ------------------------------------------------------------------------
     Arranque
     ------------------------------------------------------------------------ */
  function init() {
    syncMotionButton();
    reduceMq.addEventListener && reduceMq.addEventListener('change', syncMotionButton);
    setTapeText(C.CINTA_P1);
    $$('.barcode').forEach((b) => {
      let s = '';
      for (let i = 0; i < 34; i++) s += '<i style="width:' + (1 + ((i * 7) % 4)) + 'px"></i>';
      b.innerHTML = s;
    });
    $('.side-barcode').innerHTML = Array.from({ length: 16 }, (_, i) => '<i style="height:' + (2 + ((i * 5) % 4)) + 'px"></i>').join('');
    const nota = Number(new URLSearchParams(location.search).get('notaP1'));
    if (nota >= 1 && nota <= 10) {
      $('#seal-p1-score').textContent = nota;
      $('#seal-p1').hidden = false;
      $('#seal-p1').classList.add('in');
    }
    buildItems();
    buildDock();
    buildGradePads();
    setPose(POSES.intro, true);
    setupDust();
    bindDustEvents();
    setState('intro');
  }

  const fontsReady = document.fonts && document.fonts.ready ? Promise.race([document.fonts.ready, sleep(1500)]) : Promise.resolve();
  fontsReady.then(init);
})();
