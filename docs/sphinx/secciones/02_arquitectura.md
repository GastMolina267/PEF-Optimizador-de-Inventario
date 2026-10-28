# 2. Arquitectura del Sistema

## 2.1. Visión General y Principios de Diseño

El sistema está diseñado bajo una arquitectura en capas desacopladas, siguiendo los principios de alta cohesión y bajo acoplamiento. La capa de dominio algorítmico y lógica de negocio es completamente independiente de la interfaz gráfica de usuario (**Flet**), de los generadores de datos y de las herramientas de medición e instrumentación.

### Principio Fundamental de Dualidad
Tanto la aplicación de escritorio como los scripts de benchmarking y las pruebas automatizadas consumen **exactamente la misma interfaz pública unificada** expuesta por la fachada `MotorInventario`. Esto permite conmutar la estrategia algorítmica (`estrategia="baseline"` frente a `estrategia="optimizado"`) con garantía estricta de reproducibilidad y equivalencia de resultados.

---

## 2.2. Diagrama de Componentes

```mermaid
flowchart TD
  subgraph CapaPresentacion ["Capa de Presentación (UI)"]
    UI["src/ui/app.py (Flet Desktop)\n7 Vistas Operativas + Panel Estado"]
  end

  subgraph CapaBenchmarking ["Capa de Benchmarking y Diagnóstico"]
    Bench["benchmarks/comparar.py"]
    ProfCPU["benchmarks/perfilar_cprofile.py"]
    ProfLine["benchmarks/perfilar_lineas.py"]
    ProfMem["benchmarks/perfilar_memoria.py"]
    Scalene["benchmarks/perfilar_scalene.py"]
  end

  subgraph CapaFachada ["Capa de Fachada Unificada"]
    Motor["src/motor/motor_inventario.py (MotorInventario)\nOrquestador y Conmutador de Estrategias"]
  end

  subgraph CapaDominio ["Capa de Dominio y Algoritmos"]
    Protocolo["src/inventario/protocolo.py (Catalogo Protocol)"]
    CatBase["src/inventario/catalogo_lineal.py (Baseline O(n))"]
    CatOpt["src/inventario/catalogo_hash.py (Optimizado O(1))"]
    TopN["src/ranking/top_productos.py (Heapq vs Sort)"]
    Agrup["src/pedidos/agrupador.py (Batch Picking O(L))"]
    CombDP["src/pedidos/combinaciones.py (DP Memoizada)"]
    ProcSeq["src/pedidos/procesador_secuencial.py"]
    ProcConc["src/pedidos/procesador_concurrente.py (ProcessPool)"]
    Cache["src/cache/cache_consultas.py (LRU + Invalidación Reactiva)"]
    Obs["src/observabilidad/apm.py (Elastic APM Instrumentation)"]
  end

  subgraph CapaDatos ["Capa de Datos y Persistencia"]
    Modelos["src/modelos/ (Producto, Pedido, LineaPedido)"]
    Cargador["src/datos/cargador.py"]
    Streaming["src/datos/streaming.py (Generadores JSONL)"]
    LotesParalelo["src/datos/procesador_lotes_paralelo.py"]
    Validador["src/datos/validador.py (ValidadorDataset)"]
    Datasets["data/datasets/ (*.json)"]
  end

  UI --> Motor
  Bench --> Motor
  Motor --> Protocolo
  Protocolo -.-> CatBase
  Protocolo -.-> CatOpt
  Motor --> TopN
  Motor --> Agrup
  Motor --> CombDP
  Motor --> ProcSeq
  Motor --> ProcConc
  Motor --> Cache
  Motor --> Obs
  Motor --> Cargador
  Cargador --> Datasets
  Cargador --> Validador
  Validador --> Modelos
```

---

## 2.3. Módulos y Responsabilidades del Sistema

El código fuente en `src/` se estructura en 9 subsistemas de alta cohesión:

| Módulo / Paquete | Responsabilidad Principal | Patrón / Técnica Aplicada |
|---|---|---|
| **`src/modelos/`** | Entidades inmutables de dominio (`Producto`, `Pedido`, `LineaPedido`, `ResumenProcesamiento`). | Dataclasses validadas con slots inmutables. |
| **`src/inventario/`** | Almacenamiento de catálogo, indexación hash y búsqueda secuencial baseline. | `CatalogoProtocol` (`typing.Protocol`), índice invertido de texto y hash map $O(1)$. |
| **`src/pedidos/`** | Preparación, validación, evaluación de factibilidad, batch picking y combinaciones sustitutas. | Separación de evaluación y asignación; Programación Dinámica (Knapsack variant) con memoización. |
| **`src/ranking/`** | Extracción de los $k$ ítems con mayor frecuencia agregada. | Min-Heap acotado (`heapq.nlargest`) en $O(n \log k)$ vs ordenamiento completo $O(n \log n)$. |
| **`src/cache/`** | Fachada de consultas frecuentes en memoria con capacidad acotada y desalojo. | Caché LRU (128 slots) basada en `OrderedDict` con **invalidación reactiva atómica** ante mutaciones. |
| **`src/datos/`** | Carga, validación estricta, lectura lazy en streaming, buffering y procesamiento paralelo en lotes. | Generadores de memoria $O(1)$, buffers de disco (`open(buffering=...)`), deserialización tipada. |
| **`src/observabilidad/`** | Captura de métricas transaccionales, spans y errores para Elastic APM. | Decoradores `@medir`, contextmanagers de spans y fallback seguro desacoplado. |
| **`src/motor/`** | Fachada orquestadora unificada que expone la API del sistema y conmuta estrategias. | Patrón Fachada (*Facade*) y Estrategia (*Strategy*). |
| **`src/ui/`** | Interfaz gráfica interactiva multiplataforma de escritorio. | **Flet** (arquitectura declarativa sobre Flutter Engine), tema accesible con alto contraste. |
