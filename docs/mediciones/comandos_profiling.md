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

### Ejecución del escenario de Scalene

Desde la raíz del repo. `--program-path .` hace que Scalene perfile también `src/` y no solo
el script; `--memory` activa el perfil de memoria.

```powershell
scalene run --memory --program-path . -o docs/mediciones/scalene/scalene_despues.json benchmarks/perfilar_scalene.py
```

Para el perfil "antes", correr el mismo escenario sobre el commit `823bb18` (cierre de F3)
en la misma máquina, por ejemplo con `git worktree add ../antes 823bb18` y copiando
`benchmarks/perfilar_scalene.py`, y guardar la salida como `scalene_antes.json`.

### Reporte HTML autónomo y resumen comparativo

```powershell
scalene view --standalone docs/mediciones/scalene/scalene_despues.json   # genera scalene-profile.html
python -m benchmarks.resumir_scalene --entorno "Windows 11, Python 3.13, 8 núcleos"
```

- **Perfiles:** `docs/mediciones/scalene/scalene_antes.json` y `scalene_despues.json` (más sus `.html`).
- **Resumen:** `docs/mediciones/scalene/resumen.md`, con el tiempo total y el desglose por función
  en Python, código nativo y sistema (esperas e IPC).
- **Comparar en igualdad de condiciones:** ambos perfiles en la misma máquina y con el mismo
  método de creación de workers. En Linux, la versión anterior usaba `fork`; para la corrida
  "después" se puede forzar con `PEF_MP_START_METHOD=fork`. En Windows ambas usan `spawn`.

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
