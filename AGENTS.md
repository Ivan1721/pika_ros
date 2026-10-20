# Repository Guidelines

## Project Structure & Module Organization

This is a ROS 2 Humble workspace for Pika data collection, sensing, teleoperation and simulation. It is a fork of `agilexrobotics/pika_ros` (branch `ros2`); the working branch is `pika-custom-ros2`.

Primary source packages live under `src/`:

- `sensor_tools`: camera/gripper/localization launch files and scripts.
- `data_msgs` and `data_tools` (submodules of AgileX): custom messages, and dataset capture/sync/publish/conversion.
- `realsense-ros`: the RealSense driver stack.
- `PikaAnyArm` (submodule, fork `Ivan1721/PikaAnyArm`, branch `pika-custom-ros2`): Piper teleoperation. `pika_remote_piper` and the Piper packages `piper`, `piper_msgs`, `piper_description` are nested under `src/PikaAnyArm/piper/`.
- `pika_description`: URDF/xacro of the Pika gripper and of the Piper + Pika arm.
- `pika_sim`: Gazebo Classic simulation of the Piper + Pika gripper that plugs into the real teleoperation chain.

Root `scripts/` holds device setup and the start scripts generated for this machine; `src/sensor_tools/scripts/` holds the upstream templates. `img/` and `src/PikaAnyArm/docs_img/` contain documentation assets. `docs/` holds project documentation, indexed in `docs/README.md`; the operator guide is `docs/manuales/Manual.md` (Spanish), organized in workflows A/A+/B/C/D/D+/E.

Treat `install/` and `build/` as generated output, with one exception: `pika_locator` and `libsurvive` (Vive localization) exist only as precompiled binaries in `install/`, extracted from `source/install.zip`. Do not delete `install/`; `colcon build` cannot regenerate them.

## Build, Test, and Development Commands

```bash
source /opt/ros/humble/setup.bash
git submodule update --init --recursive
colcon build --packages-select data_msgs   # first, on a fresh clone
source install/setup.bash
colcon build
source install/setup.bash
```

For a focused build, use `colcon build --packages-select <pkg> ...`.

Use two Python environments, and do not mix them in one terminal:

- **Sensor, capture, localization and simulation** (`scripts/start_*.bash`, `data_tools`, `pika_sim`): system Python, after `conda deactivate`.
- **Teleoperation nodes** (`pika_remote_piper`): `conda activate pika`. They need `casadi`, `pinocchio` and `meshcat`.

Common launch examples:

```bash
ros2 launch data_tools run_data_capture.launch.py type:=single_pika datasetDir:=/path/to/data episodeIndex:=0
ros2 launch sensor_tools open_single_sensor.launch.py
ros2 launch pika_sim sim_piper_single.launch.py                              # simulated arm, no hardware
ros2 launch pika_remote_piper teleop_rand_single_piper.launch.py sim:=true   # teleop against the simulation
```

## Simulation

`pika_sim` replaces the Piper CAN driver with `piper_sim_bridge.py`. The bridge keeps the driver's topic contract: it reads `/joint_states_gripper` (6 joints in rad, plus the total gripper opening in m) and publishes `/joint_states_single` with names `joint0..joint6` at 200 Hz. `fake_pika_sense.py` optionally replaces the Pika Sense and Vive tracker with an RViz interactive marker. Keep this contract when you extend the simulation, so that simulators stay swappable and the teleop and capture code stays untouched. The details and pitfalls (joint reordering, `/joint_states` name clash, `package://` meshes in Gazebo Classic) are in `src/pika_sim/README.md`.

The simulated D405 and fisheye on the Pika gripper publish the same `/gripper/camera/...` topics as the hardware, with depth in 16UC1 mm like the real driver. `escena:=manzano` loads a seed-reproducible apple tree and publishes its ground truth on `/escena/verdad` and `/escena/frutas` for the active-perception code.

`control:=mit` emulates the Piper's MIT (impedance) mode with the values in `scripts/test_piper_mit_impedance.py`. Gazebo applies `kp` and `kd` as implicit joint springs and dampers, and `mit_emulador.py` sends `t_ref` as effort. Before changing MIT gains or targets, run `scripts/calcular_gravedad_mit.py`: it recomputes the gravity feedforward and checks stability. Gravity adds negative stiffness, so `kp` that is too low makes the target pose unstable even with feedforward.

## Active Perception Research

This repo hosts the active-perception code (next-best-view planner, metrics, fruit scenes), with Piper in `pika_sim` as the first robot. `milo_ws` (Ivan1721/milo_ws, branch `brazo`) is the intermediate step: it provides templates that already work (eye-in-hand camera simulation, MoveIt + OctoMap, randomized scenes, auto-labelled datasets) and is the second robot. The literature survey lives in Ivan1721/ActivePerceptionArms. Before working on this, read `docs/percepcion_activa/README.md`: decisions, the per-robot parameter contract, the roadmap, and how to resume work from another machine. Keep the code robot-agnostic: no robot names in the code, only parameters.

## Coding Style & Naming Conventions

Follow existing ROS package conventions:

- **Indentation:** 2 spaces in XML/YAML, 4 spaces in Python, and the prevailing C++ style in nearby files.
- **`snake_case`:** ROS packages, launch files, Python scripts, topics and parameters.
- **PascalCase:** message and service types, such as `CaptureStatus.msg` and `CaptureService.srv`.
- **Launch arguments:** prefer names that match existing examples, such as `datasetDir` and `episodeIndex`.

Documentation and comments in this fork's own packages are written in Spanish.

## Testing Guidelines

Run package tests with:

```bash
colcon test --packages-select <package_name>
colcon test-result --verbose
```

Test coverage is limited: only ament lint in `piper`, besides the upstream RealSense tests. Verify changes with targeted builds. When hardware behavior is touched, run the relevant launch file on connected devices. When hardware is unavailable, run the simulation headless (`gui:=false rviz:=false`) with an unused `ROS_DOMAIN_ID`.

## Syncing with Upstream

Remote `upstream` is `agilexrobotics/pika_ros`. Only the `ros2` branch matters; upstream `master` is ROS 1. Merge `upstream/ros2` into `pika-custom-ros2` and resolve conflicts as follows:

- **Ours:** `README.md`, `scripts/setup_device.py`, `src/PikaAnyArm`. Upstream PikaAnyArm V2 deleted the `piper/` layout this fork depends on; port individual fixes by hand when they apply.
- **Theirs:** `src/data_tools`, `src/data_msgs`, `source/install.zip`.

After merging, rebuild `data_msgs` first, then the dependent packages.

## Commit & Pull Request Guidelines

Commits are short, imperative and descriptive. This fork writes them in Spanish, for example `Corregir emparejamiento de puertos USB en Sense/Gripper multi`. Keep commits focused, and do not commit generated caches such as `__pycache__/` or `.pyc` files.

Changes inside `src/PikaAnyArm` are committed and pushed in the submodule first; then commit the updated submodule pointer in this repo.

Pull requests should:

- describe the changed packages,
- list the build and test commands that were run,
- note the hardware required,
- link related issues,
- include screenshots or logs for launch, RViz, camera or dataset workflow changes.

## Security & Configuration Tips

Do not commit machine-specific device IDs (Vive tracker serials, RealSense serial numbers outside the generated start scripts), secrets, or private dataset paths. Push over SSH; never embed tokens in remote URLs. Local CAN, udev and tracker settings belong in shell setup or in ignored local notes. Before running scripts that use `sudo`, device permissions or `/dev/*` paths on shared machines, review them.
