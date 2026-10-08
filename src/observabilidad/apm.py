"""Integración con Elastic APM: métricas de rendimiento y errores de la aplicación.

Qué se envía a Elastic:

- **Transacciones**: cada operación de negocio del motor (cargar un dataset, buscar,
  procesar pedidos, armar el ranking, etc.) con su duración y resultado.
- **Spans**: los pasos internos de las operaciones costosas (armar fragmentos,
  esperar al pool de procesos, leer lotes de un archivo).
- **Etiquetas**: estrategia, tamaño del dataset, tamaño de lote y workers, para filtrar
  y comparar en Kibana (baseline vs optimizado, secuencial vs pool).
- **Errores**: excepciones de las operaciones instrumentadas y los registros de
  ``logging`` con nivel ERROR o superior.

Activación: solo si existe la variable ``ELASTIC_APM_SERVER_URL`` (en el entorno o en
un archivo ``.env`` en la raíz del repo). Sin ella todo funciona igual y no se envía
nada, que es lo que ocurre en los tests y en el CI. Las credenciales nunca van al
repositorio: ver ``.env.example``.

Los workers del ``ProcessPoolExecutor`` no inicializan el agente. Se mide desde el
proceso principal: el envío de trabajo y la espera de resultados.
"""

from __future__ import annotations

import atexit
import functools
import logging
import os
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import Any, TypeVar

try:
    import elasticapm
except ImportError:  # pragma: no cover
    elasticapm = None  # type: ignore[assignment]

NOMBRE_SERVICIO = "optimizador-inventario"
VERSION_SERVICIO = "2.0.0"
RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
VARIABLES_APM = (
    "ELASTIC_APM_SERVER_URL",
    "ELASTIC_APM_API_KEY",
    "ELASTIC_APM_SECRET_TOKEN",
    "ELASTIC_APM_ENVIRONMENT",
    "ELASTIC_APM_SERVICE_NAME",
)

_cliente: Any | None = None
_registro = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def leer_archivo_env(ruta: Path) -> dict[str, str]:
    """Lee pares ``CLAVE=valor`` de un archivo ``.env`` (ignora comentarios y vacías)."""
    if not ruta.is_file():
        return {}
    valores: dict[str, str] = {}
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        valores[clave.strip()] = valor.strip().strip('"').strip("'")
    return valores


def obtener_configuracion(
    entorno: Mapping[str, str] | None = None, archivo_env: Path | None = None
) -> dict[str, str]:
    """Junta la configuración de APM: variables de entorno primero, ``.env`` después."""
    entorno = os.environ if entorno is None else entorno
    desde_archivo = leer_archivo_env(archivo_env or RAIZ_PROYECTO / ".env")
    return {
        clave: entorno.get(clave) or desde_archivo.get(clave, "")
        for clave in VARIABLES_APM
        if entorno.get(clave) or desde_archivo.get(clave)
    }


def configurar_apm(
    entorno: Mapping[str, str] | None = None,
    archivo_env: Path | None = None,
    fabrica_cliente: Callable[..., Any] | None = None,
) -> Any | None:
    """Crea el cliente de Elastic APM si hay configuración; si no, deja todo desactivado.

    Argumentos:
        entorno: Variables a usar (por defecto, ``os.environ``).
        archivo_env: Archivo ``.env`` alternativo (por defecto, el de la raíz del repo).
        fabrica_cliente: Constructor del cliente; los tests pasan uno falso.

    Retorna:
        El cliente creado, o ``None`` si falta ``ELASTIC_APM_SERVER_URL`` o no está instalado.
    """
    global _cliente
    if _cliente is not None:
        return _cliente

    config = obtener_configuracion(entorno, archivo_env)
    if not config.get("ELASTIC_APM_SERVER_URL"):
        return None

    if fabrica_cliente is None:
        if elasticapm is None:
            _registro.warning("Librería 'elastic-apm' no instalada. APM desactivado.")
            return None
        fabrica_cliente = elasticapm.Client

    _cliente = fabrica_cliente(
        service_name=config.get("ELASTIC_APM_SERVICE_NAME", NOMBRE_SERVICIO),
        service_version=VERSION_SERVICIO,
        server_url=config["ELASTIC_APM_SERVER_URL"],
        api_key=config.get("ELASTIC_APM_API_KEY") or None,
        secret_token=config.get("ELASTIC_APM_SECRET_TOKEN") or None,
        environment=config.get("ELASTIC_APM_ENVIRONMENT", "desarrollo"),
        # Ninguna configuración remota: todo lo define el repo.
        central_config=False,
        # La app no usa frameworks web; no hace falta auto-instrumentar librerías.
        instrument=False,
        transaction_sample_rate=1.0,
        metrics_interval="30s",
    )
    logging.getLogger().addHandler(ManejadorErroresAPM())
    atexit.register(cerrar_apm)
    _registro.info("Elastic APM activo: %s", config["ELASTIC_APM_SERVER_URL"])
    return _cliente


def cerrar_apm() -> None:
    """Envía lo pendiente y cierra el cliente (se llama sola al salir)."""
    global _cliente
    if _cliente is None:
        return
    for manejador in list(logging.getLogger().handlers):
        if isinstance(manejador, ManejadorErroresAPM):
            logging.getLogger().removeHandler(manejador)
    _cliente.close()
    _cliente = None


def apm_activo() -> bool:
    """Indica si hay un cliente de Elastic APM configurado."""
    return _cliente is not None


def _hay_transaccion_activa() -> bool:
    if elasticapm is None:
        return False
    return elasticapm.get_transaction_id() is not None


@contextmanager
def transaccion(
    nombre: str, tipo: str = "operacion", etiquetas: Mapping[str, Any] | None = None
) -> Iterator[None]:
    """Mide un bloque como transacción de APM; si falla, registra el error y lo relanza.

    Si APM está desactivado no hace nada.
    """
    if _cliente is None:
        yield
        return

    _cliente.begin_transaction(tipo)
    if etiquetas and elasticapm is not None:
        elasticapm.label(**etiquetas)
    try:
        yield
    except Exception:
        _cliente.capture_exception(handled=False)
        _cliente.end_transaction(nombre, "failure")
        raise
    _cliente.end_transaction(nombre, "success")


@contextmanager
def span(nombre: str, tipo: str = "app", etiquetas: Mapping[str, Any] | None = None):
    """Mide un paso interno dentro de la transacción activa (no hace nada sin APM)."""
    if _cliente is None or not _hay_transaccion_activa() or elasticapm is None:
        yield
        return
    with elasticapm.capture_span(nombre, span_type=tipo, labels=dict(etiquetas or {})):
        yield


def etiquetar(**etiquetas: Any) -> None:
    """Agrega etiquetas a la transacción activa (no hace nada sin APM)."""
    if _cliente is not None and _hay_transaccion_activa() and elasticapm is not None:
        elasticapm.label(**etiquetas)


def registrar_error(mensaje: str | None = None) -> None:
    """Envía la excepción que se está manejando como error ya controlado."""
    if _cliente is not None:
        _cliente.capture_exception(handled=True, extra={"mensaje": mensaje} if mensaje else None)


def medir(nombre: str, tipo: str = "operacion") -> Callable[[F], F]:
    """Decorador: la función se mide como transacción, o como span si ya hay una activa.

    Así una operación llamada desde la UI es una transacción propia, y la misma
    operación dentro de un escenario más grande aparece como un paso de ese escenario.
    """

    def decorador(funcion: F) -> F:
        @functools.wraps(funcion)
        def envoltura(*args: Any, **kwargs: Any) -> Any:
            if _cliente is None:
                return funcion(*args, **kwargs)
            if _hay_transaccion_activa():
                with span(nombre, tipo):
                    return funcion(*args, **kwargs)
            with transaccion(nombre, tipo):
                return funcion(*args, **kwargs)

        return envoltura  # type: ignore[return-value]

    return decorador


class ManejadorErroresAPM(logging.Handler):
    """Envía a Elastic los registros de ``logging`` con nivel ERROR o superior."""

    def __init__(self) -> None:
        super().__init__(level=logging.ERROR)

    def emit(self, record: logging.LogRecord) -> None:
        """Envía el registro como excepción (si trae una) o como mensaje de error."""
        if _cliente is None:
            return
        try:
            if record.exc_info:
                _cliente.capture_exception(
                    exc_info=record.exc_info, handled=True, extra={"logger": record.name}
                )
            else:
                _cliente.capture_message(
                    param_message={"message": record.msg, "params": record.args},
                    level=record.levelname.lower(),
                    logger_name=record.name,
                )
        except Exception:  # noqa: BLE001 - un error al reportar no debe romper la app
            self.handleError(record)
