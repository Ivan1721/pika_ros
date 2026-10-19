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

## 介绍

Pika 数据套装产品（以下简称Pika）是一款针对**具身智能**领域数据采集场景的**空间数据采集产品**，是一款面向通用操作、轻量化的便携式采执一体化解决方案， 由采集装置及模型推理执行器以及配套的定位基站和数据背包构成。支持高效、准确、快捷、轻量的采集机器人的空间操作数据。

Pika具备超高精度的**毫米级空间信息采集能力**，支持采集数据涵盖六自由度精准空间信息、深度信息、超广角可见光视觉信息以及夹持信息。满足具身智能领域的**数据采集多信息融合需求**。执行器可以基于采集器采集的数据用于模型推理的执行器终端。

如果您在使用过程中遇到任何问题，或者有任何建议和反馈，请通过以下方式联系我们：

- GitHub Issues: https://github.com/agilexrobotics/pika_ros/issues
- 电子邮件: [support@agilex.ai](mailto:support@agilex.ai)

我们的技术团队将尽快回复您的问题，并提供必要的支持和帮助。

pika sdk：https://github.com/agilexrobotics/pika_sdk

pika 遥操作：https://github.com/agilexrobotics/PikaAnyArm

有关更多信息，您可以参考 [Pika 产品用户手册 beta（CN）](https://agilexsupport.yuque.com/staff-hso6mo/peoot3/vm7e26ho2hmuw0ng) 和 [PIKA使用QA查询](https://agilexsupport.yuque.com/staff-hso6mo/peoot3/ltl2m8a3crra12kg)。

## 支持的环境平台

### 软件环境

- 架构：x86_64
- 操作系统：Ubuntu22.04
- ROS：humble

## 关于本分支（fork）

本仓库是 [agilexrobotics/pika_ros](https://github.com/agilexrobotics/pika_ros)（`ros2` 分支）的分支，维护于 [Ivan1721/pika_ros](https://github.com/Ivan1721/pika_ros)，工作分支为 `pika-custom-ros2`。

| 新增内容 | 位置 |
|---|---|
| 西班牙语安装与操作指南，包含流程 A/A+（遥操作）、B（仅机械臂）、C（相机与关节采集）、D/D+（仿真）、E（数据处理） | [docs/manuales/Manual.md](docs/manuales/Manual.md) |
| Pika 夹爪（D405 + 鱼眼相机）及 Piper + Pika 的 URDF | [src/pika_description](src/pika_description/README.md) |
| Piper + Pika 夹爪的 Gazebo 仿真，接入真实遥操作链路，无需 CAN、Pika Sense 或定位基站 | [src/pika_sim](src/pika_sim/README.md) |
| PikaAnyArm 分支，保留上游 V2 中删除的 `piper/` 结构（`pika_remote_piper`、`piper_ros`） | 子模块 `src/PikaAnyArm` → [Ivan1721/PikaAnyArm](https://github.com/Ivan1721/PikaAnyArm) |
| 修复：`setup_device.py` 的 USB 配对、`open_multi_gripper.launch.py` 的节点名与夹爪跟随、从上游移植的 IK/遥操作修复 | git 历史 |
| 主动感知研究计划：Pika + Piper、Milo（[Ivan1721/milo_ws](https://github.com/Ivan1721/milo_ws)）与 ActivePerceptionArms 综述如何衔接（Milo 作为中间环节） | [docs/percepcion_activa](docs/percepcion_activa/README.md) |
| 标定指南、数据手册、功耗预算 | [docs/](docs/README.md) |

### 快速开始

```bash
cd ~/pika_ros
git submodule update --init --recursive
source /opt/ros/humble/setup.bash
colcon build --packages-select data_msgs && source install/setup.bash
colcon build && source install/setup.bash
```

`pika_locator` 与 `libsurvive`（Vive 定位）仅以预编译二进制形式提供于 `source/install.zip`，见 Manual 第 6 节。没有任何硬件时，使用 **Flujo D+**（`ros2 launch pika_sim sim_piper_single.launch.py`）。

已知问题见 Manual 末尾；贡献与上游同步规范见 [AGENTS.md](AGENTS.md)。
