# pika_description

Paquete ROS 2 con la descripción URDF del gripper Pika (Agilex Robotics).

## Dependencias externas

| Paquete | Fuente | Contenido utilizado |
|---|---|---|
| `piper_description` | `~/piper_ros` | `gripper_base.STL`, `link7.STL`, `link8.STL` |
| `realsense2_description` | submódulo `src/realsense-ros` | `d405.stl` |

El workspace `piper_ros` debe estar sourced antes que `pika_ros`:

```bash
source ~/piper_ros/install/setup.bash
source ~/pika_ros/install/setup.bash
```

## Estructura del modelo

```
world
 └── gripper_base          ← housing + mecanismo (gripper_base.STL)
      ├── pika_depth_link   ← Intel RealSense D405 (d405.stl)
      ├── pika_fisheye_link ← cámara fisheye 200° (sin malla — pendiente)
      ├── pika_jaw_left     ← garra izquierda (link7.STL, joint prismático)
      ├── pika_jaw_right    ← garra derecha   (link8.STL, joint prismático)
      └── pika_tcp          ← Tool Center Point (frame TF auxiliar)
```

La geometría de garras y su conexión a la brida es idéntica a la del Piper arm
(`joint7`/`joint8` en `piper_description/urdf/piper_description.urdf`).

## Posiciones de referencia (desde `gripper_base`)

| Elemento | Z (m) | Y (m) | Notas |
|---|---|---|---|
| Eje de garras | 0.1358 | 0 | = joint7/joint8 del Piper |
| Intel D405 | 0.0898 | 0.095 | 46 mm sobre eje de garras |
| Cámara fisheye | 0.0623 | 0.092 | 73.5 mm sobre eje de garras |
| TCP | 0.185 | 0 | estimado |

## Marco de coordenadas

```
Origen = cara de la brida (interfaz con link6 del Piper / parent)
+Z  → hacia las garras (eje herramienta)
+X  → apertura de las garras (derecha mirando la cara frontal)
+Y  → cara frontal del dispositivo (hacia el espacio de trabajo)
```

## Lanzar visualización

```bash
source ~/piper_ros/install/setup.bash
source ~/pika_ros/install/setup.bash
ros2 launch pika_description display_pika_gripper.launch.py
```

Abre RViz con el modelo completo y un slider para controlar la apertura de las garras.

## Archivos

```
urdf/
  pika_gripper_macro.urdf.xacro     ← macro xacro parametrizable (prefix, parent, origin)
  pika_gripper_standalone.urdf.xacro ← wrapper standalone para visualización
launch/
  display_pika_gripper.launch.py    ← robot_state_publisher + joint_state_publisher_gui + rviz2
rviz/
  pika_gripper.rviz                 ← configuración de RViz (Fixed Frame: world)
```

## Integrar en otro URDF

```xml
<xacro:include filename="$(find pika_description)/urdf/pika_gripper_macro.urdf.xacro"/>

<xacro:pika_gripper
  prefix="left_"
  parent="link6"
  origin_xyz="0 0 0"
  origin_rpy="0 0 0"/>
```

## Pendientes

- Malla 3D del housing Pika (215 × 191 × 143 mm) para `gripper_base` visual propio
- Malla 3D de la cámara fisheye para `pika_fisheye_link`
- Calibración de posición Z del TCP
