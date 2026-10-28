====================================
Optimizador de Inventario y Pedidos
====================================

Sistema de simulación, benchmarking y optimización logística desarrollado para la
cátedra de **Programación Eficiente** en la Universidad Blas Pascal (UBP - 2026).

El proyecto implementa una dualidad algorítmica estricta (*Baseline* vs. *Optimizado*),
permitiendo contrastar el rendimiento de estructuras de datos (listas vs. tablas hash con LRU),
algoritmos de ordenamiento (completos vs. Heaps Top-k), programación dinámica con memoización,
procesamiento concurrente con pools de procesos (reduciendo IPC), manejo eficiente de flujos
masivos de datos (streaming, buffering y procesamiento por lotes) y una suite integral de
seguridad y control de calidad continua en CI/CD.

.. toctree::
   :maxdepth: 2
   :caption: Documentación Canónica del Proyecto (Parcial 3)

   secciones/01_descripcion_funcional
   secciones/02_arquitectura
   secciones/03_instalacion_ejecucion
   secciones/04_diseno_tecnico
   secciones/05_api_contratos
   secciones/06_pruebas
   secciones/07_rendimiento
   secciones/08_seguridad
   secciones/09_mantenimiento

.. toctree::
   :maxdepth: 2
   :caption: Mediciones Detalladas y Profiling

   mediciones/tabla_comparativa
   mediciones/linea_base_parcial1
   mediciones/linea_base_parcial2
   mediciones/archivos_grandes
   mediciones/resumen_scalene
   mediciones/comandos_profiling

.. toctree::
   :maxdepth: 2
   :caption: Planificación y Registro Histórico

   guias/resumen_parcial_2
   guias/planificacion_parcial_3
   guias/seguridad_politica
   guias/planificacion_parcial_1
   guias/planificacion_parcial_2
   guias/analisis
   guias/flujo_aplicacion
   guias/observabilidad
   guias/propuestas_mejora

Índices y Tablas
================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
