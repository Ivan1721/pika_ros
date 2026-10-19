<div align="center">
  <h1 align="center"> pika_ros </h1>
  <h3 align="center"> Agilex Robotics </h3>
  <p align="center">
    <a href="README.md"> English </a> | <a href="README_zh.md">中文</a> | <a href="README_es.md">Español</a>
  </p>
</div>
<div align="center">

![ubuntu](https://img.shields.io/badge/Ubuntu-22.04-orange.svg)
![ROS2](https://img.shields.io/badge/ROS-humble-blue.svg)

</div>

## Introduction

Pika (hereinafter "Pika") is a **spatial data acquisition product** for **embodied intelligence** data collection scenarios. It is a lightweight, portable, general-purpose acquisition-and-execution solution, composed of a data collection unit, a model-inference execution unit, and a companion localization base station and data backpack. It supports efficient, accurate, fast, and lightweight acquisition of a robot's spatial manipulation data.

Pika provides ultra-high-precision **millimeter-level spatial information acquisition**, capturing data that spans precise 6-DOF spatial information, depth information, ultra-wide-angle visible-light vision, and gripper information — meeting the **multi-modal data fusion** needs of embodied intelligence. The execution unit can use data collected by the acquisition unit for model-inference execution.

If you run into any issues, or have suggestions or feedback, please reach us through:

- GitHub Issues: https://github.com/agilexrobotics/pika_ros/issues
- Email: [support@agilex.ai](mailto:support@agilex.ai)

Our technical team will respond as soon as possible with the necessary support.

Pika SDK: https://github.com/agilexrobotics/pika_sdk

Pika teleoperation: https://github.com/agilexrobotics/PikaAnyArm

For more information, see the [Pika Product User Manual beta (CN)](https://agilexsupport.yuque.com/staff-hso6mo/peoot3/vm7e26ho2hmuw0ng) and the [PIKA Usage Q&A](https://agilexsupport.yuque.com/staff-hso6mo/peoot3/ltl2m8a3crra12kg).

## Supported Environment

### Software Environment

- Architecture: x86_64
- Operating System: Ubuntu 22.04
- ROS: Humble

## About this fork

This repository is a fork of [agilexrobotics/pika_ros](https://github.com/agilexrobotics/pika_ros) (branch `ros2`), maintained at [Ivan1721/pika_ros](https://github.com/Ivan1721/pika_ros). The working branch is `pika-custom-ros2`.

| What it adds | Where |
|---|---|
| Step-by-step setup and operation guide (Spanish), with workflows A/A+ (teleoperation), B (arm only), C (camera + joint capture), D/D+ (simulation), E (data pipeline) | [docs/manuales/Manual.md](docs/manuales/Manual.md) |
| URDF of the Pika gripper (D405 + fisheye) and of the Piper + Pika arm | [src/pika_description](src/pika_description/README.md) |
| Gazebo simulation of the Piper + Pika gripper that plugs into the real teleoperation chain. It needs no CAN, Pika Sense or base stations | [src/pika_sim](src/pika_sim/README.md) |
| PikaAnyArm fork that keeps the `piper/` layout (`pika_remote_piper`, `piper_ros`) removed upstream in V2 | submodule `src/PikaAnyArm` → [Ivan1721/PikaAnyArm](https://github.com/Ivan1721/PikaAnyArm) |
| Fixes: USB pairing in `setup_device.py`, node names and gripper mirroring in `open_multi_gripper.launch.py`, IK/teleop fixes ported from upstream | git history |
| Calibration guide, datasheets, power budget | [docs/](docs/README.md) |

### Quick start

```bash
cd ~/pika_ros
git submodule update --init --recursive
source /opt/ros/humble/setup.bash
colcon build --packages-select data_msgs && source install/setup.bash
colcon build && source install/setup.bash
```

`pika_locator` and `libsurvive` (Vive localization) ship only as precompiled binaries in `source/install.zip`; see Manual §6. To choose a workflow for your hardware, see the quick table in the Manual. With no hardware at all, use **Flujo D+** (`ros2 launch pika_sim sim_piper_single.launch.py`).

Known issues are listed at the end of the Manual. Contribution and upstream-sync guidelines are in [AGENTS.md](AGENTS.md).
