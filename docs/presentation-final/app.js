/* ==========================================================================
   PRESENTACIÓN INTERACTIVA — PROYECTO FINAL PEF (OPCIÓN 6)
   Ritual: el muelle se enciende → se abre el portón (arrastrando) → la caja
   llega → el público maneja al operario PRD-01 con el mouse: apunta el
   escáner a las guías, agarra la caja con la ventosa, la lleva a la mesa y
   corta la cinta con el láser → mesa con 11 bultos (el operario los alcanza
   a cámara) → entrega en el estante E-12 → sello del tribunal.
   Enter siempre completa la maniobra en curso de forma automática.
   ========================================================================== */
(function () {
  'use strict';

  const C = window.PEF4_CONTENIDO;
  const LAMINAS = C.LAMINAS;
  const $ = (s, r) => (r || document).querySelector(s);
  const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
  const html = document.documentElement;
  const body = document.body;
  const svgNS = 'http://www.w3.org/2000/svg';
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));

  /* ------------------------------------------------------------------------
     Movimiento
     ------------------------------------------------------------------------ */
  const MOTION_KEY = 'pef4-force-motion';
  const reduceMq = window.matchMedia('(prefers-reduced-motion: reduce)');
  const motionOn = () => !reduceMq.matches || html.classList.contains('force-motion');
  const ms = (x) => (motionOn() ? x : 0);
  const sleep = (t) => new Promise((res) => setTimeout(res, t));
  const ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);

  let runToken = 0;
  const alive = (tok) => tok === runToken;

  function tween(dur, fn, tok, easing) {
    const e = easing || ease;
    return new Promise((res) => {
      if (!dur) { fn(1); res(); return; }
      const t0 = performance.now();
      const step = (now) => {
        if (tok !== undefined && !alive(tok)) { res(); return; }
        const t = Math.min(1, Math.max(0, (now - t0) / dur));
        fn(e(t));
        if (t < 1) requestAnimationFrame(step); else res();
      };
      requestAnimationFrame(step);
    });
  }

  /* ------------------------------------------------------------------------
     Sonido sintetizado (Web Audio): servos, ventosa, láser, sellos
     ------------------------------------------------------------------------ */
  const sfx = (() => {
    let ctx = null;
    let master = null;
    let servoGain = null;
    let servoOsc = null;
    let laserNode = null;
    let on = true;
    try { on = sessionStorage.getItem('pef4-sound') !== '0'; } catch (e) { /* sin almacenamiento */ }
    const init = () => {
      if (ctx) return;
      try {
        ctx = new (window.AudioContext || window.webkitAudioContext)();
        master = ctx.createGain();
        master.gain.value = on ? 0.5 : 0;
        master.connect(ctx.destination);
        servoOsc = ctx.createOscillator();
        servoOsc.type = 'sawtooth';
        servoOsc.frequency.value = 90;
        const lp = ctx.createBiquadFilter();
        lp.type = 'lowpass';
        lp.frequency.value = 520;
        servoGain = ctx.createGain();
        servoGain.gain.value = 0;
        servoOsc.connect(lp); lp.connect(servoGain); servoGain.connect(master);
        servoOsc.start();
      } catch (e) { ctx = null; }
    };
    const ok = () => ctx && on && ctx.state !== 'closed';
    const tone = (f, dur, type, vol, f2) => {
      if (!ok()) return;
      const t = ctx.currentTime;
      const o = ctx.createOscillator();
      const g = ctx.createGain();
      o.type = type || 'sine';
      o.frequency.setValueAtTime(f, t);
      if (f2) o.frequency.exponentialRampToValueAtTime(f2, t + dur);
      g.gain.setValueAtTime(vol || 0.15, t);
      g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
      o.connect(g); g.connect(master);
      o.start(t); o.stop(t + dur + 0.02);
    };
    const noise = (dur, vol, f1, f2, q) => {
      if (!ok()) return;
      const t = ctx.currentTime;
      const len = Math.floor(ctx.sampleRate * dur);
      const buf = ctx.createBuffer(1, len, ctx.sampleRate);
      const d = buf.getChannelData(0);
      for (let i = 0; i < len; i++) d[i] = Math.random() * 2 - 1;
      const src = ctx.createBufferSource();
      src.buffer = buf;
      const bp = ctx.createBiquadFilter();
      bp.type = 'bandpass';
      bp.Q.value = q || 1.2;
      bp.frequency.setValueAtTime(f1, t);
      bp.frequency.exponentialRampToValueAtTime(f2 || f1, t + dur);
      const g = ctx.createGain();
      g.gain.setValueAtTime(vol, t);
      g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
      src.connect(bp); bp.connect(g); g.connect(master);
      src.start(t);
    };
    return {
      init,
      get on() { return on; },
      toggle() {
        on = !on;
        try { sessionStorage.setItem('pef4-sound', on ? '1' : '0'); } catch (e) { /* sin almacenamiento */ }
        if (master) master.gain.value = on ? 0.5 : 0;
        if (!on) this.laser(false);
        return on;
      },
      servo(speed) {
        if (!servoGain) return;
        const t = ctx.currentTime;
        servoGain.gain.setTargetAtTime(Math.min(0.11, speed * 2.2), t, 0.05);
        servoOsc.frequency.setTargetAtTime(80 + Math.min(260, speed * 2600), t, 0.05);
      },
      clunk() { tone(70, 0.35, 'sine', 0.5, 40); noise(0.12, 0.25, 1800, 600); },
      hum() { tone(120, 0.6, 'triangle', 0.05, 121); },
      beep() { tone(1320, 0.09, 'sine', 0.12); setTimeout(() => tone(1760, 0.12, 'sine', 0.1), 90); },
      boot() { tone(220, 0.25, 'sine', 0.12, 880); setTimeout(() => tone(1320, 0.18, 'sine', 0.08), 220); },
      suction() { noise(0.28, 0.35, 3000, 400, 0.8); tone(110, 0.18, 'sine', 0.3, 60); },
      release() { noise(0.35, 0.25, 500, 3500, 0.8); },
      whoosh() { noise(0.35, 0.18, 400, 2400, 0.9); },
      chime() { [523, 659, 784, 1047].forEach((f, i) => setTimeout(() => tone(f, 0.5, 'triangle', 0.09), i * 90)); },
      stamp() { tone(55, 0.4, 'sine', 0.7, 35); noise(0.18, 0.4, 900, 200); },
      sizzle() { noise(0.09, 0.14, 5200, 2400, 0.7); },
      powerDown() { tone(660, 1.2, 'sawtooth', 0.07, 55); tone(330, 1.2, 'sine', 0.1, 40); },
      laser(state) {
        if (!ok()) return;
        if (state && !laserNode) {
          const o = ctx.createOscillator();
          const lfo = ctx.createOscillator();
          const lg = ctx.createGain();
          const g = ctx.createGain();
          o.type = 'square'; o.frequency.value = 740;
          lfo.frequency.value = 38; lg.gain.value = 60;
          lfo.connect(lg); lg.connect(o.frequency);
          g.gain.value = 0.035;
          o.connect(g); g.connect(master);
          o.start(); lfo.start();
          laserNode = { o, lfo };
        } else if (!state && laserNode) {
          laserNode.o.stop(); laserNode.lfo.stop(); laserNode = null;
        }
      }
    };
  })();
  ['pointerdown', 'keydown'].forEach((ev) => addEventListener(ev, () => sfx.init(), { once: true }));

  /* ------------------------------------------------------------------------
     Efectos de pantalla (chispas y polvo en el canvas superior)
     ------------------------------------------------------------------------ */
  const fx = (() => {
    const cv = $('#fx-canvas');
    const ctx = cv.getContext('2d');
    let parts = [];
    let running = false;
    const resize = () => { cv.width = innerWidth * devicePixelRatio; cv.height = innerHeight * devicePixelRatio; };
    resize();
    addEventListener('resize', resize);
    const loop = () => {
      ctx.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0);
      ctx.clearRect(0, 0, innerWidth, innerHeight);
      parts = parts.filter((p) => p.life > 0);
      parts.forEach((p) => {
        p.x += p.vx; p.y += p.vy; p.vy += p.g; p.life -= 1; p.r += p.gr || 0;
        ctx.globalAlpha = Math.max(0, p.life / p.max) * (p.a || 1);
        ctx.fillStyle = p.c;
        ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2); ctx.fill();
      });
      ctx.globalAlpha = 1;
      if (parts.length) requestAnimationFrame(loop); else { running = false; ctx.clearRect(0, 0, innerWidth, innerHeight); }
    };
    const add = (p) => { if (!motionOn()) return; parts.push(p); if (!running) { running = true; requestAnimationFrame(loop); } };
    const COLORS = { light: '#F6EFE5', green: '#4ADE80', amber: '#F2A516', lens: '#5BD2F0', kraft: '#C49A6C' };
    return {
      sparks(x, y, n, col) {
        for (let i = 0; i < n; i++) {
          const a = Math.random() * Math.PI * 2;
          const v = 1.5 + Math.random() * 4.5;
          add({ x, y, vx: Math.cos(a) * v, vy: Math.sin(a) * v - 1.8, g: 0.2, r: 1.2 + Math.random() * 1.8, life: 24 + Math.random() * 20, max: 44, c: COLORS[col] || '#FFD27A' });
        }
      },
      embers(x, y, n) {
        const cols = ['#FFFFFF', '#FFE0A3', '#FF9A3D', '#FF6B2E'];
        for (let i = 0; i < n; i++) {
          add({ x, y, vx: (Math.random() - 0.5) * 9, vy: -1 - Math.random() * 5, g: 0.28, r: 0.8 + Math.random() * 1.6, life: 18 + Math.random() * 22, max: 40, c: cols[(Math.random() * cols.length) | 0] });
        }
      },
      smoke(x, y, n) {
        for (let i = 0; i < n; i++) {
          add({ x: x + (Math.random() - 0.5) * 8, y, vx: (Math.random() - 0.5) * 0.6, vy: -0.7 - Math.random() * 0.9, g: -0.004, r: 3 + Math.random() * 3, gr: 0.32, a: 0.3, life: 55 + Math.random() * 30, max: 85, c: '#B8B2A8' });
        }
      },
      puff(x, y, n, col) {
        for (let i = 0; i < n; i++) {
          const a = Math.random() * Math.PI * 2;
          const v = 0.4 + Math.random() * 1.8;
          add({ x, y, vx: Math.cos(a) * v, vy: Math.sin(a) * v - 0.4, g: -0.01, r: 2 + Math.random() * 4, life: 30 + Math.random() * 30, max: 60, c: COLORS[col] || COLORS.light });
        }
      }
    };
  })();

  /* ------------------------------------------------------------------------
     Escena SVG: coordenadas y cámara
     ------------------------------------------------------------------------ */
  const scene = $('#scene');
  const dockScene = $('#dock-scene');
  const toScreen = (x, y) => {
    const m = scene.getScreenCTM();
    return { x: m.a * x + m.c * y + m.e, y: m.b * x + m.d * y + m.f };
  };
  const toSvg = (cx, cy) => {
    const pt = scene.createSVGPoint();
    pt.x = cx; pt.y = cy;
    const p = pt.matrixTransform(scene.getScreenCTM().inverse());
    return { x: p.x, y: p.y };
  };

  const WIDE = { x: 0, y: 0, w: 1600, h: 900 };
  const cam = { ...WIDE };
  const applyCam = () => scene.setAttribute('viewBox', `${cam.x.toFixed(1)} ${cam.y.toFixed(1)} ${cam.w.toFixed(1)} ${cam.h.toFixed(1)}`);
  function setCam(v) { Object.assign(cam, v); applyCam(); }
  function tweenCam(to, dur, tok) {
    const from = { ...cam };
    return tween(ms(dur), (k) => {
      cam.x = from.x + (to.x - from.x) * k;
      cam.y = from.y + (to.y - from.y) * k;
      cam.w = from.w + (to.w - from.w) * k;
      cam.h = from.h + (to.h - from.h) * k;
      applyCam();
    }, tok);
  }
  const view = (x, y, w) => ({ x, y, w, h: w * 9 / 16 });
  const HUB_VIEW = view(470, 160, 1050);

  /* ------------------------------------------------------------------------
     Luces del muelle y polvo en el aire
     ------------------------------------------------------------------------ */
  const cones = $$('.cone');
  const bulbs = $$('.bulb');
  const darkness = $('#darkness');
  let lightLevel = 0;
  function setLamp(i, on) {
    cones[i].setAttribute('opacity', on ? 1 : 0);
    bulbs[i].setAttribute('fill', on ? '#FFE2B0' : '#4A4234');
  }
  function lightsInstant() {
    cones.forEach((_, i) => setLamp(i, true));
    darkness.setAttribute('opacity', 0);
    lightLevel = 1;
  }
  async function lightsOn(tok) {
    for (let i = 0; i < cones.length; i++) {
      if (!alive(tok)) return;
      setLamp(i, true); sfx.clunk();
      await sleep(ms(70));
      setLamp(i, false);
      await sleep(ms(90));
      setLamp(i, true);
      if (i === 1) { await sleep(ms(60)); setLamp(i, false); await sleep(ms(50)); setLamp(i, true); }
      const target = 0.62 - (i + 1) * 0.2;
      const from = Number(darkness.getAttribute('opacity'));
      await tween(ms(260), (k) => { darkness.setAttribute('opacity', Math.max(0, from + (target - from) * k).toFixed(3)); lightLevel = (i + k) / cones.length; }, tok);
      await sleep(ms(220));
    }
    darkness.setAttribute('opacity', 0);
    lightLevel = 1;
    sfx.hum();
  }

  const dust = (() => {
    const cv = $('#dust');
    const ctx = cv.getContext('2d');
    const CONOS = [[470, 610, 400, 720], [900, 1040, 820, 1180], [1310, 1440, 1220, 1560]];
    const ps = Array.from({ length: 70 }, (_, i) => {
      const c = i % 3;
      return { c, t: Math.random(), u: Math.random(), vy: 0.0006 + Math.random() * 0.0012, vu: (Math.random() - 0.5) * 0.0015, r: 0.8 + Math.random() * 1.8, ph: Math.random() * 6.28 };
    });
    const resize = () => {
      const r = cv.getBoundingClientRect();
      cv.width = Math.round(r.width * devicePixelRatio);
      cv.height = Math.round(r.height * devicePixelRatio);
    };
    resize();
    addEventListener('resize', resize);
    return {
      draw(now) {
        const r = cv.getBoundingClientRect();
        ctx.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0);
        ctx.clearRect(0, 0, r.width, r.height);
        if (lightLevel <= 0.01 || !motionOn()) return;
        const m = scene.getScreenCTM();
        ps.forEach((p) => {
          p.t += p.vy; if (p.t > 1) p.t -= 1;
          p.u = clamp(p.u + p.vu + Math.sin(now / 1500 + p.ph) * 0.0008, 0.05, 0.95);
          const k = CONOS[p.c];
          const y = 110 + p.t * 640;
          const f = (y - 90) / 680;
          const x0 = k[0] + (k[2] - k[0]) * f;
          const x1 = k[1] + (k[3] - k[1]) * f;
          const x = x0 + (x1 - x0) * p.u;
          const sx = m.a * x + m.e - r.left;
          const sy = m.d * y + m.f - r.top;
          ctx.globalAlpha = lightLevel * (0.25 + 0.35 * Math.sin(now / 600 + p.ph) ** 2);
          ctx.fillStyle = '#FFE9C4';
          ctx.beginPath(); ctx.arc(sx, sy, p.r * Math.max(0.6, m.a), 0, Math.PI * 2); ctx.fill();
        });
        ctx.globalAlpha = 1;
      }
    };
  })();

  /* ------------------------------------------------------------------------
     La caja
     ------------------------------------------------------------------------ */
  const boxEl = $('#box');
  const shadowEl = $('#box-shadow');
  const caja = { x: -260, y: 650, surface: 650, carried: false };
  const TOP_DX = 19;   // punto de la ventosa: centro de la tapa
  const TOP_DY = -137;
  const TABLE_BOX = { x: 990, y: 660 };
  const SHELF_BOX = { x: 1395, y: 520 };
  const BELT_BOX = { x: 420, y: 650 };

  function renderBox() {
    boxEl.setAttribute('transform', `translate(${caja.x.toFixed(1)} ${caja.y.toFixed(1)})`);
    const lift = caja.surface - caja.y;
    shadowEl.setAttribute('cx', (caja.x + TOP_DX).toFixed(1));
    if (caja.carried && lift > 4) {
      shadowEl.setAttribute('cy', 772);
      shadowEl.setAttribute('rx', 90);
      shadowEl.setAttribute('opacity', 0.22);
    } else {
      shadowEl.setAttribute('cy', caja.surface + 2);
      shadowEl.setAttribute('rx', 120);
      shadowEl.setAttribute('opacity', 0.45);
    }
  }

  /* ------------------------------------------------------------------------
     Operario PRD-01: cinemática de 3 articulaciones + bucle de control
     Hombro en (bx, 600). Eslabones de 240 y 215. El cabezal apunta siempre
     hacia abajo y la ventosa queda 104 unidades debajo de la muñeca.
     ------------------------------------------------------------------------ */
  const robotEl = $('#robot');
  const j1 = $('#j1');
  const j2 = $('#j2');
  const j3 = $('#j3');
  const L1 = 240;
  const L2 = 215;
  const L3 = 104;
  const SHOULDER_Y = 600;
  const HOME_X = 720;
  const DEG = 180 / Math.PI;
  const robot = { bx: HOME_X, a1: 0, a2: 0 };
  const HOME = () => ({ x: HOME_X + 70, y: 560 });

  function wrap(a) { while (a > Math.PI) a -= 2 * Math.PI; while (a < -Math.PI) a += 2 * Math.PI; return a; }

  function ik(wx, wy, bx) {
    const dx = wx - bx;
    const dy = wy - SHOULDER_Y;
    const d = Math.max(Math.abs(L1 - L2) + 1, Math.min(L1 + L2 - 1, Math.hypot(dx, dy)));
    const base = Math.atan2(dy, dx);
    const alpha = Math.acos((L1 * L1 + d * d - L2 * L2) / (2 * L1 * d));
    const sols = [base - alpha, base + alpha].map((a1) => {
      const ex = bx + L1 * Math.cos(a1);
      const ey = SHOULDER_Y + L1 * Math.sin(a1);
      return { a1, a2: Math.atan2(wy - ey, wx - ex), ey };
    });
    return sols[0].ey <= sols[1].ey ? sols[0] : sols[1];
  }

  function wrist() {
    return {
      x: robot.bx + L1 * Math.cos(robot.a1) + L2 * Math.cos(robot.a2),
      y: SHOULDER_Y + L1 * Math.sin(robot.a1) + L2 * Math.sin(robot.a2)
    };
  }
  const tip = () => { const w = wrist(); return { x: w.x, y: w.y + L3 }; };
  const eye = () => { const w = wrist(); return { x: w.x + 43, y: w.y + 62 }; };

  let carriedBulto = null;
  function renderRobot() {
    robotEl.setAttribute('transform', `translate(${robot.bx.toFixed(1)} 0)`);
    j1.setAttribute('transform', `translate(0 ${SHOULDER_Y}) rotate(${(robot.a1 * DEG).toFixed(2)})`);
    j2.setAttribute('transform', `translate(${L1} 0) rotate(${((robot.a2 - robot.a1) * DEG).toFixed(2)})`);
    j3.setAttribute('transform', `translate(${L2} 0) rotate(${((Math.PI / 2 - robot.a2) * DEG).toFixed(2)})`);
    const t = tip();
    if (caja.carried) {
      caja.x = t.x - TOP_DX;
      caja.y = t.y - TOP_DY;
      renderBox();
    }
    if (carriedBulto !== null) {
      bultosG.children[carriedBulto].setAttribute('transform', `translate(${t.x.toFixed(1)} ${(t.y + 22).toFixed(1)})`);
    }
  }

  function setPose(tx, ty, bx) {
    const s = ik(tx, ty - L3, bx);
    robot.bx = bx; robot.a1 = s.a1; robot.a2 = s.a2;
    renderRobot();
  }

  // Modo de control: 'script' (tweens), 'follow' (sigue un objetivo con suavizado), 'idle' (respira y mira al puntero)
  const ctrl = { mode: 'idle', target: null, bxTarget: null, gain: 0.16 };

  async function moveTip(tx, ty, dur, opts) {
    const o = opts || {};
    ctrl.mode = 'script';
    const bx1 = o.bx !== undefined ? o.bx : robot.bx;
    const s = ik(tx, ty - L3, bx1);
    const from = { bx: robot.bx, a1: robot.a1, a2: robot.a2 };
    const to = { bx: bx1, a1: from.a1 + wrap(s.a1 - from.a1), a2: from.a2 + wrap(s.a2 - from.a2) };
    robotEl.classList.add('busy');
    await tween(ms(dur), (k) => {
      robot.bx = from.bx + (to.bx - from.bx) * k;
      robot.a1 = from.a1 + (to.a1 - from.a1) * k;
      robot.a2 = from.a2 + (to.a2 - from.a2) * k;
    }, o.tok);
    robotEl.classList.remove('busy');
  }

  function follow(target, bxTarget, gain) {
    ctrl.mode = 'follow';
    ctrl.target = target;
    ctrl.bxTarget = bxTarget === undefined ? null : bxTarget;
    ctrl.gain = gain || 0.16;
  }
  const idle = () => { ctrl.mode = 'idle'; ctrl.bxTarget = HOME_X; };

  const setEye = (s) => robotEl.setAttribute('data-eye', s);
  const baseScreen = (a, b) => { $('#base-l1').textContent = a; $('#base-l2').textContent = b; };
  const suction = (on) => { $('#suction-led').setAttribute('fill', on ? '#F2A516' : '#3A3F48'); };

  /* ------------------------------------------------------------------------
     Puntero sobre la escena
     ------------------------------------------------------------------------ */
  const ptr = { x: 800, y: 450, has: false, down: false };
  let interaction = null;
  const OVERLAYS = '.step-panel, .console, .hint, .hub, .intro-card, .final-hud, .destino, .skip-btn, .topbar';
  const sobreOverlay = (e) => e.target.closest && e.target.closest(OVERLAYS);
  dockScene.addEventListener('pointermove', (e) => {
    const p = toSvg(e.clientX, e.clientY);
    ptr.x = p.x; ptr.y = p.y; ptr.has = true;
    if (interaction && interaction.move) interaction.move(ptr);
  });
  dockScene.addEventListener('pointerdown', (e) => {
    if (sobreOverlay(e)) return;
    const p = toSvg(e.clientX, e.clientY);
    ptr.x = p.x; ptr.y = p.y; ptr.down = true;
    if (interaction && interaction.down) { e.preventDefault(); interaction.down(ptr); }
  });
  addEventListener('pointerup', () => {
    ptr.down = false;
    if (interaction && interaction.up) interaction.up(ptr);
  });
  const cursor = (cls) => {
    dockScene.classList.remove('is-interactive', 'can-grab', 'is-carrying', 'can-drag-door');
    if (cls) dockScene.classList.add(cls);
  };

  // Una fase interactiva termina cuando el público la completa o con Enter ('auto')
  let phase = null;
  function waitPhase(start) {
    return new Promise((res) => {
      phase = {
        finish(how) {
          if (phase !== this) return;
          phase = null;
          interaction = null;
          cursor(null);
          sfx.laser(false);
          res(how);
        }
      };
      start(phase);
    });
  }

  /* ------------------------------------------------------------------------
     Bucle principal: robot, polvo, bultos flotando
     ------------------------------------------------------------------------ */
  const bultosG = $('#bultos');
  let bob = false;
  let last = performance.now();
  const prev = { a1: 0, a2: 0, bx: 0 };
  function loop(now) {
    const dt = Math.min(0.05, (now - last) / 1000);
    last = now;
    if (ctrl.mode === 'follow' && ctrl.target) {
      if (ctrl.bxTarget !== null) robot.bx += (ctrl.bxTarget - robot.bx) * 0.06;
      const s = ik(ctrl.target.x, ctrl.target.y - L3, robot.bx);
      robot.a1 += wrap(s.a1 - robot.a1) * ctrl.gain;
      robot.a2 += wrap(s.a2 - robot.a2) * ctrl.gain;
    } else if (ctrl.mode === 'idle') {
      const h = HOME();
      let ox = ptr.has ? clamp((ptr.x - h.x) * 0.07, -45, 45) : 0;
      let oy = ptr.has ? clamp((ptr.y - h.y) * 0.05, -30, 25) : 0;
      if (hoverIdx >= 0 && state === 'hub') {
        const b = bultoPos(hoverIdx);
        ox = clamp((b.x - h.x) * 0.16, -95, 95);
        oy = -45;
      }
      robot.bx += (HOME_X - robot.bx) * 0.05;
      const s = ik(h.x + ox, h.y + oy + Math.sin(now / 900) * 6 - L3, robot.bx);
      robot.a1 += wrap(s.a1 - robot.a1) * 0.05;
      robot.a2 += wrap(s.a2 - robot.a2) * 0.05;
    }
    renderRobot();
    const speed = Math.abs(robot.a1 - prev.a1) + Math.abs(robot.a2 - prev.a2) + Math.abs(robot.bx - prev.bx) / 300;
    prev.a1 = robot.a1; prev.a2 = robot.a2; prev.bx = robot.bx;
    sfx.servo(speed);
    if (interaction && interaction.frame) interaction.frame(dt, now);
    if (bob && motionOn()) {
      Array.from(bultosG.children).forEach((g, i, arr) => {
        if (i === carriedBulto) return;
        const p = bultoPos(i, arr.length);
        g.setAttribute('transform', `translate(${p.x.toFixed(1)} ${(p.y + Math.sin(now / 650 + i * 0.8) * 4).toFixed(1)}) rotate(${(Math.sin(now / 900 + i) * 3).toFixed(2)})`);
      });
    }
    dust.draw(now);
    requestAnimationFrame(loop);
  }

  /* ------------------------------------------------------------------------
     Láser, hologramas y marcas en la escena
     ------------------------------------------------------------------------ */
  const laser = $('#laser');
  const laserLine = $('#laser-line');
  function drawLaser(x0, y0, x1, y1) {
    const e = eye();
    laser.setAttribute('points', `${e.x},${e.y} ${x0},${y0} ${x1},${y1}`);
    laserLine.setAttribute('x1', x0); laserLine.setAttribute('y1', y0);
    laserLine.setAttribute('x2', x1); laserLine.setAttribute('y2', y1);
    laser.setAttribute('opacity', 1); laserLine.setAttribute('opacity', 0.9);
  }
  const laserOff = () => { laser.setAttribute('opacity', 0); laserLine.setAttribute('opacity', 0); };

  const holo = $('#holo');
  const el = (tag, attrs, parent) => {
    const n = document.createElementNS(svgNS, tag);
    Object.entries(attrs || {}).forEach(([k, v]) => n.setAttribute(k, v));
    (parent || holo).appendChild(n);
    return n;
  };
  function ring(x, y, color) {
    const c = el('circle', { cx: x, cy: y, r: 16, fill: 'none', stroke: color || '#5BD2F0', 'stroke-width': 2.5, class: 'ring-pulse' });
    setTimeout(() => c.remove(), 1200);
  }
  // Tarjeta holográfica: líneas [texto, clase]
  function holoCard(x, y, w, lineas, ancla) {
    const h = 20 + lineas.length * 17;
    const g = el('g', { class: 'holo-card' });
    if (ancla) el('line', { x1: x + w / 2, y1: y + h, x2: ancla.x, y2: ancla.y, stroke: '#5BD2F0', 'stroke-width': 1.2, 'stroke-dasharray': '3 3', opacity: 0.8 }, g);
    if (ancla) el('circle', { cx: ancla.x, cy: ancla.y, r: 3.5, fill: '#5BD2F0' }, g);
    el('rect', { x, y, width: w, height: h, rx: 6, fill: 'url(#p-scan)', stroke: '#5BD2F0', 'stroke-width': 1.4, filter: 'url(#f-glow)' }, g);
    el('rect', { x, y, width: w, height: h, rx: 6, fill: '#071A22', 'fill-opacity': 0.55 }, g);
    el('path', { d: `M${x} ${y + 10} V${y} H${x + 10} M${x + w - 10} ${y + h} H${x + w} V${y + h - 10}`, stroke: '#A5F3FC', 'stroke-width': 2.2, fill: 'none' }, g);
    lineas.forEach((l, i) => {
      const t = el('text', { x: x + 10, y: y + 22 + i * 17, class: l[1] || 'holo-t', 'font-size': l[2] || 11 }, g);
      t.textContent = l[0];
    });
    requestAnimationFrame(() => g.classList.add('on'));
    return g;
  }
  const clearHolo = () => { holo.innerHTML = ''; };

  /* ------------------------------------------------------------------------
     Consola e indicaciones
     ------------------------------------------------------------------------ */
  const consoleEl = $('#console');
  const consoleBody = $('#console-body');
  function log(text, cls) {
    const p = document.createElement('p');
    if (cls) p.className = cls;
    p.innerHTML = text;
    consoleBody.appendChild(p);
    while (consoleBody.children.length > 9) consoleBody.firstElementChild.remove();
  }
  async function logs(lines, tok, gap) {
    for (const l of lines) {
      if (!alive(tok)) return;
      log(l[0], l[1]);
      await sleep(ms(gap || 280));
    }
  }
  const hintEl = $('#hint');
  function hint(text, prog) {
    $('#hint-text').innerHTML = text;
    $('#hint-prog').innerHTML = prog || '';
    hintEl.hidden = false;
  }
  const hintOff = () => { hintEl.hidden = true; };
  const dots = (n, total) => Array.from({ length: total }, (_, i) => `<i class="${i < n ? 'on' : ''}"></i>`).join('');

  /* ------------------------------------------------------------------------
     Bultos que salen de la caja
     ------------------------------------------------------------------------ */
  // Dos filas sobre la mesa: 6 arriba y 5 abajo
  function bultoPos(i) {
    const fila = i < 6 ? 0 : 1;
    const k = fila ? i - 6 : i;
    return { x: (fila ? 834 : 790) + k * 88, y: fila ? 404 : 304 };
  }
  function partir(texto, max) {
    const lineas = [];
    let actual = '';
    texto.split(' ').forEach((w) => {
      if ((actual + ' ' + w).trim().length > max) { lineas.push(actual.trim()); actual = w; } else actual += ' ' + w;
    });
    if (actual.trim()) lineas.push(actual.trim());
    return lineas.slice(0, 3);
  }
  function crearBultos() {
    bultosG.innerHTML = '';
    LAMINAS.forEach((l, i) => {
      const g = document.createElementNS(svgNS, 'g');
      g.setAttribute('class', 'bulto');
      g.setAttribute('role', 'button');
      g.setAttribute('aria-label', `${l.sku}: ${l.titulo}`);
      g.innerHTML = `
        <rect class="b-outline" x="-37" y="-29" width="74" height="58" rx="7" fill="none" stroke="#5BD2F0" stroke-width="2.5"/>
        <g class="b-body">
          <rect x="-30" y="-22" width="60" height="44" rx="2" fill="#C49A6C" stroke="#8D5F38"/>
          <rect x="-30" y="-22" width="60" height="7" fill="#B88D5F"/>
          <rect x="-4" y="-22" width="8" height="44" fill="#D4A45A"/>
          <rect x="-24" y="0" width="48" height="15" fill="#FFFEFB"/>
          <text x="0" y="11" text-anchor="middle" font-family="JetBrains Mono, monospace" font-size="9" font-weight="700" fill="#1B1410">${l.sku}</text>
          <circle class="b-num-bg" cx="-20" cy="-11" r="8" fill="#1D2026"/>
          <text x="-20" y="-7.6" text-anchor="middle" font-family="JetBrains Mono, monospace" font-size="9" font-weight="700" fill="#F6EFE5">${i + 1}</text>
        </g>
        <g class="b-seen"><circle cx="25" cy="-20" r="8" fill="#15803D" stroke="#0B1418" stroke-width="1.5"/><path d="M21 -20 l3 3 l5 -6" stroke="#FFFFFF" stroke-width="2" fill="none"/></g>
        <rect class="b-tag-bg" x="-42" y="29" width="84" height="17" rx="8.5" fill="#0B1418" fill-opacity="0.88" stroke="#5BD2F0" stroke-opacity="0.5"/>
        <text class="b-tag-t" x="0" y="41" text-anchor="middle" font-family="Albert Sans, sans-serif" font-size="9" font-weight="700" fill="#E6F7FB">${l.etiqueta}</text>`;
      g.setAttribute('opacity', 0);
      g.addEventListener('click', () => { if (state === 'hub') alcanzarBulto(i); });
      g.addEventListener('mouseenter', () => { if (state === 'hub') resaltarBulto(i); });
      g.addEventListener('mouseleave', () => { if (state === 'hub') resaltarBulto(-1); });
      bultosG.appendChild(g);
    });
  }
  function marcarBultos() {
    const sig = firstUnseen();
    Array.from(bultosG.children).forEach((g, i) => {
      g.classList.toggle('seen', seen.has(i));
      g.classList.toggle('next', i === sig && !seen.has(i));
    });
  }
  async function sacarBultos(tok) {
    const els = Array.from(bultosG.children);
    const ox = TABLE_BOX.x + TOP_DX;
    const oy = TABLE_BOX.y - 150;
    await Promise.all(els.map(async (g, i) => {
      await sleep(ms(i * 120));
      const p = bultoPos(i);
      g.setAttribute('opacity', 1);
      sfx.whoosh();
      const giro = (i % 2 ? 1 : -1) * (200 + i * 20);
      await tween(ms(850), (k) => {
        const x = ox + (p.x - ox) * k;
        const y = oy + (p.y - oy) * k - Math.sin(k * Math.PI) * 130;
        g.setAttribute('transform', `translate(${x.toFixed(1)} ${y.toFixed(1)}) rotate(${((1 - k) * giro).toFixed(1)}) scale(${(0.35 + 0.65 * k).toFixed(2)})`);
      }, tok, (t) => 1 - Math.pow(1 - t, 3));
      const s = toScreen(p.x, p.y);
      fx.puff(s.x, s.y, 5, 'kraft');
    }));
  }
  function bultosEnArco() {
    Array.from(bultosG.children).forEach((g, i) => {
      const p = bultoPos(i);
      g.setAttribute('opacity', 1);
      g.setAttribute('transform', `translate(${p.x.toFixed(1)} ${p.y.toFixed(1)})`);
    });
  }
  async function guardarBultos(tok) {
    bob = false;
    const els = Array.from(bultosG.children);
    const ox = caja.x + TOP_DX;
    const oy = caja.y - 140;
    await Promise.all(els.map(async (g, i) => {
      await sleep(ms(i * 60));
      const p = bultoPos(i, els.length);
      await tween(ms(450), (k) => {
        const x = p.x + (ox - p.x) * k;
        const y = p.y + (oy - p.y) * k - Math.sin(k * Math.PI) * 40;
        g.setAttribute('transform', `translate(${x.toFixed(1)} ${y.toFixed(1)}) scale(${(1 - k * 0.6).toFixed(2)})`);
      }, tok);
      g.setAttribute('opacity', 0);
    }));
  }

  /* ------------------------------------------------------------------------
     Panel de maniobra, etapas y notas
     ------------------------------------------------------------------------ */
  const MANIOBRAS = [
    {
      step: 'llegada', titulo: 'La caja llega al muelle',
      texto: 'Viene de <code>main</code> con las tres guías pegadas. La espera <b>PRD-01</b>: es el subsistema <code>src/ia/</code> que sumamos en el Final. Al arrancar, el motor carga el modelo entrenado desde un archivo de 2,6 KB.',
      src: 'src/motor/motor_inventario.py · _cargar_modelo_ia_si_existe()',
      notas: 'El muelle arranca a oscuras: se prenden las luces y alguien del equipo (o del tribunal) arrastra el portón hacia arriba. La caja que despachamos en el Parcial 3 entra por la cinta. El brazo es el personaje nuevo: representa el módulo de IA. Lo que dice la consola es lo que pasa de verdad al crear MotorInventario: instancia PredictorDemanda y carga el .joblib con los dos modelos.'
    },
    {
      step: 'lectura', titulo: 'Antes de tocarla, lee el historial',
      texto: 'Lo mismo hace con cada producto del catálogo: no decide solo por el stock de hoy, mira su historial de pedidos y lo resume en <b>10 datos</b>. Acá el historial son las guías de los tres parciales.',
      src: 'src/ia/extractor_features.py · ExtractorFeatures.extraer_vector()',
      notas: 'Invitar a alguien del tribunal a manejar el escáner con el mouse: el brazo sigue la mano. Cada guía escaneada proyecta su holograma con los números del parcial. Es la metáfora del extractor de features: el operario no mira solo la foto de hoy, mira el historial. En el bulto 03 se ven los 10 datos de productos reales.'
    },
    {
      step: 'descarga', titulo: 'La IA mueve la caja, no la reemplaza',
      texto: 'Lo que hay adentro sigue siendo el sistema de los tres parciales: catálogo hash O(1), streaming, CI. El operario se suma como una capa más dentro de <code>MotorInventario</code>, con dos métodos nuevos.',
      src: 'MotorInventario.predecir_quiebres_stock() · entrenar_modelo_ia()',
      notas: 'Con el mouse: llevar la ventosa sobre la tapa, clic para agarrar, llevarla a la mesa y clic para apoyarla. El robot se desplaza por el riel solo. El mensaje: la IA no reemplazó lo anterior; es una capa que se apoya en el catálogo O(1) del Parcial 1 y en todo el control de calidad. Si se cae el modelo, el motor vuelve a la regla convencional.'
    },
    {
      step: 'apertura', titulo: 'La abrimos por última vez',
      texto: 'Corta la cinta del Quality Gate y salen <b>11 bultos</b>: el problema, el modelo, la cascada, las mediciones, lo que validamos y las conclusiones. Cada bulto es una lámina con su archivo de evidencia.',
      src: 'docs/final/planificacion-proyecto-final.md · P4.0 a P4.6',
      notas: 'Mantener apretado y pasar el láser por la cinta, igual que el cúter del Parcial 2. Al abrirse, los bultos salen volando y quedan flotando sobre la mesa. Cada uno es un tema; al elegirlo, el operario lo alcanza a cámara.'
    }
  ];

  const NOTAS_RITUAL = {
    intro: 'Arrancamos donde terminó el Parcial 3: la caja pasó la aduana y quedó en main. Hoy llega a su destino, el centro de distribución para el que construimos el sistema. Presionar Enter o «Encender el muelle».',
    hub: 'Mesa de inspección. Elegir un bulto: el operario lo alcanza a cámara y se abre la lámina. → recorre en orden, Esc vuelve siempre acá, P entrega la caja.',
    final: 'Entrega: el operario cierra la caja, le pega la guía final y la deja en el estante. Después la evalúa con la regla O(1) y proyecta la decisión: no tiene historial de pedidos, así que no hace falta encender el modelo. PUNTUAR: el tribunal elige la nota y sella la entrega.',
    destino: 'Recorrido completo P1 → P2 → P3 → main → estante. R vuelve a la mesa para preguntas.'
  };

  const panel = $('#step-panel');
  const steps = $$('#ritual-steps li');
  const maneuverMarks = $$('#maneuvers li');
  function setStep(key) {
    const order = steps.map((s) => s.dataset.step);
    const idx = order.indexOf(key);
    steps.forEach((s, i) => { s.classList.toggle('on', i === idx); s.classList.toggle('done', i < idx); });
  }
  function showPanel(i, visible) {
    const m = MANIOBRAS[i];
    $('#sp-eyebrow').textContent = 'Maniobra ' + (i + 1) + ' de ' + MANIOBRAS.length;
    $('#sp-title').textContent = m.titulo;
    $('#sp-text').innerHTML = m.texto;
    $('#sp-src').textContent = m.src;
    $('#btn-next-step').innerHTML = (i === MANIOBRAS.length - 1 ? 'Ir a la mesa' : 'Siguiente maniobra') + ' <kbd>Enter</kbd>';
    panel.classList.toggle('show', visible);
    maneuverMarks.forEach((li, k) => { li.classList.toggle('on', k === i); li.classList.toggle('done', k < i); });
    setNotes(m.notas, 'Maniobra ' + (i + 1));
  }

  /* ------------------------------------------------------------------------
     Estado general
     ------------------------------------------------------------------------ */
  let state = 'intro';
  let maniobra = -1;
  let maniobraCorriendo = false;
  let entregada = false;
  let current = -1;
  const seen = new Set();

  function setState(s) {
    state = s;
    body.className = body.className.replace(/\bstate-\S+/g, '').trim() + ' state-' + s;
    const slides = s === 'slides';
    body.classList.toggle('mode-slides', slides);
    body.classList.toggle('mode-stage', !slides);
  }

  /* ------------------------------------------------------------------------
     Maniobra 1: se enciende el muelle, se abre el portón, llega la caja
     ------------------------------------------------------------------------ */
  const shutter = $('#door-shutter');
  const doorHandle = $('#door-handle');
  const setDoor = (h) => { shutter.setAttribute('height', h.toFixed(1)); doorHandle.setAttribute('transform', `translate(0 ${(h - 508).toFixed(1)})`); };
  let doorH = 508;

  async function m0(tok) {
    $('#intro-card').classList.add('gone');
    await lightsOn(tok);
    if (!alive(tok)) return;
    consoleEl.classList.add('show');
    // Arranque del operario
    sfx.boot();
    setEye('ready');
    const e0 = eye();
    ring(e0.x, e0.y); setTimeout(() => ring(e0.x, e0.y), 250); setTimeout(() => ring(e0.x, e0.y, '#F2A516'), 500);
    baseScreen('PRD-01', 'CARGANDO');
    const pWake = logs([
      ['encendido · operario <span class="c-key">PRD-01</span>', 'c-dim'],
      ['MotorInventario() → PredictorDemanda()'],
      ['cargando data/modelos/predictor_ia.joblib · 2.673 B'],
      ['regresor: StandardScaler → Ridge(alpha=1.0)'],
      ['clasificador: StandardScaler → LogisticRegression(C=1.0)'],
      ['listo · estrategia por defecto: <span class="c-key">HIBRIDA</span>', 'c-ok']
    ], tok, 300);
    // El portón se abre arrastrando la manija
    await tweenCam(view(0, 160, 1180), 900, tok);
    hint('Arrastrá el portón hacia arriba para abrir el muelle');
    const how = await waitPhase((ph) => {
      let arrastrando = false;
      let y0 = 0;
      let h0 = 0;
      const enPorton = (p) => p.x > 20 && p.x < 350 && p.y > 240 && p.y < 780;
      interaction = {
        move(p) {
          cursor(enPorton(p) || arrastrando ? 'can-drag-door' : null);
          if (!arrastrando) return;
          doorH = clamp(h0 + (p.y - y0), 0, 508);
          setDoor(doorH);
          if (doorH < 90) ph.finish('user');
        },
        down(p) { if (enPorton(p)) { arrastrando = true; y0 = p.y; h0 = doorH; } },
        up() { arrastrando = false; }
      };
    });
    hintOff();
    if (how === 'abort' || !alive(tok)) return;
    const hFrom = doorH;
    await tween(ms(how === 'auto' ? 900 : 300), (k) => { doorH = hFrom * (1 - k); setDoor(doorH); }, tok);
    sfx.clunk();
    // La caja entra por la cinta
    $('#conveyor').classList.add('belt-run');
    const x0 = caja.x;
    await tween(ms(2400), (k) => { caja.x = x0 + (BELT_BOX.x - x0) * k; renderBox(); }, tok);
    caja.x = BELT_BOX.x; renderBox();
    $('#conveyor').classList.remove('belt-run');
    await pWake;
    baseScreen('PRD-01', 'LISTO · HIBRIDA');
    await Promise.all([tweenCam(WIDE, 900, tok), moveTip(BELT_BOX.x + 160, 470, 900, { tok })]);
  }

  /* ------------------------------------------------------------------------
     Maniobra 2: el público apunta el escáner a las tres guías
     ------------------------------------------------------------------------ */
  const GUIAS = [
    { zona: [-86, -112, 74, 50], card: ['GUÍA P1 · EMPAQUE', 'búsqueda O(1) · hash', '718,3× más rápida'] },
    { zona: [-6, -94, 66, 44], card: ['GUÍA P2 · AUDITORÍA', '193 tests · cob. 90 %', 'Quality Gate · CC ≤ 12'] },
    { zona: [18, -50, 72, 36], card: ['GUÍA P3 · ADUANA CI', '7 etapas · 15 controles', 'canal verde 7 / 7'] }
  ];
  function guiaCard(i) {
    const g = GUIAS[i];
    const bx = caja.x;
    const by = caja.y;
    const ancla = { x: bx + g.zona[0] + g.zona[2] / 2, y: by + g.zona[1] + 6 };
    holoCard(168 + i * 166, 372, 162, [[g.card[0], 'holo-k', 9.5], [g.card[1], 'holo-t', 10.5], [g.card[2], 'holo-h', 11]], ancla);
    sfx.beep();
    const s = toScreen(ancla.x, ancla.y);
    fx.puff(s.x, s.y, 8, 'lens');
    log(g.card[0] + ' · ' + g.card[2], 'c-ok');
  }

  async function m1(tok) {
    setEye('think');
    baseScreen('PRD-01', 'LEYENDO GUÍAS');
    consoleEl.classList.remove('show');
    await Promise.all([tweenCam(view(160, 300, 780), 1000, tok), moveTip(BELT_BOX.x + 150, 440, 800, { tok })]);
    if (!alive(tok)) return;
    const hechas = [false, false, false];
    const acum = [0, 0, 0];
    const marcos = GUIAS.map((g) => el('rect', { x: caja.x + g.zona[0] - 4, y: caja.y + g.zona[1] - 4, width: g.zona[2] + 8, height: g.zona[3] + 8, rx: 4, fill: 'none', stroke: '#5BD2F0', 'stroke-width': 2, 'stroke-dasharray': '0 999', opacity: 0.9 }));
    const per = (g) => 2 * (g.zona[2] + g.zona[3] + 16);
    hint('Mové el mouse: el escáner sigue tu mano. Apuntá a cada guía', dots(0, 3));
    const how = await waitPhase((ph) => {
      cursor('is-interactive');
      const objetivo = { x: ptr.x + 70, y: ptr.y - 175 };
      follow(objetivo, null, 0.14);
      interaction = {
        frame(dt) {
          objetivo.x = ptr.x + 70;
          objetivo.y = Math.min(ptr.y - 175, 470);
          const cerca = ptr.x > caja.x - 130 && ptr.x < caja.x + 160 && ptr.y > caja.y - 200 && ptr.y < caja.y + 20;
          if (cerca) drawLaser(ptr.x - 26, ptr.y, ptr.x + 26, ptr.y); else laserOff();
          GUIAS.forEach((g, i) => {
            if (hechas[i]) return;
            const zx = caja.x + g.zona[0];
            const zy = caja.y + g.zona[1];
            if (ptr.x >= zx && ptr.x <= zx + g.zona[2] && ptr.y >= zy && ptr.y <= zy + g.zona[3]) {
              acum[i] += dt;
              marcos[i].setAttribute('stroke-dasharray', `${(per(g) * Math.min(1, acum[i] / 0.7)).toFixed(1)} 999`);
              if (acum[i] >= 0.7) {
                hechas[i] = true;
                marcos[i].setAttribute('stroke', '#86EFAC');
                guiaCard(i);
                const n = hechas.filter(Boolean).length;
                hint('Mové el mouse: el escáner sigue tu mano. Apuntá a cada guía', dots(n, 3));
                if (n === 3) ph.finish('user');
              }
            }
          });
        }
      };
    });
    if (how === 'abort' || !alive(tok)) return;
    if (how === 'auto') {
      for (let i = 0; i < 3; i++) {
        if (hechas[i] || !alive(tok)) continue;
        const g = GUIAS[i];
        const cx = caja.x + g.zona[0] + g.zona[2] / 2;
        const cy = caja.y + g.zona[1] + g.zona[3] / 2;
        await moveTip(cx + 70, cy - 175, 450, { tok });
        await tween(ms(550), (k) => {
          const y = caja.y + g.zona[1] + k * g.zona[3];
          drawLaser(cx - 30, y, cx + 30, y);
          marcos[i].setAttribute('stroke-dasharray', `${(per(g) * k).toFixed(1)} 999`);
        }, tok);
        marcos[i].setAttribute('stroke', '#86EFAC');
        hechas[i] = true;
        guiaCard(i);
        hint('El operario escanea las guías', dots(i + 1, 3));
      }
    }
    laserOff();
    hintOff();
    sfx.chime();
    holoCard(300, 308, 240, [['historial completo · 3 / 3', 'holo-ok', 11.5], ['→ se acepta la entrega', 'holo-t', 10.5]]);
    setEye('ok');
    await sleep(ms(900));
    await moveTip(BELT_BOX.x + 160, 440, 600, { tok });
  }

  /* ------------------------------------------------------------------------
     Maniobra 3: agarrar la caja con la ventosa y llevarla a la mesa
     ------------------------------------------------------------------------ */
  async function soltarEnMesa(tok) {
    ctrl.mode = 'script';
    caja.surface = TABLE_BOX.y;
    await moveTip(TABLE_BOX.x + TOP_DX, 400, 450, { tok, bx: 820 });
    await moveTip(TABLE_BOX.x + TOP_DX, TABLE_BOX.y + TOP_DY, 550, { tok });
    caja.carried = false;
    caja.x = TABLE_BOX.x; caja.y = TABLE_BOX.y; renderBox();
    suction(false); sfx.release();
    log('ventosa: OFF · caja en la mesa', 'c-ok');
    const s = toScreen(TABLE_BOX.x + TOP_DX, TABLE_BOX.y);
    fx.puff(s.x, s.y, 16, 'light');
    await moveTip(TABLE_BOX.x + TOP_DX, TABLE_BOX.y + TOP_DY - 120, 450, { tok });
  }
  function agarrar() {
    caja.carried = true;
    suction(true); sfx.suction();
    log('ventosa: <span class="c-key">ON</span> · 1 bulto · 12,4 kg', 'c-warn');
    const t = tip();
    ring(t.x, t.y, '#F2A516');
  }

  async function m2(tok) {
    clearHolo();
    consoleEl.classList.add('show');
    setEye('ready');
    baseScreen('PRD-01', 'CARGA 1 BULTO');
    await tweenCam(view(150, 170, 1180), 900, tok);
    if (!alive(tok)) return;
    const top = () => ({ x: caja.x + TOP_DX, y: caja.y + TOP_DY });
    const anillo = el('circle', { cx: top().x, cy: top().y, r: 22, fill: 'none', stroke: '#F2A516', 'stroke-width': 3, class: 'grab-ring', opacity: 0 });
    const fantasma = el('rect', { x: TABLE_BOX.x - 95, y: TABLE_BOX.y - 149, width: 228, height: 149, rx: 4, fill: '#5BD2F0', 'fill-opacity': 0.06, stroke: '#5BD2F0', 'stroke-width': 2, 'stroke-dasharray': '8 6', opacity: 0 });
    hint('Llevá la ventosa sobre la tapa de la caja y hacé clic para agarrarla');
    const sobreMesa = () => Math.abs(caja.x - TABLE_BOX.x) < 110;
    const how = await waitPhase((ph) => {
      cursor('is-interactive');
      const objetivo = { x: ptr.x, y: ptr.y };
      follow(objetivo, robot.bx, 0.18);
      interaction = {
        frame() {
          const t = top();
          objetivo.x = ptr.x;
          if (caja.carried) {
            objetivo.y = Math.min(ptr.y, 470);
            fantasma.setAttribute('opacity', sobreMesa() ? 1 : 0.45);
            fantasma.setAttribute('fill-opacity', sobreMesa() ? 0.16 : 0.04);
          } else {
            const encima = Math.abs(ptr.x - t.x) < 120;
            objetivo.y = Math.min(ptr.y, encima ? t.y : 610);
            const cerca = Math.hypot(tip().x - t.x, tip().y - t.y) < 60;
            anillo.setAttribute('opacity', cerca ? 1 : 0.35);
            cursor(cerca ? 'can-grab' : 'is-interactive');
          }
          ctrl.bxTarget = clamp((ptr.x + 760) / 2, 656, 1124);
        },
        down() {
          const t = top();
          if (!caja.carried) {
            if (Math.hypot(tip().x - t.x, tip().y - t.y) < 60) {
              agarrar();
              anillo.remove();
              cursor('is-carrying');
              hint('Llevala a la mesa de inspección y hacé clic para apoyarla');
            }
          } else if (sobreMesa()) {
            ph.finish('user');
          }
        }
      };
    });
    if (how === 'abort' || !alive(tok)) return;
    hintOff();
    anillo.remove();
    if (how === 'auto') {
      if (!caja.carried) {
        const t = top();
        await moveTip(t.x, t.y - 60, 500, { tok, bx: HOME_X });
        await moveTip(t.x, t.y, 350, { tok });
        agarrar();
        anillo.remove();
      }
      await moveTip(caja.x + TOP_DX + 40, 380, 600, { tok });
      log('trayectoria: cinta C-1 → mesa de inspección');
      await moveTip(TABLE_BOX.x + TOP_DX, 380, 1000, { tok, bx: 820 });
    }
    await soltarEnMesa(tok);
    fantasma.remove();
    await tweenCam(WIDE, 700, tok);
  }

  /* ------------------------------------------------------------------------
     Maniobra 4: cortar la cinta con el láser y abrir la caja
     ------------------------------------------------------------------------ */
  // Recorrido de la cinta: baja por el frente y sigue por la tapa
  const CORTE = [[0, -99], [0, -125], [38, -149]];
  const LARGO = [26, Math.hypot(38, 24)];
  function puntoCorte(t) {
    const total = LARGO[0] + LARGO[1];
    const d = t * total;
    if (d <= LARGO[0]) return { x: CORTE[0][0], y: CORTE[0][1] - d };
    const k = (d - LARGO[0]) / LARGO[1];
    return { x: CORTE[1][0] + (CORTE[2][0] - CORTE[1][0]) * k, y: CORTE[1][1] + (CORTE[2][1] - CORTE[1][1]) * k };
  }
  function proyectarCorte(px, py) {
    let mejor = { t: 0, d: Infinity };
    for (let i = 0; i <= 60; i++) {
      const t = i / 60;
      const p = puntoCorte(t);
      const d = Math.hypot(px - p.x, py - p.y);
      if (d < mejor.d) mejor = { t, d };
    }
    return mejor;
  }

  async function m3(tok) {
    setEye('cut');
    baseScreen('PRD-01', 'CORTE LÁSER');
    consoleEl.classList.remove('show');
    const T = TABLE_BOX;
    const W = (t) => { const p = puntoCorte(t); return { x: T.x + p.x, y: T.y + p.y }; };
    const tramo = (a, b) => {
      const pts = [];
      const n = Math.max(2, Math.ceil((b - a) * 48));
      for (let i = 0; i <= n; i++) { const p = W(a + (b - a) * i / n); pts.push(p.x.toFixed(2) + ',' + p.y.toFixed(2)); }
      return pts.join(' ');
    };
    const g = el('g', {});
    const guia = el('polyline', { points: tramo(0, 1), fill: 'none', stroke: '#5BD2F0', 'stroke-width': 0.8, 'stroke-dasharray': '2.2 2.2', opacity: 0.9 }, g);
    const inicio = el('circle', { cx: W(0).x, cy: W(0).y, r: 4.5, fill: '#FF7A2E', 'fill-opacity': 0.25, stroke: '#FF7A2E', 'stroke-width': 1.3, class: 'grab-ring' }, g);
    const quemado = el('polyline', { fill: 'none', stroke: '#2A1608', 'stroke-width': 2.2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, g);
    const fundido = el('polyline', { fill: 'none', stroke: '#FFB547', 'stroke-width': 2.4, 'stroke-linecap': 'round', filter: 'url(#f-glow)' }, g);
    const haloHaz = el('line', { stroke: '#FF5A2E', 'stroke-width': 7, opacity: 0, filter: 'url(#f-blur)' }, g);
    const haz = el('line', { stroke: '#FFF4E0', 'stroke-width': 1.3, opacity: 0 }, g);
    const destello = el('circle', { r: 7, fill: 'url(#g-flare)', opacity: 0 }, g);
    const mira = el('circle', { r: 1.5, fill: '#FF3B30', opacity: 0 }, g);
    let prog = 0;
    let ultSizzle = 0;
    const barra = () => { const b = $('#hint-prog .bar b'); if (b) b.style.width = Math.round(prog * 100) + '%'; };
    const cortar = (now) => {
      const p = W(prog);
      const e = eye();
      const fl = 0.75 + Math.random() * 0.25;
      [haz, haloHaz].forEach((l) => { l.setAttribute('x1', e.x); l.setAttribute('y1', e.y); l.setAttribute('x2', p.x); l.setAttribute('y2', p.y); });
      haz.setAttribute('opacity', fl);
      haloHaz.setAttribute('opacity', (0.55 * fl).toFixed(2));
      destello.setAttribute('cx', p.x); destello.setAttribute('cy', p.y);
      destello.setAttribute('r', (5 + Math.random() * 5).toFixed(1));
      destello.setAttribute('opacity', 1);
      quemado.setAttribute('points', tramo(0, prog));
      fundido.setAttribute('points', tramo(Math.max(0, prog - 0.14), prog));
      inicio.setAttribute('opacity', 0);
      const s = toScreen(p.x, p.y);
      if (Math.random() < 0.85) fx.embers(s.x, s.y, 3);
      if (Math.random() < 0.3) fx.smoke(s.x, s.y, 1);
      scene.classList.add('shake');
      sfx.laser(true);
      if (now - ultSizzle > 130) { sfx.sizzle(); ultSizzle = now; }
      barra();
    };
    const pausar = () => {
      haz.setAttribute('opacity', 0); haloHaz.setAttribute('opacity', 0); destello.setAttribute('opacity', 0);
      scene.classList.remove('shake');
      sfx.laser(false);
    };
    await Promise.all([tweenCam(view(880, 440, 260), 1100, tok), moveTip(W(0).x + 60, W(0).y - 210, 900, { tok, bx: 820 })]);
    if (!alive(tok)) { g.remove(); return; }
    hint('Mantené apretado sobre el punto naranja y seguí la cinta con el láser', '<span class="bar"><b></b></span>');
    const how = await waitPhase((ph) => {
      cursor('is-interactive');
      const objetivo = { x: ptr.x + 60, y: ptr.y - 210 };
      follow(objetivo, 820, 0.22);
      interaction = {
        frame(dt, now) {
          const pr = proyectarCorte(ptr.x - T.x, ptr.y - T.y);
          if (ptr.down && pr.d < 16 && pr.t <= prog + 0.2) {
            if (pr.t > prog) prog = Math.min(pr.t, prog + 0.02);
            const p = W(prog);
            objetivo.x = p.x + 60;
            objetivo.y = p.y - 210;
            mira.setAttribute('opacity', 0);
            cortar(now);
            if (prog >= 0.985) ph.finish('user');
          } else {
            pausar();
            objetivo.x = ptr.x + 60;
            objetivo.y = Math.min(ptr.y - 210, 420);
            mira.setAttribute('cx', ptr.x); mira.setAttribute('cy', ptr.y);
            mira.setAttribute('opacity', 0.9);
          }
        }
      };
    });
    mira.remove();
    if (how === 'abort' || !alive(tok)) { pausar(); g.remove(); return; }
    if (how === 'auto') {
      const desde = prog;
      await tween(ms(1800 * (1 - desde)) || 1, (k) => {
        prog = desde + (1 - desde) * k;
        const p = W(prog);
        follow({ x: p.x + 60, y: p.y - 210 }, 820, 0.3);
        cortar(performance.now());
      }, tok, (t) => t);
    }
    prog = 1;
    quemado.setAttribute('points', tramo(0, 1));
    barra();
    pausar();
    hintOff();
    // La estela se enfría y la cinta queda quemada
    await tween(ms(700), (k) => fundido.setAttribute('opacity', (1 - k).toFixed(2)), tok);
    $('#tape-top').setAttribute('fill', '#8C5E2A');
    $('#tape-front').setAttribute('fill', '#8C5E2A');
    guia.remove();
    await sleep(ms(250));
    // La caja se abre de golpe
    await Promise.all([tweenCam(view(700, 250, 640), 700, tok), moveTip(HOME().x, HOME().y, 800, { tok, bx: HOME_X })]);
    if (!alive(tok)) { g.remove(); return; }
    idle();
    g.remove();
    boxEl.classList.add('box-open');
    sfx.stamp(); sfx.chime();
    const s = toScreen(T.x + TOP_DX, T.y - 170);
    fx.puff(s.x, s.y, 34, 'light');
    fx.sparks(s.x, s.y, 46, 'amber');
    consoleEl.classList.add('show');
    log('contenido: <span class="c-key">' + LAMINAS.length + ' bultos</span> · manifiesto impreso', 'c-ok');
    setEye('ready');
    await sleep(ms(450));
    tweenCam(HUB_VIEW, 1300, tok);
    await sacarBultos(tok);
    marcarBultos();
    bob = true;
    baseScreen('PRD-01', 'EN ESPERA');
  }

  const RUNNERS = [m0, m1, m2, m3];

  async function runManiobra(i) {
    const tok = ++runToken;
    maniobra = i;
    maniobraCorriendo = true;
    setState('maniobra');
    setStep(MANIOBRAS[i].step);
    showPanel(i, false);
    await RUNNERS[i](tok);
    if (!alive(tok)) return;
    maniobraCorriendo = false;
    ctrl.mode === 'follow' && idle();
    showPanel(i, true);
  }

  function siguiente() {
    if (phase) { phase.finish('auto'); return; }
    if (state === 'intro') { runManiobra(0); return; }
    if (state !== 'maniobra' || maniobraCorriendo) return;
    if (maniobra < MANIOBRAS.length - 1) runManiobra(maniobra + 1);
    else showHub();
  }

  /* Coloca todo como queda al terminar las maniobras (para S y para volver) */
  function escenaEnMesa() {
    runToken++;
    if (phase) phase.finish('abort');
    maniobraCorriendo = false;
    hintOff();
    clearHolo();
    sfx.laser(false);
    $('#intro-card').classList.add('gone');
    lightsInstant();
    doorH = 0; setDoor(0);
    $('#conveyor').classList.remove('belt-run');
    $('#tape-cut').setAttribute('opacity', 0);
    $('#slot').setAttribute('opacity', 1);
    laserOff();
    suction(false);
    caja.carried = false;
    carriedBulto = null;
    caja.x = TABLE_BOX.x; caja.y = TABLE_BOX.y; caja.surface = TABLE_BOX.y;
    renderBox();
    boxEl.classList.add('box-open');
    boxEl.classList.remove('has-final-label', 'sealed', 'engr-on-side', 'engr-on-top');
    $('#tape-top').setAttribute('fill', '#D4A45A');
    $('#tape-front').setAttribute('fill', '#D4A45A');
    darkness.removeAttribute('mask');
    $('#spot-cone').setAttribute('opacity', 0);
    macro.hidden = true;
    macro.classList.remove('show');
    msvg.style.transform = '';
    msvg.style.filter = '';
    scene.classList.remove('shake');
    bultosEnArco();
    marcarBultos();
    bob = true;
    setPose(HOME().x, HOME().y, HOME_X);
    idle();
    setCam(WIDE);
    setEye('ready');
    baseScreen('PRD-01', 'EN ESPERA');
    if (!consoleBody.children.length) {
      log('operario PRD-01 · modelo cargado · HIBRIDA', 'c-ok');
      log('caja PEF-2026 en la mesa · ' + LAMINAS.length + ' bultos', 'c-ok');
    }
    entregada = false;
  }

  /* ------------------------------------------------------------------------
     Mesa (hub) y el operario alcanzando cada bulto a cámara
     ------------------------------------------------------------------------ */
  const hub = $('#hub');
  function renderManifest() {
    $('#manifest-list').innerHTML = LAMINAS.map((l, i) => `
      <li><button type="button" class="mf-row${seen.has(i) ? ' seen' : ''}" data-i="${i}" style="--i:${i}">
        ${C.ICONOS[l.icono]}
        <span class="mf-sku">${l.sku} · ${l.fase}</span>
        <span class="mf-name">${l.etiqueta}<small>${l.titulo}</small></span>
        <span class="mf-seen">✓ visto</span>
      </button></li>`).join('');
    $$('#manifest-list .mf-row').forEach((b) => {
      b.addEventListener('click', () => alcanzarBulto(Number(b.dataset.i)));
      b.addEventListener('mouseenter', () => resaltarBulto(Number(b.dataset.i)));
      b.addEventListener('mouseleave', () => resaltarBulto(-1));
    });
  }
  let hoverIdx = -1;
  let tooltip = null;
  function resaltarBulto(i) {
    hoverIdx = i;
    Array.from(bultosG.children).forEach((g, k) => g.classList.toggle('hl', k === i));
    $$('#manifest-list .mf-row').forEach((r) => r.classList.toggle('hl', Number(r.dataset.i) === i));
    if (tooltip) { tooltip.remove(); tooltip = null; }
    if (i < 0) return;
    const l = LAMINAS[i];
    const b = bultoPos(i);
    const lineas = [[`${l.sku} · ${l.fase} · ${l.tema}`, 'holo-k', 9.5]].concat(partir(l.titulo, 36).map((t) => [t, 'holo-t', 10.5]));
    const w = 250;
    const h = 20 + lineas.length * 17;
    tooltip = holoCard(clamp(b.x - w / 2, 750, 1290 - w), b.y - 38 - h, w, lineas);
  }

  function showHub() {
    const desdeLaminas = state === 'slides';
    const finManiobras = state === 'maniobra' && !maniobraCorriendo && !phase && maniobra === MANIOBRAS.length - 1;
    if (state === 'intro' || (state === 'maniobra' && !finManiobras)) escenaEnMesa();
    if (entregada) escenaEnMesa();
    runToken++;
    alcanzando = false;
    closeSlides();
    if (carriedBulto !== null || desdeLaminas) {
      carriedBulto = null;
      bultosEnArco();
      bob = true;
      setPose(HOME().x, HOME().y, HOME_X);
    }
    if (finManiobras) tweenCam(HUB_VIEW, 700); else setCam(HUB_VIEW);
    idle();
    setState('hub');
    setStep('mesa');
    panel.classList.remove('show');
    $('#final-hud').hidden = true;
    $('#destino').hidden = true;
    $('#destino').classList.remove('show');
    consoleEl.classList.remove('show');
    $('#btn-skip').hidden = true;
    hintOff();
    maneuverMarks.forEach((li) => { li.classList.remove('on'); li.classList.add('done'); });
    renderManifest();
    marcarBultos();
    resaltarBulto(-1);
    hub.hidden = false;
    setNotes(NOTAS_RITUAL.hub, 'Mesa');
  }

  let alcanzando = false;
  async function alcanzarBulto(i) {
    if (alcanzando) return;
    if (!motionOn() || state !== 'hub') { openSlide(i, 'up'); return; }
    alcanzando = true;
    const tok = ++runToken;
    hub.hidden = true;
    resaltarBulto(-1);
    const b = bultoPos(i);
    setEye('think');
    await moveTip(b.x, b.y - 22, 650, { tok, bx: clamp(b.x - 110, 656, 1124) });
    if (!alive(tok)) return;
    carriedBulto = i;
    sfx.suction();
    ring(b.x, b.y, '#F2A516');
    setEye('ok');
    const lleva = { x: b.x - 20, y: b.y - 60 };
    await moveTip(lleva.x, lleva.y, 380, { tok });
    const t = tip();
    const flash = $('#flash');
    flash.classList.remove('off');
    sleep(ms(380)).then(() => flash.classList.add('on'));
    sfx.whoosh();
    await tweenCam({ x: t.x - 60, y: t.y + 22 - 34, w: 120, h: 67.5 }, 750, tok);
    if (!alive(tok)) return;
    openSlide(i, 'up');
    flash.classList.remove('on');
    flash.classList.add('off');
    alcanzando = false;
  }

  /* ------------------------------------------------------------------------
     Láminas
     ------------------------------------------------------------------------ */
  const slidesScene = $('#slides-scene');
  const desk = $('#desk');
  let timers = [];
  let rafs = [];
  const api = {
    ms,
    later(t, fn) { const id = setTimeout(fn, t); timers.push(id); return id; },
    raf(fn) {
      const rec = { on: true };
      const lp = (now) => { if (!rec.on) return; fn(now); requestAnimationFrame(lp); };
      requestAnimationFrame(lp);
      rafs.push(rec);
    },
    goTo(i) { openSlide(i, i > current ? 'right' : 'left'); },
    bindGoto(root) {
      $$('[data-goto]', root).forEach((n) => n.addEventListener('click', () => api.goTo(Number(n.dataset.goto))));
    }
  };
  function limpiar() {
    timers.forEach(clearTimeout); timers = [];
    rafs.forEach((r) => { r.on = false; }); rafs = [];
  }

  function renderDock() {
    $('#dock-strip').innerHTML = LAMINAS.map((l, i) => `<button type="button" class="dock-item${i === current ? ' active' : ''}${seen.has(i) ? ' seen' : ''}" data-i="${i}" title="${l.sku} · ${l.etiqueta}">${C.ICONOS[l.icono]}<span>${String(i + 1).padStart(2, '0')}</span></button>`).join('');
    $$('#dock-strip .dock-item').forEach((b) => b.addEventListener('click', () => api.goTo(Number(b.dataset.i))));
    $('#btn-prev').disabled = current <= 0;
    $('#btn-next').innerHTML = (current >= LAMINAS.length - 1 ? 'Entregar la caja' : 'Siguiente') + ' <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>';
  }

  function openSlide(i, dir) {
    if (i < 0 || i >= LAMINAS.length) return;
    limpiar();
    const l = LAMINAS[i];
    const prevSheet = desk.querySelector('.sheet:not(.leave-left):not(.leave-right)');
    if (prevSheet) {
      prevSheet.classList.add(dir === 'left' ? 'leave-right' : 'leave-left');
      setTimeout(() => prevSheet.remove(), ms(520) + 20);
    }
    current = i;
    seen.add(i);
    hub.hidden = true;
    slidesScene.hidden = false;
    requestAnimationFrame(() => slidesScene.classList.add('show'));
    setState('slides');
    setStep('mesa');
    const sh = document.createElement('article');
    sh.className = 'sheet enter-' + (dir || 'up');
    sh.innerHTML = `
      <header class="sheet-head">
        <div class="plate pop">${C.ICONOS[l.icono]}</div>
        <div class="sheet-titles">
          <p class="tagline">${l.sku} · ${l.fase} · ${l.tema}</p>
          <h2>${l.titulo}</h2>
          <p class="sheet-sub">${l.sub}</p>
        </div>
        <div class="sheet-meta"><span class="doc-ref">MANIFIESTO PEF-2026-FINAL</span><span class="verif">Medido</span></div>
      </header>
      <div class="sheet-body">${l.html()}</div>
      <footer class="sheet-foot"><span>Evidencia: <code>${l.evidencia}</code></span><span>${String(i + 1).padStart(2, '0')} / ${LAMINAS.length}</span></footer>`;
    desk.appendChild(sh);
    if (l.init) l.init(sh, api);
    renderDock();
    setNotes(l.notas, l.sku + ' · ' + l.etiqueta);
  }

  function closeSlides() {
    limpiar();
    slidesScene.classList.remove('show');
    slidesScene.hidden = true;
    desk.innerHTML = '';
  }

  /* ------------------------------------------------------------------------
     Entrega final
     ------------------------------------------------------------------------ */
  async function entregar() {
    if (alcanzando) return;
    if (state === 'intro' || (state === 'maniobra' && (phase || maniobra < MANIOBRAS.length - 1))) escenaEnMesa();
    closeSlides();
    hub.hidden = true;
    panel.classList.remove('show');
    $('#btn-skip').hidden = true;
    hintOff();
    setState('final');
    setStep('entrega');
    setNotes(NOTAS_RITUAL.final, 'Entrega');
    consoleEl.classList.add('show');
    if (entregada) { mostrarFinalHud(); return; }
    if (caja.x !== TABLE_BOX.x || !boxEl.classList.contains('box-open') || carriedBulto !== null) escenaEnMesa();
    const tok = ++runToken;
    setCam(WIDE);
    setEye('ready');
    baseScreen('PRD-01', 'ENTREGA');
    log('guardando bultos en la caja…', 'c-dim');
    await Promise.all([tweenCam(view(560, 160, 1000), 900, tok), guardarBultos(tok)]);
    if (!alive(tok)) return;
    boxEl.classList.remove('box-open');
    $('#tape-top').setAttribute('fill', '#D4A45A');
    $('#tape-front').setAttribute('fill', '#D4A45A');
    sfx.clunk();
    await sleep(ms(250));
    boxEl.classList.add('has-final-label');
    sfx.stamp();
    const s1 = toScreen(caja.x - 40, caja.y - 40);
    fx.puff(s1.x, s1.y, 12, 'amber');
    log('guía final pegada · destino: estante E-12', 'c-warn');
    const top = { x: TABLE_BOX.x + TOP_DX, y: TABLE_BOX.y + TOP_DY };
    await moveTip(top.x, top.y - 60, 600, { tok });
    await moveTip(top.x, top.y, 400, { tok });
    agarrar();
    await moveTip(top.x, 360, 650, { tok });
    log('riel R-1 → estante E-12');
    const bxShelf = 1130;
    await Promise.all([
      tweenCam(view(760, 100, 840), 1500, tok),
      moveTip(SHELF_BOX.x + TOP_DX - 60, 330, 1500, { tok, bx: bxShelf })
    ]);
    caja.surface = SHELF_BOX.y;
    await moveTip(SHELF_BOX.x + TOP_DX, 330, 500, { tok });
    await moveTip(SHELF_BOX.x + TOP_DX, SHELF_BOX.y + TOP_DY, 600, { tok });
    caja.carried = false;
    caja.x = SHELF_BOX.x; caja.y = SHELF_BOX.y; renderBox();
    suction(false); sfx.release();
    $('#slot').setAttribute('opacity', 0);
    const s2 = toScreen(SHELF_BOX.x + TOP_DX, SHELF_BOX.y);
    fx.puff(s2.x, s2.y, 16, 'light');
    log('ventosa: OFF · caja en el estante', 'c-ok');
    // La evalúa como a cualquier producto del catálogo y proyecta la decisión
    setEye('think');
    await moveTip(SHELF_BOX.x - 150, 300, 700, { tok, bx: 1040 });
    log('evaluar_producto(caja PEF-2026, <span class="c-key">CONVENCIONAL</span>)', 'c-dim');
    await tween(ms(1300), (k) => {
      const y = SHELF_BOX.y - 120 + k * 112;
      drawLaser(SHELF_BOX.x - 92, y, SHELF_BOX.x + 92, y);
    }, tok);
    laserOff();
    const decision = [
      ['evaluar_producto(caja)', 'holo-k', 10],
      ['pedidos en el historial: 0'],
      ['→ demanda proyectada: 0 u'],
      ['→ P(quiebre) = 0,0 %'],
      ['riesgo BAJO · regla O(1)', 'holo-ok', 12],
      ['modelo: no hizo falta encenderlo', 'holo-h']
    ];
    const card = holoCard(1000, 150, 230, decision, { x: SHELF_BOX.x - 60, y: SHELF_BOX.y - 100 });
    const textos = $$('text', card);
    textos.forEach((t) => t.setAttribute('opacity', 0));
    for (const t of textos) {
      if (!alive(tok)) return;
      await sleep(ms(380));
      t.setAttribute('opacity', 1);
      sfx.beep();
    }
    await logs([
      ['P(quiebre) = 0,0 % · riesgo <span class="c-ok">BAJO</span>'],
      ['estado: <span class="c-key">ENTREGADO</span>', 'c-ok']
    ], tok, 300);
    setEye('ok');
    baseScreen('PRD-01', 'ENTREGADO');
    // Saludo del operario
    const r0 = tip();
    await moveTip(r0.x - 40, 420, 500, { tok });
    await moveTip(r0.x - 40, 470, 300, { tok });
    setEye('off'); await sleep(ms(120)); setEye('ok');
    await moveTip(r0.x - 40, 400, 400, { tok });
    entregada = true;
    if (alive(tok)) { idleEnEntrega(); mostrarFinalHud(); }
  }
  function idleEnEntrega() { ctrl.mode = 'script'; }

  function mostrarFinalHud() {
    $('#final-hud').hidden = false;
    $('#grade-dock').hidden = true;
    $('.final-actions').hidden = false;
  }

  /* Nota del tribunal */
  let pendingGrade = null;
  const pads = $('#grade-pads');
  pads.innerHTML = Array.from({ length: 10 }, (_, i) => `<button type="button" data-n="${i + 1}">${i + 1}</button>`).join('');
  $$('button', pads).forEach((b) => b.addEventListener('click', () => {
    pendingGrade = Number(b.dataset.n);
    $$('button', pads).forEach((x) => x.classList.toggle('on', x === b));
    $('#btn-seal').disabled = false;
  }));
  $('#btn-puntuar').addEventListener('click', () => { $('#grade-dock').hidden = false; $('.final-actions').hidden = true; });
  $('#btn-grade-cancel').addEventListener('click', () => { $('#grade-dock').hidden = true; $('.final-actions').hidden = false; });
  $('#btn-seal').addEventListener('click', () => { if (pendingGrade) grabarYCerrar(); });

  /* Primer plano (cámara 2) para el grabado */
  const macro = $('#macro');
  const msvg = $('#macro-svg');
  const engrBurnt = $('#engr-burnt');
  const engrHot = $('#engr-hot');
  const clipR = $('#engr-clip-rect');
  const bandR = $('#engr-band-rect');
  const mcHead = $('#mc-head');
  const mcBeam = $('#mc-beam');
  const mcGlow = $('#mc-beam-glow');
  const mcFlare = $('#mc-flare');
  const mToScreen = (x, y) => { const m = msvg.getScreenCTM(); return { x: m.a * x + m.c * y + m.e, y: m.b * x + m.d * y + m.f }; };
  const FUENTES = { serif: 'DM Serif Display, Georgia, serif', mono: 'JetBrains Mono, monospace', hand: 'Caveat, cursive' };
  const notaItems = (n) => [
    { t: 'NOTA FINAL', x: 800, y: 250, s: 54, f: 'mono', ls: 18, w: 700 },
    { t: String(n), x: 800, y: 590, s: 330, f: 'serif' },
    { t: 'TRIBUNAL EVALUADOR · PEF 2026 · UBP', x: 800, y: 680, s: 30, f: 'mono', ls: 6 }
  ];
  const NOMBRES = [
    { t: 'ENTREGA FINAL · PEF 2026', x: 800, y: 190, s: 40, f: 'mono', ls: 12, w: 700 },
    { t: 'Edgar Karpowicz', x: 800, y: 330, s: 112, f: 'hand', w: 700 },
    { t: 'Gastón Molina', x: 800, y: 450, s: 112, f: 'hand', w: 700 },
    { t: 'Tomás Molina', x: 800, y: 570, s: 112, f: 'hand', w: 700 },
    { t: 'fin del recorrido · P1 → P2 → P3 → Final', x: 800, y: 650, s: 28, f: 'mono', ls: 4 }
  ];

  async function macroIn(cara) {
    $('#macro-side').setAttribute('opacity', cara === 'side' ? 1 : 0);
    $('#macro-lid').setAttribute('opacity', cara === 'lid' ? 1 : 0);
    engrBurnt.innerHTML = '';
    engrHot.innerHTML = '';
    $('#macro-bar').style.width = '0';
    mcHead.setAttribute('transform', 'translate(800 -260)');
    macro.hidden = false;
    sfx.whoosh();
    requestAnimationFrame(() => macro.classList.add('show'));
    await sleep(ms(450) || 30);
  }
  async function macroOut() {
    macro.classList.remove('show');
    await sleep(ms(400) || 30);
    macro.hidden = true;
    msvg.style.transform = '';
    msvg.style.filter = '';
  }
  // Paneo rápido de la cámara del lateral a la tapa
  async function macroALaTapa() {
    msvg.style.transition = `transform ${ms(380)}ms ease-in, filter ${ms(380)}ms ease-in`;
    msvg.style.transform = 'translateY(22%)';
    msvg.style.filter = 'blur(10px)';
    sfx.whoosh();
    await sleep(ms(380));
    $('#macro-side').setAttribute('opacity', 0);
    $('#macro-lid').setAttribute('opacity', 1);
    engrBurnt.innerHTML = '';
    engrHot.innerHTML = '';
    $('#macro-bar').style.width = '0';
    $('#macro-label').textContent = 'CÁMARA 2 · TAPA DE LA CAJA · GRABADO LÁSER';
    msvg.style.transition = 'none';
    msvg.style.transform = 'translateY(-22%)';
    void msvg.getBoundingClientRect();
    msvg.style.transition = `transform ${ms(420)}ms ease-out, filter ${ms(420)}ms ease-out`;
    msvg.style.transform = '';
    msvg.style.filter = '';
    await sleep(ms(450));
  }

  // Grabado por barrido (raster): el láser recorre renglones de ida y vuelta
  async function grabar(items, dur, etiqueta, tok) {
    $('#macro-step').textContent = etiqueta;
    const bar = $('#macro-bar');
    items.forEach((it) => {
      [engrBurnt, engrHot].forEach((grp, k) => {
        const t = document.createElementNS(svgNS, 'text');
        t.setAttribute('x', it.x);
        t.setAttribute('y', it.y);
        t.setAttribute('text-anchor', 'middle');
        t.setAttribute('font-family', FUENTES[it.f]);
        t.setAttribute('font-size', it.s);
        if (it.ls) t.setAttribute('letter-spacing', it.ls);
        if (it.w) t.setAttribute('font-weight', it.w);
        t.setAttribute('fill', k ? '#FFC46B' : '#2A1406');
        if (!k) t.setAttribute('opacity', 0.92);
        t.textContent = it.t;
        grp.appendChild(t);
      });
    });
    const bb = engrBurnt.getBBox();
    const x0 = bb.x - 6;
    const w = bb.width + 12;
    const y0 = bb.y - 4;
    const h = bb.height + 8;
    clipR.setAttribute('x', x0); clipR.setAttribute('width', w);
    clipR.setAttribute('y', y0); clipR.setAttribute('height', 0);
    bandR.setAttribute('x', x0); bandR.setAttribute('width', w);
    const renglones = Math.max(8, Math.round(h / 16));
    let hx = x0;
    let ult = 0;
    sfx.laser(true);
    await tween(ms(dur) || 1, (k) => {
      const lin = k * renglones;
      const idx = Math.floor(lin);
      const f = lin - idx;
      const x = x0 + (idx % 2 ? 1 - f : f) * w;
      const y = y0 + k * h;
      clipR.setAttribute('height', (k * h).toFixed(1));
      bandR.setAttribute('y', (y - 9).toFixed(1));
      bandR.setAttribute('height', 12);
      hx += (x - hx) * 0.35;
      mcHead.setAttribute('transform', `translate(${hx.toFixed(1)} ${(y - 260).toFixed(1)})`);
      const ny = y - 140;
      [mcBeam, mcGlow].forEach((l) => { l.setAttribute('x1', hx); l.setAttribute('y1', ny); l.setAttribute('x2', x); l.setAttribute('y2', y); });
      const fl = 0.7 + Math.random() * 0.3;
      mcBeam.setAttribute('opacity', fl);
      mcGlow.setAttribute('opacity', (0.5 * fl).toFixed(2));
      mcFlare.setAttribute('cx', x); mcFlare.setAttribute('cy', y);
      mcFlare.setAttribute('r', (20 + Math.random() * 14).toFixed(1));
      mcFlare.setAttribute('opacity', 1);
      const s = mToScreen(x, y);
      if (Math.random() < 0.7) fx.embers(s.x, s.y, 2);
      if (Math.random() < 0.25) fx.smoke(s.x, s.y, 1);
      const now = performance.now();
      if (now - ult > 140) { sfx.sizzle(); ult = now; }
      bar.style.width = Math.round(k * 100) + '%';
    }, tok, (t) => t);
    sfx.laser(false);
    clipR.setAttribute('height', h);
    bandR.setAttribute('height', 0);
    [mcBeam, mcGlow, mcFlare].forEach((n) => n.setAttribute('opacity', 0));
    await tween(ms(500), (k) => mcHead.setAttribute('transform', `translate(${hx.toFixed(1)} ${(y0 + h - 260 - k * 520).toFixed(1)})`), tok);
  }

  async function grabarYCerrar() {
    const tok = ++runToken;
    $('#final-hud').hidden = true;
    clearHolo();
    consoleEl.classList.remove('show');
    setEye('cut');
    baseScreen('PRD-01', 'GRABADO LÁSER');
    await Promise.all([tweenCam(view(1300, 330, 330), 900, tok), moveTip(SHELF_BOX.x + 150, 320, 900, { tok, bx: 1124 })]);
    if (!alive(tok)) return;
    $('#macro-label').textContent = 'CÁMARA 2 · LATERAL DE LA CAJA · GRABADO LÁSER';
    await macroIn('side');
    await grabar(notaItems(pendingGrade), 3600, 'Grabando la nota del tribunal', tok);
    if (!alive(tok)) return;
    $('#engr-side-grade').textContent = pendingGrade;
    boxEl.classList.add('engr-on-side');
    sfx.chime();
    await sleep(ms(900));
    await macroALaTapa();
    await grabar(NOMBRES, 5200, 'Grabando los nombres del equipo', tok);
    if (!alive(tok)) return;
    boxEl.classList.add('engr-on-top');
    sfx.chime();
    await sleep(ms(1000));
    await macroOut();
    await cierre(tok);
  }

  // Cierre: el operario se apaga, las luces se van y queda un foco sobre la caja
  async function cierre(tok) {
    await sleep(ms(1100));
    consoleEl.classList.add('show');
    log('nota y nombres grabados en la caja PEF-2026', 'c-ok');
    log('fin del recorrido · P1 → P2 → P3 → Final', 'c-warn');
    setEye('ok');
    await Promise.all([tweenCam(WIDE, 1800, tok), moveTip(1120, 650, 1600, { tok, bx: 1050 })]);
    if (!alive(tok)) return;
    log('apagando operario PRD-01…', 'c-dim');
    baseScreen('PRD-01', 'APAGADO');
    sfx.powerDown();
    for (const e of ['off', 'ok', 'off', 'ok', 'off']) { setEye(e); await sleep(ms(150)); }
    await sleep(ms(500));
    consoleEl.classList.remove('show');
    darkness.setAttribute('mask', 'url(#m-spot)');
    for (let i = cones.length - 1; i >= 0; i--) {
      if (!alive(tok)) return;
      setLamp(i, false);
      sfx.clunk();
      const from = Number(darkness.getAttribute('opacity'));
      const to = 0.3 * (cones.length - i);
      await tween(ms(320), (k) => {
        darkness.setAttribute('opacity', (from + (to - from) * k).toFixed(3));
        lightLevel = Math.max(0, (i - k) / cones.length);
      }, tok);
      await sleep(ms(450));
    }
    lightLevel = 0;
    sfx.clunk();
    await tween(ms(600), (k) => $('#spot-cone').setAttribute('opacity', k.toFixed(2)), tok);
    const h0 = doorH;
    await tween(ms(1300), (k) => { doorH = h0 + (508 - h0) * k; setDoor(doorH); }, tok);
    sfx.clunk();
    await sleep(ms(600));
    if (!alive(tok)) return;
    tweenCam(view(560, 140, 1000), 3400, tok);
    mostrarDestino();
  }

  let destinoToken = 0;
  async function mostrarDestino() {
    const mio = ++destinoToken;
    setState('destino');
    setNotes(NOTAS_RITUAL.destino, 'Recorrido');
    const d = $('#destino');
    const q = new URLSearchParams(location.search);
    const notas = [['P1', Number(q.get('notaP1'))], ['P2', Number(q.get('notaP2'))], ['P3', Number(q.get('notaP3'))], ['FINAL', pendingGrade]]
      .filter((n) => n[1] >= 1 && n[1] <= 10);
    $('#dest-notas').innerHTML = notas.map((n, i) => `<div class="dest-nota" style="--i:${i}"><span>NOTA ${n[0]}</span><strong>${n[1]}</strong></div>`).join('');
    d.hidden = false;
    requestAnimationFrame(() => d.classList.add('show'));
    const stops = $$('.ruta-st', d);
    const box = $('#ruta-box');
    const fill = $('#ruta-fill');
    const stamp = $('#dest-stamp');
    stops.forEach((x) => x.classList.remove('on'));
    stamp.classList.remove('in');
    box.style.transition = 'none';
    fill.style.transition = 'none';
    fill.style.width = '0';
    const centro = (st) => (st.offsetLeft + st.offsetWidth / 2) + 'px';
    box.style.left = centro(stops[0]);
    void box.offsetWidth;
    box.style.transition = '';
    fill.style.transition = '';
    await sleep(ms(500));
    for (let i = 0; i < stops.length; i++) {
      if (mio !== destinoToken || d.hidden) return;
      box.style.left = centro(stops[i]);
      fill.style.width = (i / (stops.length - 1)) * 100 + '%';
      box.classList.remove('hop'); void box.offsetWidth; box.classList.add('hop');
      sfx.whoosh();
      await sleep(ms(700) || 10);
      stops[i].classList.add('on');
      const r = stops[i].querySelector('.rs-dot').getBoundingClientRect();
      fx.puff(r.left + r.width / 2, r.top + r.height / 2, 8, i === stops.length - 1 ? 'amber' : 'light');
      await sleep(ms(300));
    }
    stamp.classList.add('in');
    sfx.stamp();
    await sleep(ms(260));
    sfx.chime();
    const rs = stamp.getBoundingClientRect();
    fx.sparks(rs.left + rs.width / 2, rs.top + rs.height / 2, 30);
    fx.puff(rs.left + rs.width / 2, rs.top + rs.height / 2, 18, 'green');
  }

  /* ------------------------------------------------------------------------
     Notas, ayuda, cronómetro, sonido, movimiento, pantalla completa
     ------------------------------------------------------------------------ */
  const notesPanel = $('#notes-panel');
  function setNotes(text, k) { $('#notes-body').innerHTML = `<p class="notes-k">${k || ''}</p><p>${text}</p>`; }
  const toggleNotes = () => { notesPanel.hidden = !notesPanel.hidden; };
  $('#btn-notes').addEventListener('click', toggleNotes);
  $('#btn-notes-close').addEventListener('click', toggleNotes);

  const help = $('#help-modal');
  const toggleHelp = () => { help.hidden = !help.hidden; };
  $('#btn-help').addEventListener('click', toggleHelp);
  $('#btn-help-close').addEventListener('click', toggleHelp);
  help.addEventListener('click', (e) => { if (e.target === help) toggleHelp(); });

  const minutos = Math.max(1, Math.min(60, Number(new URLSearchParams(location.search).get('min')) || 15));
  let restante = minutos * 60;
  let timerId = null;
  const timerBtn = $('#btn-timer');
  const pintarTimer = () => {
    const a = Math.abs(restante);
    $('#timer-display').textContent = (restante < 0 ? '−' : '') + String(Math.floor(a / 60)).padStart(2, '0') + ':' + String(a % 60).padStart(2, '0');
    timerBtn.classList.toggle('warn', restante <= 180 && restante > 0);
    timerBtn.classList.toggle('over', restante <= 0);
  };
  const toggleTimer = () => {
    if (timerId) { clearInterval(timerId); timerId = null; timerBtn.classList.remove('running'); return; }
    timerBtn.classList.add('running');
    timerId = setInterval(() => { restante -= 1; pintarTimer(); }, 1000);
  };
  pintarTimer();
  timerBtn.addEventListener('click', toggleTimer);

  const pintarSonido = () => {
    $('#btn-sound').classList.toggle('is-muted', !sfx.on);
    $('#sound-label').textContent = sfx.on ? 'Sonido' : 'Silencio';
  };
  const toggleSound = () => { sfx.init(); sfx.toggle(); pintarSonido(); };
  $('#btn-sound').addEventListener('click', toggleSound);
  pintarSonido();

  const pintarMotion = () => {
    const off = !motionOn();
    $('#btn-motion').classList.toggle('is-off', off);
    $('#motion-label').textContent = off ? 'Sin animaciones' : 'Animaciones';
  };
  const toggleMotion = () => {
    const forced = html.classList.toggle('force-motion');
    try { sessionStorage.setItem(MOTION_KEY, forced ? '1' : '0'); } catch (e) { /* sin almacenamiento */ }
    pintarMotion();
  };
  $('#btn-motion').addEventListener('click', toggleMotion);
  pintarMotion();

  const toggleFull = () => {
    if (document.fullscreenElement) document.exitFullscreen().catch(() => {});
    else html.requestFullscreen().catch(() => {});
  };
  $('#btn-full').addEventListener('click', toggleFull);

  /* ------------------------------------------------------------------------
     Botones y teclado
     ------------------------------------------------------------------------ */
  $('#btn-start').addEventListener('click', siguiente);
  $('#btn-next-step').addEventListener('click', siguiente);
  $('#btn-skip').addEventListener('click', showHub);
  $('#btn-open-first').addEventListener('click', () => alcanzarBulto(firstUnseen()));
  $('#btn-deliver-hub').addEventListener('click', entregar);
  $('#btn-back-hub').addEventListener('click', showHub);
  $('#btn-dest-back').addEventListener('click', showHub);
  $('#btn-dest-replay').addEventListener('click', mostrarDestino);
  $('#btn-hub').addEventListener('click', showHub);
  $('#btn-prev').addEventListener('click', () => api.goTo(current - 1));
  $('#btn-next').addEventListener('click', () => { if (current >= LAMINAS.length - 1) entregar(); else api.goTo(current + 1); });

  function firstUnseen() {
    for (let i = 0; i < LAMINAS.length; i++) if (!seen.has(i)) return i;
    return 0;
  }

  document.addEventListener('keydown', (e) => {
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    const tag = (e.target.tagName || '').toLowerCase();
    if (tag === 'input' || tag === 'textarea') return;
    const k = e.key;
    if (!help.hidden && k !== 'h' && k !== 'H' && k !== '?' && k !== 'Escape') return;
    if (k === 'Escape' && !help.hidden) { toggleHelp(); return; }
    if (k === 'h' || k === 'H' || k === '?') { toggleHelp(); return; }
    if (k === 'n' || k === 'N') { toggleNotes(); return; }
    if (k === 't' || k === 'T') { toggleTimer(); return; }
    if (k === 'm' || k === 'M') { toggleMotion(); return; }
    if (k === 'a' || k === 'A') { toggleSound(); return; }
    if (k === 'f' || k === 'F') { toggleFull(); return; }

    if (state === 'intro' || state === 'maniobra') {
      if (k === 'Enter') { e.preventDefault(); siguiente(); }
      else if (k === 's' || k === 'S') showHub();
      else if (k === 'p' || k === 'P') entregar();
      return;
    }
    if (state === 'hub') {
      if (k === 'ArrowRight' || k === ' ' || k === 'Enter') {
        if (e.target.closest && e.target.closest('.mf-row') && k !== 'ArrowRight') return;
        e.preventDefault();
        alcanzarBulto(firstUnseen());
      } else if (k === 'p' || k === 'P') entregar();
      return;
    }
    if (state === 'slides') {
      if (k === 'ArrowRight' || k === ' ' || k === 'PageDown') {
        if (k === ' ' && e.target.closest && e.target.closest('button')) return;
        e.preventDefault();
        if (current >= LAMINAS.length - 1) entregar(); else api.goTo(current + 1);
      } else if (k === 'ArrowLeft' || k === 'PageUp') { e.preventDefault(); api.goTo(current - 1); }
      else if (k === 'Escape') showHub();
      else if (k === 'p' || k === 'P') entregar();
      return;
    }
    if (state === 'final' || state === 'destino') {
      if (k === 'r' || k === 'R' || k === 'Escape') showHub();
    }
  });

  /* ------------------------------------------------------------------------
     Arranque: muelle a oscuras, operario dormido
     ------------------------------------------------------------------------ */
  crearBultos();
  renderBox();
  setDoor(508);
  setPose(HOME().x, HOME().y, HOME_X);
  ctrl.mode = 'idle';
  setEye('off');
  applyCam();
  setNotes(NOTAS_RITUAL.intro, 'Portada');
  reduceMq.addEventListener('change', pintarMotion);
  requestAnimationFrame(loop);
})();
