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
| `escena` | `ninguna` | `manzano`: carga el manzano de percepción activa (ver más abajo) |
| `semilla` | `7` | semilla del follaje del manzano; 7 es la de la documentación |
| `arbol` | `primitivas` | `helios`: manzano realista generado con Helios (ver más abajo) |
| `ruta_helios` | `~/.cache/pika_sim/manzanos/apple_fruitingwall_e640_s7` | carpeta del árbol de Helios que se carga |
| `camaras` | `true` | `false`: sin la D405 ni la fisheye del gripper (Gazebo más liviano, p. ej. en modo MIT) |
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

## Cámaras del gripper

La D405 y la fisheye del gripper Pika están simuladas con los topics del hardware real (los de
`single_pika_teleop_data_params.yaml` en `data_tools`), a 640 × 480 y 30 Hz:

| Topic | Contenido |
|---|---|
| `/gripper/camera/color/image_raw` y `camera_info` | D405 color, 87° de campo horizontal |
| `/gripper/camera/aligned_depth_to_color/image_raw` y `camera_info` | D405 profundidad en **16UC1 mm**, como el driver real; 0 fuera de 7–50 cm |
| `/gripper/camera/depth/color/points` | D405 nube de puntos, en `pika_d405_optical_frame` |
| `/gripper/camera_fisheye/color/image_raw` y `camera_info` | fisheye equidistante de 180° en horizontal (la real tiene 200° en diagonal) |

- **Profundidad:** Gazebo la publica en 32FC1 metros por `/gripper/camera/depth_sim/image_raw`, y `profundidad_mm.py` la convierte. Sin esa conversión, `dataCapture.cpp` guardaría 0 y 1, porque convierte con cv_bridge a 16UC1 sin reescalar.
- **Orientación (supuesto):** las dos cámaras miran a lo largo de +Z de `gripper_base`, el eje de la herramienta, igual que en la demo de NBV. En la imagen, las garras quedan abajo. Hay que confirmarlo con el gripper real o con el CAD de AgileX.
- **Verificado:** con el brazo en la mejor vista del manzano, miles de puntos de la nube caen a menos de 3 mm de la superficie de cada manzana y ninguno dentro, así que el marco óptico y el TF son correctos.
- Gazebo avisa `Error advertising topic [.../pika_fisheye/image]`. Es su transporte interno y no afecta a los topics de ROS.

## Escenario agrícola: manzano

```bash
ros2 launch pika_sim sim_piper_single.launch.py escena:=manzano [semilla:=7]
```

`escena_manzano.py` genera un manzano reproducible: la misma semilla da siempre el mismo árbol. Tiene
tronco, cinco ramas, follaje al azar a lo largo de las ramas y cuatro manzanas. La manzana objetivo
queda en (0,55; 0; 0,30) m, detrás de un racimo de hojas. Los objetos son solo visuales, sin
colisión, así que el brazo atraviesa las hojas.

El nodo spawnea el árbol y publica la verdad del terreno, con QoS *transient local* para que la
reciba quien se conecte después:

| Topic | Tipo | Contenido |
|---|---|---|
| `/escena/frutas` | `visualization_msgs/MarkerArray` | manzanas en el marco `world`; la objetivo en amarillo (RViz la muestra) |
| `/escena/verdad` | `std_msgs/String` (JSON) | semilla; manzanas (centro, radio, objetivo); hojas (centro, normal, radio); ramas |

Parámetros del nodo: `semilla` (7), `n_manzanas` (4, hasta 6), `densidad_hojas` (16 intentos por
rama) y `objetivo_ocluida` (`true`: racimo delante de la objetivo). El launch solo expone la
semilla; los demás se cambian corriendo el nodo aparte:

```bash
ros2 run pika_sim escena_manzano.py --ros-args -p semilla:=3 -p n_manzanas:=6 -p densidad_hojas:=24
```

### Manzano realista (Helios)

![Manzano de Helios con el Piper](../../docs/percepcion_activa/img/nbv_helios_escena_panel.png)

`arbol:=helios` reemplaza los discos y cilindros por un manzano completo de
[Helios](https://github.com/PlantSimulationLab/PyHelios) (UC Davis), un simulador de plantas
procedural. El árbol trae tronco, ramas con sus horquetas, pecíolos, hojas, pedúnculos y manzanas,
con texturas fotográficas de corteza, hoja y fruto. Por defecto se usa `apple_fruitingwall`, un muro
frutal en espaldera, que es el sistema de los huertos pensados para cosecha robótica.

**1. Generar el árbol una vez** (unos 20 s). PyHelios va en un entorno virtual aparte, sin ROS:

```bash
python3 -m venv ~/.venvs/helios && ~/.venvs/helios/bin/pip install pyhelios3d pillow
env -u PYTHONPATH ~/.venvs/helios/bin/python -I ~/pika_ros/src/pika_sim/scripts/generar_manzano_helios.py \
    [--modelo apple_fruitingwall|apple] [--edad 640] [--semilla 7]
```

El script escribe en `~/.cache/pika_sim/manzanos/<modelo>_e<edad>_s<semilla>/`:
- las mallas `madera.obj`, `hojas.obj` y `frutas.obj`, con sus texturas;
- `verdad.json`, con el centro y el radio de cada manzana;
- `triangulos.npz`, con los triángulos de hojas y madera para la visibilidad, y solo los de tronco y ramas para los choques.

Cada hoja se recorta a la silueta de la foto de hoja de manzano. Helios la dibuja como un
rectángulo curvo con transparencia, y la cámara de profundidad de Gazebo no respeta la
transparencia: vería rectángulos. La misma semilla da el mismo árbol. La edad fija la fenología:
hacia los 450 días el árbol está en reposo invernal, sin hojas.

**2. Lanzar:**

```bash
ros2 launch pika_sim sim_piper_single.launch.py escena:=manzano arbol:=helios
```

El nodo elige como objetivo la manzana cuya vista de frente se acerque más a 30 % de visibilidad
(parámetro `visibilidad_frontal`). Ubica el árbol para que esa manzana quede en (0,55; 0; 0,30) m.
Las manzanas candidatas son las que dejan la plataforma entre 0,4 y 1,4 m de altura.
- **Plataforma:** el robot queda sobre una plataforma. El suelo de Gazebo se reemplaza por uno de huerto a la altura que resulta, 0,77 m con el árbol por defecto.
- **Hilera:** se agrega un árbol vecino a cada lado (parámetro `vecinos`).
- **Verdad del terreno:** `/escena/verdad` trae las manzanas en `world`, la ruta de `triangulos.npz` y la transformación del árbol a `world`.

Con 117 manzanas y unos 140 000 triángulos por árbol, Gazebo sigue en tiempo real (factor 1,0) y
las cámaras del gripper a 30 Hz.

**Licencias:** PyHelios es MIT, y el núcleo de Helios y sus texturas son LGPL-2.1. Por eso el repo
guarda el generador y no las mallas: cada máquina las genera.

## Escena de demostración de NBV

Con la simulación en modo teleop corriendo (`gui:=false rviz:=false` sirve), el script hace lo siguiente:

```bash
ros2 launch pika_sim sim_piper_single.launch.py gui:=false rviz:=false escena:=manzano
ros2 run pika_sim escena_nbv_demo.py --salida ~/pika_ros/docs/percepcion_activa/img
python3 ~/pika_ros/src/pika_sim/scripts/panel_nbv.py ~/pika_ros/docs/percepcion_activa/img nbv_manzano
```

1. Arma una escena:
   - `manzano` (por defecto): si la simulación se lanzó con `escena:=manzano`, usa ese árbol (lo lee de `/escena/verdad`); si no, lo genera y spawnea con `--semilla`;
   - `prueba`: una fruta y tres hojas.
2. Genera 20 vistas candidatas en un casquete y calcula la visibilidad de cada una (trazando rayos contra las hojas y las otras frutas) y si es alcanzable (IK para la D405, con |J5| > 10°).
   - Con el manzano de Helios, los rayos se trazan contra los triángulos reales de hojas y madera.
   - Además, se descartan las vistas en que la cámara o las puntas de las garras, unos 15 cm por delante de la D405, pasarían a menos de 3 cm de tronco o ramas (`--despeje`). Pecíolos y pedúnculos no cuentan, porque ceden.
   - El casquete es de 0,22 m con primitivas y de 0,30 m con Helios (`--radio`). Con 0,22 m, las garras quedan a unos 3 cm de la piel de la manzana, entre las ramas: con el árbol de Helios, 18 de las 20 vistas chocaban.
3. Lleva el brazo a la mejor vista.
4. Guarda lo que ven la D405 (`_d405_color.png`, `_d405_profundidad.png`) y la fisheye (`_fisheye.png`) del gripper en esa vista.
5. Guarda capturas de cámaras virtuales: la escena, la vista frontal y la elegida, más un JSON con los números.

`panel_nbv.py` arma con todo eso la figura `<prefijo>_escena_panel.png`. El prefijo es `nbv_manzano`, `nbv_helios` (árbol de Helios) o, para la escena de prueba, `nbv`.
La demo se puede repetir sobre la misma simulación: borra sus marcadores y cámaras auxiliares.

Las cámaras de Gazebo necesitan `DISPLAY`: en una sesión sin pantalla, usar un servidor X virtual. Es
una demostración para documentación, no el planner del paso 4. Los colores AgileX del brazo en
Gazebo se definen en `urdf/pika_piper_gazebo.urdf.xacro` (Gazebo Classic no usa los materiales
del URDF).

## Pendiente

- Confirmar hacia dónde miran la D405 y la fisheye reales (con el gripper o el CAD de AgileX).
- Probar una captura completa con `data_tools`: el config `single_pika_teleop` pide además topics del Sense y del brazo.
- Niveles de oclusión controlados (25–100 %): con Helios, elegir la manzana objetivo por nivel de visibilidad y variar la edad y la semilla ([recursos públicos](../../docs/percepcion_activa/recursos_publicos.md)).
- Choques del brazo completo con las ramas: la demo solo revisa la cámara y las garras. Hace falta MoveIt (paso 2 de la hoja de ruta).
- Árbol libre (`--modelo apple`): parte de la copa (~2 % de los triángulos) cae sobre la plataforma y el brazo la atraviesa. Habría que podar en el generador lo que quede del lado del robot; el muro frutal no tiene el problema.
- Versión para dos brazos (`teleop_rand_multi_piper.launch.py`).
