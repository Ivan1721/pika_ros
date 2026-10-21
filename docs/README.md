# Documentación

Desde el 21 de octubre de 2026, la documentación del proyecto (guía de operación con los flujos A–E,
arquitectura, energía, percepción activa, informes de simulación) y el código de investigación
(`pika_sim`, `pika_description` con el modelo oficial del gripper de AgileX, herramientas del modo
MIT) están en el repositorio privado `Ivan1721/Next-Best-View`, que usa este fork como submódulo
(`deps/pika_ros`).

Este fork conserva el lado del hardware: drivers (`sensor_tools`), el fork de PikaAnyArm, `data_tools`,
los scripts de arranque de la máquina y los binarios del localizador Vive en `install/`. Las pautas
de trabajo están en [AGENTS.md](../AGENTS.md).

El historial completo de lo que se movió queda en la etiqueta `archivo-sim-gazebo`.

Fuente oficial de AgileX para el kit Pika: [portal de documentación en Yuque](https://agilexsupport.yuque.com/staff-hso6mo/peoot3/rcrola7ogxquhivi).
