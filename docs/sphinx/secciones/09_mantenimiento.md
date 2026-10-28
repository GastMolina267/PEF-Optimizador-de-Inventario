# 9. Mantenimiento y Reproducción Local de Controles

## 9.1. Flujo de Contribución y Buenas Prácticas

El proyecto sigue un flujo de trabajo basado en ramas temáticas y entregas por fases atómicas:

1. **Creación de Rama:** Se crea una rama a partir de `dev`:
   ```bash
   git switch dev && git pull && git switch -c feature/nueva-mejora
   ```
2. **Commits Convencionales:** Mensajes claros con prefijos convencionales (`feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `ci`, `chore`).
3. **Control Local Previo:** Antes de abrir un Pull Request, **el desarrollador debe ejecutar la suite local de controles**. Ningún código debe subirse si incumple las condiciones mínimas de calidad y seguridad.
4. **Pull Requests y Quality Gate:** Todo PR hacia `dev` o `main` debe superar la matriz de GitHub Actions y el Quality Gate de SonarQube Cloud.

---

## 9.2. Guía Canónica de Reproducción Local de Controles

En estricta conformidad con el **requisito adicional explícito de la cátedra** (*"la documentación debe explicar cómo ejecutar localmente los mismos controles de calidad y eficiencia que se ejecutan en el CI"*), a continuación se presenta la suite exacta de comandos reproducibles:

```bash
# =============================================================================
# SUITE DE VERIFICACIÓN LOCAL DE CONTROLES (PEF 2026 - PARCIAL 3)
# =============================================================================

# 1. Preparación del entorno con uv (fuente de verdad locked)
uv sync --locked --extra dev --extra docs

# 2. Compilación de sintaxis bytecode (Zero Syntax Errors)
python -m compileall -q src automations benchmarks tests scripts main.py

# 3. Linter y formato estricto de código (Ruff)
ruff check .
ruff format --check .

# 4. Complejidad cognitiva (complexipy <= 15 por función)
complexipy src automations benchmarks scripts main.py --max-complexity-allowed 15 --failed

# 5. Tipado estático estricto (Mypy)
mypy src/

# 6. Análisis estático de seguridad SAST (Bandit)
bandit -r src/ -ll

# 7. Detección preventiva de secretos (Gitleaks)
gitleaks detect --source . --verbose

# 8. Suite modular de pruebas unitarias y cobertura (Pytest >= 85%)
pytest tests/ -v --cov=src --cov-report=term-missing --cov-fail-under=85

# 9. Verificación de presupuesto de memoria heap (tracemalloc)
pytest tests/integracion/test_presupuesto_memoria.py -v

# 10. Microbenchmarks continuos de no regresión (pytest-benchmark)
pytest tests/integracion/test_benchmarks.py -v --benchmark-only

# 11. Auditoría de dependencias y vulnerabilidades (pip-audit)
pip-audit -r requirements.txt -r requirements-dev.txt

# 12. Construcción de documentación técnica externa con Sphinx (-W: cero advertencias)
sphinx-build -W -b html docs/sphinx docs/sphinx/_build/html

# 13. Validación de integridad de hipervínculos externos (Sphinx linkcheck)
sphinx-build -b linkcheck docs/sphinx docs/sphinx/_build/linkcheck
```

---

## 9.3. Diagnóstico y Resolución de Fallos en el Pipeline de CI

Si el pipeline de GitHub Actions falla en alguna de sus etapas:

| Etapa del CI | Síntoma / Error Típico | Causa Probable | Comando Local para Diagnosticar y Resolver |
|---|---|---|---|
| **Etapa 3: Calidad Estática** | `ruff format --check` falla | Diferencias de indentación o saltos de línea | `ruff format .` |
| **Etapa 3: Calidad Estática** | `complexipy` reporta CC > 15 | Función con demasiadas bifurcaciones o bucles anidados | Descomponer la función en funciones auxiliares puras. |
| **Etapa 3: Calidad Estática** | `mypy src/` reporta error de tipos | Firma de función incompatible o falta de tipos | `mypy src/` y tipar argumentos/retornos explícitamente. |
| **Etapa 3: Calidad Estática** | `bandit` falla con código 1 | Llamada insegura en `src/` | `bandit -r src/ -ll` y evaluar si es vulnerabilidad o falso positivo a etiquetar. |
| **Etapa 4: Pruebas y Cobertura** | Cobertura < 85% | Código nuevo añadido sin tests asociados | `pytest tests/ --cov=src --cov-report=term-missing` y agregar pruebas para las líneas no cubiertas. |
| **Etapa 5: Dependencias y Docs** | `sphinx-build -W` falla | Error de sintaxis en rST, MyST o docstrings rotos | `sphinx-build -W -b html docs/sphinx docs/sphinx/_build/html` |
| **Etapa 5: Dependencias y Docs** | `linkcheck` reporta enlace roto | URL externa inaccesible o 404 | Corregir hipervínculo en el documento fuente correspondiente. |
| **Etapa 6: Memoria y Benchmarks** | `test_presupuesto_memoria` falla | Fuga de memoria o procesamiento no lazy en streaming | `pytest tests/integracion/test_presupuesto_memoria.py -v -s` |
