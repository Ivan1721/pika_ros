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

### Modo MIT (impedancia)

`control:=mit` emula el modo MIT del Piper con los valores de
`scripts/test_piper_mit_impedance.py` (`KP`, `KD`, `TARGETS`, `T_FF`, `ESCALA_GRAVEDAD`). Así se
prueban ganancias y compensación de gravedad sin el brazo. No usa la teleop.

```bash
ros2 launch pika_sim sim_piper_single.launch.py control:=mit [escala_gravedad:=0] [mit_script:=<ruta>]
ros2 topic pub --once /mit_emulador/perturbacion std_msgs/msg/Float64MultiArray "{data: [0, 1.0, 0, 0, 0, 0]}"
```

- **`kp·(q_d − q) + kd·(0 − q̇)`:** lo aplica Gazebo como resorte + amortiguador **implícitos** en cada articulación (`springStiffness`, `springReference`, `damping`). Un PD calculado desde un nodo ROS a 200 Hz sería inestable con las inercias mínimas de la muñeca.
- **`t_ref`** (y la perturbación): los manda `mit_emulador.py` como esfuerzo por `mit_ff_controller`.
- **Validación:** cada pieza se probó por separado (sin gravedad, el resorte llega a `q_d`; el esfuerzo desvía exactamente `τ/kp`). El conjunto coincide con el cálculo de pinocchio: sin compensación cae a la pose plegada; con `KP` J2 = 20, J3 = 15 sostiene la pose y cede [4,0°, 0,7°] por 1 N·m en J2.

### Argumentos

| Argumento | Default | Efecto |
|---|---|---|
| `control` | `teleop` | `mit`: emulación del modo MIT, sin puente ni Sense falso |
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

En modo MIT, el emulador reporta `q − q_d` en `/rosout` cada 2 s.

## Escena de demostración de NBV

Con la simulación en modo teleop corriendo (`gui:=false rviz:=false` sirve), el script hace lo siguiente:

```bash
ros2 run pika_sim escena_nbv_demo.py --salida ~/pika_ros/docs/percepcion_activa/img
python3 ~/pika_ros/src/pika_sim/scripts/panel_nbv.py ~/pika_ros/docs/percepcion_activa/img
```

1. Arma una escena: rama, fruta y hojas que la ocluyen de frente.
2. Genera 20 vistas candidatas en un casquete y calcula la visibilidad de cada una (trazando rayos contra las hojas) y si es alcanzable (IK para la D405, con |J5| > 10°).
3. Lleva el brazo a la mejor vista.
4. Guarda capturas de cámaras virtuales: la escena, la vista frontal y la elegida, más un JSON con los números.

`panel_nbv.py` arma con todo eso la figura `nbv_escena_panel.png`.

Las cámaras de Gazebo necesitan `DISPLAY`: en una sesión sin pantalla, usar un servidor X virtual. Es
una demostración para documentación, no el planner del paso 4. Los colores AgileX del brazo en
Gazebo se definen en `urdf/pika_piper_gazebo.urdf.xacro` (Gazebo Classic no usa los materiales
del URDF).

## Pendiente

- Cámaras D405 y fisheye simuladas en la pinza (topics `/gripper/camera/...` para `data_tools`).
- Escena con frutas y oclusión controlada.
- Versión para dos brazos (`teleop_rand_multi_piper.launch.py`).
