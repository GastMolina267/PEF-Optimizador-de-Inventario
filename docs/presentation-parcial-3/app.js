/* ==========================================================================
   PRESENTACIÓN INTERACTIVA — TERCER PARCIAL PEF (OPCIÓN 6)
   La caja del Parcial 2 pasa por la aduana de Integración Continua:
   cinta transportadora → 7 puestos (= 7 etapas del pipeline) → oficina de
   aduana (informe) → despacho a main → sello del tribunal.
   ========================================================================== */
(function () {
  'use strict';

  const C = window.PEF3_CONTENIDO;
  const $ = (s, r) => (r || document).querySelector(s);
  const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
  const html = document.documentElement;
  const body = document.body;

  /* ------------------------------------------------------------------------
     Movimiento
     ------------------------------------------------------------------------ */
  const MOTION_KEY = 'pef3-force-motion';
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
  const STEP_OF = { intro: 'intro', aduana: 'aduana', hub: 'hub', slides: 'hub', despacho: 'final', final: 'final' };
  const STEP_ORDER = ['intro', 'aduana', 'hub', 'final'];

  function setState(s) {
    state = s;
    body.className = body.className.replace(/\bstate-\S+/g, '').trim() + ' state-' + s;
    body.classList.toggle('theme-light', s === 'slides');
    body.classList.toggle('theme-dark', s !== 'slides');
    const idx = STEP_ORDER.indexOf(STEP_OF[s]);
    $$('#ritual-steps li').forEach((li, i) => {
      li.classList.toggle('active', i === idx);
      li.classList.toggle('done', idx > -1 && i < idx);
    });
    $('#brand-sub').textContent = s === 'slides'
      ? 'Informe de aduana — Tercer Parcial (Opción 6)'
      : 'Aduana de Integración Continua — Tercer Parcial (Opción 6)';
    refreshNotes();
  }

  /* ------------------------------------------------------------------------
     FX: chispas, tinta y motas de luz
     ------------------------------------------------------------------------ */
  const fx = (function () {
    const cv = $('#fx-canvas');
    const ctx = cv.getContext('2d');
    let W = 0;
    let H = 0;
    const parts = [];
    const motes = [];
    const hooks = [];
    function resize() {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
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
    for (let i = 0; i < 40; i++) motes.push({ x: Math.random(), y: Math.random(), r: 0.6 + Math.random() * 1.8, v: 0.00004 + Math.random() * 0.00012, p: Math.random() * 6 });
    const PAL = {
      dust: ['140,124,104', '176,160,138', '98,86,72'],
      light: ['150,135,115', '190,176,156'],
      ink: ['190,18,60', '159,18,57', '225,29,72'],
      green: ['34,197,94', '134,239,172', '21,128,61'],
      spark: ['252,211,77', '245,158,11', '255,247,237', '253,186,116']
    };
    function puff(x, y, n, kind) {
      if (motionOff()) return;
      const pal = PAL[kind || 'dust'];
      for (let i = 0; i < n; i++) {
        const a = Math.random() * Math.PI * 2;
        const sp = 0.4 + Math.random() * 1.8;
        parts.push({ x, y, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp - 0.4, g: 0.04, life: 0, max: 40 + Math.random() * 40, r: 1 + Math.random() * 2.6, c: pal[(Math.random() * pal.length) | 0], soft: kind === 'dust' || kind === 'light' });
      }
    }
    function sparks(x, y, n, kind) {
      if (motionOff()) return;
      const pal = PAL[kind || 'spark'];
      for (let i = 0; i < n; i++) {
        const a = -Math.PI / 2 + (Math.random() - 0.5) * Math.PI * 1.4;
        const sp = 1.5 + Math.random() * 3.6;
        parts.push({ x, y, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp, g: 0.06, life: 0, max: 30 + Math.random() * 40, r: 1 + Math.random() * 1.8, c: pal[(Math.random() * pal.length) | 0], spark: true });
      }
    }
    function loop() {
      ctx.clearRect(0, 0, W, H);
      hooks.forEach((h) => h());
      if (body.classList.contains('theme-dark') && !motionOff()) {
        for (const m of motes) {
          m.y -= m.v * 16;
          m.p += 0.01;
          if (m.y < -0.05) { m.y = 1.05; m.x = Math.random(); }
          const x = (0.25 + m.x * 0.5) * W + Math.sin(m.p) * 12;
          ctx.fillStyle = 'rgba(255,226,180,0.14)';
          ctx.beginPath(); ctx.arc(x, m.y * H, m.r, 0, Math.PI * 2); ctx.fill();
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
        const a = (1 - t) * (p.spark ? 1 : 0.8);
        ctx.fillStyle = 'rgba(' + p.c + ',' + a.toFixed(3) + ')';
        ctx.beginPath(); ctx.arc(p.x, p.y, p.soft ? p.r * (1 + t * 2) : p.r, 0, Math.PI * 2); ctx.fill();
      }
      requestAnimationFrame(loop);
    }
    requestAnimationFrame(loop);
    return { puff, sparks, hook: (f) => hooks.push(f) };
  })();

  /* ------------------------------------------------------------------------
     Caja 3D: poses y geometría en pantalla
     ------------------------------------------------------------------------ */
  const rig = $('#rig');
  const boxEl = $('#box');
  const belt = $('#belt');
  const POSES = {
    intro: { rx: -16, ry: -26, s: 0.86, tx: 270, ty: 20 },
    aduana: { rx: -17, ry: -30, s: 0.84, tx: -210, ty: 14 },
    hub: { rx: -32, ry: -26, s: 0.6, tx: 0, ty: 40 },
    label: { rx: -12, ry: -14, s: 1.05, tx: 0, ty: 0 },
    final: { rx: -26, ry: -32, s: 0.9, tx: 0, ty: 20 },
    stamp: { rx: -62, ry: -4, s: 1.12, tx: 0, ty: 50 }
  };
  let pose = Object.assign({}, POSES.intro);
  function viewScale() { return Math.max(0.55, Math.min(1, window.innerHeight / 880, window.innerWidth / 1380)); }
  function setPose(p, instant) {
    pose = Object.assign({ tx: 0, ty: 0 }, p);
    const k = viewScale();
    if (instant) rig.classList.add('no-trans');
    rig.style.setProperty('--rx', pose.rx + 'deg');
    rig.style.setProperty('--ry', pose.ry + 'deg');
    rig.style.setProperty('--s', (pose.s * k).toFixed(3));
    rig.style.setProperty('--tx', (pose.tx || 0) * k + 'px');
    rig.style.setProperty('--ty', (pose.ty || 0) * k + 'px');
    if (instant) { void rig.offsetWidth; rig.classList.remove('no-trans'); }
  }
  function bounds() {
    const rs = ['.f-front', '.f-right', '.f-left', '.tape-plane'].map((s) => $(s, boxEl).getBoundingClientRect()).filter((r) => r.width > 0);
    const l = Math.min(...rs.map((r) => r.left));
    const t = Math.min(...rs.map((r) => r.top));
    const r = Math.max(...rs.map((x) => x.right));
    const b = Math.max(...rs.map((x) => x.bottom));
    return { left: l, top: t, right: r, bottom: b, width: r - l, height: b - t, cx: (l + r) / 2, cy: (t + b) / 2 };
  }
  function moveBelt(dur) {
    belt.classList.add('moving');
    clearTimeout(moveBelt.t);
    moveBelt.t = setTimeout(() => belt.classList.remove('moving'), dur);
  }
  function shake() {
    if (motionOff()) return;
    $('#scene3d').animate([{ transform: 'translate(0,0)' }, { transform: 'translate(-3px,2px)' }, { transform: 'translate(3px,-1px)' }, { transform: 'translate(0,0)' }], { duration: 240 });
  }

  /* ------------------------------------------------------------------------
     Portal, panel del puesto y recorrido
     ------------------------------------------------------------------------ */
  const portal = $('#portal');
  const efx = $('#efx');
  let stIndex = -1;
  let stBusy = false;
  const stDone = new Array(7).fill(false);
  let autoRun = false;

  function buildTrack() {
    $('#track').innerHTML = C.PUESTOS.map((p, i) => `
      <div class="tk-node" data-i="${i}"><span class="tk-dot">${i + 1}</span><span class="tk-name">${C.ETAPAS_CORTAS[i]}</span></div>`).join('<span class="tk-line"></span>');
  }
  function syncTrack() {
    $$('.tk-node').forEach((n, i) => {
      n.classList.toggle('active', i === stIndex);
      n.classList.toggle('done', stDone[i]);
    });
    $$('.tk-line').forEach((l, i) => l.classList.toggle('done', stDone[i]));
  }
  function placePortal() { /* el arco vive dentro del rig 3D: sigue solo la pose de la caja */ }
  async function portalIn(i) {
    $('#portal-name').textContent = 'PUESTO ' + (i + 1) + ' · ' + C.PUESTOS[i].n.toUpperCase();
    portal.classList.remove('passed');
    placePortal();
    portal.classList.add('on');
    if (motionOff()) return;
    await portal.animate([{ transform: 'translateX(1500px)', opacity: 0 }, { transform: 'translateX(1200px)', opacity: 1, offset: 0.15 }, { transform: 'translateX(0)', opacity: 1 }], { duration: 800, easing: 'cubic-bezier(.2,.8,.2,1)' }).finished.catch(() => {});
  }
  async function portalOut() {
    if (!portal.classList.contains('on')) return;
    if (!motionOff()) {
      await portal.animate([{ transform: 'translateX(0)', opacity: 1 }, { transform: 'translateX(-1200px)', opacity: 1, offset: 0.85 }, { transform: 'translateX(-1500px)', opacity: 0 }], { duration: 700, easing: 'cubic-bezier(.6,0,.8,.4)' }).finished.catch(() => {});
    }
    portal.classList.remove('on');
  }
  function renderPanel(i) {
    const p = C.PUESTOS[i];
    $('#sp-eyebrow').textContent = p.e;
    $('#sp-title').textContent = p.n;
    $('#sp-checks').innerHTML = p.c.map((c) => `
      <li><span class="sp-tick"></span><div><b>${c[0]}</b><code>${c[1]}</code></div><span class="sp-res">${c[2]}</span></li>`).join('');
    $('#btn-next-station').innerHTML = (i === 6 ? 'Ir a la oficina de aduana' : 'Siguiente puesto') + ' <kbd>Enter</kbd>';
  }
  async function tickChecks() {
    const lis = $$('#sp-checks li');
    for (const li of lis) {
      li.classList.add('run');
      await sleep(ms(380) || 20);
      li.classList.remove('run');
      li.classList.add('ok');
    }
  }

  /* ------------------------------------------------------------------------
     Efectos de cada puesto
     ------------------------------------------------------------------------ */
  const SIL = [
    '<rect x="6" y="8" width="26" height="34" rx="2"/>', '<path d="M8 6 l22 -3 4 36 -22 3z"/>', '<rect x="4" y="12" width="32" height="22" rx="3"/>',
    '<circle cx="20" cy="18" r="13"/><path d="M14 30 l-4 12 6 -4 4 6 2 -12"/>', '<path d="M15 4 h10 v12 l10 22 a4 4 0 0 1 -4 6 h-22 a4 4 0 0 1 -4 -6 l10 -22z"/>',
    '<circle cx="12" cy="34" r="6"/><circle cx="26" cy="38" r="6"/><path d="M16 30 L36 8 M22 32 L38 22"/>', '<circle cx="18" cy="18" r="12"/><path d="M27 27 l10 10"/>',
    '<rect x="8" y="10" width="24" height="30"/><rect x="4" y="4" width="32" height="9" rx="4"/>', '<rect x="4" y="8" width="32" height="26" rx="4"/>',
    '<rect x="4" y="4" width="9" height="9"/><rect x="15" y="4" width="9" height="9"/><rect x="26" y="4" width="9" height="9"/><rect x="4" y="15" width="9" height="9"/><rect x="15" y="15" width="9" height="9"/><rect x="26" y="15" width="9" height="9"/>',
    '<path d="M20 10 C12 6 6 6 2 8 V34 C6 32 12 32 20 36 C28 32 34 32 38 34 V8 C34 6 28 6 20 10Z"/>', '<rect x="4" y="6" width="32" height="24" rx="1"/><circle cx="30" cy="30" r="6"/>',
    '<circle cx="20" cy="8" r="6"/><rect x="16" y="13" width="8" height="12"/><rect x="6" y="25" width="28" height="8" rx="2"/>'
  ];
  function efxBox(cls, b, extra) {
    const d = document.createElement('div');
    d.className = 'fx-' + cls;
    Object.assign(d.style, extra || {});
    if (state === 'aduana') efx.appendChild(d); // si se saltó la inspección, el efecto no se muestra
    return d;
  }
  function clearEfx() { efx.innerHTML = ''; boxEl.classList.remove('xray', 'scanning'); portal.classList.remove('rail'); }

  const EFECTOS = {
    async ticket() {
      $('#ingreso-ticket').classList.add('on');
      await sleep(ms(300));
      const r = $('#ingreso-ticket').getBoundingClientRect();
      fx.sparks(r.left + r.width / 2, r.top + r.height / 2, 16);
    },
    async precinto() {
      $('#precinto').classList.add('on');
      await sleep(ms(300));
      const r = $('#precinto').getBoundingClientRect();
      fx.sparks(r.left + r.width / 2, r.top, 14);
    },
    async rayos() {
      const b = bounds();
      const dog = efxBox('dog', b, { left: (b.left - 120) + 'px', top: (b.bottom - 70) + 'px' });
      dog.innerHTML = C.ARTE.perro + '<span class="sniff-q">sniff</span>';
      if (!motionOff()) {
        dog.animate([
          { transform: 'translateX(0)' },
          { transform: 'translateX(' + (b.width + 120) + 'px)', offset: 0.7 },
          { transform: 'translateX(' + (b.width + 160) + 'px)' }
        ], { duration: 3400, easing: 'ease-in-out', fill: 'forwards' });
        // 1) el láser recorre la caja en 3D (ida y vuelta)
        portal.classList.add('rail');
        boxEl.classList.add('scanning');
        await sleep(2700);
        boxEl.classList.remove('scanning');
        if (state !== 'aduana') return;
      }
      // 2) la pantalla de rayos X muestra lo que encontró
      const nb = bounds();
      const scan = efxBox('scan', nb, { left: nb.left + 'px', top: nb.top + 'px', width: nb.width + 'px', height: nb.height + 'px' });
      scan.innerHTML = '<div class="sil-grid">' + SIL.map((x, k) => '<svg viewBox="0 0 40 46" style="--i:' + k + '">' + x + '</svg>').join('') + '</div><span class="scan-lbl">13 objetos del Parcial 2 · sin contrabando</span>';
      await sleep(ms(1500) || 50);
      dog.classList.add('ok');
      scan.classList.add('done');
    },
    async muestras() {
      const b = bounds();
      const g = efxBox('gauge', b, { left: (b.right + 26) + 'px', top: (b.cy - 90) + 'px' });
      g.innerHTML = '<svg viewBox="0 0 120 120"><circle class="g-bg" cx="60" cy="60" r="50"/><circle class="g-thr" cx="60" cy="60" r="50"/><circle class="g-fg" cx="60" cy="60" r="50"/></svg><div class="g-c"><b>0 %</b><span>cobertura</span><em>0 tests</em></div>';
      const fg = g.querySelector('.g-fg');
      const n = g.querySelector('b');
      const t = g.querySelector('em');
      const t0 = performance.now();
      const dur = ms(1600) || 1;
      await new Promise((res) => {
        const step = (now) => {
          const k = Math.min(1, (now - t0) / dur);
          const e = 1 - Math.pow(1 - k, 3);
          fg.style.strokeDashoffset = String(314.16 * (1 - 0.9 * e));
          n.textContent = Math.round(90 * e) + ' %';
          t.textContent = Math.round(198 * e) + ' tests ✓';
          if (k < 1) requestAnimationFrame(step); else res();
        };
        requestAnimationFrame(step);
      });
      fx.sparks(b.cx, b.top, 18, 'green');
    },
    async manifiesto() {
      const b = bounds();
      const m = efxBox('manifest', b, { left: Math.max(12, b.left - 260) + 'px', top: Math.max(70, b.top - 30) + 'px' });
      m.innerHTML = '<p class="mf-h">MANIFIESTO DE CARGA · SPHINX</p>' +
        ['Descripción funcional', 'Arquitectura', 'Instalación', 'Diseño técnico', 'API y contratos', 'Pruebas', 'Rendimiento', 'Seguridad', 'Mantenimiento'].map((s, i) => '<p class="mf-l" style="--i:' + i + '"><span>' + (i + 1) + '</span>' + s + '<em>✓</em></p>').join('') +
        '<p class="mf-f">-W: 0 advertencias · pip-audit: 0 vulnerabilidades</p>';
      await sleep(ms(1900) || 50);
    },
    async balanza() {
      const b = bounds();
      const s = efxBox('scale', b, { left: (b.right + 22) + 'px', top: (b.cy - 80) + 'px' });
      s.innerHTML = '<div class="sc-disp"><span>PICO HEAP</span><b>0,00 MB</b><i><u></u></i><em>límite 10 MB</em></div><div class="sc-watch"><span>⏱</span><b>— ns</b><em>búsqueda hash</em></div>';
      const v = s.querySelector('.sc-disp b');
      const bar = s.querySelector('.sc-disp u');
      const w = s.querySelector('.sc-watch b');
      const t0 = performance.now();
      const dur = ms(1400) || 1;
      await new Promise((res) => {
        const step = (now) => {
          const k = Math.min(1, (now - t0) / dur);
          const e = 1 - Math.pow(1 - k, 3);
          v.textContent = (1.03 * e).toFixed(2).replace('.', ',') + ' MB';
          bar.style.width = (10.3 * e) + '%';
          w.textContent = Math.round(71 + (1 - e) * 900) + ' ns';
          if (k < 1) requestAnimationFrame(step); else res();
        };
        requestAnimationFrame(step);
      });
      s.classList.add('ok');
    },
    async semaforo() {
      const b = bounds();
      const l = efxBox('light', b, { left: (b.right + 26) + 'px', top: (b.top - 10) + 'px' });
      l.innerHTML = '<i class="r"></i><i class="a"></i><i class="v"></i>';
      const lamps = l.querySelectorAll('i');
      for (const [k, d] of [[0, 380], [1, 380], [2, 0]]) {
        lamps.forEach((x, j) => x.classList.toggle('on', j === k));
        await sleep(ms(d));
      }
      await sleep(ms(300));
      $('#customs-stamp').classList.add('in');
      await sleep(ms(260));
      const r = $('#customs-stamp').getBoundingClientRect();
      fx.puff(r.left + r.width / 2, r.top + r.height / 2, 22, 'green');
      fx.sparks(r.left + r.width / 2, r.top, 26);
      shake();
    }
  };

  async function runStation(i) {
    stIndex = i;
    stBusy = true;
    syncTrack();
    renderPanel(i);
    $('#station-panel').classList.add('show');
    await portalIn(i);
    const efecto = EFECTOS[C.PUESTOS[i].fx];
    await Promise.all([efecto ? efecto() : Promise.resolve(), tickChecks()]);
    stDone[i] = true;
    $('#portal-led').classList.add('ok');
    portal.classList.add('passed');
    syncTrack();
    stBusy = false;
    refreshNotes();
  }
  async function nextStation() {
    if (state !== 'aduana' || stBusy) return;
    if (stIndex >= 6) { enterHub(); return; }
    stBusy = true;
    $('#portal-led').classList.remove('ok');
    clearEfx();
    portal.classList.remove('rail');
    await portalOut();
    if (!motionOff()) {
      moveBelt(900);
      boxEl.animate([{ transform: 'translateX(0) rotateZ(0)' }, { transform: 'translateX(0) rotateZ(-0.8deg)', offset: 0.3 }, { transform: 'translateX(0) rotateZ(0.5deg)', offset: 0.7 }, { transform: 'translateX(0) rotateZ(0)' }], { duration: 900 });
      await sleep(700);
    }
    stBusy = false;
    await runStation(stIndex + 1);
  }
  async function runAll() {
    if (state !== 'aduana' || autoRun) return;
    autoRun = true;
    $('#btn-run-all').disabled = true;
    while (state === 'aduana' && stIndex < 6) {
      while (stBusy) await sleep(100);
      await nextStation();
      await sleep(ms(900));
    }
    autoRun = false;
    $('#btn-run-all').disabled = false;
  }

  /* ------------------------------------------------------------------------
     Presentación de la caja: llega por la cinta
     ------------------------------------------------------------------------ */
  async function presentar() {
    if (state !== 'intro') return;
    setState('aduana');
    $('#intro-card').classList.add('gone');
    setPose(POSES.aduana);
    boxEl.classList.add('arrived');
    if (!motionOff()) {
      moveBelt(1400);
      boxEl.animate([{ transform: 'rotateZ(0)' }, { transform: 'rotateZ(-0.8deg)', offset: 0.3 }, { transform: 'rotateZ(0.6deg)', offset: 0.7 }, { transform: 'rotateZ(0)' }], { duration: 1300 });
      await sleep(1350);
      shake();
    }
    $('#track').classList.add('show');
    await runStation(0);
  }

  /* ------------------------------------------------------------------------
     Oficina de aduana (objetos del informe)
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
      el.setAttribute('aria-label', 'Ítem ' + (i + 1) + ': ' + l.titulo);
      el.innerHTML = '<span class="item-art">' + C.ARTE[l.arte] + '</span><span class="item-tag" style="--tilt:' + (((i * 37) % 7) - 3) + 'deg"><b>' + String(i + 1).padStart(2, '0') + '</b>' + l.etiqueta + '<em class="item-check">✓</em></span>';
      el.addEventListener('click', () => { if (state === 'hub') openSlide(i); });
      layer.appendChild(el);
      items.push(el);
    });
  }
  function ringSlot(i) {
    const W = window.innerWidth;
    const H = window.innerHeight;
    const n = C.LAMINAS.length;
    const a = -Math.PI / 2 + (i / n) * Math.PI * 2;
    return [W / 2 + Math.min(W * 0.41, 640) * Math.cos(a), H * 0.515 + Math.min(H * 0.3, 290) * Math.sin(a)];
  }
  function placeItem(el, i) {
    const [x, y] = ringSlot(i);
    el.style.transform = 'translate(' + (x - ITEM_W / 2) + 'px,' + (y - ITEM_H / 2) + 'px) rotate(' + (((i * 53) % 9) - 4) + 'deg)';
  }
  function layoutRing() { items.forEach((el, i) => placeItem(el, i)); }
  async function dropItems() {
    layer.classList.add('show');
    await Promise.all(items.map((el, i) => sleep(ms(i * 90)).then(async () => {
      placeItem(el, i);
      const to = el.style.transform;
      el.style.opacity = 1;
      if (motionOff()) return;
      const [x, y] = ringSlot(i);
      await el.animate([
        { transform: 'translate(' + (x - ITEM_W / 2) + 'px,' + (y - ITEM_H / 2 - 260) + 'px) rotate(' + (i % 2 ? 14 : -14) + 'deg)', opacity: 0 },
        { transform: to, opacity: 1, offset: 0.8 },
        { transform: to + ' translateY(-8px)', offset: 0.9 },
        { transform: to, opacity: 1 }
      ], { duration: 760, easing: 'cubic-bezier(.3,.7,.3,1)' }).finished.catch(() => {});
      fx.puff(x, y + 50, 5, 'light');
    })));
  }
  async function enterHub(instant) {
    clearEfx();
    portal.classList.remove('on');
    $('#station-panel').classList.remove('show');
    $('#track').classList.remove('show');
    $('#final-hud').hidden = true;
    setState('hub');
    setPose(POSES.hub, !!instant);
    $('#hub-hud').hidden = false;
    if (!layer.classList.contains('show')) {
      await sleep(instant ? 0 : ms(500));
      if (instant || motionOff()) { layer.classList.add('show'); items.forEach((el) => { el.style.opacity = 1; }); layoutRing(); } else await dropItems();
    } else {
      items.forEach((el) => { el.style.opacity = 1; });
      layoutRing();
    }
  }
  function skipToHub() {
    if (!['intro', 'aduana'].includes(state)) return;
    $('#intro-card').classList.add('gone');
    boxEl.classList.add('arrived');
    boxEl.getAnimations().forEach((a) => a.cancel());
    ['#ingreso-ticket', '#precinto'].forEach((s) => $(s).classList.add('on'));
    $('#customs-stamp').classList.add('in');
    stDone.fill(true);
    stIndex = 6;
    syncTrack();
    enterHub(true);
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
    const step = (now) => {
      const t = Math.min(1, (now - t0) / 1000);
      el.textContent = Math.round(target * (1 - Math.pow(1 - t, 3))) + suf;
      if (t < 1 && el.isConnected) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }
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
      const nz = Math.max(0.74, Math.min(1.22, z * (avail * 0.98) / h));
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
    despachar: () => despachar()
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
    $$('.dock-item').forEach((b, i) => { b.classList.toggle('active', i === current); b.classList.toggle('seen', visited.has(i)); });
    $('#btn-prev').disabled = current === 0;
    $('#btn-next').disabled = current === C.LAMINAS.length - 1;
    items.forEach((el, i) => el.classList.toggle('seen', visited.has(i)));
  }
  function renderSheet(i) {
    const l = C.LAMINAS[i];
    const a = document.createElement('article');
    a.className = 'sheet';
    a.innerHTML = `
      <header class="sheet-head">
        <div class="plate"><span class="plate-art">${C.ARTE[l.arte]}</span></div>
        <div class="sheet-titles">
          <p class="tagline">Ítem ${String(i + 1).padStart(2, '0')} / ${C.LAMINAS.length} · ${l.fase} · ${l.tema}</p>
          <h2>${l.titulo}</h2>
          <p class="sheet-sub">${l.sub}</p>
        </div>
        <div class="sheet-meta"><span class="doc-ref">ACTA-P3-${String(i + 1).padStart(2, '0')}</span><span class="verif">Inspeccionado</span></div>
      </header>
      <div class="sheet-body"><div class="fit">${l.html()}</div></div>
      <footer class="sheet-foot"><span>Evidencia: <code>${l.evidencia}</code></span><span>${l.etiqueta}</span></footer>`;
    return a;
  }
  async function openSlide(i) {
    if (i < 0 || i >= C.LAMINAS.length) return;
    if (!['hub', 'slides'].includes(state)) return;
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
        Object.assign(fly.style, { left: r0.left + 'px', top: r0.top + 'px', width: r0.width + 'px', height: r0.height + 'px' });
        body.appendChild(fly);
        const dx = r1.left - r0.left;
        const dy = r1.top - r0.top;
        const sc = r1.width / r0.width;
        await fly.animate([
          { transform: 'translate(0,0) scale(1)' },
          { transform: 'translate(' + dx * 0.5 + 'px,' + (dy * 0.5 - 60) + 'px) scale(' + (1 + sc) / 1.6 + ') rotate(-8deg)', offset: 0.5 },
          { transform: 'translate(' + dx + 'px,' + dy + 'px) scale(' + sc + ')' }
        ], { duration: 820, easing: 'cubic-bezier(.4,0,.2,1)', fill: 'forwards' }).finished.catch(() => {});
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
     Despacho a main y sello del tribunal
     ------------------------------------------------------------------------ */
  async function despachar() {
    if (state === 'slides') { goHub(); await sleep(ms(700) || 50); }
    if (state !== 'hub') return;
    setState('despacho');
    clearEfx();
    $('#hub-hud').hidden = true;
    await Promise.all(items.map((el, i) => sleep(ms(i * 50)).then(() => {
      if (motionOff()) { el.style.opacity = 0; return; }
      const cur = el.style.transform;
      return el.animate([{ transform: cur, opacity: 1 }, { transform: cur + ' translateY(-40px) scale(.7)', opacity: 0 }], { duration: 420, easing: 'ease-in', fill: 'forwards' }).finished.then(() => { el.style.opacity = 0; el.getAnimations().forEach((a) => a.cancel()); });
    })));
    layer.classList.remove('show');
    setPose(POSES.final);
    await sleep(ms(1350));
    $('#portal-name').textContent = 'SALIDA · MAIN · TAG PARCIAL-3';
    $('#portal-led').classList.add('ok');
    await portalIn6();
    setState('final');
    $('#final-hud').hidden = false;
    $('#grade-dock').hidden = true;
  }
  async function portalIn6() {
    portal.classList.remove('passed');
    placePortal();
    portal.classList.add('on', 'exit');
    if (!motionOff()) await portal.animate([{ transform: 'translateX(1500px)', opacity: 0 }, { transform: 'translateX(1200px)', opacity: 1, offset: 0.15 }, { transform: 'translateX(0)', opacity: 1 }], { duration: 800, easing: 'cubic-bezier(.2,.8,.2,1)' }).finished.catch(() => {});
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
    portal.classList.remove('on');
    setPose(POSES.stamp);
    await sleep(ms(1300) || 60);
    const seal = $('#seal-p3');
    $('#seal-p3-score').textContent = pendingGrade;
    seal.hidden = false;
    seal.classList.remove('in');
    const r = seal.getBoundingClientRect();
    const cx = r.left + r.width / 2;
    const cy = r.top + r.height / 2;
    const st = $('#rubber-stamp');
    st.innerHTML = C.ARTE.liberado;
    if (!motionOff()) {
      st.classList.add('on');
      const a = st.animate([
        { transform: 'translate(' + (cx - 90) + 'px,' + (cy - 520) + 'px) scale(1.15) rotate(-6deg)', opacity: 0, easing: 'cubic-bezier(.2,.7,.3,1)' },
        { transform: 'translate(' + (cx - 90) + 'px,' + (cy - 260) + 'px) scale(1.1) rotate(-3deg)', opacity: 1, offset: 0.45, easing: 'cubic-bezier(.7,0,1,.7)' },
        { transform: 'translate(' + (cx - 90) + 'px,' + (cy - 140) + 'px) scale(.96)', opacity: 1, offset: 0.62, easing: 'linear' },
        { transform: 'translate(' + (cx - 90) + 'px,' + (cy - 140) + 'px) scale(.96)', opacity: 1, offset: 0.74, easing: 'cubic-bezier(.4,0,.2,1)' },
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
    $('#final-msg').innerHTML = 'Sellado por el tribunal · <b>nota ' + pendingGrade + '</b> · despachando a main…';
    await sleep(ms(700));
    setPose(POSES.final);
    await sleep(ms(1300));
    // vuelve el arco de salida y la caja lo cruza por la cinta hacia main
    await portalIn6();
    if (!motionOff()) {
      moveBelt(1800);
      await boxEl.animate([{ transform: 'translateX(0)' }, { transform: 'translateX(2400px)' }], { duration: 1800, easing: 'cubic-bezier(.5,0,.8,.6)', fill: 'forwards' }).finished.catch(() => {});
    }
    boxEl.classList.add('gone');
    $('#final-hud').classList.add('sent');
    $('#final-msg').innerHTML = 'Despachada a <b>main</b> · tag parcial-3 · nota ' + pendingGrade;
    $('#final-hud').classList.remove('stamping');
    $('#btn-puntuar').hidden = true;
    await sleep(ms(500));
    await mostrarDestino();
  }
  /* Destino: recorrido de la caja por los tres parciales hasta main */
  let destinoToken = 0;
  async function mostrarDestino() {
    const mio = ++destinoToken;
    const d = $('#destino');
    const q = new URLSearchParams(location.search);
    const notas = [['P1', Number(q.get('notaP1'))], ['P2', Number(q.get('notaP2'))], ['P3', pendingGrade]].filter((n) => n[1] >= 1 && n[1] <= 10);
    $('#dest-notas').innerHTML = notas.map((n, i) => '<div class="dest-nota" style="--i:' + i + '"><span>NOTA ' + n[0] + '</span><strong>' + n[1] + '</strong></div>').join('');
    portal.classList.remove('on', 'exit');
    $('#final-hud').hidden = true;
    d.hidden = false;
    requestAnimationFrame(() => d.classList.add('show'));
    const stops = $$('.ruta-st', d);
    const caja = $('#ruta-box');
    const fill = $('#ruta-fill');
    const stamp = $('#dest-stamp');
    stops.forEach((x) => x.classList.remove('on'));
    stamp.classList.remove('in');
    caja.classList.remove('done');
    caja.style.transition = 'none';
    fill.style.transition = 'none';
    fill.style.width = '0';
    const centro = (st) => (st.offsetLeft + st.offsetWidth / 2) + 'px';
    caja.style.left = centro(stops[0]);
    void caja.offsetWidth;
    caja.style.transition = '';
    fill.style.transition = '';
    await sleep(ms(500));
    for (let i = 0; i < stops.length; i++) {
      if (mio !== destinoToken || d.hidden) return;
      caja.style.left = centro(stops[i]);
      fill.style.width = (i / (stops.length - 1)) * 100 + '%';
      caja.classList.remove('hop'); void caja.offsetWidth; caja.classList.add('hop');
      await sleep(ms(750) || 10);
      stops[i].classList.add('on');
      const r = stops[i].querySelector('.rs-dot').getBoundingClientRect();
      fx.puff(r.left + r.width / 2, r.top + r.height / 2, 8, i === stops.length - 1 ? 'green' : 'light');
      await sleep(ms(350));
    }
    caja.classList.add('done');
    await sleep(ms(300));
    stamp.classList.add('in');
    await sleep(ms(260));
    const rs = stamp.getBoundingClientRect();
    fx.sparks(rs.left + rs.width / 2, rs.top + rs.height / 2, 30);
    fx.puff(rs.left + rs.width / 2, rs.top + rs.height / 2, 18, 'green');
    shake();
  }
  function ocultarDestino() {
    destinoToken++;
    const d = $('#destino');
    d.classList.remove('show');
    d.hidden = true;
  }

  async function reopen() {
    if (state !== 'final') return;
    ocultarDestino();
    $('#final-hud').hidden = true;
    portal.classList.remove('on', 'exit');
    if (boxEl.classList.contains('gone')) {
      boxEl.getAnimations().forEach((a) => a.cancel());
      boxEl.classList.remove('gone');
      if (!motionOff()) {
        moveBelt(1200);
        await boxEl.animate([{ transform: 'translateX(-2200px)' }, { transform: 'translateX(0)' }], { duration: 1200, easing: 'cubic-bezier(.2,.6,.3,1)' }).finished.catch(() => {});
      }
    }
    $('#btn-puntuar').hidden = false;
    $('#final-hud').classList.remove('sent');
    layer.classList.remove('show');
    enterHub();
  }
  (function () {
    let drag = null;
    boxScene.addEventListener('pointerdown', (e) => {
      if (state !== 'final' || e.target.closest('button, .grade-dock')) return;
      drag = { x: e.clientX, y: e.clientY, rx: pose.rx, ry: pose.ry };
      rig.classList.add('no-trans');
    });
    window.addEventListener('pointermove', (e) => {
      if (!drag) return;
      pose = Object.assign({}, pose, { ry: drag.ry + (e.clientX - drag.x) * 0.35, rx: Math.max(-80, Math.min(10, drag.rx - (e.clientY - drag.y) * 0.3)) });
      rig.style.setProperty('--rx', pose.rx + 'deg');
      rig.style.setProperty('--ry', pose.ry + 'deg');
    });
    window.addEventListener('pointerup', () => { if (drag) { drag = null; rig.classList.remove('no-trans'); } });
  })();

  /* ------------------------------------------------------------------------
     Cronómetro, notas, ayuda, pantalla completa
     ------------------------------------------------------------------------ */
  let timerLeft = 15 * 60;
  let timerId = null;
  function fmtTime(s) { const m = Math.floor(Math.abs(s) / 60); const r = Math.abs(s) % 60; return (s < 0 ? '−' : '') + String(m).padStart(2, '0') + ':' + String(r).padStart(2, '0'); }
  function toggleTimer() {
    const b = $('#btn-timer');
    if (timerId) { clearInterval(timerId); timerId = null; b.classList.remove('running'); return; }
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
    } else if (state === 'aduana' && stIndex >= 0) {
      const p = C.PUESTOS[stIndex];
      nb.innerHTML = '<p class="notes-k">Puesto ' + (stIndex + 1) + ' · ' + p.n + '</p><p>' + C.NOTAS_RITUAL.aduana + '</p><p>' + p.e + ': ' + p.c.map((c) => c[0] + ' (' + c[2] + ')').join(', ') + '.</p>';
    } else {
      const k = state === 'despacho' ? 'despacho' : state;
      nb.innerHTML = '<p class="notes-k">' + k + '</p><p>' + (C.NOTAS_RITUAL[k] || '') + '</p>';
    }
  }
  function toggleNotes() { $('#notes-panel').hidden = !$('#notes-panel').hidden; refreshNotes(); }
  function toggleHelp(force) { const m = $('#help-modal'); m.hidden = force === undefined ? !m.hidden : !force; }
  function toggleFull() {
    if (!document.fullscreenElement) document.documentElement.requestFullscreen().catch(() => {});
    else document.exitFullscreen().catch(() => {});
  }

  /* ------------------------------------------------------------------------
     Teclado y botones
     ------------------------------------------------------------------------ */
  document.addEventListener('keydown', (e) => {
    if (e.target.matches && e.target.matches('input, textarea, select')) return;
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    const k = e.key;
    if (!$('#help-modal').hidden) { if (['Escape', 'h', 'H', '?'].includes(k)) toggleHelp(false); return; }
    if (k === 'h' || k === 'H' || k === '?') { toggleHelp(true); return; }
    if (k === 't' || k === 'T') { toggleTimer(); return; }
    if (k === 'n' || k === 'N') { toggleNotes(); return; }
    if (k === 'm' || k === 'M') { toggleMotion(); return; }
    if (k === 'f' || k === 'F') { toggleFull(); return; }
    if (k === 's' || k === 'S') { skipToHub(); return; }
    const avanzar = k === 'Enter' || k === 'ArrowRight' || k === ' ' || k === 'PageDown';
    switch (state) {
      case 'intro':
        if (avanzar) { e.preventDefault(); presentar(); }
        break;
      case 'aduana':
        if (avanzar) { e.preventDefault(); nextStation(); } else if (k === 'a' || k === 'A') runAll();
        break;
      case 'hub':
        if (avanzar) { e.preventDefault(); openSlide(visited.size ? current : 0); }
        else if (k === 'p' || k === 'P') despachar();
        break;
      case 'slides':
        if (k === 'ArrowRight' || k === ' ' || k === 'PageDown') { e.preventDefault(); openSlide(Math.min(C.LAMINAS.length - 1, current + 1)); }
        else if (k === 'ArrowLeft' || k === 'PageUp') { e.preventDefault(); openSlide(Math.max(0, current - 1)); }
        else if (k === 'Home') openSlide(0);
        else if (k === 'End') openSlide(C.LAMINAS.length - 1);
        else if (k === 'Escape' || k === '0') goHub();
        else if (k === 'p' || k === 'P') despachar();
        break;
      case 'final':
        if (k === 'r' || k === 'R') reopen();
        else if (k === 'Enter' && $('#grade-dock').hidden && !$('#btn-puntuar').hidden) $('#btn-puntuar').click();
        break;
      default:
        break;
    }
  });

  $('#btn-receive').addEventListener('click', presentar);
  $('#btn-next-station').addEventListener('click', nextStation);
  $('#btn-run-all').addEventListener('click', runAll);
  $('#btn-skip').addEventListener('click', skipToHub);
  $('#btn-start').addEventListener('click', () => openSlide(visited.size ? current : 0));
  $('#btn-despachar-hub').addEventListener('click', despachar);
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
  $('#btn-puntuar').addEventListener('click', () => { if (state === 'final') { $('#grade-dock').hidden = false; portal.classList.remove('on'); setPose(POSES.label); } });
  $('#btn-grade-cancel').addEventListener('click', () => { $('#grade-dock').hidden = true; setPose(POSES.final); });
  $('#btn-seal').addEventListener('click', sealBox);
  $('#btn-reopen').addEventListener('click', reopen);
  $('#btn-dest-back').addEventListener('click', reopen);
  $('#btn-dest-replay').addEventListener('click', () => mostrarDestino());
  window.addEventListener('resize', () => {
    setPose(pose, true);
    if (state === 'hub' || state === 'slides') layoutRing();
    if (state === 'slides') fitSheet(sheetEl);
    if (portal.classList.contains('on')) placePortal();
  });

  /* ------------------------------------------------------------------------
     Arranque
     ------------------------------------------------------------------------ */
  function init() {
    syncMotionButton();
    if (reduceMq.addEventListener) reduceMq.addEventListener('change', syncMotionButton);
    $$('[data-tape-text]').forEach((el) => { el.textContent = (C.CINTA_P2 + '   •   ').repeat(3); });
    $$('.barcode').forEach((b) => { let s = ''; for (let i = 0; i < 34; i++) s += '<i style="width:' + (1 + ((i * 7) % 4)) + 'px"></i>'; b.innerHTML = s; });
    $('.side-barcode').innerHTML = Array.from({ length: 16 }, (_, i) => '<i style="height:' + (2 + ((i * 5) % 4)) + 'px"></i>').join('');
    const q = new URLSearchParams(location.search);
    [['notaP1', '#seal-p1', '#seal-p1-score'], ['notaP2', '#seal-p2', '#seal-p2-score']].forEach(([p, s, sc]) => {
      const n = Number(q.get(p));
      if (n >= 1 && n <= 10) { $(sc).textContent = n; $(s).hidden = false; $(s).classList.add('in'); }
    });
    buildTrack();
    buildItems();
    buildDock();
    buildGradePads();
    setPose(POSES.intro, true);
    setState('intro');
  }
  const fontsReady = document.fonts && document.fonts.ready ? Promise.race([document.fonts.ready, sleep(1500)]) : Promise.resolve();
  fontsReady.then(init);
})();
