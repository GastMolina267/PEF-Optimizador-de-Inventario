"""Observabilidad: envío de métricas de rendimiento y errores a Elastic APM."""

from src.observabilidad.apm import (
    apm_activo,
    cerrar_apm,
    configurar_apm,
    etiquetar,
    medir,
    registrar_error,
    span,
    transaccion,
)

__all__ = [
    "apm_activo",
    "cerrar_apm",
    "configurar_apm",
    "etiquetar",
    "medir",
    "registrar_error",
    "span",
    "transaccion",
]
