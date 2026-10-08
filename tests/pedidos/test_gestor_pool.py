"""Pruebas unitarias para el gestor del ciclo de vida del ProcessPoolExecutor."""

from __future__ import annotations

import multiprocessing

from src.pedidos import gestor_pool
from src.pedidos.gestor_pool import GestorPool, pool_archivos, pool_pedidos


class TestGestorPool:
    def test_ciclo_de_vida_gestor_pool(self):
        gestor = GestorPool()
        assert not gestor.activo
        assert gestor.max_workers is None

        executor = gestor.obtener_executor(max_workers=2)
        assert gestor.activo
        assert gestor.max_workers == 2

        # Reutiliza el executor si no cambia configuración
        mismo_executor = gestor.obtener_executor(max_workers=2)
        assert mismo_executor is executor

        # Reiniciar con diferente cantidad de workers
        nuevo_executor = gestor.reiniciar(max_workers=3)
        assert gestor.max_workers == 3
        assert nuevo_executor is not executor

        # Cerrar
        gestor.cerrar(wait=True)
        assert not gestor.activo
        assert gestor.max_workers is None

    def test_contexto_multiproceso_respeta_variable_de_entorno(self, monkeypatch):
        monkeypatch.setenv("PEF_MP_START_METHOD", "spawn")
        assert gestor_pool._contexto_multiproceso().get_start_method() == "spawn"
        monkeypatch.delenv("PEF_MP_START_METHOD")
        esperado = (
            "forkserver" if "forkserver" in multiprocessing.get_all_start_methods() else "spawn"
        )
        assert gestor_pool._contexto_multiproceso().get_start_method() == esperado

    def test_singletons_disponibles(self):
        assert isinstance(pool_pedidos, GestorPool)
        assert isinstance(pool_archivos, GestorPool)
