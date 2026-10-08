"""Pruebas de los ajustes sobre F3-F5 (rama p2/f5b-ajustes-f3-f5).

Cubren:
1. El núcleo único de evaluación (evaluar_lineas y sus helpers).
2. El procesador concurrente: sub-mapa de stock por fragmento y descuento secuencial.
3. El procesamiento JSONL: misma salida en secuencial y paralelo, lotes en vuelo
   acotados y validación de pedidos sin líneas.
4. El motor: secuencial por defecto.
5. GestorPool: método de creación de workers.
6. La UI: orden de tablas y panel de estado centralizados en PantallaBase.
7. Los generadores de informes de benchmarks (Scalene y archivos grandes).
"""

from __future__ import annotations

import json
import multiprocessing
from concurrent.futures import Future
from pathlib import Path

import pytest

from benchmarks import perfilar_archivos_grandes as bench
from benchmarks.resumir_scalene import cargar_perfil, generar_resumen
from src.datos import procesador_lotes_paralelo as lotes
from src.datos.procesador_lotes_paralelo import (
    procesar_pedidos_jsonl_paralelo,
    procesar_pedidos_jsonl_secuencial,
)
from src.inventario.catalogo_hash import CatalogoHash
from src.modelos.pedido import EstadoPedido, LineaPedido, Pedido
from src.modelos.producto import Producto
from src.motor.motor_inventario import MotorInventario
from src.pedidos import gestor_pool
from src.pedidos.evaluador import (
    ContadorEstados,
    crear_consulta_stock,
    evaluar_lineas,
    evaluar_pedido,
    evaluar_pedido_compacto,
    resultado_desde_compacto,
)
from src.pedidos.procesador_concurrente import _armar_fragmentos, procesar_pedidos_concurrente
from src.pedidos.procesador_secuencial import procesar_pedidos_secuencial
from src.ui.pantallas import (
    PantallaAgrupacion,
    PantallaAlternativas,
    PantallaCatalogo,
    PantallaComparacion,
    PantallaPedidos,
    PantallaTopProductos,
)

BASE_DIR = Path(__file__).resolve().parent.parent
DEMO_ORAL = BASE_DIR / "data" / "datasets" / "demo_oral.json"


def _catalogo(stocks: dict[int, int]) -> CatalogoHash:
    return CatalogoHash(
        [
            Producto(id_, f"Producto {id_}", "Ferretería y Herramientas", stock, 100.0)
            for id_, stock in stocks.items()
        ]
    )


def _escribir_jsonl(ruta: Path, pedidos: list[dict]) -> Path:
    ruta.write_text("\n".join(json.dumps(p) for p in pedidos) + "\n", encoding="utf-8")
    return ruta


# =========================================================================
# 1. Núcleo de evaluación
# =========================================================================


class TestNucleoEvaluacion:
    def test_cubierto(self):
        estado, lineas = evaluar_lineas([(1, 5), (2, 3)], lambda i: {1: 10, 2: 3}.get(i, 0))
        assert estado is EstadoPedido.CUBIERTO
        assert lineas == ((1, 5, 5, 0), (2, 3, 3, 0))

    def test_parcial_ordena_cubiertas_primero(self):
        estado, lineas = evaluar_lineas([(2, 5), (1, 4)], lambda i: {1: 10, 2: 3}.get(i, 0))
        assert estado is EstadoPedido.PARCIAL
        assert lineas == ((1, 4, 4, 0), (2, 5, 3, 2))

    def test_imposible(self):
        estado, lineas = evaluar_lineas([(3, 2), (9, 1)], lambda i: 0)
        assert estado is EstadoPedido.IMPOSIBLE
        assert lineas == ((3, 2, 0, 2), (9, 1, 0, 1))

    def test_roundtrip_compacto_igual_a_evaluar_pedido(self):
        pedido = Pedido(7, [LineaPedido(1, 4), LineaPedido(2, 5), LineaPedido(3, 1)])
        mapa = {1: 10, 2: 3, 3: 0}
        directo = evaluar_pedido(pedido, mapa)
        lineas = [(lin.id_producto, lin.cantidad) for lin in pedido.lineas]
        via_compacto = resultado_desde_compacto(
            evaluar_pedido_compacto(pedido.id, lineas, crear_consulta_stock(mapa))
        )
        assert directo == via_compacto

    def test_consulta_stock_desde_catalogo_y_mapeo(self):
        assert crear_consulta_stock(_catalogo({1: 4}))(1) == 4
        assert crear_consulta_stock(_catalogo({1: 4}))(99) == 0
        assert crear_consulta_stock({1: 4})(1) == 4

    def test_consulta_stock_rechaza_fuente_invalida(self):
        with pytest.raises(TypeError, match="no soportada"):
            crear_consulta_stock([1, 2, 3])

    def test_contador_acepta_enum_y_valor(self):
        contador = ContadorEstados()
        for estado in (EstadoPedido.CUBIERTO, "cubierto", "parcial", EstadoPedido.IMPOSIBLE):
            contador.registrar(estado)
        assert (contador.cubiertos, contador.parciales, contador.imposibles) == (2, 1, 1)
        assert contador.total == 4


# =========================================================================
# 2. Procesador concurrente
# =========================================================================


class TestProcesadorConcurrente:
    def test_fragmentos_llevan_solo_el_stock_referenciado(self):
        catalogo = _catalogo({i: i for i in range(1, 101)})
        pedidos = [Pedido(1, [LineaPedido(5, 1)]), Pedido(2, [LineaPedido(7, 1)])]
        fragmentos = _armar_fragmentos(catalogo, pedidos, workers=2)
        assert [stock for _, stock in fragmentos] == [{5: 5}, {7: 7}]
        assert [compactos for compactos, _ in fragmentos] == [[(1, ((5, 1),))], [(2, ((7, 1),))]]

    def test_descuento_delegado_al_secuencial(self):
        pedidos = [Pedido(i, [LineaPedido(1, 5)]) for i in (1, 2, 3)]
        cat_sec, cat_conc = _catalogo({1: 10}), _catalogo({1: 10})
        sec = procesar_pedidos_secuencial(cat_sec, pedidos, descontar_stock=True)
        conc = procesar_pedidos_concurrente(cat_conc, pedidos, descontar_stock=True)
        assert [r.estado for r in conc.resultados] == [r.estado for r in sec.resultados]
        assert cat_conc.buscar_por_id(1).stock == cat_sec.buscar_por_id(1).stock == 0
        assert conc.estrategia == "optimizado_concurrente_descuento_secuencial"

    def test_resultados_en_orden_original(self, dataset_pequeno):
        productos, pedidos = dataset_pequeno
        catalogo = CatalogoHash(productos)
        conc = procesar_pedidos_concurrente(catalogo, pedidos, max_workers=2)
        sec = procesar_pedidos_secuencial(catalogo, pedidos)
        assert [r.id_pedido for r in conc.resultados] == [p.id for p in pedidos]
        assert conc.resultados == sec.resultados


# =========================================================================
# 3. Procesamiento JSONL por lotes
# =========================================================================


class _ExecutorSincronico:
    """Executor que corre cada tarea al instante y registra cuántas quedan sin consumir."""

    def __init__(self, initializer=None, initargs=()):
        if initializer:
            initializer(*initargs)
        self.pendientes = 0
        self.maximo_pendientes = 0

    def submit(self, funcion, *args):
        futuro: Future = Future()
        futuro.set_result(funcion(*args))
        self.pendientes += 1
        self.maximo_pendientes = max(self.maximo_pendientes, self.pendientes)
        original = futuro.result

        def result(*a, **kw):
            self.pendientes -= 1
            return original(*a, **kw)

        futuro.result = result
        return futuro


class TestLotesJsonl:
    @pytest.fixture
    def archivo_pedidos(self, tmp_path: Path) -> Path:
        pedidos = [
            {"id": i, "lineas": [{"id_producto": 1 + i % 3, "cantidad": 1 + i % 4}]}
            for i in range(1, 51)
        ]
        return _escribir_jsonl(tmp_path / "pedidos.jsonl", pedidos)

    def test_paralelo_igual_a_secuencial(self, archivo_pedidos):
        stock = {1: 2, 2: 0, 3: 50}
        sec = procesar_pedidos_jsonl_secuencial(
            archivo_pedidos, stock, tamano_lote=7, reconstruir_dataclasses=True
        )
        par = procesar_pedidos_jsonl_paralelo(
            archivo_pedidos,
            stock,
            tamano_lote=7,
            max_workers=2,
            reconstruir_dataclasses=True,
            max_lotes_en_vuelo=1,
        )
        assert par.resultados == sec.resultados
        assert (par.pedidos_cubiertos, par.pedidos_parciales, par.pedidos_imposibles) == (
            sec.pedidos_cubiertos,
            sec.pedidos_parciales,
            sec.pedidos_imposibles,
        )
        assert par.pedidos_procesados == 50

    def test_lotes_en_vuelo_acotados(self, archivo_pedidos, monkeypatch):
        executor_falso: dict[str, _ExecutorSincronico] = {}

        def obtener_executor(max_workers=None, initializer=None, initargs=()):
            executor_falso["e"] = _ExecutorSincronico(initializer, initargs)
            return executor_falso["e"]

        monkeypatch.setattr(lotes.pool_archivos, "obtener_executor", obtener_executor)
        resumen = procesar_pedidos_jsonl_paralelo(
            archivo_pedidos, {1: 5, 2: 5, 3: 5}, tamano_lote=5, max_workers=2
        )
        assert resumen.pedidos_procesados == 50
        # 10 lotes, pero nunca más de 2 por worker sin consumir.
        assert executor_falso["e"].maximo_pendientes == 4

    def test_pedido_sin_lineas_es_error(self, tmp_path: Path):
        ruta = _escribir_jsonl(tmp_path / "vacio.jsonl", [{"id": 1, "lineas": []}])
        with pytest.raises(ValueError, match="no tiene líneas"):
            procesar_pedidos_jsonl_secuencial(ruta, {1: 1})

    def test_archivo_inexistente(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            procesar_pedidos_jsonl_paralelo(tmp_path / "no.jsonl", {})


# =========================================================================
# 4. Motor y 5. GestorPool
# =========================================================================


def test_motor_procesa_en_secuencial_por_defecto():
    motor = MotorInventario(estrategia="optimizado")
    motor.cargar_dataset(BASE_DIR / "data" / "datasets" / "grande.json")
    assert motor.procesar_pedidos().estrategia == "baseline_secuencial"


def test_contexto_multiproceso_respeta_variable_de_entorno(monkeypatch):
    monkeypatch.setenv("PEF_MP_START_METHOD", "spawn")
    assert gestor_pool._contexto_multiproceso().get_start_method() == "spawn"
    monkeypatch.delenv("PEF_MP_START_METHOD")
    esperado = "forkserver" if "forkserver" in multiprocessing.get_all_start_methods() else "spawn"
    assert gestor_pool._contexto_multiproceso().get_start_method() == esperado


# =========================================================================
# 6. UI: comportamiento común en PantallaBase
# =========================================================================


@pytest.mark.parametrize(
    "clase",
    [
        PantallaAgrupacion,
        PantallaAlternativas,
        PantallaCatalogo,
        PantallaComparacion,
        PantallaPedidos,
        PantallaTopProductos,
    ],
)
def test_alternar_sentido_orden(clase):
    motor = MotorInventario(estrategia="baseline")
    motor.cargar_dataset(DEMO_ORAL)
    pantalla = clase(motor=motor, on_actualizar_panel=lambda **kw: None, notificar=lambda *a: None)
    inicial = pantalla.orden_ascendente
    pantalla._alternar_sentido_orden()
    assert pantalla.orden_ascendente is not inicial
    assert pantalla.btn_sentido_orden.tooltip.startswith(
        "Orden ascendente" if not inicial else "Orden descendente"
    )
    pantalla._alternar_sentido_orden()
    assert pantalla.orden_ascendente is inicial


def test_publicar_resultado_completa_el_panel():
    motor = MotorInventario(estrategia="optimizado")
    motor.cargar_dataset(DEMO_ORAL)
    recibido: dict = {}
    pantalla = PantallaTopProductos(
        motor=motor, on_actualizar_panel=lambda **kw: recibido.update(kw), notificar=print
    )
    pantalla._publicar_resultado(tiempo_ms=1.5, resultado_negocio="ok")
    assert recibido == {
        "dataset": "activo",
        "n_productos": len(motor.catalogo),
        "n_pedidos": len(motor.pedidos),
        "estrategia": "optimizado",
        "tiempo_ms": 1.5,
        "resultado_negocio": "ok",
    }


# =========================================================================
# 7. Informes de benchmarks
# =========================================================================


def _perfil_scalene(ruta: Path, segundos: float, funciones: list[tuple[str, float]]) -> Path:
    datos = {
        "elapsed_time_sec": segundos,
        "max_footprint_mb": 10.0,
        "files": {
            "/repo/src/pedidos/procesador_concurrente.py": {
                "functions": [
                    {
                        "line": nombre,
                        "n_cpu_percent_python": 1.0,
                        "n_cpu_percent_c": pct,
                        "n_sys_percent": pct,
                        "n_peak_mb": 0.0,
                    }
                    for nombre, pct in funciones
                ]
            }
        },
    }
    ruta.write_text(json.dumps(datos), encoding="utf-8")
    return ruta


def test_resumen_scalene(tmp_path: Path):
    antes = cargar_perfil(_perfil_scalene(tmp_path / "a.json", 4.0, [("procesar", 20.0)]))
    despues = cargar_perfil(_perfil_scalene(tmp_path / "d.json", 3.0, [("_evaluar_en_pool", 5.0)]))
    texto = generar_resumen(antes, despues, "prueba")
    assert "25 % menos" in texto
    assert "`src/pedidos/procesador_concurrente.py · procesar`" in texto
    assert "`src/pedidos/procesador_concurrente.py · _evaluar_en_pool`" in texto


def test_conclusiones_del_benchmark_salen_de_los_datos():
    sin_ganancia = [{"lote": 10, "speedup": 0.8}, {"lote": 20, "speedup": 0.9}]
    assert "no superó" in bench._conclusion_lotes(sin_ganancia, workers=2)
    con_ganancia = [{"lote": 10, "speedup": 0.8}, {"lote": 20, "speedup": 1.4}]
    assert "1.40×" in bench._conclusion_lotes(con_ganancia, workers=4)

    csv_igual = {"filas": 10, "kb": 1.0, "defecto_ms": 10.0, "explicito_ms": 10.2}
    assert "no es significativa" in bench._conclusion_csv(csv_igual)
    csv_mejor = {"filas": 10, "kb": 1.0, "defecto_ms": 10.0, "explicito_ms": 5.0}
    assert "50 % más rápido" in bench._conclusion_csv(csv_mejor)

    lectura = {
        "completa_ms": 10.0,
        "completa_mb": 100.0,
        "streaming_ms": 12.0,
        "streaming_mb": 1.0,
    }
    assert "99.0 % menos" in bench._conclusion_lectura(lectura)
    assert "más lento" in bench._conclusion_lectura(lectura)
