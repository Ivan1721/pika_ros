---
name: actualizar-puntero-nbv
description: Después de commitear y pushear cambios en ~/pika_ros (drivers, teleop, scripts, data_tools), mover el submódulo deps/pika_ros de Next-Best-View al nuevo commit y verificar que el overlay sigue compilando. Usar cuando se termine un cambio en pika_ros, cuando se pregunte si NBV está al día con el fork, o antes de reproducir resultados en otra máquina.
---

# Actualizar el puntero `deps/pika_ros` en Next-Best-View

Next-Best-View (`~/nbv_ws/src/Next-Best-View`, privado, rama `main`) fija este fork en el submódulo `deps/pika_ros`,
que tiene `COLCON_IGNORE`: **no se compila**. Lo que se compila es `~/pika_ros`. El puntero solo deja anotado qué
versión del fork corresponde a cada commit de NBV, y nada obliga a que coincidan. Por eso hay que moverlo a mano.

## 1. Comprobar que hay algo que actualizar

```bash
FORK=$(git -C ~/pika_ros rev-parse HEAD)
PIN=$(git -C ~/nbv_ws/src/Next-Best-View ls-tree HEAD deps/pika_ros | awk '{print $3}')
echo "fork $FORK"; echo "pin  $PIN"
git -C ~/pika_ros status --short
git -C ~/pika_ros log --oneline -1 origin/pika-custom-ros2
```

- Si `FORK == PIN`, no hay nada que hacer.
- Si `~/pika_ros` tiene cambios sin commitear, o su HEAD no está en `origin/pika-custom-ros2`, **para**: el puntero
  debe apuntar a un commit publicado. Pregunta al usuario si commitear y pushear primero.

## 2. Mover el puntero

```bash
cd ~/nbv_ws/src/Next-Best-View
git -C deps/pika_ros fetch origin
git -C deps/pika_ros checkout "$FORK"
git -C deps/pika_ros submodule update --init --recursive
git add deps/pika_ros
git diff --cached --submodule=log deps/pika_ros
```

Muestra al usuario la lista de commits que entran.

## 3. Verificar el overlay

Fuera de conda:

```bash
conda deactivate
source ~/pika_ros/install/setup.bash
cd ~/nbv_ws && colcon build
source ~/nbv_ws/install/setup.bash
```

Si el cambio tocó la teleop o el puente de simulación, propone además la prueba corta del Flujo D+ (README de
`pika_sim`): `ros2 launch pika_sim sim_piper_single.launch.py` y, en otra terminal con `conda activate pika`,
`ros2 launch pika_remote_piper teleop_rand_single_piper.launch.py sim:=true`.

## 4. Commit

Mensaje en español, del estilo `deps/pika_ros: <qué cambió en el fork> (<hash corto>)`, por ejemplo
`deps/pika_ros: fork limpio tras la migracion (c5e253f)`. Haz push a `main` solo con el visto bueno del usuario.

**Nunca recompiles `pika_sim` ni `pika_description` dentro de `~/pika_ros`**: viven solo en NBV y se duplicarían
los paquetes.
