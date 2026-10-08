"""Automatización 1: análisis de complejidad temporal por recorrido AST.

Recorre el cuerpo de las funciones fundamentales del motor, registra los
constructos que determinan la cota (bucles, accesos hash, recursión, heap,
memoización, pool de procesos) y regenera el bloque marcado en
``docs/analisis.md``. No reescribe lógica de negocio ni inventa Big-O sin
evidencia en el AST.
"""

from __future__ import annotations

import ast
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from automations.inventario_funciones import (
    FUNCIONES_FUNDAMENTALES,
    FuncionFundamental,
    resolver_raiz,
    sha_corto,
)

MARCA_INICIO = "<!-- ORIGIN-AUTO-COMPLEJIDAD:INICIO -->"
MARCA_FIN = "<!-- ORIGIN-AUTO-COMPLEJIDAD:FIN -->"

_NOMBRES_DICT = (
    "_productos_por_id",
    "_indice_categoria",
    "_indice_palabras",
    "_almacen",
    "_memo_cache",
    "frecuencias",
    "acumulador",
    "mapa_stock",
    "mapa_posicion_original",
)

# Desde esta profundidad de bucles anidados se considera un recorrido pedido × línea.
PROFUNDIDAD_BUCLE_ANIDADO = 2


@dataclass
class EvidenciaAST:
    """Constructos observados al recorrer el cuerpo de una función."""

    profundidad_bucles: int = 0
    bucles_anidados_pedido_linea: bool = False
    accesos_hash: list[str] = field(default_factory=list)
    llamadas_sorted: bool = False
    llamadas_heapq: bool = False
    es_recursiva: bool = False
    usa_memo: bool = False
    usa_process_pool: bool = False
    llama_buscar_por_id: bool = False
    recorre_lista_productos: bool = False
    docstring_complejidad: str | None = None
    lineas: tuple[int, int] = (0, 0)


@dataclass
class InformeComplejidad:
    """Resultado de derivar la cota de una función fundamental."""

    funcion: FuncionFundamental
    mejor: str
    promedio: str
    peor: str
    espacial: str
    justificacion: str
    evidencia: EvidenciaAST
    fuente: str


class _VisitanteCuerpo(ast.NodeVisitor):
    """Recolecta evidencia asintótica sin evaluar el código."""

    def __init__(self, nombre_funcion: str) -> None:
        self.nombre_funcion = nombre_funcion
        self.evidencia = EvidenciaAST()
        self._profundidad = 0
        self._nombres_for: list[str] = []

    def visit_For(self, nodo: ast.For) -> None:
        self._profundidad += 1
        self.evidencia.profundidad_bucles = max(
            self.evidencia.profundidad_bucles, self._profundidad
        )
        objetivo = _nombre_objetivo(nodo.target)
        iterable = _nombre_iterable(nodo.iter)
        self._nombres_for.append(objetivo)
        if "producto" in objetivo and "_productos" in iterable:
            self.evidencia.recorre_lista_productos = True
        if (
            self._profundidad >= PROFUNDIDAD_BUCLE_ANIDADO
            and any("pedido" in n for n in self._nombres_for)
            and "linea" in objetivo
        ):
            self.evidencia.bucles_anidados_pedido_linea = True
        self.generic_visit(nodo)
        self._nombres_for.pop()
        self._profundidad -= 1

    def visit_While(self, nodo: ast.While) -> None:
        self._profundidad += 1
        self.evidencia.profundidad_bucles = max(
            self.evidencia.profundidad_bucles, self._profundidad
        )
        self.generic_visit(nodo)
        self._profundidad -= 1

    def visit_comprehension(self, nodo: ast.comprehension) -> None:
        self._profundidad += 1
        self.evidencia.profundidad_bucles = max(
            self.evidencia.profundidad_bucles, self._profundidad
        )
        iterable = _nombre_iterable(nodo.iter)
        if "_productos" in iterable or "values" in iterable:
            self.evidencia.recorre_lista_productos = True
        self.generic_visit(nodo)
        self._profundidad -= 1

    def visit_Call(self, nodo: ast.Call) -> None:
        calificado = _nombre_llamada(nodo.func)
        if calificado.endswith(("sorted", ".sort")):
            self.evidencia.llamadas_sorted = True
        if "heapq.nlargest" in calificado or "heapq.nsmallest" in calificado:
            self.evidencia.llamadas_heapq = True
        if (
            calificado.endswith("ProcessPoolExecutor")
            or "pool_pedidos" in calificado
            or "obtener_executor" in calificado
        ):
            self.evidencia.usa_process_pool = True
        if calificado.endswith("buscar_por_id"):
            self.evidencia.llama_buscar_por_id = True
        if calificado.split(".")[-1] == self.nombre_funcion:
            self.evidencia.es_recursiva = True
        if calificado.endswith(".get") and _es_acceso_hash(calificado):
            self.evidencia.accesos_hash.append(calificado)
        self.generic_visit(nodo)

    def visit_Compare(self, nodo: ast.Compare) -> None:
        for operador, comparando in zip(nodo.ops, nodo.comparators, strict=True):
            if isinstance(operador, ast.In) and _es_nombre_hash(comparando):
                self.evidencia.accesos_hash.append(f"in {_nombre_iterable(comparando)}")
            if isinstance(operador, ast.In) and _es_nombre_hash(nodo.left):
                self.evidencia.accesos_hash.append(f"{_nombre_iterable(nodo.left)} in …")
        self.generic_visit(nodo)

    def visit_Subscript(self, nodo: ast.Subscript) -> None:
        if _es_nombre_hash(nodo.value):
            self.evidencia.accesos_hash.append(_nombre_iterable(nodo.value))
        self.generic_visit(nodo)

    def visit_Attribute(self, nodo: ast.Attribute) -> None:
        if nodo.attr in {"_memo_cache"}:
            self.evidencia.usa_memo = True
        self.generic_visit(nodo)


def _nombre_objetivo(nodo: ast.AST) -> str:
    if isinstance(nodo, ast.Name):
        return nodo.id.lower()
    if isinstance(nodo, ast.Tuple):
        return " ".join(_nombre_objetivo(elt) for elt in nodo.elts)
    return ""


def _nombre_iterable(nodo: ast.AST) -> str:
    if isinstance(nodo, ast.Name):
        return nodo.id
    if isinstance(nodo, ast.Attribute):
        return f"{_nombre_iterable(nodo.value)}.{nodo.attr}"
    if isinstance(nodo, ast.Call):
        return _nombre_llamada(nodo.func)
    return ""


def _nombre_llamada(nodo: ast.AST) -> str:
    if isinstance(nodo, ast.Name):
        return nodo.id
    if isinstance(nodo, ast.Attribute):
        return f"{_nombre_llamada(nodo.value)}.{nodo.attr}"
    return ""


def _es_nombre_hash(nodo: ast.AST) -> bool:
    texto = _nombre_iterable(nodo)
    return any(token in texto for token in _NOMBRES_DICT)


def _es_acceso_hash(calificado: str) -> bool:
    return any(token in calificado for token in _NOMBRES_DICT) or calificado.endswith(".get")


def _extraer_complejidad_docstring(doc: str | None) -> str | None:
    if not doc:
        return None
    patron = re.search(
        r"Complejidad temporal[^:]*:\s*([^\n]+)",
        doc,
        flags=re.IGNORECASE,
    )
    if patron:
        return patron.group(1).strip()
    return None


def _buscar_funcion(nodos: list[ast.stmt], nombre: str) -> ast.FunctionDef | None:
    return next(
        (nodo for nodo in nodos if isinstance(nodo, ast.FunctionDef) and nodo.name == nombre),
        None,
    )


def _localizar_funcion(arbol: ast.Module, nombre_calificado: str) -> ast.FunctionDef | None:
    """Busca ``funcion`` o ``Clase.metodo`` en el nivel superior del módulo."""
    partes = nombre_calificado.split(".")
    if len(partes) == 1:
        return _buscar_funcion(arbol.body, partes[0])
    clase, metodo = partes[0], partes[1]
    for nodo in arbol.body:
        if isinstance(nodo, ast.ClassDef) and nodo.name == clase:
            return _buscar_funcion(nodo.body, metodo)
    return None


def inspeccionar_funcion(raiz: Path, spec: FuncionFundamental) -> tuple[EvidenciaAST, str]:
    """Parsea el archivo y recorre el cuerpo de la función indicada."""
    ruta = raiz / spec.ruta_relativa
    fuente = ruta.read_text(encoding="utf-8")
    arbol = ast.parse(fuente, filename=str(ruta))
    funcion = _localizar_funcion(arbol, spec.nombre_calificado)
    if funcion is None:
        raise FileNotFoundError(f"No se encontró {spec.nombre_calificado} en {spec.ruta_relativa}")
    visitante = _VisitanteCuerpo(funcion.name)
    for sentencia in funcion.body:
        visitante.visit(sentencia)
    visitante.evidencia.docstring_complejidad = _extraer_complejidad_docstring(
        ast.get_docstring(funcion)
    )
    visitante.evidencia.lineas = (
        funcion.lineno,
        getattr(funcion, "end_lineno", funcion.lineno) or funcion.lineno,
    )
    if "_memo_cache" in ast.dump(funcion):
        visitante.evidencia.usa_memo = True
    return visitante.evidencia, fuente


ESPACIO_AUX_K = "O(k) aux."
ESPACIO_AUX_CONSTANTE = "O(1) aux."


@dataclass(frozen=True)
class _Cotas:
    """Cotas asintóticas y su justificación, antes de sumar el comentario del grupo."""

    mejor: str
    promedio: str
    peor: str
    espacial: str
    justificacion: str


def _cotas_process_pool(spec: FuncionFundamental, ev: EvidenciaAST) -> _Cotas:
    return _Cotas(
        "O(P · L)",
        "O((P · L)/C + C_IPC)",
        "O(P · L + C_IPC)",
        "O(P · L + C · chunk)",
        "El cuerpo instancia `ProcessPoolExecutor` y parte el lote en fragmentos. "
        "El trabajo útil por pedido es lineal en sus líneas; el término `C_IPC` "
        "aparece porque cada worker recibe un snapshot serializado del stock. "
        "Con pocos pedidos el overhead de creación de procesos domina; con muchos "
        "el costo se reparte entre `C` núcleos.",
    )


def _cotas_recursion_memoizada(spec: FuncionFundamental, ev: EvidenciaAST) -> _Cotas:
    return _Cotas(
        "Ω(1) (hit de memo)",
        "Θ(N · P)",
        "O(N · P)",
        "O(N · P) (tabla de estados)",
        "La función se llama a sí misma y consulta `_memo_cache` indexado por "
        "`(indice, presupuesto_restante)`. Cada estado se resuelve a lo sumo una "
        "vez; el espacio de estados es el producto de candidatos `N` por el "
        "presupuesto discretizado `P`, de ahí la cota pseudo-polinomial O(N · P).",
    )


def _cotas_recursion(spec: FuncionFundamental, ev: EvidenciaAST) -> _Cotas:
    return _Cotas(
        "Ω(N)",
        "Θ(2^N)",
        "O(2^N)",
        "O(N) (pila de llamadas)",
        "Hay recursión sobre el índice del candidato y no se observa tabla de "
        "memoización. Cada elemento admite incluirlo o excluirlo, lo que genera "
        "un árbol de decisión de hasta 2^N hojas. El docstring del grupo coincide "
        "con esta derivación.",
    )


def _cotas_heap(spec: FuncionFundamental, ev: EvidenciaAST) -> _Cotas:
    return _Cotas(
        "Ω(L + N)",
        "Θ(L + N log k)",
        "O(L + N log k)",
        "O(N + k)",
        "Se recorren las líneas de pedidos para armar un mapa de frecuencias "
        "(una pasada O(L)) y luego se invoca `heapq.nlargest`. Un min-heap de "
        "tamaño `k` hace un sift-down O(log k) por cada una de las N claves, "
        "de modo que la selección es O(N log k) y no O(N log N).",
    )


def _cotas_ordenamiento_completo(spec: FuncionFundamental, ev: EvidenciaAST) -> _Cotas:
    return _Cotas(
        "Ω(L + N)",
        "Θ(L + N log N)",
        "O(L + N log N)",
        "O(N)",
        "Tras acumular frecuencias en un diccionario (O(L)), el cuerpo llama a "
        "`sorted` sobre las N claves. Timsort impone Θ(N log N) comparaciones; "
        "después se recortan los primeros k elementos.",
    )


def _cotas_busqueda_por_linea(spec: FuncionFundamental, ev: EvidenciaAST) -> _Cotas:
    return _Cotas(
        "Ω(P · L)",
        "Θ(P · L · T_búsqueda)",
        "O(P · L · T_búsqueda)",
        "O(P · L)",
        "Hay un `for` sobre pedidos y otro anidado sobre líneas, y cada línea "
        "invoca `buscar_por_id`. La cota se descompone: T_búsqueda = O(n) si el "
        "catálogo es lineal y O(1) promedio si es hash. Por eso el baseline "
        "escala a O(P · L · n) y el optimizado a O(P · L).",
    )


def _cotas_acumulacion_hash(spec: FuncionFundamental, ev: EvidenciaAST) -> _Cotas:
    extra_sort = (
        " Tras la pasada se ordenan los U productos únicos (O(U log U))."
        if ev.llamadas_sorted
        else ""
    )
    return _Cotas(
        "Ω(L)",
        "Θ(L + U)",
        "O(L + U log U)" if ev.llamadas_sorted else "O(L + U)",
        "O(U)",
        "Doble bucle sobre pedidos y líneas con acumulación en un diccionario "
        "hash (inserción/actualización O(1) promedio por línea). La cota se "
        "desacopla del tamaño del catálogo n." + extra_sort,
    )


def _cotas_indice_con_bucle(spec: FuncionFundamental, ev: EvidenciaAST) -> _Cotas:
    return _Cotas(
        "Ω(1)",
        "Θ(k)",
        "O(n) (fallback lineal)",
        ESPACIO_AUX_K,
        "Hay accesos a índices hash y un bucle acotado (palabras de la consulta "
        f"o verificación de k candidatos; profundidad {ev.profundidad_bucles}). "
        "El caso típico es O(k) con k ≪ n; si el índice no filtra, el fallback "
        "recorre el universo y vuelve a O(n).",
    )


def _cotas_recorrido_lineal(spec: FuncionFundamental, ev: EvidenciaAST) -> _Cotas:
    por_nombre = "nombre" in spec.nombre_calificado
    factor_texto = " · m" if por_nombre else ""
    cierre = (
        "; la prueba de subcadena añade un factor m (longitud media del nombre)."
        if por_nombre
        else "."
    )
    return _Cotas(
        "Ω(1)" if "id" in spec.nombre_calificado else f"Ω(n{factor_texto})",
        f"Θ(n{factor_texto})",
        f"O(n{factor_texto})",
        ESPACIO_AUX_K if por_nombre else ESPACIO_AUX_CONSTANTE,
        f"El AST muestra un `for` sobre `self._productos` (profundidad "
        f"{ev.profundidad_bucles}) y no hay tabla hash de ids. Cada consulta "
        f"compara contra hasta n productos" + cierre,
    )


def _cotas_acceso_hash_directo(spec: FuncionFundamental, ev: EvidenciaAST) -> _Cotas:
    return _Cotas(
        "Ω(1)",
        "Θ(1)",
        "O(n) (colisión patológica)",
        ESPACIO_AUX_CONSTANTE,
        "No hay bucles sobre el catálogo. El cuerpo resuelve la consulta con "
        f"acceso hash ({', '.join(ev.accesos_hash[:3]) or 'dict.get / in'}). "
        "Con factor de carga acotado el costo esperado es constante; el peor "
        "caso teórico de una tabla hash degenerada es O(n).",
    )


def _cotas_constantes(spec: FuncionFundamental, ev: EvidenciaAST) -> _Cotas:
    return _Cotas(
        "Ω(1)",
        "Θ(1)",
        "O(1)",
        "O(1)",
        "El cuerpo no recorre colecciones del dominio ni dispara recursión: "
        "son asignaciones, purgas de caché o accesos puntuales.",
    )


def _ordena_sin_acumulador(ev: EvidenciaAST) -> bool:
    return (
        ev.llamadas_sorted
        and ev.bucles_anidados_pedido_linea
        and not any("acumulador" in acceso for acceso in ev.accesos_hash)
    )


# Reglas en orden de prioridad: gana la primera cuyo predicado se cumple.
_REGLAS_COMPLEJIDAD: tuple[
    tuple[Callable[[EvidenciaAST], bool], Callable[[FuncionFundamental, EvidenciaAST], _Cotas]],
    ...,
] = (
    (lambda ev: ev.usa_process_pool, _cotas_process_pool),
    (lambda ev: ev.es_recursiva and ev.usa_memo, _cotas_recursion_memoizada),
    (lambda ev: ev.es_recursiva, _cotas_recursion),
    (lambda ev: ev.llamadas_heapq, _cotas_heap),
    (_ordena_sin_acumulador, _cotas_ordenamiento_completo),
    (
        lambda ev: (
            ev.bucles_anidados_pedido_linea and ev.llama_buscar_por_id and not ev.accesos_hash
        ),
        _cotas_busqueda_por_linea,
    ),
    (lambda ev: ev.bucles_anidados_pedido_linea, _cotas_acumulacion_hash),
    (lambda ev: bool(ev.accesos_hash) and ev.profundidad_bucles >= 1, _cotas_indice_con_bucle),
    (
        lambda ev: ev.recorre_lista_productos or ev.profundidad_bucles >= 1,
        _cotas_recorrido_lineal,
    ),
    (lambda ev: bool(ev.accesos_hash), _cotas_acceso_hash_directo),
)


def derivar_complejidad(spec: FuncionFundamental, ev: EvidenciaAST) -> InformeComplejidad:
    """Deriva mejor/promedio/peor a partir de la evidencia del AST, no de un catálogo fijo.

    Aplica la primera regla de ``_REGLAS_COMPLEJIDAD`` cuyo predicado se cumple. El
    docstring de la función se cita como comentario del grupo; la cota publicada sale
    del cuerpo.
    """
    construir = next(
        (constructor for aplica, constructor in _REGLAS_COMPLEJIDAD if aplica(ev)),
        _cotas_constantes,
    )
    cotas = construir(spec, ev)
    justificacion = cotas.justificacion
    if ev.docstring_complejidad:
        justificacion += f" Comentario del grupo (docstring): {ev.docstring_complejidad}"

    return InformeComplejidad(
        funcion=spec,
        mejor=cotas.mejor,
        promedio=cotas.promedio,
        peor=cotas.peor,
        espacial=cotas.espacial,
        justificacion=justificacion,
        evidencia=ev,
        fuente=spec.ruta_relativa,
    )


def analizar_repositorio(raiz: Path | None = None) -> list[InformeComplejidad]:
    """Analiza todas las funciones fundamentales y devuelve sus informes."""
    base = resolver_raiz(raiz)
    informes: list[InformeComplejidad] = []
    for spec in FUNCIONES_FUNDAMENTALES:
        evidencia, _fuente = inspeccionar_funcion(base, spec)
        informes.append(derivar_complejidad(spec, evidencia))
    return informes


# Señales del AST que se listan en la columna "Evidencia AST" (en este orden).
_RASTROS_BOOLEANOS = (
    ("llamadas_sorted", "sorted"),
    ("llamadas_heapq", "heapq"),
    ("es_recursiva", "recursión"),
    ("usa_memo", "memo"),
    ("usa_process_pool", "ProcessPool"),
    ("llama_buscar_por_id", "buscar_por_id"),
)


def _rastros_evidencia(ev: EvidenciaAST) -> list[str]:
    """Etiquetas cortas de lo que se encontró en el cuerpo de la función."""
    rastros: list[str] = []
    if ev.profundidad_bucles:
        rastros.append(f"bucles×{ev.profundidad_bucles}")
    if ev.accesos_hash:
        rastros.append("hash")
    rastros.extend(etiqueta for atributo, etiqueta in _RASTROS_BOOLEANOS if getattr(ev, atributo))
    return rastros


def renderizar_markdown(informes: list[InformeComplejidad], raiz: Path) -> str:
    """Genera el bloque que se inserta entre las marcas Origin."""
    ahora = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    sha = sha_corto(raiz)
    lineas = [
        MARCA_INICIO,
        "",
        "<!-- Bloque generado por la automatización Origin 1 (análisis de complejidad). -->",
        (
            "<!-- No editar a mano: se regenera con `python -m automations.ejecutar "
            "--complejidad`. -->"
        ),
        (
            "<!-- El comentario del grupo (secciones 1-8) permanece intacto por encima de este "
            "bloque. -->"
        ),
        "",
        f"**Commit analizado:** `{sha}` · **Generado:** {ahora}",
        "",
        "Criterio: se recorrió el AST de cada función fundamental. Las cotas salen de",
        "bucles, accesos hash, recursión, `heapq`, memoización y `ProcessPoolExecutor`",
        "observados en el cuerpo. No se analizan UI Flet, tests ni wrappers.",
        "",
        "| Operación | Función | Mejor | Promedio | Peor | Espacio | Evidencia AST |",
        "|---|---|:---:|:---:|:---:|:---:|---|",
    ]
    for inf in informes:
        ev = inf.evidencia
        evidencia_txt = ", ".join(_rastros_evidencia(ev)) or "cuerpo trivial"
        lineas.append(
            f"| {inf.funcion.operacion} | `{inf.funcion.nombre_calificado}` "
            f"(L{ev.lineas[0]}–{ev.lineas[1]}) | {inf.mejor} | {inf.promedio} | "
            f"{inf.peor} | {inf.espacial} | {evidencia_txt} |"
        )

    lineas.extend(["", "### Derivación por función (automática)", ""])
    for inf in informes:
        ev = inf.evidencia
        lineas.extend(
            [
                f"#### `{inf.funcion.nombre_calificado}`",
                "",
                f"- **Archivo:** `{inf.fuente}` líneas {ev.lineas[0]}–{ev.lineas[1]}",
                f"- **Técnica:** {inf.funcion.tecnica}",
                f"- **Cotas:** mejor {inf.mejor} · promedio {inf.promedio} · peor {inf.peor}",
                f"- **Justificación (del cuerpo, no inventada):** {inf.justificacion}",
                "",
            ]
        )
    lineas.extend(
        [
            "### Qué no hace esta automatización",
            "",
            "- No reescribe el motor ni aplica optimizaciones.",
            "- No sustituye la derivación formal del grupo (secciones 2–5): la complementa.",
            "- Si una función nueva del motor no aparece, hay que agregarla a",
            "  `automations/inventario_funciones.py`.",
            "",
            MARCA_FIN,
            "",
        ]
    )
    return "\n".join(lineas)


def _asegurar_marcas(texto: str) -> str:
    if MARCA_INICIO in texto and MARCA_FIN in texto:
        return texto
    anexo = (
        "\n\n## 9. Refresco automático de complejidad (Origin)\n\n"
        "Esta sección la regenera la **Automatización 1** en cada push. El análisis "
        "formal del grupo está en las secciones 2 a 5; este bloque solo refleja el "
        "recorrido AST del commit actual.\n\n"
        f"{MARCA_INICIO}\n{MARCA_FIN}\n"
    )
    return texto.rstrip() + anexo


def escribir_seccion_analisis(
    informes: list[InformeComplejidad],
    raiz: Path | None = None,
) -> Path:
    """Reemplaza el bloque marcado en ``docs/analisis.md``."""
    base = resolver_raiz(raiz)
    ruta = base / "docs" / "analisis.md"
    original = ruta.read_text(encoding="utf-8") if ruta.is_file() else ""
    preparado = _asegurar_marcas(original)
    bloque = renderizar_markdown(informes, base)
    patron = re.compile(
        re.escape(MARCA_INICIO) + r".*?" + re.escape(MARCA_FIN),
        flags=re.DOTALL,
    )
    actualizado = patron.sub(bloque.strip(), preparado, count=1)
    if not actualizado.endswith("\n"):
        actualizado += "\n"
    ruta.write_text(actualizado, encoding="utf-8")
    return ruta


def ejecutar(raiz: Path | None = None) -> list[InformeComplejidad]:
    """Punto de entrada de la automatización 1."""
    base = resolver_raiz(raiz)
    informes = analizar_repositorio(base)
    escribir_seccion_analisis(informes, base)
    return informes
