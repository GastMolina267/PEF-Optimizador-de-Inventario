# Documentación del Proyecto: Optimizador de Inventario y Pedidos

Bienvenido al repositorio central de documentación técnica, académica y metodológica del proyecto desarrollado para la cátedra de **Programación Eficiente** (Universidad Blas Pascal, 2026).

---

## 🗂️ Estructura y Organización de Documentos

La documentación se organiza cronológica y temáticamente por hitos de entrega académica, preservando la trazabilidad de la evolución del software desde la línea base inicial hasta la integración de Inteligencia Artificial:

```
docs/
├── README.md                           # Este índice de navegación canónico
├── parcial-1/                          # Primer Parcial (Estructuras de datos, DP, Heaps, Cache)
│   ├── project-planning.md             # Planificación inicial y división en 7 etapas
│   ├── option-six-to-be-implemented.txt # Enunciado y rúbrica oficial de la cátedra (Opción 6)
│   ├── app-flow-explanation.md         # Explicación exhaustiva del flujo de datos y funciones backend
│   └── Primer-Parcial-Programacion-Eficiente.docx # Consigna original de la cátedra
├── parcial-2/                          # Segundo Parcial (Concurrencia, Streaming, APM)
│   ├── planificacion-parcial-2.md      # Planificación de fases de concurrencia y telemetría
│   ├── resumen-parcial-2.md            # Resumen de logros, speedups y autocrítica IPC
│   ├── observabilidad-apm.md           # Arquitectura de instrumentación y Elastic APM
│   └── Parcial-II.txt                  # Requerimientos y pautas del Parcial 2
├── parcial-3/                          # Tercer Parcial (CI/CD, SAST, SCA, QA, Sphinx Docs)
│   ├── planificacion-parcial-3.md      # Plan de 7 etapas de Aduana de CI, SonarCloud y Sphinx
│   ├── seguridad-politica.md           # Política de seguridad, mitigación SAST y triaje de falsos positivos
│   └── Parcial-3.docx                  # Consigna y pautas oficiales del Parcial 3
├── final/                              # Proyecto Final (Inteligencia Artificial Aplicada e Integrada)
│   ├── planificacion-proyecto-final.md # Plan de trabajo (7 fases P4.0 a P4.6) y especificación técnica
│   └── Programacion-eficiente.pptx     # Presentación de cátedra con pautas del proyecto final (pág. 356+)
├── analisis.md                         # Derivación formal de complejidades temporales y espaciales
├── propuestas-mejora.md                # Diagnóstico continuo de hotspots y oportunidades de refactor
├── automatizaciones-origin.md          # Especificación de automations locales y en la nube (Cursor Origin)
├── prompts-origin/                     # Prompts reproducibles para agentes de análisis AST y métricas
├── mediciones/                         # Reportes empíricos (.prof, .txt, .json, Scalene, memory_profiler)
├── presentation/                       # Presentación interactiva Parcial 1 (11 diapositivas)
├── presentation-parcial-2/             # Presentación interactiva Parcial 2 (Auditoría de Remito)
├── presentation-parcial-3/             # Presentación interactiva Parcial 3 (Aduana de CI en 7 etapas)
└── sphinx/                             # Suite de documentación Sphinx + Furo publicada en GitHub Pages
```

---

## 🎯 Acceso Rápido por Hito Académico

### 1. Proyecto Final — Inteligencia Artificial (2026)
- 🤖 **Plan de Implementación:** [final/planificacion-proyecto-final.md](final/planificacion-proyecto-final.md)
- 📊 **Presentación de Cátedra:** [final/Programacion-eficiente.pptx](final/Programacion-eficiente.pptx)
- **Objetivos Centrales:**
  - **IA aplicada al desarrollo de software:** Asistentes de IA para generación rigurosa de pruebas de estrés, análisis de mutación, detección de regresiones de memoria y optimización de código, con validación empírica obligatoria.
  - **IA integrada en la aplicación:** Subsistema `src/ia/` con predictor inteligente de demanda y alerta temprana de quiebre de stock (`scikit-learn`), enfrentado empíricamente contra la regla analítica convencional $O(1)$ de punto de reorden bajo métricas estrictas de latencia ($\mu s$), memoria heap (`tracemalloc`) y precisión predictiva ($R^2$, $MAE$).

### 2. Tercer Parcial — Calidad Continua, Seguridad y CI/CD
- 📋 **Planificación Integral:** [parcial-3/planificacion-parcial-3.md](parcial-3/planificacion-parcial-3.md)
- 🛡️ **Política de Seguridad:** [parcial-3/seguridad-politica.md](parcial-3/seguridad-politica.md)
- 🖥️ **Presentación Interactiva:** [presentation-parcial-3/index.html](presentation-parcial-3/index.html)

### 3. Segundo Parcial — Concurrencia, Streaming y APM
- 📋 **Planificación del Hito:** [parcial-2/planificacion-parcial-2.md](parcial-2/planificacion-parcial-2.md)
- 📈 **Resumen y Autocrítica IPC:** [parcial-2/resumen-parcial-2.md](parcial-2/resumen-parcial-2.md)
- 📡 **Observabilidad APM:** [parcial-2/observabilidad-apm.md](parcial-2/observabilidad-apm.md)
- 🖥️ **Presentación Interactiva:** [presentation-parcial-2/index.html](presentation-parcial-2/index.html)

### 4. Primer Parcial — Algoritmos, Estructuras y Rendimiento
- 📋 **Plan Canónico:** [parcial-1/project-planning.md](parcial-1/project-planning.md)
- 🔍 **Flujo de la Aplicación:** [parcial-1/app-flow-explanation.md](parcial-1/app-flow-explanation.md)
- 📜 **Enunciado y Rúbrica:** [parcial-1/option-six-to-be-implemented.txt](parcial-1/option-six-to-be-implemented.txt)
- 🖥️ **Presentación Interactiva (11 Slides):** [presentation/index.html](presentation/index.html)

---

## 📖 Documentación Canónica en Sphinx
La documentación técnica completa, con navegación multi-página, diagramas Mermaid interactivos y autodoc de clases y módulos se compila con:

```bash
# Compilar documentación localmente
.venv/Scripts/sphinx-build -W -b html docs/sphinx docs/sphinx/_build/html

# Visualizar en el navegador
start docs/sphinx/_build/html/index.html
```

Versión desplegada automáticamente en GitHub Pages ante cada push a `main`:
🔗 **[gastmolina267.github.io/PEF-Optimizador-de-Inventario](https://gastmolina267.github.io/PEF-Optimizador-de-Inventario/)**
