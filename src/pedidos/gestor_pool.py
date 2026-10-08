"""Módulo de gestión del ciclo de vida del ProcessPoolExecutor para tareas paralelas."""

from __future__ import annotations

import atexit
import contextlib
import os
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor
from typing import Any


class GestorPool:
    """Administrador controlado para el ciclo de vida de ProcessPoolExecutor.

    Encapsula el inicio, reutilización, reinicio ante fallas (BrokenProcessPool)
    y apagado seguro de los procesos de trabajo (workers) entre ejecuciones.
    """

    def __init__(self) -> None:
        self._executor: ProcessPoolExecutor | None = None
        self._max_workers: int | None = None
        self._initializer: Callable[..., Any] | None = None
        self._initargs: tuple[Any, ...] = ()

    @property
    def activo(self) -> bool:
        """Indica si el pool tiene un executor activo."""
        return self._executor is not None

    @property
    def max_workers(self) -> int | None:
        """Cantidad de trabajadores configurada en el executor actual."""
        return self._max_workers

    def obtener_executor(
        self,
        max_workers: int | None = None,
        initializer: Callable[..., Any] | None = None,
        initargs: tuple[Any, ...] = (),
    ) -> ProcessPoolExecutor:
        """Retorna una instancia reutilizable de ProcessPoolExecutor.

        Si la cantidad de workers o la inicialización cambia, recrea el pool limpiamente.
        """
        workers = max_workers or min(os.cpu_count() or 4, 8)

        # Reutilizar si no cambió la configuración
        if (
            self._executor is not None
            and self._max_workers == workers
            and self._initializer == initializer
            and self._initargs == initargs
        ):
            return self._executor

        # Si cambió la configuración, apagar el anterior
        if self._executor is not None:
            self.cerrar(wait=True)

        self._max_workers = workers
        self._initializer = initializer
        self._initargs = initargs
        self._executor = ProcessPoolExecutor(
            max_workers=workers,
            initializer=initializer,
            initargs=initargs,
        )
        return self._executor

    def reiniciar(
        self,
        max_workers: int | None = None,
        initializer: Callable[..., Any] | None = None,
        initargs: tuple[Any, ...] = (),
    ) -> ProcessPoolExecutor:
        """Fuerza el reinicio del pool (útil ante BrokenProcessPool o recarga de datos)."""
        self.cerrar(wait=False)
        return self.obtener_executor(max_workers, initializer, initargs)

    def cerrar(self, wait: bool = True) -> None:
        """Cierra ordenadamente los procesos del pool."""
        if self._executor is not None:
            with contextlib.suppress(Exception):
                self._executor.shutdown(wait=wait, cancel_futures=True)
            self._executor = None
            self._max_workers = None
            self._initializer = None
            self._initargs = ()


# Instancia singleton predeterminada
pool_pedidos = GestorPool()


def _cerrar_pool_al_salir() -> None:
    pool_pedidos.cerrar(wait=True)


atexit.register(_cerrar_pool_al_salir)
