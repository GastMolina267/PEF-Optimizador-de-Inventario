"""Pruebas unitarias para funciones públicas y ramas no cubiertas (Fase F2: Red de seguridad).

Verifica contratos de API, serialización, manejo de errores, métodos de caché,
catálogos, validadores y motor que previamente no contaban con cobertura explícita.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.cache.cache_consultas import CacheLRU, GestorCacheConsultas, MetricasCache
from src.datos.cargador import (
    cargar_dataset_json,
    guardar_dataset_json,
    validar_dataset,
)
from src.datos.validador import ValidadorDataset
from src.inventario.catalogo_hash import CatalogoHash
from src.inventario.catalogo_lineal import CatalogoLineal
from src.modelos.pedido import (
    EstadoPedido,
    LineaPedido,
    Pedido,
    ResultadoLinea,
    ResultadoPedido,
    ResumenProcesamiento,
)
from src.modelos.producto import Producto
from src.motor.motor_inventario import MotorInventario
from src.pedidos.agrupador import (
    DetalleDemandaPedido,
    ItemPickingConsolidado,
    LotePickingConsolidado,
    agrupar_pedidos_batch,
)
from src.pedidos.combinaciones import BuscadorAlternativas, CombinacionAlternativa
from src.pedidos.procesador_concurrente import (
    _cerrar_executor,
    procesar_pedidos_concurrente,
)
from src.pedidos.procesador_secuencial import procesar_pedidos_secuencial
from src.ranking.top_productos import (
    calcular_top_solicitados,
    calcular_top_solicitados_heap,
    calcular_top_solicitados_lineal,
)

# =========================================================================
# 1. Modelos de dominio
# =========================================================================


class TestModelosDominioDetalle:
    def test_producto_clonar_y_serializacion(self):
        p = Producto(id=1, nombre="Taladro", categoria="Herramientas", stock=5, precio=150.0)
        clon = p.clonar()
        assert clon.id == p.id
        assert clon.nombre == p.nombre
        assert clon.stock == p.stock
        assert clon is not p

        d = p.a_diccionario()
        reconstruido = Producto.desde_diccionario(d)
        assert reconstruido == p

    def test_producto_validaciones_exhaustivas(self):
        with pytest.raises(ValueError, match="entero positivo"):
            Producto(id=-5, nombre="P", categoria="C", stock=1, precio=10.0)
        with pytest.raises(ValueError, match="vacío"):
            Producto(id=1, nombre="  ", categoria="C", stock=1, precio=10.0)
        with pytest.raises(ValueError, match="vacía"):
            Producto(id=1, nombre="P", categoria="  ", stock=1, precio=10.0)
        with pytest.raises(ValueError, match="mayor o igual a 0"):
            Producto(id=1, nombre="P", categoria="C", stock=-2, precio=10.0)
        with pytest.raises(ValueError, match="mayor o igual a 0.0"):
            Producto(id=1, nombre="P", categoria="C", stock=1, precio=-10.0)

    def test_linea_pedido_serializacion_y_validaciones(self):
        lp = LineaPedido(id_producto=10, cantidad=3)
        d = lp.a_diccionario()
        assert d == {"id_producto": 10, "cantidad": 3}
        lp2 = LineaPedido.desde_diccionario(d)
        assert lp2 == lp

        with pytest.raises(ValueError, match="entero positivo"):
            LineaPedido(id_producto=0, cantidad=3)
        with pytest.raises(ValueError, match="mayor a 0"):
            LineaPedido(id_producto=10, cantidad=0)

    def test_pedido_serializacion_y_validaciones(self):
        ped = Pedido(id=5, lineas=[LineaPedido(1, 2), LineaPedido(2, 4)])
        d = ped.a_diccionario()
        assert d["id"] == 5
        assert len(d["lineas"]) == 2
        ped2 = Pedido.desde_diccionario(d)
        assert ped2 == ped

        with pytest.raises(ValueError, match="entero positivo"):
            Pedido(id=0, lineas=[LineaPedido(1, 1)])
        with pytest.raises(ValueError, match="al menos una línea"):
            Pedido(id=1, lineas=[])

    def test_resumen_procesamiento_metricas_borde(self):
        resumen_vacio = ResumenProcesamiento(
            pedidos_procesados=0,
            pedidos_cubiertos=0,
            pedidos_parciales=0,
            pedidos_imposibles=0,
            tiempo_ejecucion_ms=0.0,
        )
        assert resumen_vacio.porcentaje_cobertura == 0.0

        rl = ResultadoLinea(id_producto=1, cantidad_solicitada=5, cantidad_asignada=5, faltante=0)
        assert rl.satisfecha_completamente is True
        rp = ResultadoPedido(id_pedido=1, estado=EstadoPedido.CUBIERTO, lineas_cubiertas=[rl])
        assert rp.es_exitoso is True


# =========================================================================
# 2. Catálogos: Métodos y errores
# =========================================================================


class TestCatalogosDetalle:
    def test_catalogo_lineal_metodos_borde(self):
        prods = [
            Producto(id=1, nombre="Lija Fina", categoria="Pinturas", stock=20, precio=50.0),
            Producto(id=2, nombre="Lija Gruesa", categoria="Pinturas", stock=15, precio=60.0),
        ]
        cat = CatalogoLineal(prods)
        assert len(cat) == 2
        assert [p.id for p in cat] == [1, 2]

        # Inserción duplicada
        with pytest.raises(ValueError, match="Conflicto de identificador"):
            cat.agregar(Producto(id=1, nombre="Duplicado", categoria="Pinturas", stock=1, precio=10.0))

        # Actualizar stock
        with pytest.raises(ValueError, match="no puede ser negativo"):
            cat.actualizar_stock(1, -5)
        assert cat.actualizar_stock(99, 10) is False
        assert cat.actualizar_stock(1, 30) is True
        assert cat.buscar_por_id(1).stock == 30

        # Descontar stock
        with pytest.raises(ValueError, match="debe ser positiva"):
            cat.descontar_stock(1, 0)
        assert cat.descontar_stock(99, 5) is False
        assert cat.descontar_stock(1, 50) is False  # Insuficiente
        assert cat.descontar_stock(1, 10) is True
        assert cat.buscar_por_id(1).stock == 20

        # Clonar
        clon = cat.clonar()
        assert len(clon) == 2
        assert clon is not cat

    def test_catalogo_hash_metodos_borde(self):
        prods = [
            Producto(id=1, nombre="Tornillo Madera 2 Pulgadas", categoria="Fijaciones", stock=100, precio=5.0),
            Producto(id=2, nombre="Tarugo Nylon 8mm", categoria="Fijaciones", stock=80, precio=3.0),
        ]
        cat = CatalogoHash(prods)
        assert len(cat) == 2
        assert {p.id for p in cat} == {1, 2}

        # Inserción duplicada
        with pytest.raises(ValueError, match="Conflicto de identificador"):
            cat.agregar(Producto(id=1, nombre="Duplicado", categoria="Fijaciones", stock=1, precio=1.0))

        # Búsqueda texto vacío
        assert cat.buscar_por_nombre("") == []
        assert cat.buscar_por_nombre("   ") == []

        # Búsqueda con término no indexado
        assert cat.buscar_por_nombre("inexistente") == []

        # Actualizar stock
        with pytest.raises(ValueError, match="no puede ser negativo"):
            cat.actualizar_stock(1, -1)
        assert cat.actualizar_stock(999, 10) is False
        assert cat.actualizar_stock(1, 150) is True
        assert cat.buscar_por_id(1).stock == 150

        # Descontar stock
        with pytest.raises(ValueError, match="debe ser positiva"):
            cat.descontar_stock(1, -5)
        assert cat.descontar_stock(999, 10) is False
        assert cat.descontar_stock(1, 200) is False  # Insuficiente
        assert cat.descontar_stock(1, 50) is True
        assert cat.buscar_por_id(1).stock == 100

        # Desindexar nombre
        cat._desindexar_nombre(prods[0])
        # Clonar
        clon = cat.clonar()
        assert len(clon) == 2


# =========================================================================
# 3. Caché y Métricas
# =========================================================================


class TestCacheDetalle:
    def test_cache_lru_capacidad_y_eviccion(self):
        with pytest.raises(ValueError, match="mayor a 0"):
            CacheLRU(capacidad_maxima=0)

        cache = CacheLRU[str](capacidad_maxima=2)
        assert cache.capacidad == 2

        cache.guardar("a", "1")
        cache.guardar("b", "2")
        assert len(cache) == 2

        # Actualizar clave existente
        cache.guardar("a", "1_actualizado")
        assert cache.obtener("a") == "1_actualizado"

        # Provocar evicción de 'b'
        cache.guardar("c", "3")
        assert cache.metricas.evicciones == 1
        assert cache.obtener("b") is None
        assert cache.obtener("c") == "3"

        # Invalidar clave
        assert cache.invalidar_clave("a") is True
        assert cache.invalidar_clave("inexistente") is False

        # Limpiar
        cache.limpiar()
        assert len(cache) == 0

    def test_metricas_cache_consultas(self):
        m = MetricasCache()
        assert m.total_consultas == 0
        assert m.tasa_aciertos == 0.0

    def test_gestor_cache_consultas_operaciones(self, productos_muestra):
        gestor = GestorCacheConsultas(capacidad_busquedas=4, capacidad_ranking=4)
        p = productos_muestra[:2]

        # Búsqueda por categoría
        assert gestor.obtener_busqueda_categoria("Herramientas") is None
        gestor.guardar_busqueda_categoria("Herramientas", p)
        assert gestor.obtener_busqueda_categoria("Herramientas") == p

        # Invalidación por nuevos pedidos
        gestor.guardar_top_solicitados(5, [(p[0], 10)])
        assert gestor.obtener_top_solicitados(5) is not None
        gestor.invalidar_por_nuevos_pedidos()
        assert gestor.obtener_top_solicitados(5) is None

        # Invalidación por mutación de stock
        assert gestor.obtener_busqueda_categoria("Herramientas") == p
        gestor.invalidar_por_mutacion_stock()
        assert gestor.obtener_busqueda_categoria("Herramientas") is None

        # Estadísticas consolidadas
        stats = gestor.obtener_estadisticas()
        assert "tasa_aciertos_global_pct" in stats
        assert "total_entradas_activas" in stats


# =========================================================================
# 4. Cargador, Validador y Persistencia JSON
# =========================================================================


class TestCargadorYValidadorExhaustivo:
    def test_guardar_y_cargar_dataset_json(self, tmp_path: Path, productos_muestra, pedidos_muestra):
        ruta_salida = tmp_path / "test_dataset.json"
        guardar_dataset_json(
            ruta_salida,
            productos_muestra,
            pedidos_muestra,
            metadatos={"origen": "test_f2", "version": 2},
        )
        assert ruta_salida.is_file()

        prods_cargados, peds_cargados = cargar_dataset_json(ruta_salida)
        assert len(prods_cargados) == len(productos_muestra)
        assert len(peds_cargados) == len(pedidos_muestra)
        assert prods_cargados[0].id == productos_muestra[0].id

    def test_cargar_dataset_errores_archivo(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            cargar_dataset_json(tmp_path / "no_existe.json")

        archivo_invalido = tmp_path / "corrupto.json"
        archivo_invalido.write_text("{json_invalido: 123", encoding="utf-8")
        with pytest.raises(ValueError, match="Error de sintaxis JSON"):
            cargar_dataset_json(archivo_invalido)

    def test_validar_dataset_errores_estructura(self):
        with pytest.raises(ValueError, match="objeto JSON"):
            validar_dataset(["no_es_dict"])  # type: ignore
        with pytest.raises(ValueError, match="'productos'"):
            validar_dataset({"pedidos": []})
        with pytest.raises(ValueError, match="'pedidos'"):
            validar_dataset({"productos": []})
        with pytest.raises(ValueError, match="no es un objeto JSON"):
            validar_dataset({"productos": ["invalido"], "pedidos": []})
        with pytest.raises(ValueError, match="no es un objeto JSON"):
            validar_dataset({"productos": [], "pedidos": ["invalido"]})

    def test_validador_dataset_clase_reglas(self):
        # Producto con stock o precio negativo
        p_invalido = Producto(id=1, nombre="Valido", categoria="C", stock=0, precio=10.0)
        object.__setattr__(p_invalido, "stock", -5)
        object.__setattr__(p_invalido, "precio", -1.0)
        object.__setattr__(p_invalido, "id", -2)

        ped_invalido = Pedido(id=1, lineas=[LineaPedido(id_producto=999, cantidad=1)])
        object.__setattr__(ped_invalido, "id", -1)

        val = ValidadorDataset([p_invalido], [ped_invalido])
        res = val.validar_todo()
        assert res.es_valido is False
        assert any("no positivo" in err for err in res.errores)
        assert any("no existe en catálogo" in err for err in res.errores)


# =========================================================================
# 5. Motor de Inventario y Ranking
# =========================================================================


class TestMotorInventarioDetalle:
    def test_motor_inicializacion_optimizada(self, productos_muestra):
        motor = MotorInventario(productos=productos_muestra, estrategia="optimizado")
        assert motor.es_optimizado is True
        assert isinstance(motor.catalogo, CatalogoHash)

    def test_motor_cambio_estrategia_y_errores(self, motor_baseline):
        with pytest.raises(ValueError, match="Estrategia inválida"):
            motor_baseline.cambiar_estrategia("estrategia_falsa")

        # Mismo modo no hace nada
        motor_baseline.cambiar_estrategia("baseline")
        assert motor_baseline.es_optimizado is False

        # Cambio a optimizado y vuelta a baseline
        motor_baseline.cambiar_estrategia("optimizado")
        assert motor_baseline.es_optimizado is True
        assert isinstance(motor_baseline.catalogo, CatalogoHash)

        motor_baseline.cambiar_estrategia("baseline")
        assert motor_baseline.es_optimizado is False
        assert isinstance(motor_baseline.catalogo, CatalogoLineal)

    def test_motor_busqueda_categoria_con_cache(self, motor_optimizado):
        prods1 = motor_optimizado.buscar_por_categoria("Herramientas", usar_cache=True)
        prods2 = motor_optimizado.buscar_por_categoria("Herramientas", usar_cache=True)
        assert prods1 == prods2
        assert len(prods1) > 0

    def test_motor_top_productos_con_cache(self, motor_optimizado):
        top1 = motor_optimizado.obtener_top_solicitados(k=5, usar_cache=True)
        top2 = motor_optimizado.calcular_top_productos(k=5, usar_cache=True)
        assert top1 == top2

    def test_motor_descuento_invalida_cache(self, motor_optimizado):
        motor_optimizado.buscar_por_nombre("taladro", usar_cache=True)
        assert len(motor_optimizado.cache._cache_busquedas) > 0
        motor_optimizado.procesar_pedidos(descontar_stock=True)
        assert len(motor_optimizado.cache._cache_busquedas) == 0

    def test_motor_estadisticas_completas(self, motor_optimizado):
        stats = motor_optimizado.obtener_estadisticas()
        assert stats["estrategia"] == "optimizado"
        assert stats["total_productos"] > 0
        assert "metricas_cache" in stats

    def test_ranking_funciones_borde(self, catalogo_hash_muestra, pedidos_muestra):
        assert calcular_top_solicitados_lineal(pedidos_muestra, catalogo_hash_muestra, k=0) == []
        assert calcular_top_solicitados_lineal([], catalogo_hash_muestra, k=5) == []
        assert calcular_top_solicitados_heap(pedidos_muestra, catalogo_hash_muestra, k=-1) == []
        assert calcular_top_solicitados_heap([], catalogo_hash_muestra, k=5) == []

        res = calcular_top_solicitados(pedidos_muestra, catalogo_hash_muestra, k=3, metodo="heap")
        assert len(res) <= 3
        res_lin = calcular_top_solicitados(pedidos_muestra, catalogo_hash_muestra, k=3, metodo="lineal")
        assert len(res_lin) <= 3


# =========================================================================
# 6. Agrupador y Alternativas
# =========================================================================


class TestAgrupadorYAlternativasDetalle:
    def test_lote_picking_metodos_auxiliares(self, productos_muestra):
        det = DetalleDemandaPedido(id_pedido=1, cantidad=5)
        item = ItemPickingConsolidado(
            id_producto=1,
            producto=productos_muestra[0],
            cantidad_total=5,
            demandas_por_pedido=[det],
        )
        assert item.total_pedidos_solicitantes == 1
        d = item.a_diccionario()
        assert d["id_producto"] == 1
        assert d["cantidad_total"] == 5

        lote = LotePickingConsolidado(total_pedidos=1, total_unidades=5, items=[item])
        assert lote.total_productos_distintos == 1
        assert lote.obtener_por_producto(1) is item
        assert lote.obtener_por_producto(999) is None

        # Lista vacía
        lote_vacio = agrupar_pedidos_batch([])
        assert lote_vacio.total_pedidos == 0

    def test_buscador_alternativas_metodos_auxiliares(self, productos_muestra):
        buscador = BuscadorAlternativas(productos_muestra)
        comb = CombinacionAlternativa(productos=[productos_muestra[0]], costo_total=12500.0)
        assert comb.cantidad_items == 1

        res = buscador.buscar_alternativas("Herramientas", 15000.0)
        assert res.total_combinaciones > 0
        buscador.limpiar_cache()
        assert len(buscador._memo_cache) == 0


# =========================================================================
# 7. Procesadores: Descuentos y Ciclo de Vida
# =========================================================================


class TestProcesadoresDetalle:
    def test_procesador_secuencial_politica_todo_lo_posible(self, catalogo_lineal_muestra, pedidos_muestra):
        res = procesar_pedidos_secuencial(
            catalogo_lineal_muestra,
            pedidos_muestra,
            descontar_stock=True,
            politica_descuento="todo_lo_posible",
        )
        assert res.pedidos_procesados == len(pedidos_muestra)

    def test_procesador_concurrente_lista_vacia_y_cierre(self, catalogo_hash_muestra):
        res = procesar_pedidos_concurrente(catalogo_hash_muestra, [])
        assert res.pedidos_procesados == 0
        assert res.tiempo_ejecucion_ms == 0.0

        # Cierre explícito del executor
        _cerrar_executor()
