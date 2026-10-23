---
name: sincronizar-upstream-agilex
description: Traer cambios de AgileX (agilexrobotics/pika_ros, rama ros2, y sus submódulos) al fork pika-custom-ros2 con la política de conflictos acordada, recompilar en orden y revisar las regresiones conocidas. Usar cuando se pida sincronizar, actualizar o mergear desde upstream/AgileX, o revisar qué cambió AgileX.
---

# Sincronizar el fork con AgileX

El fork `Ivan1721/pika_ros` (rama `pika-custom-ros2`) sigue a `agilexrobotics/pika_ros` **rama `ros2`**.
`upstream/master` es la versión ROS 1: se ignora siempre.

## 1. Ver qué trae AgileX antes de mergear

```bash
cd ~/pika_ros
git status --short                      # el árbol debe estar limpio
git fetch upstream
git log --oneline pika-custom-ros2..upstream/ros2
git diff --stat pika-custom-ros2...upstream/ros2
```

Resume al usuario qué cambió (por archivo o paquete) y **espera su visto bueno antes de mergear**.

## 2. Merge con la política acordada (2026-10-19)

```bash
git merge --no-ff upstream/ros2
```

Si hay conflictos, se resuelven así:

| Ruta | Se queda | Por qué |
|---|---|---|
| `README.md` | **nuestro** | versión trilingüe EN/ZH/ES |
| `README_CN.md` de upstream | se descarta | ya está dentro del README trilingüe |
| `scripts/setup_device.py` | **nuestro** | en español, 3 opciones, arreglo del emparejamiento USB; las opciones 4/5 de upstream son para un casco que no tenemos |
| `src/PikaAnyArm` (puntero del submódulo) | **nuestro** | fork `Ivan1721/PikaAnyArm`, ver paso 4 |
| `src/data_tools`, `src/data_msgs` | **de AgileX** | submódulos de AgileX sin cambios propios |
| `source/install.zip` | **de AgileX** | binarios del localizador Vive |

Cualquier otro conflicto: muéstraselo al usuario, no lo resuelvas por tu cuenta.

Después:

```bash
git submodule update --init --recursive
```

## 3. Recompilar en orden (fuera de conda)

```bash
conda deactivate
source /opt/ros/humble/setup.bash
cd ~/pika_ros
colcon build --packages-select data_msgs
source install/setup.bash
colcon build --packages-select data_tools sensor_tools
source install/setup.bash
chmod 777 -R ~/pika_ros/install/
```

**Nunca borres `install/`**: `pika_locator` y `libsurvive` solo existen como binarios ahí. Si se perdieron, se
recuperan de `source/install.zip`.

## 4. PikaAnyArm: no se mergea la V2

AgileX reestructuró PikaAnyArm en la V2: movió todo a `agx_arm/pika_remote_agx_arm/` y borró `piper/`. Los launch,
los flujos A/A+ del Manual y el `CLAUDE.md` dependen de `piper/`, así que el fork **no se sincroniza en bloque**.

```bash
cd ~/pika_ros/src/PikaAnyArm
git fetch upstream
git log --oneline pika-custom-ros2..upstream/ros2   # revisar uno por uno
```

Solo se portan a mano los arreglos que apliquen a `piper/` (a octubre de 2026, ninguno aplicaba). Antes de portar,
pregunta al usuario.

## 5. Revisar las regresiones conocidas

- **Topics de la V2 en `data_tools`:** desde el commit `b3704f4` de upstream, `config/single_pika_teleop_data_params.yaml`
  y `multi_pika_teleop_data_params.yaml` usan topics de la V2 (`/control/joint_states`, `/feedback/joint_states`,
  `/ik_fk_pose`, `/feedback/tcp_pose`, `/left_arm/...`). Nuestro fork publica `/joint_states_gripper[_l|_r]`,
  `/joint_states_single_gripper[_l|_r]`, `/piper_IK[_l|_r]/receive_end_pose_orient` y
  `/piper_FK[_l|_r]/urdf_end_pose_orient`. Si el merge vuelve a tocar esas configs, avisa: la captura con teleop no
  va a encontrar sus topics.
- **LeRobot:** `hdf5_to_lerobot.py` importa `lerobot.datasets` (≥ 0.2). Si cambió, confirma con el usuario qué
  versión usa el equipo.
- Revisa `git diff` en `src/sensor_tools` y en `scripts/`: los scripts de arranque de la raíz son específicos de
  esta máquina (seriales de RealSense, `/dev/ttyUSB5x`) y no deben pisarse.

## 6. Cerrar

1. Commit del merge en español, describiendo qué se tomó de AgileX y qué se mantuvo.
2. `git push origin pika-custom-ros2`, solo con el visto bueno del usuario.
3. Actualizar el puntero en Next-Best-View con la skill `actualizar-puntero-nbv`.

**No subas a este repo** (es público) nada de la investigación ni material entregado por AgileX: eso va en
Next-Best-View.
