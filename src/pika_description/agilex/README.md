# Archivos de AgileX

Enviados por el soporte de AgileX (Cyntia) en el grupo de WhatsApp "Universidad Andrés
Bello&AgileX" el 20 de octubre de 2026, a pedido del equipo. No son públicos: **antes de
publicarlos fuera del equipo hay que confirmar con AgileX que se pueden redistribuir.**

| Carpeta | Contenido | Origen |
|---|---|---|
| `gripper/` | URDF del Pika Gripper solo y montado en el Piper, y CSV de propiedades | `pika_gripper_description.zip` (exportado de SolidWorks, ROS 1) |
| `sense/` | URDF y CSV del Pika Sense | `pika_sensor_description_v3.zip` (ROS 1) |
| `planos/pika_gripper_camaras.jpeg` | Vistas frontal y lateral del gripper con la posición de las cámaras: D405 (双目) a 132 mm de las puntas y 46 mm sobre el eje de las garras; fisheye (单目) a 122 mm y 73,5 mm; largo total 194,3 mm; línea base de la D405, 18 mm | imagen del chat |
| `planos/pika_sense_dimensiones.jpeg` | Dimensiones del Pika Sense: 215 × 254 × 220 mm | imagen del chat |

Las mallas STL están en `../meshes/agilex/`. No se copiaron:
- **Las mallas `.dae` del Sense (171 MB):** se usan las STL.
- **Los STEP** `Pika Gripper模型外发.STEP` (15 MB, SolidWorks 2019) y `Pika sense.STEP` (65 MB): quedan en `~/Downloads` de la máquina de desarrollo.

Cómo se usan en este repositorio: [docs/PIPER_PIKA.md §6](../docs/PIPER_PIKA.md#6-modelo-del-gripper-pika).
