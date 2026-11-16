"""Módulo de extracción de características operativas y generación determinista de historiales."""

from __future__ import annotations

import random
from collections.abc import Iterable

import numpy as np

from src.ia.tipos import (
    DatasetHistorico,
    FeatureVector,
    RegistroHistoricoDemanda,
)
from src.modelos.pedido import LineaPedido, Pedido
from src.modelos.producto import Producto

MIN_PEDIDOS_TENDENCIA = 2


class ExtractorFeatures:
    """Extrae vectores de características a partir de productos y pedidos históricos."""

    @staticmethod
    def extraer_vector(producto: Producto, pedidos: list[Pedido]) -> FeatureVector:
        """Extrae el vector de características numéricas para un producto individual.

        Args:
            producto: Instancia del producto a evaluar.
            pedidos: Lista cronológica de pedidos históricos.

        Returns:
            Instancia inmutable de FeatureVector.
        """
        # Recolectar las cantidades solicitadas de este producto en el historial
        cantidades: list[int] = []
        quiebres_observados: int = 0

        for pedido in pedidos:
            for linea in pedido.lineas:
                if linea.id_producto == producto.id:
                    cantidades.append(linea.cantidad)
                    if linea.cantidad > producto.stock:
                        quiebres_observados += 1

        if not cantidades:
            # Producto sin histórico de demanda registrado
            return FeatureVector(
                id_producto=producto.id,
                rotacion_historica=0.0,
                frecuencia_pedidos=0.0,
                tamano_medio_lote=0.0,
                varianza_lote=0.0,
                stock_actual=producto.stock,
                precio_unitario=producto.precio,
                ratio_stock_rotacion=float(producto.stock),
                tasa_quiebre_reciente=0.0,
                tendencia_demanda=1.0,
                dias_cobertura_estimados=999.0 if producto.stock > 0 else 0.0,
            )

        rotacion_total = float(sum(cantidades))
        frecuencia = float(len(cantidades))
        tamano_medio = rotacion_total / frecuencia
        varianza = float(np.var(cantidades)) if len(cantidades) > 1 else 0.0
        ratio_stock_rot = float(producto.stock) / (rotacion_total + 1.0)
        tasa_quiebre = float(quiebres_observados) / frecuencia

        # Tendencia temporal: comparación de demanda entre segunda y primera mitad
        if len(cantidades) >= MIN_PEDIDOS_TENDENCIA:
            mitad = len(cantidades) // 2
            demanda_antigua = float(sum(cantidades[:mitad]))
            demanda_reciente = float(sum(cantidades[mitad:]))
            if demanda_antigua > 0.0:
                tendencia = demanda_reciente / demanda_antigua
            else:
                tendencia = 2.0 if demanda_reciente > 0.0 else 1.0
        else:
            tendencia = 1.0

        # Días de cobertura estimados en base al tamaño medio de lote
        if tamano_medio > 0.0:
            dias_cobertura = float(producto.stock) / tamano_medio
        else:
            dias_cobertura = 999.0 if producto.stock > 0 else 0.0

        return FeatureVector(
            id_producto=producto.id,
            rotacion_historica=rotacion_total,
            frecuencia_pedidos=frecuencia,
            tamano_medio_lote=tamano_medio,
            varianza_lote=varianza,
            stock_actual=producto.stock,
            precio_unitario=producto.precio,
            ratio_stock_rotacion=ratio_stock_rot,
            tasa_quiebre_reciente=tasa_quiebre,
            tendencia_demanda=tendencia,
            dias_cobertura_estimados=dias_cobertura,
        )

    @classmethod
    def extraer_matriz(
        cls,
        productos: Iterable[Producto],
        pedidos: list[Pedido],
    ) -> tuple[np.ndarray, list[FeatureVector]]:
        """Extrae la matriz de diseño X y la lista de vectores para una colección de productos.

        Args:
            productos: Colección o catálogo de productos.
            pedidos: Lista cronológica de pedidos históricos.

        Returns:
            Tupla (X, lista_vectores) donde X es una matriz NumPy 2D de float64.
        """
        vectores: list[FeatureVector] = [
            cls.extraer_vector(p, pedidos) for p in productos
        ]
        if not vectores:
            return np.empty((0, 10), dtype=np.float64), []

        matriz = np.array([v.a_array() for v in vectores], dtype=np.float64)
        return matriz, vectores


class GeneradorHistorialSintetico:
    """Generador reproducible y determinista de datos históricos y escenarios para IA."""

    def __init__(self, seed: int = 42) -> None:
        """Inicializa el generador fijando la semilla aleatoria."""
        self._seed = seed
        self._rnd = random.Random(seed)
        self._np_rnd = np.random.default_rng(seed)

    def generar_pedidos_sinteticos(
        self,
        catalogo: list[Producto],
        cantidad_pedidos: int = 300,
        lineas_maximas_por_pedido: int = 5,
    ) -> list[Pedido]:
        """Genera una lista reproducible de pedidos sintéticos sobre el catálogo provisto.

        Aplica una distribución de Pareto (80/20) para simular alta rotación en
        ciertos productos y rotación esporádica en otros.
        """
        if not catalogo:
            return []

        pedidos: list[Pedido] = []
        n_productos = len(catalogo)

        # Asignar probabilidades sesgadas (artículos A: 20% con 70% de demanda)
        pesos: list[float] = []
        for i in range(n_productos):
            if i < max(1, int(n_productos * 0.2)):
                pesos.append(5.0)  # Alta rotación
            elif i < int(n_productos * 0.8):
                pesos.append(1.5)  # Rotación media
            else:
                pesos.append(0.3)  # Cola larga / baja rotación

        total_pesos = sum(pesos)
        probabilidades = [p / total_pesos for p in pesos]

        for num_pedido in range(1, cantidad_pedidos + 1):
            num_lineas = self._rnd.randint(1, min(lineas_maximas_por_pedido, n_productos))
            indices_elegidos = self._np_rnd.choice(
                n_productos, size=num_lineas, replace=False, p=probabilidades
            )

            lineas: list[LineaPedido] = []
            for idx in indices_elegidos:
                prod = catalogo[int(idx)]
                # Cantidad demandada con distribución Poisson o uniforme sesgada
                cant = int(self._rnd.randint(1, 10))
                lineas.append(LineaPedido(id_producto=prod.id, cantidad=cant))

            pedidos.append(
                Pedido(
                    id=num_pedido,
                    lineas=lineas,
                )
            )

        return pedidos

    def generar_dataset_supervisado(
        self,
        catalogo: list[Producto],
        periodos: int = 20,
        pedidos_por_periodo: int = 30,
    ) -> DatasetHistorico:
        """Construye un DatasetHistorico supervisado multi-período para entrenamiento y test.

        Simula la evolución de ventas por período temporal:
        - Para cada período t y cada producto, se computan las características
          con base en las ventas acumuladas.
        - Se genera la demanda observada del período siguiente (t+1).
        - Se etiqueta el quiebre de stock real (1 si demanda > stock actual, 0 si no).
        """
        if not catalogo:
            return DatasetHistorico(
                registros=[],
                features=[],
                X=np.empty((0, 10), dtype=np.float64),
                y_demanda=np.empty(0, dtype=np.float64),
                y_quiebre=np.empty(0, dtype=np.float64),
            )

        registros: list[RegistroHistoricoDemanda] = []
        features_totales: list[FeatureVector] = []
        historial_acumulado: list[Pedido] = []

        filas_matriz: list[np.ndarray] = []
        y_demanda_valores: list[float] = []
        y_quiebre_valores: list[float] = []

        for p in range(1, periodos + 1):
            pedidos_del_periodo = self.generar_pedidos_sinteticos(
                catalogo,
                cantidad_pedidos=pedidos_por_periodo,
                lineas_maximas_por_pedido=4,
            )

            # Extraer features con los pedidos acumulados antes de este período
            for prod in catalogo:
                fv = ExtractorFeatures.extraer_vector(prod, historial_acumulado)

                # Calcular la demanda real que ocurrió en este período p para prod
                demanda_periodo = sum(
                    linea.cantidad
                    for ped in pedidos_del_periodo
                    for linea in ped.lineas
                    if linea.id_producto == prod.id
                )

                quiebre = demanda_periodo > prod.stock

                reg = RegistroHistoricoDemanda(
                    id_producto=prod.id,
                    periodo=p,
                    demanda_unidades=demanda_periodo,
                    stock_al_inicio=prod.stock,
                    quiebre_stock=quiebre,
                )

                registros.append(reg)
                features_totales.append(fv)
                filas_matriz.append(fv.a_array())
                y_demanda_valores.append(float(demanda_periodo))
                y_quiebre_valores.append(1.0 if quiebre else 0.0)

            # Acumular pedidos para el próximo período
            historial_acumulado.extend(pedidos_del_periodo)

        matriz_x = np.array(filas_matriz, dtype=np.float64)
        y_demanda = np.array(y_demanda_valores, dtype=np.float64)
        y_quiebre = np.array(y_quiebre_valores, dtype=np.float64)

        return DatasetHistorico(
            registros=registros,
            features=features_totales,
            X=matriz_x,
            y_demanda=y_demanda,
            y_quiebre=y_quiebre,
        )
