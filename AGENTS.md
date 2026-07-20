# Repository Guidelines

## Project Structure & Module Organization

This is a ROS workspace for Pika data collection, sensing, and teleoperation. Primary source packages live under `src/`: `data_msgs` defines custom messages and services, `data_tools` contains dataset capture/publish/sync utilities, `sensor_tools` contains camera/gripper/localization launch files and scripts, `realsense-ros` is the RealSense driver stack, `PikaAnyArm` contains Piper teleoperation code, and `pika_description` contains the URDF/xacro description of the Pika gripper end-effector (meshes from `piper_description` and `realsense2_description`). Root `scripts/` holds device setup and helper automation. `img/` and `src/PikaAnyArm/docs_img/` contain documentation assets. `docs/` holds project documentation: `docs/manuales/` (Manual.md Spanish setup guide, official AgileX manuals), `docs/datasheets/` (Pika product datasheets CN/ES), `docs/calibracion/` (tracker/base-station calibration guide), and `docs/energia/` (power consumption docs). Treat `install/` and `build/` as generated build output unless a task explicitly targets deployed artifacts.

## Build, Test, and Development Commands

Use ROS 2 Humble on Ubuntu 22.04 unless a package-specific README says otherwise.

```bash
source /opt/ros/humble/setup.bash
colcon build
```

Builds all workspace packages. For a focused build, use:

```bash
colcon build --packages-select data_msgs data_tools sensor_tools pika_description
```

After building, source the overlay:

```bash
source install/setup.bash
```

Common launch examples:

```bash
ros2 launch data_tools run_data_capture.launch.py type:=single_pika datasetDir:=/path/to/data episodeIndex:=0
ros2 launch sensor_tools open_single_sensor.launch.py
```

## Coding Style & Naming Conventions

Follow existing ROS package conventions. Use 2-space indentation in XML/YAML, 4 spaces in Python, and the prevailing C++ style in nearby files. Name ROS packages, launch files, Python scripts, topics, and parameters with `snake_case`. Keep message and service types in PascalCase, such as `CaptureStatus.msg` and `CaptureService.srv`. Prefer clear launch argument names matching existing examples, such as `datasetDir` and `episodeIndex`.

## Testing Guidelines

Run package tests with:

```bash
colcon test --packages-select <package_name>
colcon test-result --verbose
```

There is limited local test coverage outside upstream RealSense tests, so verify changes with targeted builds and, when hardware behavior is touched, the relevant launch file on connected devices. Add tests near the affected package when introducing reusable logic.

## Commit & Pull Request Guidelines

Recent history uses short imperative or descriptive commits, sometimes bilingual, for example `update data_tools` or `修复IK在ros2初始化之后出现的报错`. Keep commits focused and avoid committing generated caches such as `__pycache__/` or `.pyc` files. Pull requests should describe the changed packages, list build/test commands run, note required hardware, and link related issues. Include screenshots or logs for launch, RViz, camera, or dataset workflow changes.

## Security & Configuration Tips

Do not commit machine-specific device IDs, secrets, or private dataset paths. Local CAN, udev, and tracker settings belong in shell setup or ignored local notes. Review scripts that use `sudo`, device permissions, or `/dev/*` paths before running them on shared machines.
