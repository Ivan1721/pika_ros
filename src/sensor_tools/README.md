# sensor_tools

ROS 2 (Humble) package that opens the Pika hardware: the fisheye USB camera (`usb_camera.py`), the RealSense D405 (through `realsense2_camera`), and the serial gripper/IMU (`serial_gripper_imu`). Its `open_*sensor*` launch files also start the Vive localization (`pika_locator`).

## Build

From the workspace root (see the main [README](../../README.md)):

```bash
cd ~/pika_ros
colcon build --packages-select data_msgs && source install/setup.bash
colcon build --packages-select sensor_tools
```

## Start

Bind the devices once with `python3 scripts/setup_device.py` (root `scripts/` folder). It writes the udev rules and generates a `start_*.bash` script with this machine's serial numbers and device paths. Then run that script:

```bash
conda deactivate
bash ~/pika_ros/scripts/start_sensor_gripper.bash   # 1 Pika Sense + 1 Pika Gripper
bash ~/pika_ros/scripts/start_multi_sensor.bash     # 2 Pika Sense
bash ~/pika_ros/scripts/start_multi_gripper.bash    # 2 Pika Gripper
bash ~/pika_ros/scripts/start_single_sensor.bash    # 1 Pika Sense
bash ~/pika_ros/scripts/start_single_gripper.bash   # 1 Pika Gripper
```

The copies in `src/sensor_tools/scripts/` are the upstream templates. The root `scripts/` folder holds the ones generated for this machine. The step-by-step workflows (Spanish operator guide) are in the private repository `Ivan1721/Next-Best-View` (`docs/manuales/Manual.md`).

## Launch files

| Launch | Devices | Localization |
|---|---|---|
| `open_single_sensor.launch.py` | 1 Sense: D405, fisheye, serial | `pika_single_locator` |
| `open_single_gripper.launch.py` | 1 Gripper: D405, fisheye, serial motor | — |
| `open_sensor_gripper.launch.py` | 1 Sense + 1 Gripper | `pika_single_locator` |
| `open_multi_sensor.launch.py` | 2 Sense (`l_` / `r_` arguments) | `pika_double_locator` |
| `open_multi_gripper.launch.py` | 2 Gripper | — |
| `open_single_sensor_with_teleop.launch.py`, `open_multi_sensor_with_teleop.launch.py` | Sense serial only (no cameras), for teleoperation | single / double locator |
| `open_fisheye.launch.py` | fisheye only | — |
| `open_helmet*.launch.py` | helmet variants | helmet locator (`_whit_tracker`) |

Do not start `pika_locator` separately next to a launch that already includes it, because both instances compete for the Vive dongle.

## Main topics (single Sense)

| Topic | Type |
|---|---|
| `/camera/color/image_raw`, `/camera/aligned_depth_to_color/image_raw` | `sensor_msgs/Image` |
| `/camera_fisheye/color/image_raw` | `sensor_msgs/Image` |
| `/gripper/data` | `data_msgs/Gripper` |
| `/imu/data` | `sensor_msgs/Imu` |
| `/pika_pose` | `geometry_msgs/PoseStamped` |

With several devices, the launch files add prefixes (`/sensor/...`, `/gripper/...`) or `_l` / `_r` suffixes. `serial_gripper_imu` also takes the IK output on `/joint_states`, replaces position 6 with the gripper opening measured by the Sense, and republishes the result as `/joint_states_gripper`, which is the command the Piper driver consumes. A double-click on the Sense calls `/teleop_trigger`.
