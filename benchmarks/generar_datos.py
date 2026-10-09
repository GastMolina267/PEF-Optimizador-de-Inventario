"""Generador determinista de datasets sintéticos y curados.

Permite generar los escenarios de prueba estándar:
- demo_oral.json (~30 productos, ~8 pedidos, curado para la presentación)
- pequeno.json (100 productos, 20 pedidos)
- mediano.json (1.000 productos, 200 pedidos)
- grande.json (10.000 productos, 2.000 pedidos)
- masivo.json (100.000 productos, 10.000 pedidos) [opcional]
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path

from benchmarks.rutas import ruta_en_proyecto
from src.datos.cargador import guardar_dataset_json
from src.modelos.pedido import LineaPedido, Pedido
from src.modelos.producto import Producto

# Proporciones del dataset sintético.
PROPORCION_SIN_STOCK = 0.05
PROBABILIDAD_PRODUCTO_POPULAR = 0.70

# Categorías realistas para los productos sintéticos
FERRETERIA = "Ferretería y Herramientas"
ELECTRICIDAD = "Electricidad e Iluminación"
PINTURAS = "Pinturas y Adhesivos"
SEGURIDAD = "Seguridad Industrial"
PLOMERIA = "Plomería y Grifería"
BULONERIA = "Bulonería y Tornillería"

CATEGORIAS = [
    FERRETERIA,
    ELECTRICIDAD,
    PINTURAS,
    SEGURIDAD,
    PLOMERIA,
    BULONERIA,
]

NOMBRES_BASE = {
    FERRETERIA: [
        "Taladro percutor",
        "Amoladora angular",
        "Sierra caladora",
        "Juego de llaves",
        "Martillo galponero",
        "Destornillador Phillips",
        "Pinza universal",
        "Nivel de mano",
        "Cinta métrica",
        "Caja de herramientas",
        "Arco de sierra",
        "Lijadora orbital",
    ],
    ELECTRICIDAD: [
        "Cable unipolar 2.5mm",
        "Cable unipolar 4mm",
        "Foco LED 12W",
        "Foco LED 9W",
        "Disyuntor diferencial",
        "Llave térmica 16A",
        "Llave térmica 25A",
        "Toma corriente",
        "Caja de paso",
        "Cinta aisladora",
        "Plafón LED redondo",
        "Canaleta adhesiva",
    ],
    PINTURAS: [
        "Pintura látex interior",
        "Pintura látex exterior",
        "Esmalte sintético brillante",
        "Sellador de silicona",
        "Adhesivo de montaje",
        "Rodillo antigoteo",
        "Pincel de cerda",
        "Bandeja para pintar",
        "Lija al agua grano 180",
        "Aguarrás mineral",
        "Masilla para yeso",
    ],
    SEGURIDAD: [
        "Guantes de nitrilo",
        "Guantes de vaqueta",
        "Casco de protección",
        "Lentes de seguridad",
        "Protector auditivo de copa",
        "Máscara antipolvo",
        "Calzado de seguridad",
        "Arnés de sujeción",
        "Chaleco reflectivo",
        "Cono de señalización",
    ],
    PLOMERIA: [
        "Caño PVC 110mm",
        "Codo PVC 110mm",
        "Curva PVC 90°",
        "Adhesivo para PVC",
        "Canilla monocomando",
        "Flexible mallado 1/2",
        "Cinta teflón 3/4",
        "Sifón extensible",
        "Válvula esférica 1/2",
        "Flotante para tanque",
        "Rejilla de piso",
    ],
    BULONERIA: [
        "Tornillo autoperforante 10x1",
        "Tornillo autoperforante 10x2",
        "Tarugo con tope N°8",
        "Tarugo sin tope N°6",
        "Tuerca hexagonal 1/4",
        "Arandela plana 1/4",
        "Arandela grower 1/4",
        "Varilla roscada 3/8",
        "Remache de aluminio 4x12",
        "Pitón cerrado cincado",
    ],
}

MODIFICADORES = [
    "Premium",
    "Industrial",
    "Económico",
    "Reforzado",
    "Estándar",
    "Alta Resistencia",
    "Profesional",
    "Inoxidable",
    "Cincado",
    "Especial",
]


def crear_dataset_demo_oral() -> tuple[list[Producto], list[Pedido]]:
    """Crea el dataset curado para la exposición oral.

    Contiene 30 productos y 8 pedidos con nombres familiares y casos específicos:
    - Pedidos cubiertos.
    - Pedidos parciales con productos agotados (para habilitar cálculo de alternativas).
    - Pedidos imposibles.
    - Productos repetidos en varios pedidos (para batch picking consolidado).
    """
    productos = [
        Producto(1, "Taladro Percutor 750W", FERRETERIA, 15, 45000.0),
        Producto(2, "Amoladora Angular 115mm", FERRETERIA, 10, 38000.0),
        Producto(3, "Juego de Destornilladores x6", FERRETERIA, 25, 12000.0),
        Producto(4, "Martillo Galponero 500g", FERRETERIA, 30, 9500.0),
        Producto(5, "Sierra Caladora 600W", FERRETERIA, 0, 32000.0),  # Agotado deliberado
        Producto(6, "Cable Unipolar 2.5mm 100m", ELECTRICIDAD, 40, 28000.0),
        Producto(7, "Foco LED 12W Luz Fría", ELECTRICIDAD, 120, 1800.0),
        Producto(8, "Foco LED 9W Luz Cálida", ELECTRICIDAD, 80, 1500.0),
        Producto(9, "Disyuntor Diferencial 25A", ELECTRICIDAD, 20, 31000.0),
        Producto(10, "Llave Térmica Bipolar 16A", ELECTRICIDAD, 0, 8500.0),  # Agotado deliberado
        Producto(11, "Pintura Látex Interior 20L", PINTURAS, 18, 52000.0),
        Producto(12, "Pintura Látex Interior 10L", PINTURAS, 22, 29000.0),
        Producto(13, "Pintura Látex Interior 4L", PINTURAS, 35, 14000.0),
        Producto(14, "Esmalte Sintético Brillante 1L", PINTURAS, 25, 8900.0),
        Producto(15, "Rodillo Antigoteo 22cm", PINTURAS, 50, 4500.0),
        Producto(16, "Pincel N°20 Cerda Blanca", PINTURAS, 60, 2200.0),
        Producto(17, "Caño PVC 110mm x 4m", PLOMERIA, 15, 16500.0),
        Producto(18, "Codo PVC 110mm a 90°", PLOMERIA, 45, 2800.0),
        Producto(19, "Adhesivo para PVC 250cc", PLOMERIA, 30, 5100.0),
        Producto(20, "Canilla Monocomando Cocina", PLOMERIA, 12, 42000.0),
        Producto(21, "Flexible Mallado 1/2 x 40cm", PLOMERIA, 2, 3400.0),  # Stock bajo
        Producto(22, "Tornillo Autoperforante 10x1 (x100)", BULONERIA, 100, 3200.0),
        Producto(23, "Tornillo Autoperforante 10x2 (x100)", BULONERIA, 90, 4100.0),
        Producto(24, "Tarugo con Tope N°8 (x100)", BULONERIA, 150, 2100.0),
        Producto(25, "Tuerca Hexagonal 1/4 (x100)", BULONERIA, 80, 1900.0),
        Producto(26, "Arandela Grower 1/4 (x100)", BULONERIA, 85, 1400.0),
        Producto(27, "Guantes de Nitrilo Talle L", SEGURIDAD, 75, 3100.0),
        Producto(28, "Casco de Seguridad Amarillo", SEGURIDAD, 15, 9800.0),
        Producto(29, "Cinta Métrica 5m Antichoque", FERRETERIA, 40, 4900.0),
        Producto(
            30, "Sellador de Silicona Neutra 280ml", PINTURAS, 0, 6200.0
        ),  # Agotado deliberado
    ]

    pedidos = [
        # Pedido 1: Totalmente cubierto
        Pedido(1, [LineaPedido(7, 10), LineaPedido(8, 5), LineaPedido(6, 1)]),
        # Pedido 2: Totalmente cubierto (comparte Producto 22 y 24 con Pedido 4)
        Pedido(2, [LineaPedido(22, 5), LineaPedido(24, 4), LineaPedido(4, 2)]),
        # Pedido 3: Parcial (Producto 5 tiene stock 0 -> candidato para alternativas)
        Pedido(3, [LineaPedido(1, 1), LineaPedido(5, 1), LineaPedido(29, 1)]),
        # Pedido 4: Totalmente cubierto (comparte Producto 22)
        Pedido(4, [LineaPedido(22, 10), LineaPedido(23, 5), LineaPedido(25, 4)]),
        # Pedido 5: Imposible (Producto 10 y Producto 30 tienen stock 0)
        Pedido(5, [LineaPedido(10, 2), LineaPedido(30, 2)]),
        # Pedido 6: Parcial por stock insuficiente (pide 5 de Producto 21 pero solo hay 2)
        Pedido(6, [LineaPedido(21, 5), LineaPedido(18, 4)]),
        # Pedido 7: Totalmente cubierto (rubro pinturas)
        Pedido(7, [LineaPedido(11, 2), LineaPedido(15, 3), LineaPedido(16, 2)]),
        # Pedido 8: Totalmente cubierto (comparte Producto 7 y Producto 27)
        Pedido(8, [LineaPedido(7, 20), LineaPedido(27, 4), LineaPedido(29, 2)]),
    ]

    return productos, pedidos


def generar_dataset_sintetico(
    total_productos: int,
    total_pedidos: int,
    semilla: int = 42,
    max_lineas_pedido: int = 5,
) -> tuple[list[Producto], list[Pedido]]:
    """Genera determinísticamente un dataset sintético con parámetros controlados.

    Usa distribución de demanda sesgada (Zipf-like) para simular escenarios
    donde ciertos productos son mucho más populares que otros.
    """
    rnd = random.Random(semilla)
    productos: list[Producto] = []

    # 1. Generar productos
    for prod_id in range(1, total_productos + 1):
        cat = CATEGORIAS[(prod_id - 1) % len(CATEGORIAS)]
        nombres_disponibles = NOMBRES_BASE[cat]
        nombre_base = nombres_disponibles[(prod_id - 1) % len(nombres_disponibles)]
        modificador = MODIFICADORES[(prod_id // len(nombres_disponibles)) % len(MODIFICADORES)]
        nombre_completo = f"{nombre_base} {modificador} #{prod_id}"

        # ~5% de productos sin stock (para forzar casos de alternativas y pedidos parciales)
        stock = 0 if rnd.random() < PROPORCION_SIN_STOCK else rnd.randint(5, 250)

        precio = round(rnd.uniform(500.0, 65000.0), 2)

        productos.append(
            Producto(
                id=prod_id,
                nombre=nombre_completo,
                categoria=cat,
                stock=stock,
                precio=precio,
            )
        )

    # 2. Generar pedidos con demanda sesgada
    # Se concentran pedidos en el primer 20% de productos para crear productos estrella (Top-N)
    pedidos: list[Pedido] = []
    top_20_percent_idx = max(1, int(total_productos * 0.20))

    for ped_id in range(1, total_pedidos + 1):
        num_lineas = rnd.randint(1, max_lineas_pedido)
        lineas: list[LineaPedido] = []
        productos_elegidos_en_pedido: set[int] = set()

        for _ in range(num_lineas):
            # 70% de probabilidad de elegir un producto del top 20%
            if rnd.random() < PROBABILIDAD_PRODUCTO_POPULAR:
                id_prod = rnd.randint(1, top_20_percent_idx)
            else:
                id_prod = rnd.randint(1, total_productos)

            if id_prod in productos_elegidos_en_pedido:
                continue
            productos_elegidos_en_pedido.add(id_prod)

            cantidad = rnd.randint(1, 15)
            lineas.append(LineaPedido(id_producto=id_prod, cantidad=cantidad))

        if not lineas:
            lineas.append(LineaPedido(id_producto=1, cantidad=1))

        pedidos.append(Pedido(id=ped_id, lineas=lineas))

    return productos, pedidos


def generar_todos_los_datasets(directorio_destino: str | Path, semilla: int = 42) -> None:
    """Genera y guarda en disco todos los datasets estándar del proyecto."""
    destino = Path(directorio_destino)
    destino.mkdir(parents=True, exist_ok=True)

    configuraciones = [
        ("demo_oral.json", "curado", None, None),
        ("pequeno.json", "sintetico", 100, 20),
        ("mediano.json", "sintetico", 1000, 200),
        ("grande.json", "sintetico", 10000, 2000),
    ]

    for nombre_archivo, tipo, n_prods, n_peds in configuraciones:
        ruta_archivo = destino / nombre_archivo
        if tipo == "curado":
            prods, peds = crear_dataset_demo_oral()
            metadatos = {
                "nombre": "Demo Oral",
                "descripcion": "Dataset curado para la exposición oral en vivo de 10-15 minutos.",
                "total_productos": len(prods),
                "total_pedidos": len(peds),
                "semilla": "curado_manual",
            }
        else:
            prods, peds = generar_dataset_sintetico(
                total_productos=n_prods,  # type: ignore
                total_pedidos=n_peds,  # type: ignore
                semilla=semilla,
            )
            metadatos = {
                "nombre": nombre_archivo.replace(".json", "").capitalize(),
                "descripcion": (
                    f"Dataset sintético determinista ({n_prods} productos, {n_peds} pedidos)."
                ),
                "total_productos": len(prods),
                "total_pedidos": len(peds),
                "semilla": semilla,
            }

        guardar_dataset_json(ruta_archivo, prods, peds, metadatos)
        print(f"[OK] Generado {nombre_archivo:15} -> {len(prods)} productos, {len(peds)} pedidos.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generador de datasets para el Optimizador de Inventario."
    )
    parser.add_argument(
        "--salida",
        type=str,
        default="data/datasets",
        help="Directorio de destino para los archivos JSON.",
    )
    parser.add_argument(
        "--semilla",
        type=int,
        default=42,
        help="Semilla para reproducibilidad determinista.",
    )
    parser.add_argument(
        "--incluir-masivo",
        action="store_true",
        help="Genera también el dataset masivo.json (100.000 productos, 10.000 pedidos).",
    )

    args = parser.parse_args()
    try:
        destino = ruta_en_proyecto(args.salida)
    except ValueError as error:
        parser.error(str(error))
    print(f"Generando datasets estándar en '{destino}' con semilla={args.semilla}...")
    generar_todos_los_datasets(destino, args.semilla)

    if args.incluir_masivo:
        print("Generando dataset masivo.json (100k productos / 10k pedidos)...")
        prods_m, peds_m = generar_dataset_sintetico(100000, 10000, semilla=args.semilla)
        guardar_dataset_json(
            destino / "masivo.json",
            prods_m,
            peds_m,
            {
                "nombre": "Masivo",
                "descripcion": "Dataset masivo para pruebas de estrés de benchmarking.",
                "total_productos": len(prods_m),
                "total_pedidos": len(peds_m),
                "semilla": args.semilla,
            },
        )
        print("[OK] Generado masivo.json.")
