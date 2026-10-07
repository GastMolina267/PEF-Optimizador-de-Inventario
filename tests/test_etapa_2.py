"""Pruebas unitarias y de integración para la Etapa 2 (Baseline y Datos).

Verifica:
1. Modelos de dominio (Producto, LineaPedido, Pedido, resultados).
2. Validador y cargador de datasets JSON.
3. Catálogo lineal O(n) (búsquedas, agregación, stock).
4. Procesamiento secuencial de pedidos frente al catálogo lineal.
5. Top-N de productos más solicitados mediante ordenamiento completo.
6. API unificada del MotorInventario.
7. Determinismo de datasets con semilla fija.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from benchmarks.generar_datos import crear_dataset_demo_oral, generar_dataset_sintetico
from src.datos.cargador import (
    cargar_dataset_json,
    validar_dataset,
)
from src.datos.validador import ValidadorDataset
from src.inventario.catalogo_lineal import CatalogoLineal
from src.modelos.pedido import (
    EstadoPedido,
    LineaPedido,
    Pedido,
    ResumenProcesamiento,
)
from src.modelos.producto import Producto
from src.motor.motor_inventario import MotorInventario
from src.pedidos.procesador_secuencial import procesar_pedidos_secuencial
from src.ranking.top_productos import calcular_top_solicitados_lineal

BASE_DIR = Path(__file__).resolve().parent.parent
DATASETS_DIR = BASE_DIR / "data" / "datasets"


class TestModelos:
    """Pruebas para los modelos de dominio."""

    def test_creacion_producto_valido(self):
        p = Producto(id=1, nombre="Taladro", categoria="Herramientas", stock=10, precio=1500.50)
        assert p.id == 1
        assert p.nombre == "Taladro"
        assert p.categoria == "Herramientas"
        assert p.stock == 10
        assert p.precio == 1500.50

    def test_validaciones_producto_invalido(self):
        with pytest.raises(ValueError, match="identificador"):
            Producto(id=0, nombre="Taladro", categoria="Herramientas", stock=10, precio=10.0)
        with pytest.raises(ValueError, match="nombre"):
            Producto(id=1, nombre="   ", categoria="Herramientas", stock=10, precio=10.0)
        with pytest.raises(ValueError, match="categoría"):
            Producto(id=1, nombre="Taladro", categoria="", stock=10, precio=10.0)
        with pytest.raises(ValueError, match="stock"):
            Producto(id=1, nombre="Taladro", categoria="Herramientas", stock=-1, precio=10.0)
        with pytest.raises(ValueError, match="precio"):
            Producto(id=1, nombre="Taladro", categoria="Herramientas", stock=5, precio=-10.0)

    def test_serializacion_producto(self):
        p = Producto(1, "Martillo", "Ferretería", 20, 300.0)
        dicc = p.a_diccionario()
        p2 = Producto.desde_diccionario(dicc)
        assert p == p2

    def test_creacion_pedido_y_lineas(self):
        linea = LineaPedido(id_producto=1, cantidad=5)
        pedido = Pedido(id=101, lineas=[linea])
        assert pedido.id == 101
        assert len(pedido.lineas) == 1
        assert pedido.lineas[0].cantidad == 5

    def test_validaciones_pedido_invalido(self):
        with pytest.raises(ValueError, match="cantidad demandada"):
            LineaPedido(id_producto=1, cantidad=0)
        with pytest.raises(ValueError, match="id_producto"):
            LineaPedido(id_producto=-5, cantidad=3)
        with pytest.raises(ValueError, match="al menos una línea"):
            Pedido(id=1, lineas=[])


class TestCargadorYDatasets:
    """Pruebas para el cargador y validador de datasets JSON."""

    def test_carga_dataset_pequeno(self):
        ruta = DATASETS_DIR / "pequeno.json"
        assert ruta.is_file(), "El archivo pequeno.json debe existir en data/datasets/"
        productos, pedidos = cargar_dataset_json(ruta)
        assert len(productos) == 100
        assert len(pedidos) == 20

    def test_carga_dataset_demo_oral(self):
        ruta = DATASETS_DIR / "demo_oral.json"
        assert ruta.is_file(), "El archivo demo_oral.json debe existir en data/datasets/"
        productos, pedidos = cargar_dataset_json(ruta)
        assert len(productos) == 30
        assert len(pedidos) == 8

    def test_validador_detecta_integridad_referencial_rota(self):
        datos_corruptos = {
            "productos": [
                {"id": 1, "nombre": "P1", "categoria": "C1", "stock": 10, "precio": 100.0}
            ],
            "pedidos": [
                {
                    "id": 1,
                    "lineas": [{"id_producto": 999, "cantidad": 2}],  # 999 no existe en productos
                }
            ],
        }
        with pytest.raises(ValueError, match="Integridad rota"):
            validar_dataset(datos_corruptos)

    def test_validador_detecta_ids_duplicados(self):
        datos_duplicados = {
            "productos": [
                {"id": 1, "nombre": "P1", "categoria": "C1", "stock": 10, "precio": 100.0},
                {"id": 1, "nombre": "P2", "categoria": "C2", "stock": 5, "precio": 200.0},
            ],
            "pedidos": [],
        }
        with pytest.raises(ValueError, match="duplicado"):
            validar_dataset(datos_duplicados)

    def test_validador_dataset_clase(self):
        ruta = DATASETS_DIR / "demo_oral.json"
        productos, pedidos = cargar_dataset_json(ruta)
        validador = ValidadorDataset(productos, pedidos)
        res = validador.validar_todo()
        assert res.es_valido
        assert res.total_productos == 30
        assert res.total_pedidos == 8
        assert len(res.errores) == 0


class TestCatalogoLineal:
    """Pruebas para el comportamiento del catálogo lineal baseline (O(n))."""

    @pytest.fixture
    def catalogo(self) -> CatalogoLineal:
        productos = [
            Producto(1, "Taladro Percutor 750W", "Herramientas", 10, 45000.0),
            Producto(2, "Amoladora Angular 115mm", "Herramientas", 5, 38000.0),
            Producto(3, "Cable Unipolar 2.5mm", "Electricidad", 50, 2800.0),
            Producto(4, "Foco LED 12W", "Electricidad", 0, 1800.0),
        ]
        return CatalogoLineal(productos)

    def test_buscar_por_id(self, catalogo: CatalogoLineal):
        prod = catalogo.buscar_por_id(2)
        assert prod is not None
        assert prod.nombre == "Amoladora Angular 115mm"

        prod_inexistente = catalogo.buscar_por_id(999)
        assert prod_inexistente is None

    def test_buscar_por_nombre(self, catalogo: CatalogoLineal):
        resultados = catalogo.buscar_por_nombre("angular")
        assert len(resultados) == 1
        assert resultados[0].id == 2

        # Búsqueda que coincide con múltiples
        res_mult = catalogo.buscar_por_nombre("mm")  # Coincide con Amoladora 115mm y Cable 2.5mm
        assert len(res_mult) == 2

    def test_buscar_por_categoria(self, catalogo: CatalogoLineal):
        electricos = catalogo.buscar_por_categoria("electricidad")
        assert len(electricos) == 2

    def test_actualizar_y_descontar_stock(self, catalogo: CatalogoLineal):
        # Descuento exitoso
        ok = catalogo.descontar_stock(1, 4)
        assert ok is True
        prod = catalogo.buscar_por_id(1)
        assert prod is not None and prod.stock == 6

        # Descuento que excede el stock disponible
        insuficiente = catalogo.descontar_stock(1, 10)
        assert insuficiente is False
        assert prod.stock == 6  # No se muta

        # Actualizar stock directo
        catalogo.actualizar_stock(1, 20)
        assert prod.stock == 20


class TestProcesamientoYRankingBaseline:
    """Pruebas para el procesamiento secuencial de pedidos y cálculo de top-N."""

    def test_procesamiento_demo_oral(self):
        prods, peds = crear_dataset_demo_oral()
        catalogo = CatalogoLineal(prods)
        resumen = procesar_pedidos_secuencial(catalogo, peds, descontar_stock=False)

        assert resumen.pedidos_procesados == 8
        assert resumen.pedidos_cubiertos >= 1
        assert resumen.pedidos_parciales >= 1
        assert resumen.pedidos_imposibles >= 1
        assert resumen.tiempo_ejecucion_ms >= 0.0

        # Pedido 1 debe estar cubierto
        res_p1 = next(r for r in resumen.resultados if r.id_pedido == 1)
        assert res_p1.estado == EstadoPedido.CUBIERTO
        assert res_p1.es_exitoso is True

        # Pedido 3 debe ser parcial (Producto 5 tiene stock 0)
        res_p3 = next(r for r in resumen.resultados if r.id_pedido == 3)
        assert res_p3.estado == EstadoPedido.PARCIAL

        # Pedido 5 debe ser imposible (ambos productos tienen stock 0)
        res_p5 = next(r for r in resumen.resultados if r.id_pedido == 5)
        assert res_p5.estado == EstadoPedido.IMPOSIBLE

    def test_top_solicitados_lineal(self):
        prods, peds = crear_dataset_demo_oral()
        catalogo = CatalogoLineal(prods)
        top = calcular_top_solicitados_lineal(peds, catalogo, k=3)

        assert len(top) <= 3
        # Debe estar ordenado de mayor a menor
        cantidades = [cant for _, cant in top]
        assert cantidades == sorted(cantidades, reverse=True)


class TestMotorInventarioAPI:
    """Pruebas de la fachada unificada MotorInventario (Criterio de cierre Etapa 2)."""

    def test_cierre_etapa_2_con_pequeno_json(self):
        """Criterio de cierre formal de la Etapa 2:

        Se carga pequeno.json por código y se buscan productos / preparan pedidos /
        listan top-N con el catálogo lineal, obteniendo resultados consistentes.
        """
        motor = MotorInventario(estrategia="baseline")
        ruta_pequeno = DATASETS_DIR / "pequeno.json"
        motor.cargar_dataset(ruta_pequeno)

        # 1. Verificar catálogo cargado
        stats = motor.obtener_estadisticas()
        assert stats["total_productos"] == 100
        assert stats["total_pedidos"] == 20
        assert stats["estrategia"] == "baseline"

        # 2. Búsqueda por ID
        prod_1 = motor.buscar_por_id(1)
        assert prod_1 is not None
        assert prod_1.id == 1

        # 3. Búsqueda por texto
        res_nombre = motor.buscar_por_nombre("Premium")
        assert isinstance(res_nombre, list)

        # 4. Preparación de pedidos secuencial baseline
        resumen = motor.procesar_pedidos(descontar_stock=False)
        assert isinstance(resumen, ResumenProcesamiento)
        assert resumen.pedidos_procesados == 20
        assert (
            resumen.pedidos_cubiertos + resumen.pedidos_parciales + resumen.pedidos_imposibles
        ) == 20

        # 5. Top-N productos más solicitados
        top_5 = motor.obtener_top_solicitados(k=5)
        assert len(top_5) == 5
        for prod, cant in top_5:
            assert isinstance(prod, Producto)
            assert cant > 0


class TestDeterminismoSemilla:
    """Verifica que la generación sintética sea determinista."""

    def test_semilla_fija_produce_resultados_identicos(self):
        prods1, peds1 = generar_dataset_sintetico(50, 10, semilla=99)
        prods2, peds2 = generar_dataset_sintetico(50, 10, semilla=99)

        assert len(prods1) == len(prods2)
        assert len(peds1) == len(peds2)

        for p1, p2 in zip(prods1, prods2, strict=True):
            assert p1 == p2

        for ped1, ped2 in zip(peds1, peds2, strict=True):
            assert ped1 == ped2
