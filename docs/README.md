# Documentación — pika_ros

Índice de la documentación del proyecto, organizada por tema.

| Carpeta | Contenido |
|---|---|
| [`manuales/`](manuales/) | Guía de configuración en español ([Manual.md](manuales/Manual.md)), manual oficial de AgileX para el brazo Piper, y manual oficial de producto Pika (EN) |
| [`datasheets/`](datasheets/) | Hoja de datos oficial del producto Pika (chino y español) |
| [`calibracion/`](calibracion/) | Guía de despliegue y calibración de Pika Station / Tracker (Vive) |
| [`arquitectura/`](arquitectura/README.md) | Diagrama de alimentación y comunicaciones (red → fuentes → equipos → CAN/USB → drivers → nodos ROS 2), enlaces y topología USB |
| [`energia/`](energia/) | Consumo energético por componente e inventario de equipo |
| [`percepcion_activa/`](percepcion_activa/README.md) | Cómo se conectan Pika + Piper, Milo (`milo_ws`) y el survey ActivePerceptionArms: Milo como punto intermedio, decisiones, contrato por robot y hoja de ruta; [lazos de control, cinemática, impedancia y NBV](percepcion_activa/lazos_cinematica_nbv.md); [recursos públicos](percepcion_activa/recursos_publicos.md) |
| [`presentaciones/`](presentaciones/) | Resumen de contribuciones de este fork frente al repositorio original de AgileX |

Documentación de paquetes (READMEs dentro de `src/`; `pika_description` y `pika_sim` son propios de este fork):

| Paquete | Contenido |
|---|---|
| [`pika_description`](../src/pika_description/README.md) | URDF del gripper Pika y del brazo Piper + Pika |
| [`pika_sim`](../src/pika_sim/README.md) | Simulación Gazebo del Piper + Pika conectada a la teleoperación real (Flujo D+ del Manual) |
| [`sensor_tools`](../src/sensor_tools/README.md) | Launch files y topics del hardware Pika |

Problemas conocidos del software: al final de [Manual.md](manuales/Manual.md#problemas-conocidos-del-software).

Fuente primaria de todo el contenido oficial de AgileX: [portal de documentación técnica de Pika en Yuque](https://agilexsupport.yuque.com/staff-hso6mo/peoot3/rcrola7ogxquhivi).
