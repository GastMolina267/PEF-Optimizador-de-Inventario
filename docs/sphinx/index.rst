====================================
Optimizador de Inventario y Pedidos
====================================

Sistema de simulación, benchmarking y optimización logística desarrollado para la
cátedra de **Programación Eficiente** en la Universidad Blas Pascal (UBP).

El proyecto implementa una dualidad algorítmica estricta (*Baseline* vs. *Optimizado*),
permitiendo contrastar el rendimiento de estructuras de datos (listas vs. tablas hash con LRU),
algoritmos de ordenamiento (completos vs. Heaps Top-k), programación dinámica con memoización,
procesamiento concurrente con pools de procesos (reduciendo IPC) y manejo eficiente de flujos
masivos de datos (streaming, buffering y procesamiento por lotes).

.. toctree::
   :maxdepth: 2
   :caption: Guías y Arquitectura

   guias/resumen_parcial_2
   guias/analisis
   guias/flujo_aplicacion
   guias/observabilidad
   guias/planificacion_parcial_1
   guias/planificacion_parcial_2
   guias/propuestas_mejora

.. toctree::
   :maxdepth: 2
   :caption: Mediciones y Benchmarking

   mediciones/tabla_comparativa
   mediciones/linea_base_parcial1
   mediciones/linea_base_parcial2
   mediciones/archivos_grandes
   mediciones/resumen_scalene
   mediciones/comandos_profiling

.. toctree::
   :maxdepth: 2
   :caption: Referencia de la API

   api/motor
   api/modelos
   api/inventario
   api/pedidos
   api/ranking
   api/cache
   api/datos
   api/observabilidad
   api/ui

Índices y Tablas
================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
