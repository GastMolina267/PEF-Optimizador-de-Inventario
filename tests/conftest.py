"""Fixtures compartidas de pytest para la suite de pruebas del proyecto.

Fase F2: Red de seguridad antes de refactorizaciones.
Provee fixtures reutilizables para datasets versionados, modelos de dominio,
catálogos (lineal y hash) y motores en ambas estrategias.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.cache.cache_consultas import GestorCacheConsultas
from src.datos.cargador import cargar_dataset_json
from src.inventario.catalogo_hash import CatalogoHash
from src.inventario.catalogo_lineal import CatalogoLineal
from src.modelos.pedido import LineaPedido, Pedido
from src.modelos.producto import Producto
from src.motor.motor_inventario import MotorInventario

BASE_DIR = Path(__file__).resolve().parent.parent
DATASETS_DIR = BASE_DIR / "data" / "datasets"


def clonar_productos(productos: list[Producto]) -> list[Producto]:
    """Genera copias profundas independientes de una lista de productos."""
    return [p.clonar() for p in productos]


def clonar_pedidos(pedidos: list[Pedido]) -> list[Pedido]:
    """Genera copias profundas independientes de una lista de pedidos."""
    return [
        Pedido(
            id=p.id,
            lineas=[
                LineaPedido(id_producto=lp.id_producto, cantidad=lp.cantidad) for lp in p.lineas
            ],
        )
        for p in pedidos
    ]


# =========================================================================
# Fixtures de sesión: Carga en memoria única de datasets JSON
# =========================================================================


@pytest.fixture(scope="session")
def _raw_demo_oral() -> tuple[list[Producto], list[Pedido]]:
    return cargar_dataset_json(DATASETS_DIR / "demo_oral.json")


@pytest.fixture(scope="session")
def _raw_pequeno() -> tuple[list[Producto], list[Pedido]]:
    return cargar_dataset_json(DATASETS_DIR / "pequeno.json")


@pytest.fixture(scope="session")
def _raw_mediano() -> tuple[list[Producto], list[Pedido]]:
    return cargar_dataset_json(DATASETS_DIR / "mediano.json")


@pytest.fixture(scope="session")
def _raw_grande() -> tuple[list[Producto], list[Pedido]]:
    return cargar_dataset_json(DATASETS_DIR / "grande.json")


# =========================================================================
# Fixtures por función: Copias frescas desacopladas para cada test
# =========================================================================


@pytest.fixture
def dataset_demo_oral(
    _raw_demo_oral: tuple[list[Producto], list[Pedido]],
) -> tuple[list[Producto], list[Pedido]]:
    """Dataset demo_oral (~30 productos, ~8 pedidos) con copias frescas."""
    prods, peds = _raw_demo_oral
    return clonar_productos(prods), clonar_pedidos(peds)


@pytest.fixture
def dataset_pequeno(
    _raw_pequeno: tuple[list[Producto], list[Pedido]],
) -> tuple[list[Producto], list[Pedido]]:
    """Dataset pequeno (100 productos, 20 pedidos) con copias frescas."""
    prods, peds = _raw_pequeno
    return clonar_productos(prods), clonar_pedidos(peds)


@pytest.fixture
def dataset_mediano(
    _raw_mediano: tuple[list[Producto], list[Pedido]],
) -> tuple[list[Producto], list[Pedido]]:
    """Dataset mediano (1.000 productos, 200 pedidos) con copias frescas."""
    prods, peds = _raw_mediano
    return clonar_productos(prods), clonar_pedidos(peds)


@pytest.fixture
def dataset_grande(
    _raw_grande: tuple[list[Producto], list[Pedido]],
) -> tuple[list[Producto], list[Pedido]]:
    """Dataset grande (10.000 productos, 2.000 pedidos) con copias frescas."""
    prods, peds = _raw_grande
    return clonar_productos(prods), clonar_pedidos(peds)


# =========================================================================
# Fixtures de datos de muestra controlados
# =========================================================================


@pytest.fixture
def productos_muestra() -> list[Producto]:
    """Conjunto controlado de productos que abarca diferentes categorías y estados de stock."""
    return [
        Producto(
            id=1,
            nombre="Taladro Percutor 750W",
            categoria="Herramientas",
            stock=15,
            precio=12500.0,
        ),
        Producto(
            id=2,
            nombre="Amoladora Angular 115mm",
            categoria="Herramientas",
            stock=8,
            precio=9800.0,
        ),
        Producto(
            id=3,
            nombre="Set Destornilladores x6",
            categoria="Herramientas",
            stock=25,
            precio=3400.0,
        ),
        Producto(
            id=4,
            nombre="Pintura Látex Interior 20L",
            categoria="Pinturas",
            stock=10,
            precio=18500.0,
        ),
        Producto(
            id=5,
            nombre="Pincel Cerda Nro 20",
            categoria="Pinturas",
            stock=30,
            precio=1200.0,
        ),
        Producto(
            id=6,
            nombre="Rodillo Antigoteo 22cm",
            categoria="Pinturas",
            stock=0,
            precio=2300.0,
        ),
        Producto(
            id=7,
            nombre="Cable Unipolar 2.5mm 100m",
            categoria="Electricidad",
            stock=5,
            precio=14200.0,
        ),
        Producto(
            id=8,
            nombre="Llave Térmica Bipolar 20A",
            categoria="Electricidad",
            stock=12,
            precio=4500.0,
        ),
    ]


@pytest.fixture
def pedidos_muestra() -> list[Pedido]:
    """Pedidos controlados con líneas cubiertas, parciales y faltantes."""
    return [
        Pedido(
            id=101,
            lineas=[
                LineaPedido(id_producto=1, cantidad=2),
                LineaPedido(id_producto=3, cantidad=5),
            ],
        ),
        Pedido(
            id=102,
            lineas=[
                LineaPedido(id_producto=4, cantidad=2),
                LineaPedido(id_producto=5, cantidad=4),
            ],
        ),
        Pedido(
            id=103,
            lineas=[
                LineaPedido(id_producto=6, cantidad=3),  # Stock 0: faltante total
                LineaPedido(id_producto=7, cantidad=2),
            ],
        ),
        Pedido(
            id=104,
            lineas=[
                LineaPedido(id_producto=2, cantidad=10),  # Stock 8: asignación parcial
            ],
        ),
    ]


# =========================================================================
# Fixtures de estructuras y motores
# =========================================================================


@pytest.fixture
def catalogo_lineal_muestra(productos_muestra: list[Producto]) -> CatalogoLineal:
    """Instancia de CatalogoLineal cargada con productos_muestra."""
    return CatalogoLineal(clonar_productos(productos_muestra))


@pytest.fixture
def catalogo_hash_muestra(productos_muestra: list[Producto]) -> CatalogoHash:
    """Instancia de CatalogoHash cargada con productos_muestra."""
    return CatalogoHash(clonar_productos(productos_muestra))


@pytest.fixture
def gestor_cache() -> GestorCacheConsultas:
    """Instancia limpia de GestorCacheConsultas."""
    return GestorCacheConsultas(capacidad_busquedas=16, capacidad_ranking=8)


@pytest.fixture
def motor_baseline(
    productos_muestra: list[Producto], pedidos_muestra: list[Pedido]
) -> MotorInventario:
    """Instancia de MotorInventario en estrategia baseline."""
    return MotorInventario(
        productos=clonar_productos(productos_muestra),
        pedidos=clonar_pedidos(pedidos_muestra),
        estrategia="baseline",
    )


@pytest.fixture
def motor_optimizado(
    productos_muestra: list[Producto], pedidos_muestra: list[Pedido]
) -> MotorInventario:
    """Instancia de MotorInventario en estrategia optimizado."""
    return MotorInventario(
        productos=clonar_productos(productos_muestra),
        pedidos=clonar_pedidos(pedidos_muestra),
        estrategia="optimizado",
    )
