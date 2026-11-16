# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Usuario primario: el tribunal evaluador de la cátedra de Programación Eficiente (Universidad Blas Pascal), en la defensa oral del Primer Parcial (Opción 6), con 10 a 15 minutos de exposición.

El equipo presentador (Edgar Karpowicz, Gastón Molina, Tomás Molina) opera el manual, pero no es la audiencia de diseño.

## Product Purpose

Presentación HTML interactiva (`docs/presentation`) que defiende, en formato de Manual Técnico de Operaciones, el Optimizador de Inventario y Pedidos: un motor experimental en Python que demuestra, mide y justifica técnicas de programación eficiente (estructuras, Big-O, memoización vs. caché, concurrencia y perfilado) mediante la dualidad estricta línea base vs. modo optimizado.

Éxito: el tribunal comprende el problema de escala, la arquitectura, las derivaciones formales, las mediciones reales y la autocrítica, y puede puntuar el trabajo al cierre del ritual de empaquetado.

## Positioning

No es un deck de diapositivas genérico. Es un manual técnico de 11 páginas con tapa dura, hojear 3D y ritual de empaquetado/puntuación dirigido al tribunal. Un vecino no podría copiar la dualidad baseline/optimizado ni las cifras empíricas del propio motor sin falsear el producto académico.

## Operating Context

- Defensa oral presencial o proyectada; cronómetro de 15:00 en la barra; atajos de teclado (Enter para abrir, flechas, T, H, pantalla completa).
- Once páginas fijas (portada → problema → diseño → Big-O → estructuras → memoización/caché → concurrencia → perfilado → tabla de rúbrica → recorrido de la app Flet → conclusiones/autocrítica).
- Cierre: ritual de empaquetado (caja isométrica, guía de expedición, firmas del equipo, puntuación del tribunal).
- El motor Python + UI Flet y los datasets (`demo_oral.json`, etc.) son evidencia demostrable, no superficies de este producto.

## Capabilities and Constraints

- Superficie única: `docs/presentation` (HTML/CSS/JS estático + `slides.json`).
- Debe preservar: nombres del equipo; UBP / PEF / Opción 6 / PEF 2026; DOC-REF PARCIAL-1-OPCION-6; dualidad baseline vs. optimizado; 11 páginas + ritual de empaquetado.
- Métricas atadas (no inventar ni redondear de forma marketing): catálogo 10.000 SKUs; lote 2.000 pedidos; speedup global 718.3x (versión final 1.12 ms vs. baseline 804.39 ms); hash ~27.0x / búsquedas individuales >260x; ProcessPool 848.12 ms (0.95x, overhead IPC en Windows); +7.2 MB de memoria del índice hash.
- Contenido de las 11 páginas y notas de orador son verdad de producto; no añadir claims, clientes ni benchmarks que el repo no respalde.
- Fuera de alcance de este registro: rediseñar la app Flet o el motor.

## Brand Commitments

- Nombre: Optimizador de Inventario y Pedidos.
- Institución y curso: Universidad Blas Pascal, Cátedra de Programación Eficiente, Primer Parcial Opción 6, año 2026.
- Equipo (firmas obligatorias): Edgar Karpowicz, Gastón Molina, Tomás Molina.
- Destinatario explícito del ritual: Tribunal Evaluador.
- Voz: técnica, precisa, autocrítica; español de cátedra de ingeniería, no marketing de startup.

## Evidence on Hand

- Presentación: `docs/presentation/index.html`, `styles.css`, `app.js`, `slides.json`.
- Narrativa y rúbrica: `README.md`, `docs/parcial-1/app-flow-explanation.md`, `docs/analisis.md`, `docs/mediciones/`.
- No hay testimonios de clientes, prensa ni casos de uso comerciales. Está prohibido fabricarlos.

## Product Principles

1. El tribunal es el usuario: cada pantalla debe ser escaneable en segundos de defensa oral, no un informe para leer en silencio.
2. Los números y nombres son evidencia, no decoración: no se alteran, no se redondean para lucir, no se inventan.
3. La dualidad baseline vs. optimizado es el argumento central; el diseño nunca la diluye.
4. El manual de 11 páginas y el ritual de empaquetado son el producto; un rediseño puede cambiar look, no el recuento ni el cierre.
5. Autocrítica incluida: el overhead de IPC y el 0.95x del ProcessPool se muestran, no se esconden.
