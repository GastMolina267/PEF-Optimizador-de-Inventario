# Guía de Comandos de Perfilado y Herramientas Avanzadas

Este documento detalla los comandos y procedimientos para ejecutar las herramientas de perfilado empírico del proyecto (**cProfile**, **line_profiler**, **memory_profiler**, **Scalene** y **py-spy**).

---

## 1. Perfilado por Funciones (cProfile y pstats)

`cProfile` es el analizador determinista estándar de CPython. Permite identificar qué funciones consumen la mayor proporción de tiempo acumulado (`cumulative`) y propio (`tottime`).

### Ejecución directa del script del proyecto
```powershell
python -m benchmarks.perfilar_cprofile
```
- **Salida en texto:** `docs/mediciones/cprofile_resumen.txt`
- **Dumps binarios:** `docs/mediciones/escenario_mediano.prof` y `docs/mediciones/escenario_grande.prof`

### Visualización interactiva de los archivos `.prof`
Con herramientas como SnakeViz (si está instalada):
```powershell
snakeviz docs/mediciones/escenario_grande.prof
```

---

## 2. Perfilado Línea a Línea (line_profiler)

`line_profiler` desglosa el tiempo consumido instrucción por instrucción en las funciones críticas.

### Ejecución directa del script del proyecto
```powershell
python -m benchmarks.perfilar_lineas
```
- **Salida:** `docs/mediciones/line_profiler_resumen.txt`
- **Métricas reportadas:** `Hits` (llamadas), `Time` (tiempo total), `Per Hit` (promedio por línea), `% Time` (porcentaje del total).

---

## 3. Perfilado de Memoria (memory_profiler y tracemalloc)

Analiza la asignación neta en heap de las estructuras de datos y el impacto de la retención de memoria.

### Ejecución directa del script del proyecto
```powershell
python -m benchmarks.perfilar_memoria
```
- **Salida:** `docs/mediciones/memoria_resumen.txt`
- **Métricas:** Comparación de catálogo lineal vs. hash, ahorro de memoria con Min-Heap frente a `sorted()`, y ciclo de vida de la caché LRU.

---

## 4. Perfilado de Alto Nivel con Scalene (CPU, Memoria, IPC y Tiempo Nativo C)

Scalene es un profiler de alta precisión que discrimina el tiempo invertido en código Python puro, código nativo C, llamadas al sistema/IPC (Windows) y consumo de memoria.

### Ejecución directa del benchmark oficial de Scalene
```powershell
python -m scalene run -o docs/mediciones/scalene/scalene_despues.json benchmarks/perfilar_scalene.py
```

### Generación de reporte interactivo HTML autónomo (standalone)
```powershell
python -m scalene view --standalone docs/mediciones/scalene/scalene_despues.json
```
- **Reportes JSON generados:** `docs/mediciones/scalene/scalene_antes.json` y `docs/mediciones/scalene/scalene_despues.json`.
- **Reportes interactivos HTML:** `docs/mediciones/scalene/scalene_antes.html` y `docs/mediciones/scalene/scalene_despues.html`.
- **Métricas:** Desglose exacto de `% Python`, `% C`, `% Sistema (IPC)` y asignación de memoria pico por línea.

---

## 5. Muestreo y Flamegraphs con py-spy

`py-spy` es un profiler por muestreo (*sampling profiler*) escrito en Rust que corre fuera del espacio de ejecución de Python, con casi cero overhead.

### Generar un Flamegraph SVG interactivo
```powershell
py-spy record -o docs/mediciones/flamegraph.svg -- python -m benchmarks.comparar
```

### Monitoreo en vivo en terminal (Modo `top`)
Permite inspeccionar en tiempo real qué función está consumiendo CPU mientras la aplicación o los benchmarks están activos:
```powershell
# Obtener el PID de Python y ejecutar:
py-spy top --pid <PID>
```
O directamente lanzando el proceso:
```powershell
py-spy top -- python -m benchmarks.comparar
```

---

## 6. Ejecución de la Suite Comparativa Oficial

Ejecuta todas las operaciones sobre los 4 datasets estándar (`demo_oral.json`, `pequeno.json`, `mediano.json`, `grande.json`):
```powershell
python -m benchmarks.comparar
```
- **Salida en Markdown:** `docs/mediciones/tabla_comparativa.md`
- **Salida en Texto:** `docs/mediciones/tabla_comparativa.txt`
