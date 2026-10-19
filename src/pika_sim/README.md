# pika_sim

Simulación Gazebo (Classic 11) del brazo Piper con el gripper Pika, para usar la
cadena de teleoperación de `pika_remote_piper` sin el robot físico.

El paquete reemplaza dos piezas de hardware y deja el resto igual:

| Hardware | Sustituto | Topics |
|---|---|---|
| Piper + driver CAN (`piper_single_ctrl`) | `piper_sim_bridge.py` + Gazebo | entra `/joint_states_gripper`, sale `/joint_states_single` (mismo formato que el driver) |
| Pika Sense + tracker Vive (opcional) | `fake_pika_sense.py` + marcador en RViz | sale `/pika_pose`; mezcla `/joint_states` → `/joint_states_gripper`; llama `/teleop_trigger` |

`piper_FK.py`, `piper_IK.py` y `teleop_piper_publish.py` corren sin cambios.

## Uso

**Terminal 1** — simulación (sin conda):
```bash
conda deactivate
source ~/pika_ros/install/setup.bash
ros2 launch pika_sim sim_piper_single.launch.py
```

**Terminal 2** — teleop, igual que en el Flujo A pero con `sim:=true` (no arranca el driver CAN):
```bash
source ~/pika_ros/install/setup.bash
conda activate pika
ros2 launch pika_remote_piper teleop_rand_single_piper.launch.py sim:=true
```

En RViz, **click derecho sobre el bloque naranja** (Pika Sense simulado):
- *Teleop: iniciar / detener* — equivale al doble click del Sense
- *Pinza: abrir / media / cerrar*

Con la teleop iniciada, arrastra las flechas/anillos del marcador: el brazo sigue
el movimiento relativo, aplicado en el marco de la herramienta (igual que con el Vive).

### Argumentos

| Argumento | Default | Efecto |
|---|---|---|
| `sense` | `fake` | `real`: no arranca el Sense falso; correr aparte `bash scripts/start_single_sensor.bash` con el Sense y las base stations conectados |
| `gui` | `true` | `false`: Gazebo sin ventana (solo `gzserver`) |
| `rviz` | `true` | `false`: sin RViz |

### Sin RViz (scripts / pruebas)

```bash
ros2 service call /teleop_trigger std_srvs/srv/Trigger
ros2 topic pub --once /fake_pika_sense/gripper_opening std_msgs/msg/Float64 "{data: 0.05}"
```

## Detalles

- **Modelo**: `urdf/pika_piper_gazebo.urdf.xacro` incluye `pika_description/pika_piper_standalone.urdf.xacro` y agrega `ros2_control`. Las mallas `package://` se convierten a `file://` en el launch, porque Gazebo Classic no las resuelve.
- **Control**: `JointGroupPositionController` (posición directa) para `joint1..6` y para las dos garras. `piper_IK.py` ya interpola, como con el robot real.
- **Estado de Gazebo**: sale por `/joint_state_broadcaster/joint_states` (`use_local_topics`), porque `/joint_states` es la salida de `piper_IK.py`. El puente lo reordena por nombre a `joint1..6`: Gazebo no lo publica en ese orden y FK/IK leen `position[:6]`.
- **Pinza**: `position[6]` es la apertura total en metros (0–0,07), igual que el driver real; cada garra recibe la mitad.
- **Reloj**: teleop, IK y el puente usan reloj de pared, como en el robot real; Gazebo y `robot_state_publisher` usan `use_sim_time`.

## Pendiente

- Cámaras D405 y fisheye simuladas en la pinza (topics `/gripper/camera/...` para `data_tools`).
- Escena con frutas y oclusión controlada.
- Versión para dos brazos (`teleop_rand_multi_piper.launch.py`).
