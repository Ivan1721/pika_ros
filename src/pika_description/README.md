# pika_description

Paquete ROS 2 con la descripción URDF del gripper Pika (Agilex Robotics).

## Dependencias

`pika_description` es autónomo: todas las mallas del gripper están en `meshes/`, y el brazo
Piper sale del `piper_description` que se compila en este mismo workspace
(`src/PikaAnyArm/piper/piper_ros/src/piper_description`). No hace falta `~/piper_ros`.

| Launch | Requiere |
|---|---|
| `display_pika_gripper.launch.py` | solo `pika_ros` |
| `display_pika_piper.launch.py` | solo `pika_ros` |

```bash
source ~/pika_ros/install/setup.bash
```

`pika_piper_standalone.urdf.xacro` une `world` con el link raíz del brazo, que se fija con el
argumento `arm_root`:

| `piper_description` en el path | Link raíz | Argumento |
|---|---|---|
| el de este workspace (default) | `dummy_link` | — |
| el de `~/piper_ros` | `base_link` | `arm_root:=base_link` |

Si el que queda en el path es el de `~/piper_ros` y no pasas el argumento, el URDF falla con
*Two root links found*.

Medidas, grados de libertad, alcance y figuras del Piper + Pika (generadas del URDF): [docs/PIPER_PIKA.md](docs/PIPER_PIKA.md).

## Estructura del modelo

El gripper es el modelo oficial de AgileX (`pika_gripper_description`, recibido el 20-10-2026):
mallas en `meshes/agilex/gripper/`, originales y planos en `agilex/`. El detalle de la conversión
y lo que cambió respecto de la aproximación anterior está en
[docs/PIPER_PIKA.md §6](docs/PIPER_PIKA.md#6-modelo-del-gripper-pika).

```
world
 └── gripper_base          ← carcasa, motor, D405 y fisheye (gripper_base_link.STL de AgileX)
      ├── pika_depth_link   ← D405, imager izquierdo (solo marco)
      ├── pika_fisheye_link ← fisheye (solo marco)
      ├── pika_jaw_left     ← garra izquierda (gripper_left_link.STL, prismática en +Y)
      ├── pika_jaw_right    ← garra derecha   (gripper_right_link.STL, prismática en −Y)
      └── pika_tcp          ← Tool Center Point, entre las garras
```

## Posiciones de referencia (desde `gripper_base`)

| Elemento | X (m) | Y (m) | Z (m) | Fuente |
|---|---|---|---|---|
| Garras (cerradas, origen de los joints) | −0.00642 | ±0.0415 | 0.0815 | URDF de AgileX |
| Puntas de las garras | — | — | 0.190 | malla de AgileX |
| Intel D405 (双目) | −0.0524 | 0.009 | 0.0583 | plano de AgileX: 46 mm sobre el eje de las garras, 132 mm detrás de las puntas |
| Cámara fisheye (单目) | −0.0799 | 0 | 0.0683 | plano de AgileX: 73,5 mm sobre el eje de las garras, 122 mm detrás de las puntas |
| TCP | −0.00642 | 0 | 0.180 | 1 cm detrás de las puntas |

Las dos cámaras miran a lo largo de +Z. Las mallas anteriores (`gripper_base.STL`, `link7/8.STL`,
`d405.stl`, `fisheye.stl`) quedan en `meshes/` pero ya no se usan.

## Marco de coordenadas

```
Origen = cara de la brida (interfaz con link6 del Piper / parent)
+Z  → hacia las garras (eje herramienta)
+Y  → dirección en que se desplazan las garras
−X  → lado de las cámaras
(AgileX usa X herramienta, Y garras, Z cámaras: x = −z_AgileX, y = y_AgileX, z = x_AgileX)
```

## Lanzar visualización

```bash
source ~/pika_ros/install/setup.bash

# Solo el gripper Pika
ros2 launch pika_description display_pika_gripper.launch.py

# Brazo Piper (link1–6) + gripper Pika
ros2 launch pika_description display_pika_piper.launch.py              # gripper pika (default)
ros2 launch pika_description display_pika_piper.launch.py gripper:=otro  # gripper futuro
ros2 launch pika_description display_pika_piper.launch.py arm_root:=base_link  # con ~/piper_ros
```

Para simular este mismo modelo en Gazebo, ver [`pika_sim`](../pika_sim/README.md).

## Archivos

```
urdf/
  pika_gripper_macro.urdf.xacro      ← macro xacro parametrizable (prefix, parent, origin)
  pika_gripper_standalone.urdf.xacro ← wrapper standalone: world → gripper_base
  pika_piper_standalone.urdf.xacro   ← Piper arm (link1–6) + gripper Pika intercambiable (args gripper, arm_root)
launch/
  display_pika_gripper.launch.py     ← robot_state_publisher + joint_state_publisher_gui + rviz2
  display_pika_piper.launch.py       ← igual, con args gripper:=pika | ... y arm_root
rviz/
  pika_gripper.rviz                  ← config RViz standalone (Fixed Frame: world)
  pika_piper.rviz                    ← config RViz brazo completo
meshes/
  agilex/gripper/                    ← mallas oficiales del gripper (AgileX): base y garras
  agilex/sense/                      ← mallas del Pika Sense (AgileX); fake_pika_sense las usa en RViz
  gripper_base.STL, link7/8.STL, d405.stl, fisheye.stl  ← aproximación anterior, sin uso
agilex/
  gripper/, sense/                   ← URDF y CSV originales de AgileX (ROS 1, de referencia)
  planos/                            ← planos con medidas del gripper y del Sense
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
- Verificar posiciones exactas de cámaras con medición física (D405 y fisheye ajustadas visualmente en RViz)
- Calibración de posición Z del TCP
