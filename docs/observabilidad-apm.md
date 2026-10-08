# Observabilidad con Elastic APM

La aplicación envía a Elastic APM la duración de cada operación del motor, los pasos
internos de las operaciones costosas y los errores. Sirve para comparar en Kibana
baseline vs optimizado y secuencial vs pool de procesos, con datos reales de uso.

## Qué se envía

| Tipo | Ejemplos | Dónde se define |
|---|---|---|
| Transacciones | `motor.cargar_dataset`, `motor.procesar_pedidos`, `motor.obtener_top_solicitados`, `motor.procesar_pedidos_jsonl` | `@medir` en `src/motor/motor_inventario.py` |
| Spans | `pool.armar_fragmentos`, `pool.evaluar`, `lotes.procesar_archivo` | `span()` en los procesadores |
| Etiquetas | `estrategia`, `productos`, `pedidos`, `dataset`, `tamano_lote`, `workers`, `concurrente`, `cubiertos` | `MotorInventario._etiquetar` |
| Errores | Excepciones de las operaciones, `BrokenProcessPool`, `logging.error(...)` | `src/observabilidad/apm.py` |

Si una operación se llama dentro de otra transacción (por ejemplo, el escenario completo
de la pantalla de inicio o `scripts/demo_apm.py`), aparece como un span de esa transacción.

## Configuración

1. Copiar `.env.example` como `.env` en la raíz del repo. `.env` está en `.gitignore`.
2. Completar:
   - `ELASTIC_APM_SERVER_URL`: endpoint de APM del proyecto Observability. Se ve en Kibana,
     en **APM → Add data** (pestaña Flask o Django), fila `SERVER_URL`.
   - `ELASTIC_APM_API_KEY`: en esa misma pantalla, **Create API Key**. Se muestra una sola
     vez: copiarla en ese momento.
   - `ELASTIC_APM_ENVIRONMENT` (opcional): por ejemplo `oral` o el nombre de cada integrante,
     para separar las corridas en Kibana.
3. Instalar dependencias: `pip install -r requirements.txt`.

Sin `ELASTIC_APM_SERVER_URL` el agente no se inicia y la aplicación funciona igual.

## Uso

```powershell
python main.py                    # la app de escritorio envía cada operación
python -m scripts.demo_apm        # actividad de ejemplo + un error provocado
python -m scripts.demo_apm --vueltas 5
```

En Kibana: **Observability → Applications → Service inventory → optimizador-inventario**.

- **Transactions:** latencia por operación. Filtrar por `labels.estrategia` para comparar
  baseline y optimizado.
- **Trace sample** de `motor.procesar_pedidos` con `labels.concurrente : true`: muestra el
  tiempo de `pool.armar_fragmentos` y `pool.evaluar` (IPC).
- **Errors:** el `ValueError` del dataset inválido que provoca `demo_apm`.

## Decisiones

- **El agente vive solo en el proceso principal.** Los workers del pool arrancan limpios y no
  inicializan APM; el costo del paralelismo se mide desde afuera (envío y espera).
- **Sin auto-instrumentación** (`instrument=False`): la app no usa frameworks web, y así el
  agente no agrega trabajo a librerías que no interesan.
- **API key en lugar de secret token:** Elastic Cloud Serverless autentica a los agentes con
  API keys.
- **Tests sin servidor:** `tests/test_observabilidad.py` usa el cliente real con
  `disable_send=True` e intercepta su cola de eventos.
