"""Pruebas de la integración con Elastic APM (fase F6).

Se usa el cliente real de ``elasticapm`` con ``disable_send=True`` y se intercepta su
cola de eventos: así se verifica qué transacciones, spans y errores se generarían sin
necesitar un servidor de Elastic.
"""

from __future__ import annotations

import logging
from pathlib import Path

import elasticapm
import pytest

from src.motor.motor_inventario import MotorInventario
from src.observabilidad import apm

BASE_DIR = Path(__file__).resolve().parent.parent
DEMO_ORAL = BASE_DIR / "data" / "datasets" / "demo_oral.json"


@pytest.fixture
def eventos(tmp_path: Path):
    """Activa APM con un cliente que no envía nada y devuelve la lista de eventos."""
    capturados: list[tuple[str, dict]] = []

    def fabrica(**config):
        # server_version evita que el agente consulte la versión del servidor al iniciar.
        cliente = elasticapm.Client(**config, disable_send=True, server_version=(8, 15, 0))

        def encolar(tipo, datos, flush=False):
            capturados.append((tipo, datos))

        cliente.queue = encolar
        cliente.tracer.queue_func = encolar
        return cliente

    apm.cerrar_apm()
    cliente = apm.configurar_apm(
        entorno={"ELASTIC_APM_SERVER_URL": "http://localhost:8200"},
        archivo_env=tmp_path / "no_existe.env",
        fabrica_cliente=fabrica,
    )
    assert cliente is not None
    yield capturados
    apm.cerrar_apm()


def _de_tipo(capturados, tipo):
    return [datos for t, datos in capturados if t == tipo]


class TestConfiguracion:
    def test_sin_url_queda_desactivado(self, tmp_path: Path):
        apm.cerrar_apm()
        assert apm.configurar_apm(entorno={}, archivo_env=tmp_path / "x.env") is None
        assert not apm.apm_activo()

    def test_lee_archivo_env(self, tmp_path: Path):
        archivo = tmp_path / ".env"
        archivo.write_text(
            "# comentario\nELASTIC_APM_SERVER_URL='https://apm.ejemplo'\n"
            "ELASTIC_APM_API_KEY=abc\nLINEA_INVALIDA\n\n",
            encoding="utf-8",
        )
        config = apm.obtener_configuracion(entorno={}, archivo_env=archivo)
        assert config == {
            "ELASTIC_APM_SERVER_URL": "https://apm.ejemplo",
            "ELASTIC_APM_API_KEY": "abc",
        }

    def test_el_entorno_tiene_prioridad_sobre_env(self, tmp_path: Path):
        archivo = tmp_path / ".env"
        archivo.write_text("ELASTIC_APM_ENVIRONMENT=archivo\n", encoding="utf-8")
        config = apm.obtener_configuracion(
            entorno={"ELASTIC_APM_ENVIRONMENT": "oral"}, archivo_env=archivo
        )
        assert config["ELASTIC_APM_ENVIRONMENT"] == "oral"

    def test_pasa_api_key_y_entorno_al_cliente(self, tmp_path: Path):
        recibido: dict = {}

        def fabrica(**config):
            recibido.update(config)
            return elasticapm.Client(**config, disable_send=True, server_version=(8, 15, 0))

        apm.cerrar_apm()
        apm.configurar_apm(
            entorno={
                "ELASTIC_APM_SERVER_URL": "https://apm.ejemplo",
                "ELASTIC_APM_API_KEY": "clave",
                "ELASTIC_APM_ENVIRONMENT": "oral",
            },
            archivo_env=tmp_path / "x.env",
            fabrica_cliente=fabrica,
        )
        apm.cerrar_apm()
        assert recibido["api_key"] == "clave"
        assert recibido["environment"] == "oral"
        assert recibido["service_name"] == apm.NOMBRE_SERVICIO
        assert recibido["secret_token"] is None


class TestSinApm:
    def test_helpers_no_hacen_nada(self):
        apm.cerrar_apm()
        with apm.transaccion("t"), apm.span("s"):
            apm.etiquetar(x=1)
            apm.registrar_error("nada")

        @apm.medir("f")
        def funcion():
            return 42

        assert funcion() == 42


class TestConApm:
    def test_operacion_del_motor_es_una_transaccion(self, eventos):
        motor = MotorInventario(estrategia="optimizado")
        motor.cargar_dataset(DEMO_ORAL)
        motor.procesar_pedidos()

        transacciones = _de_tipo(eventos, "transaction")
        nombres = [t["name"] for t in transacciones]
        assert nombres == ["motor.cargar_dataset", "motor.procesar_pedidos"]
        procesar = transacciones[1]
        assert procesar["result"] == "success"
        etiquetas = procesar["context"]["tags"]
        assert etiquetas["estrategia"] == "optimizado"
        assert etiquetas["lote_pedidos"] == len(motor.pedidos)
        assert etiquetas["concurrente"] is False

    def test_operaciones_anidadas_son_spans_del_escenario(self, eventos):
        with apm.transaccion("escenario.prueba", "escenario"):
            motor = MotorInventario(estrategia="optimizado")
            motor.cargar_dataset(DEMO_ORAL)
            motor.procesar_pedidos(concurrente=True)

        assert [t["name"] for t in _de_tipo(eventos, "transaction")] == ["escenario.prueba"]
        spans = {s["name"] for s in _de_tipo(eventos, "span")}
        assert {
            "motor.cargar_dataset",
            "motor.procesar_pedidos",
            "pool.armar_fragmentos",
            "pool.evaluar",
        } <= spans

    def test_error_de_carga_se_registra(self, eventos, tmp_path: Path):
        invalido = tmp_path / "invalido.json"
        invalido.write_text('{"productos": [], "pedidos": "x"}', encoding="utf-8")
        with pytest.raises(ValueError):
            MotorInventario().cargar_dataset(invalido)

        errores = _de_tipo(eventos, "error")
        assert len(errores) == 1
        assert errores[0]["exception"]["type"] == "ValueError"
        assert errores[0]["exception"]["handled"] is False
        transaccion = _de_tipo(eventos, "transaction")[0]
        assert transaccion["result"] == "failure"

    def test_logging_error_se_envia(self, eventos):
        logging.getLogger("pef.prueba").error("Fallo de %s", "prueba")
        mensajes = _de_tipo(eventos, "error")
        assert mensajes[0]["log"]["message"] == "Fallo de prueba"
        assert mensajes[0]["log"]["logger_name"] == "pef.prueba"

    def test_logging_con_excepcion_se_envia_como_excepcion(self, eventos):
        try:
            raise RuntimeError("explotó")
        except RuntimeError:
            logging.getLogger("pef.prueba").exception("Algo falló")
        errores = _de_tipo(eventos, "error")
        assert errores[0]["exception"]["type"] == "RuntimeError"

    def test_cerrar_quita_el_manejador_de_logging(self, eventos):
        apm.cerrar_apm()
        assert not any(
            isinstance(m, apm.ManejadorErroresAPM) for m in logging.getLogger().handlers
        )
