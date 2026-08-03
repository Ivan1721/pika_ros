# Guía de configuración — Pika + Piper Agilex

Ubuntu 22.04 · ROS 2 Humble · x86_64

---

## 1. Instalar ROS 2 Humble

```bash
cd ~ && wget http://fishros.com/install -O fishros && . fishros
```

Seguir las instrucciones en pantalla y seleccionar ROS 2 Humble.

---

## 2. Clonar el repositorio

```bash
git clone https://github.com/agilexrobotics/pika_ros.git
cd pika_ros && git checkout ros2
git submodule update --init --recursive
cd ~/pika_ros/src/PikaAnyArm/agx_arm
git clone https://github.com/agilexrobotics/agx_arm_ros.git
cd agx_arm_ros/src/agx_arm_description
git clone -b flattened https://github.com/agilexrobotics/agx_arm_urdf.git
```

---

## 3. Instalar dependencias

```bash
sudo apt-get update && sudo apt install \
  libjsoncpp-dev libpcap-dev python3-pcl build-essential zlib1g-dev \
  libx11-dev libusb-1.0-0-dev freeglut3-dev liblapacke-dev \
  libopenblas-dev libatlas-base-dev cmake git libssl-dev pkg-config \
  libgtk-3-dev libglfw3-dev libgl1-mesa-dev libglu1-mesa-dev g++ \
  python3-pip libopenvr-dev ros-humble-diagnostic-updater cutecom

sudo add-apt-repository ppa:ubuntu-toolchain-r/test -y
sudo apt update && sudo apt install -y gcc-13 g++-13 libstdc++6 libcurl4-openssl-dev

git clone https://github.com/agilexrobotics/pyAgxArm.git
cd pyAgxArm && pip3 install .

pip3 install opencv-python
pip3 install "numpy<2"
```

---

## 4. Configurar reglas USB (Vive tracker)

```bash
cd ~/pika_ros
sudo cp scripts/81-vive.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger
```

Desconectar y reconectar el receptor inalámbrico después de este paso.

---

## 5. Instalar RealSense SDK

Extraer `source/librealsense-2.55.1.zip` y `source/curl-7.75.0.zip` **fuera** del directorio `pika_ros` (por ejemplo en `~`).

Editar `librealsense-2.55.1/CMake/external_libcurl.cmake` y reemplazar la ruta:
```
/home/agilex/pika_ros/source/curl-7.75.0
```
por la ruta real a `curl-7.75.0` en tu sistema.

```bash
cd ~/librealsense-2.55.1
mkdir build && cd build && cmake .. && sudo make install
```

Verificar instalación:
```bash
realsense-viewer
```

---

## 6. Instalar archivos precompilados

Extraer `source/install.zip` y colocar la carpeta `install/` dentro de `~/pika_ros`:

```bash
chmod 777 -R ~/pika_ros/install/
```

Atajo equivalente (definido en `.bashrc`, correr cuando haga falta — no es automático): `pika_fix_install_perms`

---

## 7. Variables de entorno

```bash
echo 'source ~/pika_ros/install/setup.bash' >> ~/.bashrc
source ~/.bashrc
```

Agregar los códigos de serie de los trackers Vive:

```bash
echo 'export pika_L_code=LHR-XXXXXXXX' >> ~/.bashrc
echo 'export pika_R_code=LHR-XXXXXXXX' >> ~/.bashrc
source ~/.bashrc
```

---

## 8. Compilar el workspace

```bash
cd ~/pika_ros
colcon build --packages-select data_msgs
source install/setup.bash
colcon build
source install/setup.bash
```

---

## 9. Vincular dispositivos USB (primera vez)

Conectar un dispositivo Pika a la vez y ejecutar:

```bash
cd ~/pika_ros/scripts/
python3 setup_device.py
```

### Opción A: Sensor Pika + un Gripper Pika (predeterminado)

Seleccionar opción **3**. El script genera `setup_sensor_gripper.bash` y `start_sensor_gripper.bash`:

| Dispositivo | Puerto |
|---|---|
| Sensor serial | `/dev/ttyUSB50` |
| Gripper serial | `/dev/ttyUSB60` |
| Fisheye sensor | `/dev/video50` |
| Fisheye gripper | `/dev/video60` |

### Opción B: Dos Sensores Pika (para captura bilateral)

Seleccionar opción **1**. El script genera `setup_multi_sensor.bash` y `start_multi_sensor.bash`:

| Dispositivo | Puerto |
|---|---|
| Sensor izquierdo serial | `/dev/ttyUSB50` |
| Sensor derecho serial | `/dev/ttyUSB51` |
| Fisheye sensor izquierdo | `/dev/video50` |
| Fisheye sensor derecho | `/dev/video51` |

### Opción C: Dos Grippers Pika (para dos brazos Piper)

Seleccionar opción **2**. El script genera `setup_multi_gripper.bash` y `start_multi_gripper.bash`:

| Dispositivo | Puerto |
|---|---|
| Gripper izquierdo serial | `/dev/ttyUSB60` |
| Gripper derecho serial | `/dev/ttyUSB61` |
| Fisheye gripper izquierdo | `/dev/video60` |
| Fisheye gripper derecho | `/dev/video61` |

### Opción D: Dos Sensores + Dos Grippers (captura + ejecución bilateral)

**Ejecutar en dos pasos:**

**Paso 1:** Ejecutar `setup_device.py` y seleccionar opción **1** (dos sensores)
```bash
cd ~/pika_ros/scripts/
python3 setup_device.py
# Seleccionar opción 1
# Conectar sensor izquierdo → localizar fisheye → desconectar
# Conectar sensor derecho → localizar fisheye → desconectar/reconectar ambos
```

**Paso 2:** Ejecutar `setup_device.py` nuevamente y seleccionar opción **2** (dos grippers)
```bash
python3 setup_device.py
# Seleccionar opción 2
# Conectar gripper izquierdo → localizar fisheye → desconectar
# Conectar gripper derecho → localizar fisheye → desconectar/reconectar ambos
```

**Resultado final:**
| Dispositivo | Puerto |
|---|---|
| Sensor izquierdo serial | `/dev/ttyUSB50` |
| Sensor derecho serial | `/dev/ttyUSB51` |
| Gripper izquierdo serial | `/dev/ttyUSB60` |
| Gripper derecho serial | `/dev/ttyUSB61` |
| Fisheye sensor izquierdo | `/dev/video50` |
| Fisheye sensor derecho | `/dev/video51` |
| Fisheye gripper izquierdo | `/dev/video60` |
| Fisheye gripper derecho | `/dev/video61` |

---

> **Orden recomendado de preparación (pasos 6, 9, 10 y 11) y por qué:**
> 1. **Permisos de `install/`** (paso 6) primero — todo lo demás (survive-cli, launch files) vive ahí; sin esto, hasta la calibración falla por "Permission denied".
> 2. **Permisos de `/dev/*` → calibrar → recién después instalar la regla udev permanente** (paso 10.3) — el `chmod 777 -R /dev/*` es un desbloqueo bruto e inmediato para poder calibrar ya, incluso si la regla udev del tracker aún no existe. La regla `81-vive.rules` (paso 4) se instala/recarga *después*, para que los permisos persistan tras reinicios sin tener que repetir el chmod amplio.
> 3. **CAN del brazo** (paso 11) y **vincular dispositivos USB** (paso 9) son independientes entre sí y del resto — se pueden hacer en cualquier momento antes de lanzar teleoperación, pero conviene dejarlos al final porque son específicos del hardware que vayas a usar (cuántos brazos, qué opción de `setup_device.py`).

## 10. Despliegue y calibración de Pika Station

### 10.1 Colocación física de las base stations

- Instalar cada base station a **90° de ángulo de visión** entre sí (pared, trípode, o superficie estable — evitar vibraciones).
- Altura mínima: **0.5 m**. Idealmente por encima de la cabeza (>2 m) con un ángulo de inclinación de **25°–35°** hacia el área de trabajo.
- Distancia mínima entre el Pika Sense y cada base station: **0.5 m**. Distancia máxima para posicionamiento preciso: **7 m**.
- Cobertura según número de base stations:

  | Base stations | Área mínima | Área máxima |
  |---|---|---|
  | 2 | 2×1.5 m | 5×5 m |
  | 4 | — | 10×10 m (máximo soportado por escena) |

- Evitar luz solar directa, superficies de vidrio/acrílico (causan drift), y no bloquear el panel frontal.
- Retirar la película protectora del panel frontal antes de encender.

### 10.2 Configurar canal (primer uso)

Con un objeto puntiagudo, presionar el botón trasero de cada base station (posición 9). Cada pulsación sube el canal en 1 (rango 0–15); el LED verde parpadea una vez por pulsación. **Todas las base stations en la misma escena deben tener canales distintos.**

Verificar que el LED de cada base station quede en **verde fijo** (operación normal).

### 10.3 Calibración

```bash
sudo chmod 777 -R /dev/*
cd ~/pika_ros/install/pika_locator/lib && ./survive-cli --force-calibrate
```

Atajo equivalente para el primer comando (definido en `.bashrc`): `pika_fix_dev_perms`

Usar `--force-calibrate` en estos casos:
- Primera vez en este equipo.
- Se agregaron o quitaron base stations.
- Se cambió el canal de alguna base station.

Usar sin la bandera (`./survive-cli`) si solo hubo drift de posición o se movieron las base stations sin cambiar canal.

**Antes de calibrar:**
- Encender la etiqueta de posicionamiento (tracker) y dejarla **quieta**, dentro del campo de visión de las base stations.
- Confirmar que el LED de la etiqueta y el de las base stations estén en verde.
- Sin luz solar directa ni objetos reflectantes (vidrio/acrílico) en el área.

**Verificar éxito:** la terminal imprime el error de la etiqueta en metros. Cuando el valor baja de **0.005**, cerrar con Ctrl+C (los mensajes en rojo después de cerrar son normales e ignorables).

### 10.4 Verificación visual en RViz

Tras lanzar el Sense (`start_single_sensor.bash` / `start_multi_sensor.bash` / `pika_double_locator.launch.py`), se abre una ventana de RViz con el TF del tracker. Presionar **Ctrl+Z** para centrar coordenadas, mover el Pika Sense y confirmar que el TF sigue el movimiento sin saltos. Si hay drift repentino, repetir la calibración (10.3, sin `--force-calibrate`).

---

## 11. Configurar CAN bus (brazo Piper)

### Para un solo brazo:

```bash
cd ~/pika_ros/src/PikaAnyArm/piper/piper_ros
bash can_activate.sh can0 1000000
```

> **Importante:** para un solo brazo, la interfaz debe llamarse **`can0`** (no `can_left`) — `start_single_piper.launch.py` y `teleop_rand_single_piper.launch.py` esperan ese nombre por defecto (`can_port:=can0`) y ninguno de los dos lo sobreescribe. El tercer argumento (dirección USB) es opcional: `can_activate.sh` lo pide solo si detecta más de una interfaz CAN en el sistema; con un solo adaptador conectado, dos argumentos bastan.

### Para dos brazos (recomendado):

```bash
bash ~/pika_ros/src/PikaAnyArm/piper/piper_ros/can_config.sh
```

El script `can_config.sh` configura automáticamente ambas interfaces a 1 Mbps:

| Interfaz | Ruta USB | Descripción |
|---|---|---|
| `can_left` | `3-1.1.3:1.0` | Brazo izquierdo |
| `can_right` | `1-1.1.3:1.0` | Brazo derecho |

> **Importante:** Si la topología USB cambia (hub diferente), editar `can_config.sh` con las rutas correctas antes de ejecutarlo. Ejecutar:
> ```bash
> lsusb -t  # para ver la topología actual
> ```

---

## Flujo A — Teleoperación Pika + Un Piper (1 brazo + 1 gripper)

**Terminal 1** (sensores Pika):
```bash
conda deactivate
source ~/pika_ros/install/setup.bash
cd ~/pika_ros/scripts && bash start_sensor_gripper.bash
```

**Terminal 2** (nodos de teleoperación):
```bash
source ~/pika_ros/install/setup.bash
conda activate pika
ros2 launch pika_remote_piper teleop_rand_single_piper.launch.py
```

---

## Flujo A+ — Teleoperación Pika + Dos Pipers (2 brazos + 2 grippers)

Requiere **2 Pika Sense** (uno por mano, con tracker Vive) + **2 Pika Gripper** (montados en los brazos como efector final) — son dispositivos físicos distintos, no confundir uno con otro.

**Requisitos previos:**
- Ejecutar `setup_device.py` con opción **1** (dos sensores Pika) → genera `start_multi_sensor.bash`
- Ejecutar `setup_device.py` con opción **2** (dos grippers Pika) → genera `start_multi_gripper.bash`
- Configurar CAN bus: `bash ~/pika_ros/src/PikaAnyArm/piper/piper_ros/can_config.sh`
- Base stations calibradas (sección 10)

**Terminal 1** (Pika Sense — lectura de pinza + tracker; **incluye el localizador**, publica `/pika_pose_l` y `/pika_pose_r`, abre RViz):
```bash
conda deactivate
source ~/pika_ros/install/setup.bash
cd ~/pika_ros/scripts && bash start_multi_sensor.bash
```

**Terminal 2** (Pika Gripper — actuadores montados en los brazos):
```bash
conda deactivate
source ~/pika_ros/install/setup.bash
cd ~/pika_ros/scripts && bash start_multi_gripper.bash
```

> **No** lanzar `pika_locator/pika_double_locator.launch.py` por separado — `open_multi_sensor.launch.py` (usado por `start_multi_sensor.bash`) ya lo incluye. Correrlo aparte crea una segunda instancia compitiendo por el mismo dongle Vive.

**Terminal 3** (nodos de teleoperación — dos brazos):
```bash
source ~/pika_ros/install/setup.bash
conda activate pika
ros2 launch pika_remote_piper teleop_rand_multi_piper.launch.py
```

> Si solo lanzas la Terminal 2 (grippers) sin la Terminal 1 (sensores), nada escucha el pellizco/doble-click de los Pika Sense: el LED del Sense puede cambiar de color por su propio firmware local, pero `/teleop_trigger_l`/`_r` nunca se llama y la teleoperación no arranca.

Este flujo lanza:
- Dos nodos Piper (izquierdo + derecho) via CAN
- FK + IK para ambos brazos
- Teleop bilateral

---

## Flujo B — Solo control del brazo Piper (con RViz)

### B.1 — Un solo brazo Piper

**Terminal 1**:
```bash
conda deactivate
source ~/pika_ros/install/setup.bash
ros2 launch piper start_single_piper_rviz.launch.py
```

### B.2 — Dos brazos Piper

**Terminal 1** (configurar CAN bus):
```bash
bash ~/pika_ros/src/PikaAnyArm/piper/piper_ros/can_config.sh
```

**Terminal 2** (visualizar dos brazos):
```bash
conda deactivate
source ~/pika_ros/install/setup.bash
ros2 launch piper start_double_piper.launch.py
```

En RViz se visualizarán ambos brazos (izquierdo y derecho).

---

## Flujo C — Captura de cámaras y joints del robot

**Terminal 1** (sensores Pika):
```bash
conda deactivate
source ~/pika_ros/install/setup.bash
cd ~/pika_ros/scripts && bash start_sensor_gripper.bash
```

**Terminal 2** (brazo Piper + captura):
```bash
chmod 777 -R ~/pika_ros/install
cd ~/pika_ros/src/PikaAnyArm/piper/piper_ros
bash can_activate.sh can0 1000000

conda deactivate
source ~/pika_ros/install/setup.bash
ros2 launch piper start_single_piper_rviz.launch.py
```

---

## Flujo D — Simulación Gazebo del brazo Piper

Workspace independiente en `~/piper_ros`. No requiere hardware CAN ni Pika.

**Compilar (primera vez o tras cambios):**
```bash
cd ~/piper_ros
colcon build --packages-select piper_gazebo
source install/setup.bash
```

**Lanzar la simulación:**
```bash
source ~/piper_ros/install/setup.bash
ros2 launch piper_gazebo piper_no_gripper_gazebo_sliders.launch.py
```

Se abrirán tres ventanas:
- **Gazebo** — simulación física del brazo
- **RViz** — visualización del modelo
- **joint_state_publisher_gui** — sliders para mover cada articulación (con botones **Randomize** y **Center**)

Mover un slider mueve el brazo en Gazebo y en RViz simultáneamente.

> **Nota técnica:** el nodo `gui_to_trajectory` hace de puente entre el GUI y el controlador `arm_controller`. Usa timestamp cero en la trayectoria para que el controlador la ejecute inmediatamente sin depender del reloj de simulación.

---

## Flujo E — Pipeline de datos (captura → HDF5 → LeRobot)

Tipos de configuración disponibles: `single_pika` | `multi_pika` | `single_pika_teleop` | `multi_pika_teleop` | `aloha` | `lift`

**1. Capturar episodio:**
```bash
source ~/pika_ros/install/setup.bash
ros2 launch data_tools run_data_capture.launch.py \
  type:=single_pika \
  datasetDir:=/ruta/datos \
  episodeIndex:=0
# Presionar ENTER para detener; esperar "Done"
```

**2. Sincronizar (Python, recomendado):**
```bash
# episodeName = nombre de la carpeta (p.ej. "episode0"); omitir para procesar todos
python3 ~/pika_ros/src/data_tools/scripts/data_sync.py \
  --type single_pika \
  --datasetDir /ruta/datos \
  --episodeName episode0
```

**3. Convertir a HDF5:**
```bash
cd ~/pika_ros/src/data_tools/scripts/
python3 data_to_hdf5.py \
  --type single_pika \
  --datasetDir /ruta/datos \
  --episodeName episode0 \
  --useCameraPointCloud ""
# Omitir --episodeName para procesar todos los episodios del dataset
```

**4. Convertir a formato LeRobot:**
```bash
cd ~/pika_ros/src/data_tools/scripts/
python3 hdf5_to_lerobot.py --datasetDir /ruta/hdf5
```

**5. Publicar datos grabados:**
```bash
ros2 launch data_tools run_data_publish.launch.py \
  type:=single_pika \
  datasetDir:=/ruta/datos \
  episodeIndex:=0
```

---

## Tabla Rápida — Configuración por escenario

| Escenario | Setup | CAN | Comando Launch | Notas |
|---|---|---|---|---|
| **1 sensor + 1 gripper** | Opción 3 | `can_left` | `teleop_rand_single_piper.launch.py` | Básico |
| **2 sensores** | Opción 1 | — | `start_multi_sensor.bash` | Captura bilateral |
| **2 grippers** | Opción 2 | `can_config.sh` | `teleop_rand_multi_piper.launch.py` | 2 brazos Piper |
| **2 sensores + 2 grippers** | Opción 1 + 2 | `can_config.sh` | `teleop_rand_multi_piper.launch.py` | Captura + ejecución |
| **2 brazos (solo RViz)** | — | `can_config.sh` | `start_double_piper.launch.py` | Visualización |

**Checklist para 2 sensores + 2 grippers:**
- [ ] Ejecutar `setup_device.py` → Opción 1 (dos sensores)
- [ ] Ejecutar `setup_device.py` → Opción 2 (dos grippers)
- [ ] Ejecutar `bash ~/pika_ros/src/PikaAnyArm/piper/piper_ros/can_config.sh`
- [ ] Terminal 1: `cd ~/pika_ros/scripts && bash start_multi_sensor.bash` (incluye el localizador — no lanzar `pika_locator` aparte)
- [ ] Terminal 2: `cd ~/pika_ros/scripts && bash start_multi_gripper.bash`
- [ ] Terminal 3 (si se usan brazos): `ros2 launch pika_remote_piper teleop_rand_multi_piper.launch.py`

---

## Problemas frecuentes

**Error `driver_openvr.so` no encontrado:**
```bash
sudo apt install libopenvr-dev
```

**Calibración congela la terminal:**
```bash
rm ~/.config/libsurvive/config.json
```
Volver a ejecutar la calibración.

**Error de permisos en `install/`:**
```bash
chmod 777 -R ~/pika_ros/install/
```

**Error `GLIBCXX_3.4.29` con CasADi en Conda:**
```bash
export LD_PRELOAD=~/miniconda3/envs/<nombre_env>/lib/libstdc++.so.6
```

### Problemas específicos de dos brazos

**Las interfaces CAN no aparecen (`can_left`, `can_right`):**
```bash
# Verificar que los adaptadores estén reconocidos
lsusb -t

# Reintentar configuración manualmente
sudo bash ~/pika_ros/src/PikaAnyArm/piper/piper_ros/can_config.sh

# Verificar estado de las interfaces
ip link show | grep can
```

**Solo un brazo responde en teleoperación:**
- Verificar que `can_config.sh` activó ambas interfaces: `ip link show`
- Verificar logs en Terminal 2: buscar errores en `piper_left_ctrl_node` o `piper_right_ctrl_node`
- Reiniciar los nodos de CAN: desconectar y reconectar los adaptadores USB

**Los grippers Pika no comunican correctamente:**
```bash
# Verificar que ambos puertos seriales están presentes
ls -la /dev/ttyUSB60 /dev/ttyUSB61

# Dar permisos si es necesario
sudo chmod 666 /dev/ttyUSB60 /dev/ttyUSB61
```
