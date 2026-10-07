"""Validador de workflows YAML y configuración del proyecto."""

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent


# 1. Validar sintaxis YAML
try:
    import yaml

    for rel_path in [".github/workflows/verify.yml", ".github/workflows/compile.yml"]:
        full_path = BASE_DIR / rel_path
        assert full_path.exists(), f"Falta el archivo {rel_path}"
        with open(full_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        name = data.get("name")
        jobs = list(data.get("jobs", {}).keys())
        print(f"✓ {rel_path}: YAML válido. Nombre: '{name}' | Jobs: {jobs}")
except ImportError:
    print("PyYAML no está disponible para validar la sintaxis YAML.")

# 2. Validar pyproject.toml
pyproject_path = BASE_DIR / "pyproject.toml"
assert pyproject_path.exists(), "Falta pyproject.toml"
try:
    import tomllib

    with open(pyproject_path, "rb") as f:
        toml_data = tomllib.load(f)
    print(f"✓ pyproject.toml válido. Proyecto: {toml_data.get('project', {}).get('name')}")
except ImportError:
    print("tomllib no disponible (Python < 3.11).")

print("Todos los archivos de configuración validados con éxito.")
