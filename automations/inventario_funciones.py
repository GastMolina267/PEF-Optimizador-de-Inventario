"""Inventario de módulos y funciones fundamentales del motor de inventario.

El criterio de “fundamental” replica el de la planificación (Etapa 6):
operaciones del enunciado y del motor/benchmarks. Se ignoran wrappers de Flet,
handlers de UI y tests salvo que contengan el algoritmo.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class FuncionFundamental:
    """Describe una operación del motor que debe analizarse en cada push."""

    ruta_relativa: str
    nombre_calificado: str
    operacion: str
    tecnica: str


# Módulos del motor que analizan las automatizaciones (rutas relativas al repositorio).
RUTA_CATALOGO_LINEAL = "src/inventario/catalogo_lineal.py"
RUTA_CATALOGO_HASH = "src/inventario/catalogo_hash.py"
RUTA_AGRUPADOR = "src/pedidos/agrupador.py"
RUTA_COMBINACIONES = "src/pedidos/combinaciones.py"
RUTA_PROCESADOR_SECUENCIAL = "src/pedidos/procesador_secuencial.py"
RUTA_PROCESADOR_CONCURRENTE = "src/pedidos/procesador_concurrente.py"
RUTA_TOP_PRODUCTOS = "src/ranking/top_productos.py"
RUTA_CACHE = "src/cache/cache_consultas.py"

# Solo código del motor.
MODULOS_FUNDAMENTALES: tuple[str, ...] = (
    RUTA_CATALOGO_LINEAL,
    RUTA_CATALOGO_HASH,
    RUTA_AGRUPADOR,
    RUTA_COMBINACIONES,
    RUTA_PROCESADOR_SECUENCIAL,
    RUTA_PROCESADOR_CONCURRENTE,
    RUTA_TOP_PRODUCTOS,
    RUTA_CACHE,
)

# Operaciones del enunciado / rúbrica. El analizador recorre el cuerpo de cada una.
FUNCIONES_FUNDAMENTALES: tuple[FuncionFundamental, ...] = (
    FuncionFundamental(
        RUTA_CATALOGO_LINEAL,
        "CatalogoLineal.buscar_por_id",
        "Búsqueda por identificador (baseline)",
        "Recorrido lineal sobre lista",
    ),
    FuncionFundamental(
        RUTA_CATALOGO_LINEAL,
        "CatalogoLineal.buscar_por_nombre",
        "Búsqueda por nombre (baseline)",
        "Recorrido lineal + subcadena",
    ),
    FuncionFundamental(
        RUTA_CATALOGO_LINEAL,
        "CatalogoLineal.agregar",
        "Alta de producto (baseline)",
        "Verificación de unicidad en lista",
    ),
    FuncionFundamental(
        RUTA_CATALOGO_HASH,
        "CatalogoHash.buscar_por_id",
        "Búsqueda por identificador (optimizado)",
        "Tabla hash por id",
    ),
    FuncionFundamental(
        RUTA_CATALOGO_HASH,
        "CatalogoHash.buscar_por_nombre",
        "Búsqueda por nombre (optimizado)",
        "Índice invertido + verificación de subcadena",
    ),
    FuncionFundamental(
        RUTA_CATALOGO_HASH,
        "CatalogoHash.agregar",
        "Alta de producto (optimizado)",
        "Inserción hash + índices secundarios",
    ),
    FuncionFundamental(
        RUTA_AGRUPADOR,
        "agrupar_pedidos_batch",
        "Agrupación / batch picking",
        "Acumulador hash en una pasada",
    ),
    FuncionFundamental(
        RUTA_TOP_PRODUCTOS,
        "calcular_top_solicitados_lineal",
        "Top-N más solicitados (baseline)",
        "Ordenamiento total de frecuencias",
    ),
    FuncionFundamental(
        RUTA_TOP_PRODUCTOS,
        "calcular_top_solicitados_heap",
        "Top-N más solicitados (optimizado)",
        "Montículo acotado heapq.nlargest",
    ),
    FuncionFundamental(
        RUTA_COMBINACIONES,
        "BuscadorAlternativas._resolver_recursivo_puro",
        "Combinaciones sustitutas (baseline)",
        "Árbol recursivo exhaustivo",
    ),
    FuncionFundamental(
        RUTA_COMBINACIONES,
        "BuscadorAlternativas._resolver_dp_memo",
        "Combinaciones sustitutas (optimizado)",
        "Programación dinámica con memoización",
    ),
    FuncionFundamental(
        RUTA_PROCESADOR_SECUENCIAL,
        "procesar_pedidos_secuencial",
        "Preparación de pedidos (secuencial)",
        "Mono-hilo, una búsqueda por línea",
    ),
    FuncionFundamental(
        RUTA_PROCESADOR_CONCURRENTE,
        "procesar_pedidos_concurrente",
        "Preparación de pedidos (concurrente)",
        "ProcessPoolExecutor + snapshot de stock",
    ),
    FuncionFundamental(
        RUTA_CACHE,
        "CacheLRU.obtener",
        "Consulta de caché LRU",
        "Acceso hash + política LRU",
    ),
    FuncionFundamental(
        RUTA_CACHE,
        "CacheLRU.guardar",
        "Escritura de caché LRU",
        "Inserción hash + desalojo del menos reciente",
    ),
    FuncionFundamental(
        RUTA_CACHE,
        "GestorCacheConsultas.invalidar_por_mutacion_stock",
        "Invalidación reactiva por stock",
        "Purga de búsquedas y categorías",
    ),
)

# Prefijos de ruta que nunca se analizan (UI, tests, wrappers).
RUTAS_EXCLUIDAS: tuple[str, ...] = (
    "src/ui/",
    "tests/",
    "benchmarks/",
)


def resolver_raiz(desde: Path | None = None) -> Path:
    """Localiza la raíz del repositorio a partir de un archivo o del CWD."""
    candidato = (desde or Path.cwd()).resolve()
    if candidato.is_file():
        candidato = candidato.parent
    for directorio in (candidato, *candidato.parents):
        if (directorio / "docs" / "project-planning.md").is_file():
            return directorio
    return Path.cwd().resolve()


def sha_corto(raiz: Path) -> str:
    """Hash corto del commit actual (``git rev-parse --short HEAD``) o ``desconocido``."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=raiz,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "desconocido"
