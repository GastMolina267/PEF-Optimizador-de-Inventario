"""Resume y compara dos perfiles de Scalene (antes / después) en Markdown.

Uso::

    python -m benchmarks.resumir_scalene
    python -m benchmarks.resumir_scalene --antes a.json --despues b.json --entorno "Windows 11, 8 núcleos"

Genera ``docs/mediciones/scalene/resumen.md``. Los porcentajes de Scalene son relativos al
tiempo total de cada corrida: sirven para ver dónde se va el tiempo dentro de un perfil;
para comparar perfiles entre sí, la referencia es el tiempo total.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SCALENE_DIR = BASE_DIR / "docs" / "mediciones" / "scalene"
CARPETAS_PROYECTO = ("/src/", "/benchmarks/")
UMBRAL_PORCENTAJE = 1.0
MAX_FILAS = 12


@dataclass
class PerfilFuncion:
    """Tiempo de una función según Scalene, en % del total de la corrida."""

    python: float
    nativo: float
    sistema: float
    pico_mb: float

    @property
    def total(self) -> float:
        return self.python + self.nativo + self.sistema


@dataclass
class Perfil:
    """Datos globales y por función de un perfil de Scalene."""

    segundos: float
    pico_mb: float
    funciones: dict[str, PerfilFuncion]


def _ruta_relativa(archivo: str) -> str:
    normalizado = "/" + archivo.replace("\\", "/").lstrip("./")
    for carpeta in CARPETAS_PROYECTO:
        if carpeta in normalizado:
            return carpeta.strip("/") + "/" + normalizado.split(carpeta, 1)[1]
    return normalizado.rsplit("/", 1)[-1]


def cargar_perfil(ruta: Path) -> Perfil:
    """Lee un JSON de Scalene y agrupa el tiempo por función del proyecto."""
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    funciones: dict[str, PerfilFuncion] = {}
    for archivo, info in datos.get("files", {}).items():
        relativo = _ruta_relativa(archivo)
        for funcion in info.get("functions", []):
            clave = f"{relativo} · {funcion['line'].strip()}"
            funciones[clave] = PerfilFuncion(
                python=float(funcion.get("n_cpu_percent_python", 0.0)),
                nativo=float(funcion.get("n_cpu_percent_c", 0.0)),
                sistema=float(funcion.get("n_sys_percent", 0.0)),
                pico_mb=float(funcion.get("n_peak_mb", 0.0)),
            )
    return Perfil(
        segundos=float(datos.get("elapsed_time_sec", 0.0)),
        pico_mb=float(datos.get("max_footprint_mb", 0.0)),
        funciones=funciones,
    )


def _celda(perfil: PerfilFuncion | None) -> str:
    if perfil is None or perfil.total < UMBRAL_PORCENTAJE:
        return "—"
    return (
        f"{perfil.total:.1f} % (py {perfil.python:.0f} · nat {perfil.nativo:.0f} "
        f"· sis {perfil.sistema:.0f})"
    )


def _totales(perfil: Perfil) -> tuple[float, float, float]:
    funciones = perfil.funciones.values()
    return (
        sum(f.python for f in funciones),
        sum(f.nativo for f in funciones),
        sum(f.sistema for f in funciones),
    )


def generar_resumen(antes: Perfil, despues: Perfil, entorno: str) -> str:
    """Arma el Markdown comparativo."""
    variacion = 100.0 * (despues.segundos - antes.segundos) / antes.segundos
    sentido = "menos" if variacion < 0 else "más"
    py_a, nat_a, sis_a = _totales(antes)
    py_d, nat_d, sis_d = _totales(despues)

    claves = sorted(
        set(antes.funciones) | set(despues.funciones),
        key=lambda c: max(
            antes.funciones.get(c, PerfilFuncion(0, 0, 0, 0)).total,
            despues.funciones.get(c, PerfilFuncion(0, 0, 0, 0)).total,
        ),
        reverse=True,
    )
    filas = [
        f"| `{clave}` | {_celda(antes.funciones.get(clave))} | {_celda(despues.funciones.get(clave))} |"
        for clave in claves[:MAX_FILAS]
        if max(
            antes.funciones.get(clave, PerfilFuncion(0, 0, 0, 0)).total,
            despues.funciones.get(clave, PerfilFuncion(0, 0, 0, 0)).total,
        )
        >= UMBRAL_PORCENTAJE
    ]

    return f"""# Scalene: antes y después de la propuesta Origin 1

Generado por `python -m benchmarks.resumir_scalene`. No editar a mano.

- **Antes:** código al cierre de F3 (commit `823bb18`), antes de los cambios de IPC.
- **Después:** código actual.
- **Escenario:** `benchmarks/perfilar_scalene.py` (búsquedas, picking, Top-N, alternativas y
  30 vueltas de procesamiento secuencial y con pool sobre `grande.json`).
- **Entorno:** {entorno}

## Resultado global

| Métrica | Antes | Después |
|---|---:|---:|
| Tiempo total bajo Scalene (s) | {antes.segundos:.2f} | {despues.segundos:.2f} |
| Pico de memoria (MB) | {antes.pico_mb:.1f} | {despues.pico_mb:.1f} |
| Tiempo en Python (% del total) | {py_a:.1f} | {py_d:.1f} |
| Tiempo en código nativo (% del total) | {nat_a:.1f} | {nat_d:.1f} |
| Tiempo de sistema: esperas, IPC, E/S (% del total) | {sis_a:.1f} | {sis_d:.1f} |

El escenario completo tardó un **{abs(variacion):.0f} % {sentido}** después de los cambios.

## Dónde se va el tiempo, por función

Porcentaje del tiempo total de cada corrida (Python · nativo · sistema). "—" indica menos
de {UMBRAL_PORCENTAJE:.0f} %.

| Función | Antes | Después |
|---|---|---|
{chr(10).join(filas)}

## Cómo leerlo

- **Tiempo de sistema** en las funciones del pool es el proceso principal esperando a los
  workers y moviendo datos por el canal IPC. Es el costo que ataca la propuesta Origin 1.
- **Nativo** incluye `pickle` y `json` (implementados en C) y la creación de dataclasses.
- Los porcentajes son relativos a cada corrida. Para comparar entre corridas, usar el
  tiempo total de la primera tabla.
"""


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Compara dos perfiles de Scalene.")
    parser.add_argument("--antes", type=Path, default=SCALENE_DIR / "scalene_antes.json")
    parser.add_argument("--despues", type=Path, default=SCALENE_DIR / "scalene_despues.json")
    parser.add_argument("--salida", type=Path, default=SCALENE_DIR / "resumen.md")
    parser.add_argument("--entorno", default="sin especificar")
    args = parser.parse_args(argv)

    contenido = generar_resumen(
        cargar_perfil(args.antes), cargar_perfil(args.despues), args.entorno
    )
    args.salida.write_text(contenido, encoding="utf-8")
    print(f"Resumen generado en {args.salida}")


if __name__ == "__main__":
    main()
