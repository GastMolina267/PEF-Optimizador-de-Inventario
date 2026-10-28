# 3. Instalación y Configuración

## 3.1. Requisitos Previos

- **Python:** Versión 3.10 o superior (el proyecto está completamente testeado y optimizado sobre Python 3.14).
- **Herramienta de Gestión:** [uv](https://docs.astral.sh/uv/) (recomendado por velocidad y reproducibilidad estricta con `uv.lock`) o `pip` estándar.
- **Sistema Operativo:** Compatible con Windows, Linux y macOS.

---

## 3.2. Clonación y Preparación del Entorno

```bash
# 1. Clonar el repositorio
git clone https://github.com/GastMolina267/PEF-Optimizador-de-Inventario.git
cd PEF-Optimizador-de-Inventario

# 2. Opción A: Instalación automatizada y locked con uv (recomendada)
uv sync --locked --extra dev --extra docs

# 3. Opción B: Instalación tradicional con virtualenv y pip
python -m venv .venv

# Activar en Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Activar en Linux / macOS:
source .venv/bin/activate

# Instalar dependencias base, desarrollo y documentación:
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

---

## 3.3. Comandos de Ejecución del Sistema

### 1. Iniciar la Aplicación de Escritorio (Flet)

```bash
# Modo ejecución directa del módulo UI:
python -m src.ui.app

# O mediante el entry point unificado con soporte PyInstaller:
python main.py
```

### 2. Ejecutar la Suite de Comparación y Benchmarks

```bash
# Tabla comparativa oficial completa (Línea Base vs Optimizado):
python -m benchmarks.comparar

# Perfilado determinista con cProfile:
python -m benchmarks.perfilar_cprofile

# Perfilado línea a línea con line_profiler:
python -m benchmarks.perfilar_lineas

# Perfilado de consumo heap con memory_profiler / tracemalloc:
python -m benchmarks.perfilar_memoria
```

### 3. Ejecutar las Pruebas Automatizadas

```bash
# Ejecutar los 198 tests unitarios y de integración:
pytest tests/ -v

# Ejecutar con medición de cobertura estricta (umbral 85%):
pytest tests/ -v --cov=src --cov-report=term-missing --cov-fail-under=85
```

### 4. Compilación Standalone Nativa (PyInstaller)

El sistema incluye un script automatizado para generar binarios independientes sin dependencias externas:

```bash
# Compilar en modo directorio (recomendado):
python scripts/compile.py

# Compilar en modo ejecutable único (onefile):
python scripts/compile.py --mode onefile

# El binario resultante se encontrará en dist/OptimizadorInventario/
```
