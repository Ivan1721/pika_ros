# Estado del proyecto: Piper + Pika para percepción activa en agricultura

Revisión completa del 21 de octubre de 2026. Resume el hardware, el software, el acceso a los
datos de cada sensor, el trabajo hecho, el estado actual, las limitaciones y los caminos posibles,
con los algoritmos que se pueden aplicar en cada área. Cada sección enlaza al documento que tiene
el detalle; este no lo repite.

**El proyecto en una frase.** Un brazo AgileX Piper con el gripper Pika (cámara de profundidad
D405 y fisheye en la pinza), sobre una plataforma remolcable, para estudiar **percepción activa**
en huertos: que el robot elija desde dónde mirar una fruta tapada por hojas, considerando si el
brazo puede llegar a esa vista. El mismo kit Pika sirve para teleoperar el brazo y para grabar
demostraciones humanas.

**Repositorios:**

| Repositorio | Qué contiene |
|---|---|
| [Ivan1721/pika_ros](https://github.com/Ivan1721/pika_ros) | Este: ROS 2 Humble para el kit Pika y el Piper, simulación (`pika_sim`), modelo del robot (`pika_description`) y percepción activa. Rama de trabajo `pika-custom-ros2`; la simulación y esta documentación están en `sim-gazebo` (sin unir todavía) |
| [Ivan1721/ActivePerceptionArms](https://github.com/Ivan1721/ActivePerceptionArms) | Revisión sistemática del estado del arte (survey), proyecto de tesis y figuras |
| [Ivan1721/milo_ws](https://github.com/Ivan1721/milo_ws) (rama `brazo`) | Milo, manipulador móvil del equipo: plantillas ya resueltas (MoveIt, OctoMap, cámara en la pinza) y segundo robot para el método |

## 1. Hardware

### 1.1 Componentes

| Equipo | Especificaciones | Rol |
|---|---|---|
| **Brazo AgileX Piper** | 6 GDL rotacionales, carga 1,5 kg, radio de trabajo 626,75 mm, repetibilidad ±0,1 mm, 4,2 kg, 24 V DC (24–26 V), ≤ 40 W continuo y ≤ 120 W pico; CAN a 1 Mbit/s; modos de posición y MIT (impedancia por articulación) | Manipulador |
| **Pika Gripper** | 617 g, 215 × 191 × 143 mm, pinza de dos dedos de 0 a 95 mm (94 mm en la malla de AgileX), fuerza de agarre 2 kg, encoder de la pinza a 100 Hz; motor a 24 V desde el último joint del Piper; un cable USB 3.0 Type-C para cámaras y datos | Efector con cámaras |
| · Intel RealSense D405 | Estéreo con obturador global, 87° × 58°, rango óptimo 7–50 cm, ±2 % a 50 cm, hasta 1280 × 720 a 90 FPS (se usa 640 × 480 a 30 FPS); línea base de 18 mm | Color y profundidad cercana |
| · Cámara fisheye | 200° en diagonal; 1280 × 720 a 30 FPS o 640 × 480 a 30/60/90 FPS | Contexto amplio (la que usan las políticas aprendidas) |
| **Pika Sense** | 448 g, 215 × 220 × 257 mm; misma D405, fisheye y pinza (sensor, sin motor); pose 6D con tracker Vive a 120 Hz, ±1,5 mm sin obstrucciones; doble click para armar la teleoperación | Mando del operador y grabación de demostraciones |
| **Pika Station** (estación base Lighthouse 2.0) | 110° × 150°, 12 V, 3 W, batería de 30 h; sin cable de datos | Referencia del tracker |
| **Plataforma remolcable** | Batería LiFePO4 Ritar 12,8 V 200 Ah (2,56 kWh) → motor Hydronit (12 V DC) e inversor Enertik de 1,2 kW / 230 V → PDU; el robot y el laptop van sobre ella | Llevar el sistema al huerto |
| **Vehículo tractor** | Hoy un AgileX Scout 2.0, **independiente**: no comparte energía ni datos con la plataforma | Remolque |
| **Computador** | Laptop con Ubuntu 22.04 y ROS 2 Humble; el equipo de desarrollo tiene Ryzen 7 5800H, 15 GB de RAM y RTX 3070 Laptop | Todo el software |

Fuentes: [hoja de datos Pika](datasheets/), [manual del Piper](manuales/agilex-piper-user-manual.pdf),
[modelo de AgileX y planos](../src/pika_description/docs/PIPER_PIKA.md#6-modelo-del-gripper-pika),
[arquitectura de alimentación y comunicaciones](arquitectura/README.md) (con diagramas),
[consumo y autonomía](energia/Consumo_Energia.md).

### 1.2 Cinemática del Piper con la Pika

| Dato | Valor |
|---|---|
| Tramos | hombro a 0,123 m; brazo 0,285 m; antebrazo 0,252 m; muñeca 0,091 m; brida → TCP 0,180 m (puntas de las garras a 0,190 m) |
| Alcance del TCP desde el hombro | 0,808 m como máximo |
| Muñeca | esférica en la práctica (ejes de J4 y J6 a < 0,09 mm del centro) → IK analítica posible |
| Singularidad | J5 = 0 alinea J4 y J6; conviene \|J5\| > ~10° |
| Límites que más pesan | J5 ±70° (limita las vistas desde abajo y muy laterales); J1 −150° … +124° |

Detalle, figuras y medidas: [PIPER_PIKA.md](../src/pika_description/docs/PIPER_PIKA.md).

## 2. Software y aplicación

### 2.1 Paquetes

| Paquete | Qué hace |
|---|---|
| `sensor_tools` | Drivers del kit Pika: D405 (`realsense2_camera`), fisheye (`usb_camera.py`), puerto serie de la pinza e IMU (`serial_gripper_imu`); incluye el localizador Vive |
| `pika_locator`, `libsurvive` | Localización del tracker (binarios en `install/`, sin fuente) |
| `pika_remote_piper` (PikaAnyArm) | Teleoperación: FK, IK (CasADi + IPOPT) y publicación de comandos al Piper |
| `piper`, `piper_description` | Driver CAN del Piper y su URDF |
| `data_tools`, `data_msgs` | Captura, sincronización y conversión de datos (ARIO → HDF5 → LeRobot / MCAP) |
| `pika_description` (propio) | URDF del Piper con el gripper Pika, con el modelo oficial de AgileX |
| `pika_sim` (propio) | Simulación en Gazebo Classic: brazo, pinza, cámaras, escenas de huerto, demo de NBV y renders |

### 2.2 Flujos de uso

Los define el [Manual](manuales/Manual.md):

| Flujo | Para qué |
|---|---|
| A / A+ | Teleoperar uno o dos Piper con uno o dos Pika Sense |
| B | Mover el Piper solo, desde RViz |
| C | Capturar imágenes y articulaciones enseñando por arrastre |
| D / D+ | Simulación en Gazebo; D+ conecta la teleoperación real a `pika_sim` |
| E | Grabar, sincronizar y convertir datos |

### 2.3 Lazos de control

```
operador ─(Vive, 120 Hz)→ Pika Sense ─/pika_pose→ teleop ─IK→ /joint_states ─(CAN, 200 Hz)→ Piper
                                                                     └── modo MIT: τ = kp(q_d − q) + kd(−q̇) + t_ref
cámaras de la pinza (30 Hz) ─→ percepción ─→ elección de vista (NBV) ─→ IK / MoveIt ─→ brazo
```

Diagramas y datos medidos de cada lazo: [lazos_cinematica_nbv.md](percepcion_activa/lazos_cinematica_nbv.md).

## 3. Acceso a los datos de los sensores

### 3.1 Topics

Con un gripper; con dos, cada topic lleva el namespace del lado (`[name]` en los `start_*.bash`).
Los mismos topics salen de la simulación con `pika_sim`.

| Dato | Topic | Tipo | Frecuencia | Notas |
|---|---|---|---|---|
| D405 color | `/gripper/camera/color/image_raw` (+ `camera_info`) | `sensor_msgs/Image` | 30 Hz | 640 × 480 |
| D405 profundidad alineada | `/gripper/camera/aligned_depth_to_color/image_raw` | `sensor_msgs/Image` | 30 Hz | 16UC1 en mm; 0 = sin dato |
| D405 nube de puntos | `/gripper/camera/depth/color/points` | `sensor_msgs/PointCloud2` | 30 Hz | en el hardware la publica el driver de la RealSense (`pointcloud.enable`, activo por defecto) |
| Fisheye | `/gripper/camera_fisheye/color/image_raw` | `sensor_msgs/Image` | 30 Hz | |
| Pinza | `/gripper/data` | `data_msgs/Gripper` | ~100 Hz | ángulo, apertura, esfuerzo, velocidad, habilitación, voltaje, temperaturas, estado |
| Pinza como articulación | `/gripper/joint_state` | `sensor_msgs/JointState` | | apertura total en m |
| IMU (versiones anteriores) | `/imu/data` | `sensor_msgs/Imu` | 100 Hz | |
| Pose del Sense | `/pika_pose` (`/pika_pose_l`, `/pika_pose_r`) | `geometry_msgs/PoseStamped` | 120 Hz | marco de las estaciones Vive |
| Articulaciones del Piper | `/joint_states_single` | `sensor_msgs/JointState` | 200 Hz | nombres `joint0..joint6` |
| Comando al Piper | `/joint_states_gripper` | `sensor_msgs/JointState` | | 6 articulaciones + apertura |
| Escena simulada (verdad del terreno) | `/escena/verdad`, `/escena/frutas` | `std_msgs/String` (JSON), `MarkerArray` | transient local | solo en `pika_sim` |

### 3.2 Cómo leerlos

```bash
ros2 topic list                                     # qué hay
ros2 topic hz /gripper/camera/color/image_raw       # frecuencia
ros2 topic echo /gripper/data                       # pinza
ros2 bag record -o sesion /gripper/camera/color/image_raw /gripper/camera/aligned_depth_to_color/image_raw /pika_pose
```

```python
import rclpy, numpy as np
from rclpy.node import Node
from sensor_msgs.msg import Image
from geometry_msgs.msg import PoseStamped

class Lector(Node):
    def __init__(self):
        super().__init__('lector')
        self.create_subscription(Image, '/gripper/camera/aligned_depth_to_color/image_raw', self.profundidad, 1)
        self.create_subscription(PoseStamped, '/pika_pose', lambda m: setattr(self, 'pose', m.pose), 1)

    def profundidad(self, m):
        z = np.frombuffer(bytes(m.data), np.uint16).reshape(m.height, m.width) / 1000.0   # metros
        self.get_logger().info(f'mediana {np.median(z[z > 0]):.3f} m')

rclpy.init(); rclpy.spin(Lector())
```

### 3.3 Grabación y formatos

| Herramienta | Salida | Uso |
|---|---|---|
| `data_tools` (Flujo E) | ARIO por episodio → HDF5 → LeRobot o MCAP | Demostraciones para aprendizaje por imitación |
| `scripts/capture_bundle.py` | N imágenes por topic + CSV de articulaciones en `~/capturas_ros/` | Capturas rápidas (Flujo C) |
| `ros2 bag` | rosbag2 | Cualquier combinación de topics |

`data_tools` exige que cada sensor publique a más de 25 Hz. En simulación, con densidad alta y las
ventanas de Gazebo y RViz abiertas, las cámaras bajan de ese umbral: para grabar hay que correr sin
ventanas.

## 4. Trabajo realizado

| Fecha | Trabajo |
|---|---|
| 19-10-2026 | Remoto por SSH y limpieza del token; sincronización con AgileX; `CLAUDE.md` y `AGENTS.md`; plan de simulación sin hardware |
| 19-10-2026 | `pika_sim`: el Piper con la Pika en Gazebo, conectado a la teleoperación real (puente del driver CAN y Sense falso) |
| 19–20-10-2026 | Revisión del modo MIT: inestabilidad con kp = 5 por la gravedad, compensación `T_FF` calculada del URDF, emulación en Gazebo |
| 20-10-2026 | Documento de lazos, cinemática e IK (error medido de la IK de la teleop: 9,4 mm y 8,5° por la regularización) |
| 20-10-2026 | Figuras del Piper con la Pika y diagramas de arquitectura (bimanual y plataforma de un brazo) |
| 20-10-2026 | Cámaras simuladas en la pinza con los topics del hardware; manzano de primitivas; demo de NBV con visibilidad y alcanzabilidad |
| 20-10-2026 | Manzano realista con Helios (muro frutal, tres densidades), seis iluminaciones, consumo de recursos medido |
| 20-10-2026 | Galería de oclusión validada: la visibilidad del planner coincide con la imagen (error medio de 2,6 puntos); [informe de escenarios](percepcion_activa/escenarios_simulacion.md) |
| 20-10-2026 | Modelo oficial del gripper y del Sense de AgileX integrado (apertura real 0–94 mm, cámaras confirmadas, `T_FF` recalculado) |
| 21-10-2026 | Herramientas de render (fondo blanco y croma) y figuras G1–G7 para el survey |

## 5. Estado actual

| Área | Estado | Detalle |
|---|---|---|
| Hardware de la plataforma | 🔧 en montaje | Eléctrica diseñada y resuelta; el robot se está trasladando; **sin parada de emergencia** (pendiente) |
| Pruebas en el robot real | ⏸ pospuestas | Desde el 19-10-2026, por el traslado |
| Teleoperación | ✅ funciona | En simulación probada sin hardware; en real, según el Flujo A |
| Modo MIT (impedancia) | ⚠️ falta probar en real | `T_FF` y estabilidad calculadas; probar con `ESCALA_GRAVEDAD` 0,5 sosteniendo el brazo |
| Grabación teleop (`*_pika_teleop`) | ⚠️ con un arreglo local | Las configs de `data_tools` esperan topics de PikaAnyArm V2; ver [problemas conocidos](manuales/Manual.md#problemas-conocidos-del-software) |
| Simulación (`pika_sim`) | ✅ | Brazo, pinza, cámaras con los topics reales, escenas de huerto, luces, renders |
| Modelo del robot | ✅ | Gripper oficial de AgileX; masa ajustada al peso publicado (falta pesarlo) |
| Visibilidad y NBV | 🟡 demo | Calcula visibilidad y alcanzabilidad; no es todavía un planner |
| MoveIt 2 | ⏳ no empezado | Paso 2 de la hoja de ruta |
| Detector de fruta | ⏳ no empezado | YOLO u otro, entrenado con datos simulados y reales |
| Rama `sim-gazebo` | ⚠️ sin unir | Todo lo de simulación y esta documentación; falta unirla a `pika-custom-ros2` |

## 6. Algoritmos posibles por área

Para cada área: qué existe, qué encaja con este sistema y qué haría falta. Lo marcado con **★** es
lo que más rinde con lo que ya hay.

### 6.1 Visión

| Tarea | Algoritmos | Encaje con Piper + Pika |
|---|---|---|
| Detección de fruta | **★ YOLO (v8/v11)**, RT-DETR; Faster R-CNN como referencia | Rápido sobre la D405 a 30 Hz; entrenar con la galería simulada (etiquetas automáticas desde la verdad del terreno) más imágenes reales |
| Segmentación de instancias | YOLO-seg, Mask R-CNN; **SAM 2** con indicaciones desde el detector | Máscara visible de la fruta → visibilidad medida, como en la galería |
| Fruta tapada (amodal) | Completado amodal de máscaras; ajuste de esfera o elipsoide a los puntos visibles | Centro y tamaño aunque esté tapada: base para elegir la vista y para cortar |
| Pose 3D de la fruta y del pedúnculo | Ajuste de esfera por RANSAC sobre la nube de la D405; FoundationPose u otros de pose 6D con modelo | La D405 a 15–35 cm da puntos densos; el pedúnculo es el punto de corte |
| Mapa de la escena | **★ OctoMap** (lo usa Milo), TSDF / Voxblox / nvblox (GPU) | Para la ganancia de información del NBV y para choques en MoveIt |
| Representaciones neuronales | NeRF, **3D Gaussian Splatting** (GS-NBV en el corpus) | Reconstrucción fina del dosel; más costosa, útil offline o con GPU |
| Uso de la fisheye | Detección de contexto, flujo óptico, entrada de políticas aprendidas | Ve toda la escena y las garras a la vez |

### 6.2 Elección de vista (percepción activa)

| Enfoque | Cómo funciona | Estado aquí |
|---|---|---|
| **★ Heurística de visibilidad** (política B) | Puntaje = fracción visible de la fruta según la máscara o el modelo | Implementada en la demo con geometría conocida; falta con el detector |
| **★ Ganancia de información volumétrica** (política A) | Rayos desde cada vista candidata sobre OctoMap; entropía de vóxeles desconocidos, con peso en la región de la fruta | Pendiente; plantilla en Milo |
| Atención a la región de interés | Vóxeles de fruta y pedúnculo pesan más (Burusa y otros, en el corpus) | Siguiente paso natural sobre la política A |
| NBV consciente de la ejecución | Puntaje que combina información con alcanzabilidad, distancia articular y choques | En parte: la demo ya descarta por IK, \|J5\| y choques con ramas |
| Aprendido | RL o redes que predicen la ganancia; benchmarks como DAVIS-Ag | Futuro; necesita muchos episodios (la simulación los da) |
| Criterio de parada | Visibilidad suficiente, ganancia marginal baja, número máximo de vistas | Definir con datos: en el corpus, la ventaja sobre vistas al azar se concentra en las primeras vistas |

### 6.3 Cinemática inversa

| Método | Ventajas | Nota para el Piper |
|---|---|---|
| Numérica con optimización (CasADi + IPOPT, la de la teleop) | Flexible, admite costos | Error de 9,4 mm / 8,5° por la regularización hacia cero; regularizar hacia `q_actual` y verificar con FK |
| **★ Analítica (desacople de Pieper)** | Exacta, todas las soluciones, microsegundos | Posible porque la muñeca es esférica; ideal para evaluar muchas vistas candidatas |
| KDL, **TRAC-IK** | Plugins estándar de MoveIt | TRAC-IK es más robusto que KDL con límites articulares |
| pick_ik, bio_ik | IK con objetivos parciales (solo dirección de la cámara) | Útil para "mirar hacia" sin fijar el giro alrededor del eje óptico |
| IK de la cámara | Resolver para el marco de la D405 y no del TCP | Ya se hace en la demo; ahorra una conversión y evita el error del TCP |

### 6.4 Planificación de movimiento (MoveIt 2)

| Pieza | Opción | Para qué |
|---|---|---|
| Configuración | SRDF, límites, controladores y `sensors_3d.yaml` (plantilla en Milo) | Paso 2 de la hoja de ruta |
| Planificadores | **★ OMPL RRTConnect**, Pilz (trayectorias lineales y PTP), CHOMP / STOMP (suaves) | RRTConnect para ir a cada vista; Pilz para el acercamiento final lineal al corte |
| Choques con el dosel | OctoMap desde la D405 como mundo de colisiones | Las ramas son el límite principal: en el muro frutal, 5 a 11 de 20 vistas chocan |
| Tareas compuestas | MoveIt Task Constructor | Mirar → acercarse → cortar → retirar, con alternativas |
| Seguimiento en vivo | MoveIt Servo | Corrección visual fina al acercarse (servoing) |
| Control en contacto | Modo MIT con kp y kd bajos | Atravesar hojas sin dañarlas; requiere la prueba en real |

### 6.5 Control y teleoperación

| Tema | Algoritmos | Nota |
|---|---|---|
| Control de posición | Trayectorias interpoladas (`JointTrajectoryController`) | El modo actual de la teleop |
| Impedancia por articulación | MIT del Piper con compensación de gravedad `T_FF` | Calculado y emulado; falta la prueba física |
| Impedancia cartesiana | Jacobiano transpuesto sobre el MIT | Para contacto con el dosel |
| Servo visual | IBVS / PBVS sobre la fruta detectada | Corrección final antes de cortar |
| Teleoperación asistida | Mezclar el comando del operador con la vista sugerida por el NBV | Nivel intermedio de autonomía; en el corpus el humano casi no aparece en agricultura |

### 6.6 Aprendizaje desde demostraciones

| Método | Encaje |
|---|---|
| **★ ACT** (Action Chunking with Transformers) y **Diffusion Policy** | Los dos están en LeRobot; `data_tools` ya convierte a ese formato |
| Modelos de visión–lenguaje–acción (π0, SmolVLA y similares) | Ajuste fino con demostraciones del Pika; necesita GPU para entrenar |
| Políticas que también mueven la cámara | Aprender a la vez dónde mirar y qué hacer (en el corpus, casi sin explorar en agricultura) |

### 6.7 Calibración y localización

| Tema | Método |
|---|---|
| Cámara ↔ pinza | Hoy viene del plano de AgileX; verificar con calibración mano–ojo (Tsai–Lenz o Park–Martin, `easy_handeye2`) |
| Intrínsecos | De fábrica en la D405; la fisheye con modelo equidistante o Kannala–Brandt (OpenCV) |
| Vive ↔ base del brazo | Transformación fija estimada con puntos tocados por el TCP |
| Base estaciones | `scripts/calibration.bash`, solo si se mueven las estaciones |

## 7. Limitaciones

**Del hardware:**
- **Alcance y muñeca:** 0,81 m desde el hombro y J5 ±70° limitan las vistas desde abajo y muy laterales; en las escenas, solo 2 a 7 de 20 vistas candidatas son alcanzables.
- **Garras por delante de la cámara:** las puntas quedan 15 cm por delante de la D405; con vistas a 22 cm de la fruta las garras se meten entre las ramas, y hay que mirar desde ~30 cm.
- **Rango de la D405:** 7–50 cm; no sirve para ver el árbol completo, sí para la fruta.
- **Carga:** 1,5 kg con un gripper de 617 g; queda ~0,9 kg útil.
- **Tracker Vive:** necesita estaciones bien ubicadas y línea de vista; en campo abierto, sol y viento complican.
- **Seguridad:** no hay parada de emergencia todavía.

**Del software:**
- La captura teleop de `data_tools` necesita un arreglo local (topics de PikaAnyArm V2).
- La IK de la teleop está ofuscada (PyArmor) y tiene un TCP distinto del modelo (0,19 m contra 0,180 m).
- `pika_locator` y `libsurvive` son binarios sin fuente.

**De la simulación:**
- Gazebo Classic: sin cámara de segmentación y sin física de hojas (el brazo las atraviesa).
- La visibilidad es geométrica: no modela el ruido de la D405 ni el desenfoque de la fisheye real.
- Solo se revisan choques de la cámara y de las garras, no del brazo completo (falta MoveIt).
- La masa del gripper es la publicada (617 g), no medida.

## 8. Innovaciones y estado del arte

Según la revisión sistemática de ActivePerceptionArms (318 estudios, 2015–2026; 64 agrícolas):
- **Del laboratorio al campo:** solo 20 estudios actúan en campo y solo 4 comparan planificadores de vistas allí.
- **La ganancia está en las primeras vistas:** frente a vistas al azar, la ventaja aparece pronto y se achica hacia las diez vistas.
- **El brazo es parte del problema:** la vista más informativa no siempre es ejecutable; pocos estudios agrícolas consideran la alcanzabilidad o el costo articular.
- **El humano casi no aparece en agricultura:** 4 de 64 estudios agrícolas lo incluyen en el lazo de percepción, aunque el operador está en el campo.
- **Tendencias recientes:** reconstrucción con Gaussian Splatting para elegir vistas, políticas de visión–acción que mueven la cámara mientras actúan, benchmarks de visión activa en manipulación, y el uso de modelos de lenguaje y visión para dar el conocimiento de la tarea.

**Dónde puede aportar este proyecto:**
1. **NBV consciente de la ejecución** en un brazo de bajo costo, con la alcanzabilidad y los choques con ramas dentro del puntaje, ya visible en la simulación.
2. **Visibilidad validada contra la imagen** (error medio de 2,6 puntos) y escenarios reproducibles con oclusión, densidad y luz controladas: base para un benchmark.
3. **El humano en el lazo:** el mismo Pika Sense sirve para teleoperar, corregir la vista elegida y grabar demostraciones de dónde mira un experto.
4. **Plataforma remolcable independiente del vehículo**, para pasar al campo.

## 9. Caminos posibles

| # | Camino | Qué da | Depende de |
|---|---|---|---|
| 1 | **MoveIt 2 para Piper + Pika** con OctoMap desde la D405 | Choques del brazo completo y trayectorias a cada vista | Plantilla de Milo |
| 2 | **Planner de NBV** con las dos políticas (volumétrica y de visibilidad) y criterio de parada | El aporte central del proyecto | 1, y el detector para la política B en real |
| 3 | **Detector de fruta** entrenado con la galería simulada y datos reales | Visibilidad medida sin verdad del terreno | Imágenes reales del huerto |
| 4 | **Experimentos por nivel de oclusión** (25–100 %) contra vistas fijas | Resultados comparables con el corpus | 2 |
| 5 | **Pruebas en el robot real:** MIT, teleop con grabación, verificación de la cámara | Validación del modelo | Montaje, parada de emergencia |
| 6 | **Demostraciones humanas** con el Sense y políticas ACT / Diffusion | Línea base aprendida y estudio del humano en el lazo | 5 |
| 7 | **Milo como segundo robot** con los mismos nodos | Mostrar que el método no depende del brazo | 2 |
| 8 | **Prueba en campo** sobre la plataforma remolcable | Evidencia en condiciones reales (escasa en el corpus) | 2, 5 |

Hoja de ruta detallada y contrato por robot: [percepcion_activa/README.md](percepcion_activa/README.md).

## 10. Documentación relacionada

| Tema | Documento |
|---|---|
| Uso diario y flujos | [manuales/Manual.md](manuales/Manual.md) |
| Hardware y cableado | [arquitectura/README.md](arquitectura/README.md), [energia/Consumo_Energia.md](energia/Consumo_Energia.md) |
| Modelo del robot | [PIPER_PIKA.md](../src/pika_description/docs/PIPER_PIKA.md), [archivos de AgileX](../src/pika_description/agilex/README.md) |
| Simulación | [src/pika_sim/README.md](../src/pika_sim/README.md) |
| Percepción activa | [plan](percepcion_activa/README.md), [lazos y NBV](percepcion_activa/lazos_cinematica_nbv.md), [escenarios de simulación](percepcion_activa/escenarios_simulacion.md), [recursos públicos](percepcion_activa/recursos_publicos.md), [frutas candidatas](percepcion_activa/frutas_candidatas.md) |
