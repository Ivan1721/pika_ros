# Repository Guidelines

## Project Structure & Module Organization

This is a ROS 2 Humble workspace for Pika data collection, sensing and teleoperation. It is a fork of `agilexrobotics/pika_ros` (branch `ros2`); the working branch is `pika-custom-ros2`.

Primary source packages live under `src/`:

- `sensor_tools`: camera/gripper/localization launch files and scripts.
- `data_msgs` and `data_tools` (submodules of AgileX): custom messages, and dataset capture/sync/publish/conversion.
- `realsense-ros`: the RealSense driver stack.
- `PikaAnyArm` (submodule, fork `Ivan1721/PikaAnyArm`, branch `pika-custom-ros2`): Piper teleoperation. `pika_remote_piper` and the Piper packages `piper`, `piper_msgs`, `piper_description` are nested under `src/PikaAnyArm/piper/`.

Root `scripts/` holds device setup and the start scripts generated for this machine; `src/sensor_tools/scripts/` holds the upstream templates. `img/` and `src/PikaAnyArm/docs_img/` contain documentation assets. The project documentation (operator guide with workflows A–E, architecture, power budget) moved with the research code to the private repository `Ivan1721/Next-Best-View` (see below).

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

- **Sensor, capture and localization** (`scripts/start_*.bash`, `data_tools`): system Python, after `conda deactivate`.
- **Teleoperation nodes** (`pika_remote_piper`): `conda activate pika`. They need `casadi`, `pinocchio` and `meshcat`.

Common launch examples:

```bash
ros2 launch data_tools run_data_capture.launch.py type:=single_pika datasetDir:=/path/to/data episodeIndex:=0
ros2 launch sensor_tools open_single_sensor.launch.py
ros2 launch pika_remote_piper teleop_rand_single_piper.launch.py            # sim:=true / index_name:=_l for Next-Best-View's simulation
```

## Research code (Next-Best-View)

Since 2026-10-21 the simulation (`pika_sim`), the robot model (`pika_description`, with AgileX's official gripper), the MIT tools, the active-perception work and the documentation live in the private repository `Ivan1721/Next-Best-View`. That repo pins this fork as the submodule `deps/pika_ros` and builds on top of this workspace as an overlay (`~/nbv_ws`). The full history of what moved is preserved there; here it remains in the tag `archivo-sim-gazebo`.

This fork keeps the hardware side: drivers (`sensor_tools`), the PikaAnyArm fork (teleop with `sim:=true` and `index_name:=_l|_r`, used by the simulation), `data_tools`, the machine's start scripts and the Vive binaries in `install/`.

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

Test coverage is limited: only ament lint in `piper`, besides the upstream RealSense tests. Verify changes with targeted builds. When hardware behavior is touched, run the relevant launch file on connected devices; without hardware, use the simulation in Next-Best-View.

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
