<div align="center">
  <h1 align="center"> pika_ros </h1>
  <h3 align="center"> Agilex Robotics </h3>
  <p align="center">
    <a href="README.md"> English </a> | <a href="README_zh.md">中文</a> | <a href="README_es.md">Español</a>
  </p>
</div>
<div align="center">

![ubuntu](https://img.shields.io/badge/Ubuntu-22.04-orange.svg)
![ROS2](https://img.shields.io/badge/ROS-humble-blue.svg)

</div>

> **Mapa de la documentación:** todos los documentos de este fork, con enlaces directos a sus secciones, están en [docs/README.md](docs/README.md).

## Introducción

Pika (en adelante, "Pika") es un **producto de captura de datos espaciales** orientado a escenarios de recolección de datos en el campo de la **inteligencia encarnada** (embodied intelligence). Es una solución ligera y portátil de captura-y-ejecución para operación de propósito general, compuesta por una unidad de captura de datos, un ejecutor con inferencia de modelos, y una estación de localización y mochila de datos complementarias. Permite capturar de forma eficiente, precisa, rápida y ligera los datos de operación espacial de un robot.

Pika ofrece una **capacidad de captura de información espacial de precisión milimétrica**, recolectando datos que abarcan información espacial precisa de 6 grados de libertad, información de profundidad, visión de luz visible en gran angular, e información de sujeción — cubriendo así las necesidades de **fusión multimodal de datos** de la inteligencia encarnada. El ejecutor puede usar los datos capturados por la unidad de recolección para la ejecución basada en inferencia de modelos.

Si tienes algún problema durante el uso, o alguna sugerencia o retroalimentación, contáctanos a través de:

- GitHub Issues: https://github.com/agilexrobotics/pika_ros/issues
- Correo electrónico: [support@agilex.ai](mailto:support@agilex.ai)

Nuestro equipo técnico responderá tus preguntas lo antes posible, brindándote el soporte y la ayuda necesarios.

Pika SDK: https://github.com/agilexrobotics/pika_sdk

Pika teleoperación: https://github.com/agilexrobotics/PikaAnyArm

Para más información, consulta el [Manual de Usuario del Producto Pika beta (CN)](https://agilexsupport.yuque.com/staff-hso6mo/peoot3/vm7e26ho2hmuw0ng) y las [Preguntas Frecuentes de uso de PIKA](https://agilexsupport.yuque.com/staff-hso6mo/peoot3/ltl2m8a3crra12kg).

## Entorno compatible

### Entorno de software

- Arquitectura: x86_64
- Sistema operativo: Ubuntu 22.04
- ROS: Humble

## Sobre este fork

Este repositorio es un fork de [agilexrobotics/pika_ros](https://github.com/agilexrobotics/pika_ros) (rama `ros2`), mantenido en [Ivan1721/pika_ros](https://github.com/Ivan1721/pika_ros). La rama de trabajo es `pika-custom-ros2`.

| Qué agrega | Dónde |
|---|---|
| Guía de instalación y uso paso a paso, con los flujos A/A+ (teleoperación), B (solo brazo), C (captura de cámaras y joints), D/D+ (simulación) y E (pipeline de datos) | [docs/manuales/Manual.md](docs/manuales/Manual.md) |
| URDF del gripper Pika (D405 + fisheye) y del brazo Piper + Pika | [src/pika_description](src/pika_description/README.md) |
| Simulación Gazebo del Piper + gripper Pika conectada a la cadena de teleoperación real. No necesita CAN, Pika Sense ni base stations | [src/pika_sim](src/pika_sim/README.md) |
| Fork de PikaAnyArm que conserva la estructura `piper/` (`pika_remote_piper`, `piper_ros`), eliminada en la V2 de upstream | submódulo `src/PikaAnyArm` → [Ivan1721/PikaAnyArm](https://github.com/Ivan1721/PikaAnyArm) |
| Correcciones: emparejamiento USB en `setup_device.py`, nombres de nodo y mimetismo del gripper en `open_multi_gripper.launch.py`, fixes de IK/teleop traídos de upstream | historial de git |
| Plan de investigación en percepción activa: cómo se conectan Pika + Piper, Milo ([Ivan1721/milo_ws](https://github.com/Ivan1721/milo_ws)) y el survey ActivePerceptionArms, con Milo como punto intermedio | [docs/percepcion_activa](docs/percepcion_activa/README.md) |
| Guía de calibración, hojas de datos, presupuesto energético | [docs/](docs/README.md) |

### Inicio rápido

```bash
cd ~/pika_ros
git submodule update --init --recursive
source /opt/ros/humble/setup.bash
colcon build --packages-select data_msgs && source install/setup.bash
colcon build && source install/setup.bash
```

`pika_locator` y `libsurvive` (localización Vive) solo existen como binarios precompilados en `source/install.zip`; ver la sección 6 del Manual. Para elegir el flujo según tu hardware, usa la tabla rápida del Manual. Sin ningún hardware, usa el **Flujo D+** (`ros2 launch pika_sim sim_piper_single.launch.py`).

Los problemas conocidos están al final del Manual. Las pautas de contribución y de sincronización con upstream están en [AGENTS.md](AGENTS.md).
