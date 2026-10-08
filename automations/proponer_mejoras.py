"""Automatización 2: hotspots y propuestas de mejora.

Prioriza artefactos de ``docs/mediciones/`` (cProfile, line_profiler, memoria,
tabla comparativa). Si faltan informes, hace un análisis estático de bucles
anidados y búsquedas lineales. Escribe ``docs/propuestas-mejora.md`` y no
aplica ningún cambio en ``src/``.
"""

from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from automations.inventario_funciones import (
    FUNCIONES_FUNDAMENTALES,
    resolver_raiz,
    sha_corto,
)

INFORMES_PRIORITARIOS: tuple[str, ...] = (
    "cprofile_resumen.txt",
    "line_profiler_resumen.txt",
    "memoria_resumen.txt",
    "tabla_comparativa.md",
    "tabla_comparativa.txt",
    "scalene/scalene_despues.json",
    "scalene/scalene_antes.json",
)


@dataclass
class EntradaPerfil:
    """Una fila extraída de un informe de profiler."""

    origen: str
    simbolo: str
    metrica: str
    valor: float
    detalle: str


@dataclass
class PropuestaMejora:
    """Recomendación que el grupo puede medir; la automatización no la aplica."""

    titulo: str
    hotspot: str
    evidencia: str
    alternativa: str
    trade_off: str
    ya_cubierta: bool
    prioridad: str


def _informes_disponibles(raiz: Path) -> list[Path]:
    carpeta = raiz / "docs" / "mediciones"
    if not carpeta.is_dir():
        return []
    hallados: list[Path] = []
    for nombre in INFORMES_PRIORITARIOS:
        ruta = carpeta / nombre
        if ruta.is_file():
            hallados.append(ruta)
    return hallados


def _parsear_cprofile(ruta: Path) -> list[EntradaPerfil]:
    """Toma las funciones de dominio con mayor tottime / cumtime."""
    texto = ruta.read_text(encoding="utf-8", errors="replace")
    entradas: list[EntradaPerfil] = []
    # ncalls tottime percall cumtime percall filename:lineno(function)
    patron = re.compile(
        r"^\s*[\d/]+\s+([\d.]+)\s+[\d.]+\s+([\d.]+)\s+[\d.]+\s+(.+)$",
        re.MULTILINE,
    )
    for tottime_s, cumtime_s, simbolo in patron.findall(texto):
        if "src\\" not in simbolo and "src/" not in simbolo:
            # Conservar IPC del SO cuando domina el tottime (CreateProcess, pickle).
            if any(
                token in simbolo
                for token in ("CreateProcess", "WaitForSingleObject", "Pickler", "pickle")
            ):
                entradas.append(
                    EntradaPerfil(
                        "cProfile",
                        simbolo,
                        "tottime_s",
                        float(tottime_s),
                        f"cumtime={cumtime_s}s (runtime / IPC)",
                    )
                )
            continue
        entradas.append(
            EntradaPerfil(
                "cProfile",
                simbolo.replace("\\", "/"),
                "tottime_s",
                float(tottime_s),
                f"cumtime={cumtime_s}s",
            )
        )
    entradas.sort(key=lambda e: e.valor, reverse=True)
    return _deduplicar(entradas)[:12]


def _deduplicar(entradas: list[EntradaPerfil]) -> list[EntradaPerfil]:
    """Elimina filas idénticas (p. ej. tottime y cumtime del mismo símbolo)."""
    vistos: set[tuple[str, str, str, float]] = set()
    unicos: list[EntradaPerfil] = []
    for entrada in entradas:
        clave = (entrada.origen, entrada.simbolo, entrada.metrica, round(entrada.valor, 6))
        if clave in vistos:
            continue
        vistos.add(clave)
        unicos.append(entrada)
    return unicos


def _parsear_line_profiler(ruta: Path) -> list[EntradaPerfil]:
    texto = ruta.read_text(encoding="utf-8", errors="replace")
    entradas: list[EntradaPerfil] = []
    funcion_actual = "desconocida"
    for linea in texto.splitlines():
        cabecera = re.search(r"Function:\s+(\S+)", linea)
        if cabecera:
            funcion_actual = cabecera.group(1)
            continue
        # Line # Hits Time Per Hit % Time  contents
        m = re.match(
            r"^\s*(\d+)\s+(\d+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+(.*)$",
            linea,
        )
        if not m:
            continue
        pct = float(m.group(5))
        if pct < 20:
            continue
        snippet = m.group(6).strip()
        if snippet.startswith('"""') or snippet.startswith("def "):
            continue
        entradas.append(
            EntradaPerfil(
                "line_profiler",
                f"{funcion_actual}:{m.group(1)}",
                "pct_tiempo",
                pct,
                snippet[:120],
            )
        )
    entradas.sort(key=lambda e: e.valor, reverse=True)
    return entradas[:10]


def _parsear_tabla_comparativa(ruta: Path) -> list[EntradaPerfil]:
    texto = ruta.read_text(encoding="utf-8", errors="replace")
    entradas: list[EntradaPerfil] = []
    for linea in texto.splitlines():
        if not linea.startswith("| `") or "Speedup" in linea:
            continue
        celdas = [c.strip() for c in linea.strip("|").split("|")]
        if len(celdas) < 7:
            continue
        dataset, operacion = celdas[0].strip("`"), celdas[1]
        speedup_txt = celdas[6].replace("*", "").replace("x", "").strip()
        try:
            speedup = float(speedup_txt)
        except ValueError:
            continue
        # Speedup < 1 implica que lo “optimizado” fue más lento.
        if speedup < 1.0:
            entradas.append(
                EntradaPerfil(
                    "tabla_comparativa",
                    f"{dataset} / {operacion}",
                    "speedup",
                    speedup,
                    f"base={celdas[4]} ms · opt={celdas[5]} ms",
                )
            )
    return entradas


def _parsear_memoria(ruta: Path) -> list[EntradaPerfil]:
    texto = ruta.read_text(encoding="utf-8", errors="replace")
    entradas: list[EntradaPerfil] = []
    dataset = "desconocido"
    for linea in texto.splitlines():
        ds = re.search(r"DATASET:\s+(\S+)", linea)
        if ds:
            dataset = ds.group(1)
        if "Catálogo Hash" in linea or "Catálogo Lineal" in linea:
            pico = re.search(r"Pico\s*=\s*([\d.,]+)\s*KB", linea)
            if pico:
                valor = (
                    float(pico.group(1).replace(".", "").replace(",", "."))
                    if "." in pico.group(1) and "," in pico.group(1)
                    else float(pico.group(1).replace(",", "."))
                )
                entradas.append(
                    EntradaPerfil(
                        "memory_profiler",
                        f"{dataset} / {linea.strip()[:40]}",
                        "pico_kb",
                        valor,
                        linea.strip(),
                    )
                )
    return entradas


def _parsear_scalene(ruta: Path) -> list[EntradaPerfil]:
    """Extrae hotspots de CPU (Python / Nativo / Sistema) y memoria desde el JSON de Scalene."""
    try:
        data = json.loads(ruta.read_text(encoding="utf-8", errors="replace"))
    except (json.JSONDecodeError, OSError):
        return []

    entradas: list[EntradaPerfil] = []
    for archivo, info in data.get("files", {}).items():
        archivo_norm = archivo.replace("\\", "/")
        if "/src/" not in archivo_norm and "/benchmarks/" not in archivo_norm:
            continue

        # Ruta relativa al repo, sin depender de dónde se clonó en cada máquina.
        nombre_corto = archivo_norm.split("/")[-1]
        for carpeta in ("/src/", "/benchmarks/"):
            if carpeta in archivo_norm:
                nombre_corto = carpeta.strip("/") + "/" + archivo_norm.split(carpeta, 1)[1]
                break

        for linea in info.get("lines", []):
            py_pct = float(linea.get("n_cpu_percent_python", 0.0))
            c_pct = float(linea.get("n_cpu_percent_c", 0.0))
            sys_pct = float(linea.get("n_sys_percent", 0.0))
            peak_mb = float(linea.get("n_peak_mb", 0.0))
            total_cpu = py_pct + c_pct + sys_pct

            if total_cpu < 1.0 and peak_mb < 0.5:
                continue

            num_linea = linea.get("lineno", 0)
            codigo = linea.get("line", "").strip()[:80]
            metrica = "cpu_sys_ipc_pct" if sys_pct > py_pct else "cpu_python_pct"
            valor = sys_pct if sys_pct > py_pct else py_pct

            entradas.append(
                EntradaPerfil(
                    origen="Scalene",
                    simbolo=f"{nombre_corto}:{num_linea}",
                    metrica=metrica,
                    valor=round(valor, 2),
                    detalle=f"py={py_pct:.1f}% c={c_pct:.1f}% sys={sys_pct:.1f}% peak={peak_mb:.1f}MB | {codigo}",
                )
            )

    entradas.sort(key=lambda e: e.valor, reverse=True)
    return entradas[:10]


def recoger_hotspots(raiz: Path) -> list[EntradaPerfil]:
    """Lee mediciones si existen; si no, no inventa números empíricos."""
    hotspots: list[EntradaPerfil] = []
    for ruta in _informes_disponibles(raiz):
        nombre = ruta.name
        if nombre.startswith("cprofile"):
            hotspots.extend(_parsear_cprofile(ruta))
        elif nombre.startswith("line_profiler"):
            hotspots.extend(_parsear_line_profiler(ruta))
        elif nombre.startswith("tabla_comparativa"):
            hotspots.extend(_parsear_tabla_comparativa(ruta))
        elif nombre.startswith("memoria"):
            hotspots.extend(_parsear_memoria(ruta))
        elif "scalene" in nombre:
            hotspots.extend(_parsear_scalene(ruta))
    return _deduplicar(hotspots)


def _hotspots_para_informe(hotspots: list[EntradaPerfil]) -> list[EntradaPerfil]:
    """Mezcla profilers y tabla: si solo se listan los 20 tottime, se ocultan los speedup < 1×."""
    por_origen: dict[str, list[EntradaPerfil]] = {}
    for h in hotspots:
        por_origen.setdefault(h.origen, []).append(h)
    elegido: list[EntradaPerfil] = []
    for origen, cupo in (
        ("cProfile", 8),
        ("line_profiler", 4),
        ("Scalene", 6),
        ("tabla_comparativa", 8),
        ("memory_profiler", 2),
    ):
        elegido.extend(por_origen.get(origen, [])[:cupo])
    return elegido


def analisis_estatico_si_faltan_informes(raiz: Path) -> list[str]:
    """Señala bucles anidados y búsquedas lineales cuando no hay profilers."""
    avisos: list[str] = []
    for spec in FUNCIONES_FUNDAMENTALES:
        ruta = raiz / spec.ruta_relativa
        if not ruta.is_file():
            continue
        arbol = ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))
        texto = ast.dump(arbol)
        if (
            "For(" in texto
            and spec.nombre_calificado.endswith("buscar_por_id")
            and "CatalogoLineal" in spec.nombre_calificado
        ):
            avisos.append(
                f"`{spec.nombre_calificado}` recorre una lista: búsqueda lineal "
                "O(n) — ya contrastada con `CatalogoHash`."
            )
        if "ProcessPoolExecutor" in texto and "concurrente" in spec.ruta_relativa:
            avisos.append(
                f"`{spec.nombre_calificado}` crea procesos: revisar overhead de IPC "
                "en lotes chicos."
            )
    return avisos


def construir_propuestas(raiz: Path, hotspots: list[EntradaPerfil]) -> list[PropuestaMejora]:
    """Traduce evidencia empírica/estática a alternativas, sin aplicarlas."""
    propuestas: list[PropuestaMejora] = []
    textos = " ".join(f"{h.simbolo} {h.detalle}" for h in hotspots)

    speedups_bajos = [h for h in hotspots if h.origen == "tabla_comparativa" and h.valor < 1.0]
    prep = [h for h in speedups_bajos if "Preparación" in h.simbolo]
    prep_grande = next((h for h in prep if "grande.json" in h.simbolo), None)

    if (
        "CreateProcess" in textos
        or "WaitForSingleObject" in textos
        or "pickle" in textos.lower()
        or prep
    ):
        detalle_tabla = ""
        if prep_grande:
            detalle_tabla = (
                f" Tras aislar CatalogoHash, `{prep_grande.simbolo}` sigue en "
                f"speedup {prep_grande.valor:.2f}× ({prep_grande.detalle}). "
                "El 1.95× previo mezclaba búsqueda O(n) con el pool."
            )
        elif prep:
            detalle_tabla = " " + "; ".join(f"{h.simbolo} {h.valor:.2f}×" for h in prep[:4])
        propuestas.append(
            PropuestaMejora(
                titulo="Reducir el overhead de IPC del pool de procesos",
                hotspot="`_winapi.CreateProcess` / `WaitForSingleObject` / `pickle.dumps` "
                "dominan tottime en cProfile; la tabla aislada muestra speedup < 1× "
                "incluso en `grande.json`.",
                evidencia="docs/mediciones/cprofile_resumen.txt (CreateProcess 0.364 s / 0.167 s) "
                "y docs/mediciones/tabla_comparativa.md (fila Preparación, mismo CatalogoHash)."
                + detalle_tabla,
                alternativa="1) Por defecto procesar en secuencial. 2) Activar ProcessPool "
                "solo si el trabajo por pedido es pesado (p. ej. DP de combinaciones) o "
                "P es claramente mayor a 2.000. El umbral «P < 200» queda corto: con "
                "catálogo O(1), 2.000 pedidos (~21 ms) no cubren el IPC. 3) Pool "
                "persistente o `shared_memory` si se insiste en paralelizar.",
                trade_off="Menos latencia de arranque a costa de más ramas de código. "
                "En la oral conviene mostrar este negativo: no toda concurrencia escala.",
                ya_cubierta=False,
                prioridad="alta",
            )
        )

    if any("CatalogoLineal.buscar_por_id" in h.simbolo for h in hotspots):
        propuestas.append(
            PropuestaMejora(
                titulo="No usar el catálogo lineal fuera del desafío experimental",
                hotspot="`CatalogoLineal.buscar_por_id`: el `for` sobre `self._productos` "
                "concentra ~99.7 % del tiempo de la función (line_profiler, 197 850 hits).",
                evidencia="docs/mediciones/line_profiler_resumen.txt",
                alternativa="En producción/demo dejar `estrategia='optimizado'`. Conservar "
                "el lineal solo como baseline medible. Si se necesita un modo mixto, "
                "cachear el último `buscar_por_id` con el LRU ya existente.",
                trade_off="El baseline debe seguir existiendo para la rúbrica; no "
                "borrarlo. La caché no cambia la cota O(n) de la primera consulta.",
                ya_cubierta=True,
                prioridad="media",
            )
        )

    if speedups_bajos:
        ejemplos = ", ".join(h.simbolo for h in speedups_bajos[:6])
        muestras = "; ".join(
            f"{h.simbolo} {h.valor:.2f}× ({h.detalle})" for h in speedups_bajos[:4]
        )
        propuestas.append(
            PropuestaMejora(
                titulo="No pagar concurrencia ni heap en escalas donde no ganan",
                hotspot=f"Speedup < 1× en: {ejemplos}",
                evidencia="docs/mediciones/tabla_comparativa.md — " + muestras,
                alternativa="Selector automático: heap solo si N > 50 o k/N < 0.1; "
                "pool de procesos solo si el trabajo por pedido no es un lookup O(1). "
                "Documentar el umbral real (hoy el pool pierde hasta grande.json) en la oral.",
                trade_off="Más ramas de código frente a una regla simple "
                "(optimizado siempre). La claridad de la demo oral puede sufrir si "
                "el selector oculta el contraste.",
                ya_cubierta=False,
                prioridad="alta",
            )
        )

    if any(
        "Hash" in h.simbolo or "índice" in h.detalle.lower() or "indice" in h.detalle.lower()
        for h in hotspots
        if h.origen == "memory_profiler"
    ):
        propuestas.append(
            PropuestaMejora(
                titulo="Compactar el índice invertido en catálogos masivos",
                hotspot="Catálogo hash en grande.json: pico ~5 MB frente a ~84 KB del lineal.",
                evidencia="docs/mediciones/memoria_resumen.txt y columna Memoria Opt de la tabla.",
                alternativa="Almacenar posting lists como arrays de ids (`array('I')`) "
                "en lugar de `set[int]`; o un trie/prefijo si las búsquedas son por "
                "comienzo de palabra. Para 100k SKUs evaluar un índice en disco "
                "(SQLite FTS) en vez de RAM.",
                trade_off="Menos memoria y peor latencia de mutación (alta/baja de "
                "productos). El trade-off actual (tiempo por memoria) ya está "
                "justificado para 10k productos.",
                ya_cubierta=False,
                prioridad="baja",
            )
        )

    if "agrupar_pedidos_batch" in textos:
        propuestas.append(
            PropuestaMejora(
                titulo="Evitar el sort final del lote de picking si la UI no lo requiere",
                hotspot="`agrupar_pedidos_batch` aparece en tottime de cProfile (grande: 0.020 s).",
                evidencia="docs/mediciones/cprofile_resumen.txt — src/pedidos/agrupador.py:70",
                alternativa="La consolidación hash ya es O(L). El `sorted(..., reverse=True)` "
                "añade O(U log U) solo para presentación. Diferir el orden a la "
                "pantalla o usar `heapq.nlargest` si solo se muestran los U′ más demandados.",
                trade_off="La tabla de agrupación dejaría de venir preordenada. "
                "Impacto menor frente a la búsqueda lineal, pero es trabajo evitable.",
                ya_cubierta=False,
                prioridad="baja",
            )
        )

    if not propuestas:
        avisos = analisis_estatico_si_faltan_informes(raiz)
        detalle = " ".join(avisos) if avisos else "Sin informes en docs/mediciones/."
        propuestas.append(
            PropuestaMejora(
                titulo="Generar informes de profiler antes de proponer cambios",
                hotspot="No hay evidencia empírica suficiente en este commit.",
                evidencia=detalle,
                alternativa="Correr `python -m benchmarks.comparar` y los scripts "
                "`perfilar_*` sobre los mismos datasets, commitear `docs/mediciones/` "
                "y re-ejecutar esta automatización.",
                trade_off="Tiempo de medición frente a propuestas especulativas.",
                ya_cubierta=False,
                prioridad="media",
            )
        )

    return propuestas


def renderizar_markdown(
    raiz: Path,
    hotspots: list[EntradaPerfil],
    propuestas: list[PropuestaMejora],
) -> str:
    ahora = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    sha = sha_corto(raiz)
    informes = _informes_disponibles(raiz)
    lineas = [
        "# Propuestas de mejora (Automatización Origin 2)",
        "",
        "<!-- Bloque generado por la automatización de hotspots. -->",
        "<!-- No aplicar estos cambios de forma automática: el grupo decide y vuelve a medir. -->",
        "",
        f"**Commit analizado:** `{sha}` · **Generado:** {ahora}",
        "",
        "## Fuentes consultadas",
        "",
    ]
    if informes:
        for ruta in informes:
            lineas.append(f"- `{ruta.relative_to(raiz).as_posix()}`")
    else:
        lineas.append("- *(no había informes en `docs/mediciones/`; se usó análisis estático)*")

    lineas.extend(["", "## Hotspots detectados", ""])
    if hotspots:
        lineas.append("| Origen | Símbolo | Métrica | Valor | Detalle |")
        lineas.append("|---|---|---|---:|---|")
        for h in _hotspots_para_informe(hotspots):
            detalle = h.detalle.replace("|", "\\|")[:140]
            lineas.append(f"| {h.origen} | `{h.simbolo}` | {h.metrica} | {h.valor} | {detalle} |")
    else:
        lineas.append("No se extrajeron filas numéricas de los informes.")

    lineas.extend(["", "## Propuestas (no aplicadas)", ""])
    for i, p in enumerate(propuestas, start=1):
        cubierta = (
            "Sí — ya existe baseline vs optimizado"
            if p.ya_cubierta
            else "No — queda a decisión del grupo"
        )
        lineas.extend(
            [
                f"### {i}. {p.titulo}",
                "",
                f"- **Prioridad:** {p.prioridad}",
                f"- **Hotspot:** {p.hotspot}",
                f"- **Evidencia:** {p.evidencia}",
                f"- **Alternativa:** {p.alternativa}",
                f"- **Trade-off (tiempo / memoria / claridad):** {p.trade_off}",
                f"- **¿Ya cubierta por el motor actual?** {cubierta}",
                "",
            ]
        )

    lineas.extend(
        [
            "## Qué no hace esta automatización",
            "",
            "- No modifica `src/`, `benchmarks/` ni tests.",
            "- No abre un PR de código: solo actualiza este informe.",
            "- No sustituye la tabla obligatoria ni los profilers del grupo.",
            "",
        ]
    )
    return "\n".join(lineas)


def escribir_informe(
    raiz: Path | None = None,
) -> tuple[Path, list[EntradaPerfil], list[PropuestaMejora]]:
    """Regenera ``docs/propuestas-mejora.md``."""
    base = resolver_raiz(raiz)
    hotspots = recoger_hotspots(base)
    propuestas = construir_propuestas(base, hotspots)
    ruta = base / "docs" / "propuestas-mejora.md"
    ruta.write_text(renderizar_markdown(base, hotspots, propuestas), encoding="utf-8")
    return ruta, hotspots, propuestas


def ejecutar(raiz: Path | None = None) -> Path:
    """Punto de entrada de la automatización 2."""
    ruta, _hotspots, _propuestas = escribir_informe(raiz)
    return ruta
