# pika_description

Paquete ROS 2 con la descripción URDF del gripper Pika (Agilex Robotics).

## Dependencias

`pika_description` es autónomo — todas las mallas están en `meshes/`.

| Launch | Requiere |
|---|---|
| `display_pika_gripper.launch.py` | solo `pika_ros` |
| `display_pika_piper.launch.py` | `piper_ros` (brazo link1–6) + `pika_ros` (gripper) |

```bash
# Solo el gripper
source ~/pika_ros/install/setup.bash

# Brazo completo + gripper Pika
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

Medidas extraídas del plano técnico oficial de Agilex (`Images/`).

| Elemento | X (m) | Y (m) | Z (m) | Fuente |
|---|---|---|---|---|
| Eje de garras | 0 | 0 | 0.1358 | = joint7/joint8 del Piper |
| Intel D405 (双目) | -0.132 | 0 | 0.0908 | plano: 45 mm sobre eje garras |
| Cámara fisheye (单目) | 0 | 0.122 | 0.0623 | plano: 73.5 mm sobre eje garras, 122 mm desde brida |
| TCP | 0 | 0 | 0.185 | estimado |

### Orientación del visual D405

El mesh `d405.stl` requiere rotación respecto al frame del joint para quedar alineado con el gripper:

```xml
<visual>
  <origin xyz="0 0 0" rpy="0 3.1416 1.5708"/>
  <!-- 90° alrededor de Z + 180° alrededor de Y -->
</visual>
```

## Marco de coordenadas

```
Origen = cara de la brida (interfaz con link6 del Piper / parent)
+Z  → hacia las garras (eje herramienta)
+X  → apertura de las garras (derecha mirando la cara frontal)
+Y  → cara frontal del dispositivo (hacia el espacio de trabajo)
```

## Lanzar visualización

```bash
# Solo el gripper Pika (independiente de piper_ros)
source ~/pika_ros/install/setup.bash
ros2 launch pika_description display_pika_gripper.launch.py

# Brazo Piper (link1–6) + gripper Pika
source ~/piper_ros/install/setup.bash
source ~/pika_ros/install/setup.bash
ros2 launch pika_description display_pika_piper.launch.py              # gripper pika (default)
ros2 launch pika_description display_pika_piper.launch.py gripper:=otro  # gripper futuro
```

## Archivos

```
urdf/
  pika_gripper_macro.urdf.xacro      ← macro xacro parametrizable (prefix, parent, origin)
  pika_gripper_standalone.urdf.xacro ← wrapper standalone: world → gripper_base
  pika_piper_standalone.urdf.xacro   ← Piper arm (link1–6) + gripper Pika intercambiable
launch/
  display_pika_gripper.launch.py     ← robot_state_publisher + joint_state_publisher_gui + rviz2
  display_pika_piper.launch.py       ← igual, con arg gripper:=pika | ...
rviz/
  pika_gripper.rviz                  ← config RViz standalone (Fixed Frame: world)
  pika_piper.rviz                    ← config RViz brazo completo
meshes/
  gripper_base.STL                   ← cuerpo del gripper
  link7.STL                          ← garra izquierda
  link8.STL                          ← garra derecha
  d405.stl                           ← Intel RealSense D405
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
- Verificar posición exacta D405 con medición física (actualmente X=-0.132 m ajustado visualmente)
- Calibración de posición Z del TCP
