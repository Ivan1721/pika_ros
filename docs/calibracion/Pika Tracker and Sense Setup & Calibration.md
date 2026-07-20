# 1. Base Station and Pika Configuration
<font style="color:#000000;">Locator Wireless Connection Diagram:</font>

<img src="https://cdn.nlark.com/yuque/0/2025/png/29291030/1749442579045-02edb87e-4b5b-4c90-b63c-acb87972070b.png" width="1852" title="" crop="0,0,1,1" id="heOWh" class="ne-image">

<font style="color:#000000;">Locator Wired Connection Diagram:</font>

<img src="https://cdn.nlark.com/yuque/0/2026/png/53402921/1778842937425-62176f68-474d-4644-94f6-980921955f16.png" width="2710" title="" crop="0,0,1,1" id="DPiNX" class="ne-image">

<font style="color:#000000;">As shown in the diagram above, this illustrates the overall workflow of Pika Station + Pika Sense data acquisition. Before officially starting data collection operations, you need to first complete the installation and deployment debugging of base stations, then perform base station pairing calibration, and finally turn on the data collector (Pika Sense) (first-time use requires software adaptation between the collector and receiver) to perform data collection.</font>

<font style="color:#000000;"></font>

## <font style="color:#000000;">1.1 Collector (Pika Sense) Positioning Tag Connection</font>
#### <font style="color:#000000;">1. Second Generation Pika Sense (With Side Type-C Port)</font>
<font style="color:#000000;">Second-generation Pika Sense users should take out the Type-C-to-Type-C data cable from the packaging and connect it to the upper interface of the dual Type-C ports on the right side of Pika Sense and the interface on the positioning tag to obtain positioning information. (Installation method as shown in the figure below)</font>

<img src="https://cdn.nlark.com/yuque/0/2026/png/53402921/1781171652435-425c3237-bfbf-4ffd-8d0d-57db9adeed89.png" width="5419" title="" crop="0,0,1,1" id="GE75f" class="ne-image">

## **<font style="color:#000000;">1.2 Base Station Hardware Deployment</font>**
<font style="color:rgb(0, 0, 0);">Base station deployment steps are as follows. Placement and frequency pairing can refer to the following video:</font>

[Base Station Placement and Frequency Pairing.mp4](https://agilexsupport.yuque.com/attachments/yuque/0/2026/mp4/69344822/1781754433998-0c3227f2-6edb-4b7e-894b-49f51463d058.mp4)

### <font style="color:#000000;">1.2.1 Installation Steps</font>
<font style="color:#000000;">1. Determine base station orientation: The base station placement position relative to the collection device is shown in the figure below. Please ensure placement according to the relative positions shown in the diagram; otherwise, positioning tag signal loss or positioning calibration failure may occur. If there is a significant angle change during collection that affects the illumination relationship, adjustments or additions of base stations should follow the principle of relative relationships shown in the diagram. </font>

<img src="https://cdn.nlark.com/yuque/0/2026/jpeg/59893225/1769583073117-0d105eee-6c76-47ec-ad93-9a2454a0be6d.jpeg" width="3395" title="" crop="0,0,1,1" id="TkO5Z" class="ne-image">

<font style="color:#000000;">2. Install the base station: It is recommended to install the base station at a 90-degree viewing angle position within the room, directly fixed to the wall. If space does not allow for such installation, you can also install the base station on a tripod, or place it on a stable surface such as a desktop. Avoid using unstable installation methods or installing on surfaces prone to vibration.</font>

<font style="color:#000000;">3. Adjust base station angle: Adjust the base station angle so that its front panel faces the center of the operation area. Each base station should be set at a minimum height of 0.5 meters (1.6 feet). Depending on the set height, adjust the base station angle upward or downward to fully cover the operation area. Secure two positioning base stations to ensure the activity range of the teach pendant is within the field of view of both base stations. For optimal performance, the distance between the collector (Pika Sense) and each base station should be at least 0.5 meters (1.6 feet).</font>

<font style="color:#000000;">4. Connect power: Connect power cables to each base station, then plug them into power outlets respectively, or connect tripod-mounted batteries to turn on the power.</font>

<font style="color:#000000;">5. Set channel (first-time use): When using positioning base stations for the first time, you need to manually set the channel for each positioning base station. Use a sharp object to press the button on the back of the base station (as shown in position 9 below). Press once to increase the channel by 1, with a range from 0-15. Each time the channel is increased, the green light on the base station will flash once. Ensure base stations are set to different channels. All base stations within the same scene must be set to different channels.</font>

<img src="https://cdn.nlark.com/yuque/0/2025/png/29291030/1749442580121-05919467-3ae7-4c42-a8dd-a0984f8c1bde.png" width="870" title="" crop="0,0,1,1" id="J1Zt9" class="ne-image">

<font style="color:#000000;">6. Verify operation: After everything is ready, the positioning base station LED should remain steadily lit in green, indicating normal operation.</font>

:::warning
⚠ **Installation Notes:**

● Do not let any object block the front panel of the base station.

● Infrared light in sunlight may affect base station data transmission and reception; please use indoors without direct sunlight.

● Glass and acrylic reflections may cause positioning data drift; please ensure no glass or acrylic reflections exist in the concentrated illumination area of the base station.

● Please ensure base stations are installed outside the collection area and securely fastened to avoid damage or performance degradation from accidental collision, dropping, or impact.

● Do not install in areas with strong lighting; overexposure will negatively affect base station performance.

● After installing base stations, remember to remove the protective film from the front panel.

● After turning on base stations, they may affect nearby infrared sensors, such as those used by TV infrared remote controls.

● To achieve accurate positioning, please ensure the distance between any base station and the collector (Pika Sense) is within 7 meters (23 feet). Ensure there are no physical obstacles (such as protruding shelves) where base stations are placed to fully cover the collector's (Pika Sense) field of view and ensure signals are not blocked.

:::

<img src="https://cdn.nlark.com/yuque/0/2025/png/29291030/1749442580100-93999794-c111-4df3-b100-353074792ef6.png" width="380" title="" crop="0,0,1,1" id="o9nNo" class="ne-image">

### <font style="color:#000000;">1.2.2 Base Station Field of View</font>
<font style="color:#000000;">Base station field of view: The horizontal field of view is 150 degrees, and the vertical field of view is 110 degrees. To maximize the operation area, please install base stations above head height (preferably more than 2 meters or 6.5 feet from the ground), and adjust the angle of each base station to between 25 degrees and 35 degrees. (Field of view as shown below)</font>

<img src="https://cdn.nlark.com/yuque/0/2025/png/29291030/1749442579423-0c41cba7-6ef4-400e-9d43-ee6393861dd6.png" width="500" title="" crop="0,0,1,1" id="fRS75" class="ne-image">

<font style="color:#000000;">1.2.3 Base Station Coverage Range</font>

<font style="color:#000000;">Two Base Stations:</font>

<font style="color:#000000;">Minimum required operation area: 2 m x 1.5 m (6 ft 6 in x 5 ft); maximum up to 5 m x 5 m (16 ft 5 in x 16 ft 5 in)</font>

<img src="https://cdn.nlark.com/yuque/0/2025/png/29291030/1749442579421-3c5ddee1-c6ee-4dec-bf90-59277759d7fd.png" width="582" title="" crop="0,0,1,1" id="k71sb" class="ne-image">

<font style="color:#000000;">Two base stations: Single-person operation</font>

:::warning
⚠**Note:** 

Avoid diagonal placement when possible; arrange at 90° or in the same direction.

:::

<font style="color:#000000;">Four Base Stations:</font>

<font style="color:#000000;">Four base stations support a maximum coverage area of 10 m x 10 m (32 ft 10 in x 32 ft 10 in). </font>

<font style="color:#000000;">(A maximum of 4 base stations can be used in one scene)</font>

<font style="color:#000000;">Single-person operation:</font>

<img src="https://cdn.nlark.com/yuque/0/2025/png/29291030/1749442579471-18f28d83-3030-4629-8149-df1767f85259.png" width="500" title="" crop="0,0,1,1" id="GRAP3" class="ne-image">

<font style="color:#000000;">Dual-person operation:</font>

<img src="https://cdn.nlark.com/yuque/0/2025/png/29291030/1749442579543-b41bf8e2-5bfc-4bc0-9f6c-5684461b5544.png" width="359" title="" crop="0,0,1,1" id="i0I9d" class="ne-image">

<font style="color:#000000;">Three Base Stations:</font>

<font style="color:#000000;">If the environment is an irregular area, you still need to deploy 3 or more base stations; refer to the figure below.</font>

<img src="https://cdn.nlark.com/yuque/0/2025/png/29291030/1749442580031-c99c7c60-0d3b-48d4-b9b8-7660eb7d2208.png" width="574" title="" crop="0,0,1,1" id="me8V4" class="ne-image"><font style="color:#000000;"></font>

### <font style="color:#000000;">1.2.4 Multi-Device Base Station Installation in Same Space</font>
<font style="color:#000000;">When multiple sets of base stations paired with collectors need to be deployed in the same space, the following methods are recommended:</font>

<font style="color:#000000;">● Prioritize physical isolation methods, using partitions or other objects to separate each set of collection equipment (base station + collector); note that partition height must exceed base station height. Currently, a maximum of 4 sets of collection equipment are supported for simultaneous collection operations in the same space. Exceeding this number may cause instability or other unexpected issues, as shown in the figure below.</font>

<img src="https://cdn.nlark.com/yuque/0/2025/png/29291030/1749442580027-bfcc9e0b-953b-4220-b907-dfc2757eb781.png" width="1035" title="" crop="0,0,1,1" id="pYnjZ" class="ne-image">

## <font style="color:#000000;">1.3 Positioning Base Station Calibration</font>
<font style="color:#000000;"></font>

<font style="color:#000000;">The purpose of calibrating positioning tags with positioning base stations is to obtain absolute coordinate values of the positioning tags in three-dimensional space.</font>

<font style="color:#000000;">Positioning base stations perform calibration through transmitting and receiving infrared light.</font>

<font style="color:#000000;">Before starting calibration, please ensure:</font>

:::warning
⚠**<font style="color:#000000;">Note: </font>**

<font style="color:#000000;">Turn on the positioning tag and place it within the FOV range of the base station while </font>**<font style="color:#DF2A3F;">keeping it stationary</font>**<font style="color:#000000;">.</font>

<font style="color:#000000;">Ensure the lights on both the base station and positioning tag are green.</font>

<font style="color:#000000;">Ensure the film on the base station has been removed and there is no obstruction in front of the base station.</font>

<font style="color:#000000;">Base stations are on </font>**<font style="color:#DF2A3F;">different channels</font>**<font style="color:#000000;">.</font>

<font style="color:#000000;">Ensure the current room has no sunlight exposure; base stations may also affect the use of other infrared devices.</font>

<font style="color:#000000;">Ensure there are no infrared-reflective objects such as glass or acrylic panels in the concentrated illumination area of the base station.</font>

<font style="color:#000000;">When deploying positioning base stations for the first time, moving positioning base stations, poor positioning results, or switching base station channels, you should run the following commands to calibrate the positioning tag.</font>

<font style="color:#000000;">Calibration does not automatically close the program; manually close it (press Ctrl + C).</font>

:::

<font style="color:#000000;">Calibration is divided into the following situations, requiring different commands based on the situation:</font>

1. <font style="color:#000000;">First-time calibration on your computer, run: </font>

```plain
cd ~/pika_ros/install/pika_locator/lib && ./survive-cli --force-calibrate
```

2. <font style="color:#000000;">If you added or reduced number of base stations, run:</font>

```plain
cd ~/pika_ros/install/pika_locator/lib && ./survive-cli --force-calibrate
```

3. <font style="color:#000000;">If you switched the channel, run:</font>

```plain
cd ~/pika_ros/install/pika_locator/lib && ./survive-cli --force-calibrate
```

4. <font style="color:#000000;">If position drift occurred, or base stations were moved during use, run:</font>

```plain
cd ~/pika_ros/install/pika_locator/lib && ./survive-cli
```

<font style="color:#000000;">Below is the terminal output information after successful calibration using one Sense for the first time:</font>

<img src="https://cdn.nlark.com/yuque/0/2026/png/68774675/1781087488436-11bf9f81-19a0-44f1-bf35-7d18a1b1afa0.png" width="896" title="" crop="0,0,1,1" id="Mtd3a" class="ne-image">

<font style="color:#000000;">①: Added base stations on channels 2 and 3</font>

<font style="color:#DF2A3F;">②: Displays the error of the positioning tag (unit/meters). When you see this information output in the terminal and the output value range is less than 0.005, you can close the calibration program. Use Ctrl+C to close it.</font>

<font style="color:#000000;">If red error messages appear after pressing Ctrl+C to terminate the program, they can be ignored.</font>

```plain
Warning: Libusb poll failed. -10 (LIBUSB_ERROR_INTERRUPTED)
```

:::warning
<font style="color:#000000;">⚠</font><font style="color:#000000;"></font>**<font style="color:#DF2A3F;">Common Calibration Exception Handling:</font>**

1. **<font style="color:#000000;">Unable to find driver_openvr.so file during calibration execution</font>**

<font style="color:#000000;">Install dependency: sudo apt install libopenvr-dev, then perform calibration again.</font>

2. **<font style="color:#000000;">Terminal remains stuck during calibration with no positioning error displayed</font>**

<font style="color:#000000;">rm ~/.config/libsurvive/config.json</font>

<font style="color:#000000;">Remove the config.json file and perform calibration again.</font>

3. **<font style="color:#000000;">Error failures displayed after calibration ends</font>**

<font style="color:#000000;">Error failures indicate that this calibration failed. Check if there is sunlight exposure in the current environment or if there are devices actively emitting infrared light. Recheck base station placement to ensure the Sense is within the base station's FOV. After checking all items above, run the calibration program again.</font>

4. **<font style="color:#000000;">TF coordinates drift after using for some time following successful calibration</font>**

<font style="color:#000000;">Check if there is sunlight exposure in the current environment or if there are devices actively emitting infrared light. Recheck base station placement to ensure the Sense is within the base station's FOV. After checking all items above, run the calibration program again.</font>

:::

# <font style="color:#000000;">2. Starting Devices</font>
<font style="color:#000000;">If using multiple Pika series devices for collection, please refer to the following document for multi-Pika device binding. If using single Sense for body-less collection scheme, you can skip this binding step.</font>

[[ROS2] Pika Series Device Binding Process](https://agilexsupport.yuque.com/staff-hso6mo/gp5vq8/vgf28uyzv2ritw7k)

## <font style="color:#000000;">2.1 Turn On Sense</font>
<font style="color:#000000;">Open a new terminal and run:</font>

```plain
cd ~/pika_ros/scripts/
bash start_single_sensor.bash  # single sensor
bash start_multi_sensor.bash  # double sensor
```

## <font style="color:#000000;">2.2 Check Sense TF Coordinate Stability in RViz</font>
<font style="color:#000000;">After starting the device, if the terminal shows no errors, an RViz window will pop up displaying the current TF coordinates of Sense. In RViz, press Ctrl+Z to center coordinates, move the Sense, check whether TF coordinates follow, and whether they are stable. If sudden drifting occurs, </font>[base station recalibration](#cV0E7)<font style="color:#000000;"> is required.</font>

<img src="https://cdn.nlark.com/yuque/0/2025/png/29291030/1749442581820-99a22836-5e76-40bd-ab37-fd04f3a18a97.png?x-oss-process=image%2Fformat%2Cwebp" width="810" title="" crop="0,0,1,1" id="bye7m" class="ne-image">

# <font style="color:#000000;">3. Coordinate Description</font>
<img src="https://cdn.nlark.com/yuque/0/2025/png/29291030/1749442582773-f53c4bc8-9ab1-4cc0-a894-ee9e45709080.png" width="4000" title="" crop="0,0,1,1" id="LOexu" class="ne-image">

<font style="color:#000000;">Pika's coordinate system is centered on the gripper, published via the pika_pose topic, with topic type geometry_msgs::PoseStamped. </font>

<font style="color:#000000;">The coordinate system of the pika_pose topic is as shown above: X-axis points forward, Y-axis points left, Z-axis points up.</font>

# <font style="color:#000000;">4. Topic Description</font>
<font style="color:rgb(0, 0, 0);">Single Sense Usage:</font>

<font style="color:rgb(0, 0, 0);">Sense gripper topic name: /gripper_l/data</font>

<font style="color:rgb(0, 0, 0);">Pose topic name: /pika_pose</font>

<font style="color:rgb(0, 0, 0);"></font>

<font style="color:rgb(0, 0, 0);">Dual Sense Usage:</font>

<font style="color:rgb(0, 0, 0);">Left Sense gripper topic name: /gripper_l/data</font>

<font style="color:rgb(0, 0, 0);">Right Sense gripper topic name: /gripper_r/data</font>

<font style="color:rgb(0, 0, 0);">Left Sense pose topic name: /pika_pose_l</font>

<font style="color:rgb(0, 0, 0);">Right Sense pose topic name: /pika_pose_r</font>

<font style="color:rgb(0, 0, 0);"></font>

<font style="color:rgb(0, 0, 0);">Subscribe to Gripper Information:</font>

<font style="color:#DF2A3F;">(ubuntu22.04-ROS2)</font>

```plain
ros2 topic echo /gripper/joint_states  # single sensor
ros2 topic echo /gripper_l/joint_states  # double sensor, left
ros2 topic echo /gripper_r/joint_states  # double sensor, right
```

<font style="color:rgb(0, 0, 0);">ros2 topic echo /gripper/data --once </font>

<font style="color:rgb(0, 0, 0);">(Output topic information only once, output data as follows:)</font>

<img src="https://cdn.nlark.com/yuque/0/2026/png/69344822/1781763330590-f2585ae6-b13d-4274-ad6b-4e3d42f49505.png" width="686" title="" crop="0,0,1,1" id="u6f0c0581" class="ne-image">

<font style="color:rgb(0, 0, 0);">Or:</font>

<font style="color:#DF2A3F;">(ubuntu22.04-ROS2)</font>

```plain
ros2 topic echo /gripper/joint_states  # single sensor
ros2 topic echo /gripper_l/joint_states  # double sensor, left
ros2 topic echo /gripper_r/joint_states  # double sensor, right
```

<font style="color:rgb(0, 0, 0);">ros2 topic echo /gripper/joint_state --once </font>

<font style="color:rgb(0, 0, 0);">(Output topic information only once, output data as follows:)</font>

<img src="https://cdn.nlark.com/yuque/0/2026/png/69344822/1781763371728-c0b12b87-6793-44f9-8784-729e56d89743.png" width="702" title="" crop="0,0,1,1" id="u73b8aee0" class="ne-image">

