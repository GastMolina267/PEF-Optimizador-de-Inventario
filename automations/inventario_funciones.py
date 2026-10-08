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


# Rutas relativas al raíz del repositorio. Solo código del motor.
MODULOS_FUNDAMENTALES: tuple[str, ...] = (
    "src/inventario/catalogo_lineal.py",
    "src/inventario/catalogo_hash.py",
    "src/pedidos/agrupador.py",
    "src/pedidos/combinaciones.py",
    "src/pedidos/procesador_secuencial.py",
    "src/pedidos/procesador_concurrente.py",
    "src/ranking/top_productos.py",
    "src/cache/cache_consultas.py",
)

# Operaciones del enunciado / rúbrica. El analizador recorre el cuerpo de cada una.
FUNCIONES_FUNDAMENTALES: tuple[FuncionFundamental, ...] = (
    FuncionFundamental(
        "src/inventario/catalogo_lineal.py",
        "CatalogoLineal.buscar_por_id",
        "Búsqueda por identificador (baseline)",
        "Recorrido lineal sobre lista",
    ),
    FuncionFundamental(
        "src/inventario/catalogo_lineal.py",
        "CatalogoLineal.buscar_por_nombre",
        "Búsqueda por nombre (baseline)",
        "Recorrido lineal + subcadena",
    ),
    FuncionFundamental(
        "src/inventario/catalogo_lineal.py",
        "CatalogoLineal.agregar",
        "Alta de producto (baseline)",
        "Verificación de unicidad en lista",
    ),
    FuncionFundamental(
        "src/inventario/catalogo_hash.py",
        "CatalogoHash.buscar_por_id",
        "Búsqueda por identificador (optimizado)",
        "Tabla hash por id",
    ),
    FuncionFundamental(
        "src/inventario/catalogo_hash.py",
        "CatalogoHash.buscar_por_nombre",
        "Búsqueda por nombre (optimizado)",
        "Índice invertido + verificación de subcadena",
    ),
    FuncionFundamental(
        "src/inventario/catalogo_hash.py",
        "CatalogoHash.agregar",
        "Alta de producto (optimizado)",
        "Inserción hash + índices secundarios",
    ),
    FuncionFundamental(
        "src/pedidos/agrupador.py",
        "agrupar_pedidos_batch",
        "Agrupación / batch picking",
        "Acumulador hash en una pasada",
    ),
    FuncionFundamental(
        "src/ranking/top_productos.py",
        "calcular_top_solicitados_lineal",
        "Top-N más solicitados (baseline)",
        "Ordenamiento total de frecuencias",
    ),
    FuncionFundamental(
        "src/ranking/top_productos.py",
        "calcular_top_solicitados_heap",
        "Top-N más solicitados (optimizado)",
        "Montículo acotado heapq.nlargest",
    ),
    FuncionFundamental(
        "src/pedidos/combinaciones.py",
        "BuscadorAlternativas._resolver_recursivo_puro",
        "Combinaciones sustitutas (baseline)",
        "Árbol recursivo exhaustivo",
    ),
    FuncionFundamental(
        "src/pedidos/combinaciones.py",
        "BuscadorAlternativas._resolver_dp_memo",
        "Combinaciones sustitutas (optimizado)",
        "Programación dinámica con memoización",
    ),
    FuncionFundamental(
        "src/pedidos/procesador_secuencial.py",
        "procesar_pedidos_secuencial",
        "Preparación de pedidos (secuencial)",
        "Mono-hilo, una búsqueda por línea",
    ),
    FuncionFundamental(
        "src/pedidos/procesador_concurrente.py",
        "procesar_pedidos_concurrente",
        "Preparación de pedidos (concurrente)",
        "ProcessPoolExecutor + snapshot de stock",
    ),
    FuncionFundamental(
        "src/cache/cache_consultas.py",
        "CacheLRU.obtener",
        "Consulta de caché LRU",
        "Acceso hash + política LRU",
    ),
    FuncionFundamental(
        "src/cache/cache_consultas.py",
        "CacheLRU.guardar",
        "Escritura de caché LRU",
        "Inserción hash + desalojo del menos reciente",
    ),
    FuncionFundamental(
        "src/cache/cache_consultas.py",
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
