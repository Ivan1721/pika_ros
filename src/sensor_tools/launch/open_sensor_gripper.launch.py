import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, Command, PythonExpression
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():

    share_dir = get_package_share_directory('sensor_tools')

    declared_arguments = [
        DeclareLaunchArgument('camera_fps', default_value='30'),
        DeclareLaunchArgument('camera_height', default_value='480'),
        DeclareLaunchArgument('camera_width', default_value='640'),
        DeclareLaunchArgument('camera_profile', default_value='640x480x30'),
        DeclareLaunchArgument('gripper_fisheye_port', default_value='23'),
        DeclareLaunchArgument('sensor_serial_port', default_value='/dev/ttyUSB0'),
        DeclareLaunchArgument('gripper_serial_port', default_value='/dev/ttyUSB1'),
        DeclareLaunchArgument('gripper_depth_camera_no', default_value='230322272619'),
        DeclareLaunchArgument('sensor_joint_name', default_value='sensor_gripper_center_joint'),
        DeclareLaunchArgument('gripper_joint_name', default_value='gripper_gripper_center_joint'),
        DeclareLaunchArgument('motor_current_limit', default_value='1000.0'),
        DeclareLaunchArgument('motor_current_redundancy', default_value='500.0'),
        DeclareLaunchArgument('mit_mode', default_value='true'),
        DeclareLaunchArgument('ctrl_rate', default_value='50.0'),
        # parte:=sensor (Sense + localizador) o parte:=gripper (Gripper con sus cámaras) para repartir el
        # montaje entre dos computadores con los mismos topics que parte:=todo
        DeclareLaunchArgument('parte', default_value='todo')
    ]
    camera_fps = LaunchConfiguration('camera_fps')
    camera_height = LaunchConfiguration('camera_height')
    camera_width = LaunchConfiguration('camera_width')
    camera_profile = LaunchConfiguration('camera_profile')
    gripper_fisheye_port = LaunchConfiguration('gripper_fisheye_port')
    sensor_serial_port = LaunchConfiguration('sensor_serial_port')
    gripper_serial_port = LaunchConfiguration('gripper_serial_port')
    gripper_depth_camera_no = LaunchConfiguration('gripper_depth_camera_no')
    sensor_joint_name = LaunchConfiguration('sensor_joint_name')
    gripper_joint_name = LaunchConfiguration('gripper_joint_name')
    motor_current_limit = LaunchConfiguration('motor_current_limit')
    motor_current_redundancy = LaunchConfiguration('motor_current_redundancy')
    mit_mode = LaunchConfiguration('mit_mode')
    ctrl_rate = LaunchConfiguration('ctrl_rate')
    parte = LaunchConfiguration('parte')
    con_sensor = IfCondition(PythonExpression(["'", parte, "' in ('todo', 'sensor')"]))
    con_gripper = IfCondition(PythonExpression(["'", parte, "' in ('todo', 'gripper')"]))

    locator_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(get_package_share_directory('pika_locator'), 'launch', 'pika_single_locator.launch.py')]),
        condition=con_sensor
    )


    gripper_depth_camera_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(get_package_share_directory('realsense2_camera'), 'launch', 'rs_launch.py')]),
        launch_arguments={'serial_no': gripper_depth_camera_no,
                          'camera_namespace': "gripper",
                          'camera_name': "camera",
                          'rgb_camera.color_profile': camera_profile, 
                          'depth_module.color_profile': camera_profile, 
                          'depth_module.depth_profile': camera_profile,
                          'depth_module.infra_profile': camera_profile}.items(),
        condition=con_gripper
    )

    return LaunchDescription(declared_arguments+[
        locator_launch,
        gripper_depth_camera_launch,
        Node(
            package='sensor_tools',
            executable='usb_camera.py',
            name='gripper_camera_fisheye',
            parameters=[{'camera_port': gripper_fisheye_port,
                         'camera_fps': camera_fps,
                         'camera_height': camera_height,
                         'camera_width': camera_width,
                         'camera_frame_id': "gripper/camera_fisheye_link"}],
            remappings=[
                ('/camera_rgb/color/image_raw', '/gripper/camera_fisheye/color/image_raw'),
                ('/camera_rgb/color/camera_info', '/gripper/camera_fisheye/color/camera_info')
            ],
            condition=con_gripper,
            respawn=True,
            output='screen'
        ),
        Node(
            package='sensor_tools',
            executable='serial_gripper_imu',
            name='sensor_serial_gripper_imu',
            parameters=[{'serial_port': sensor_serial_port,
                         'joint_name': sensor_joint_name}],
            remappings=[
                ('/imu/data', '/sensor/imu/data'),
                ('/gripper/data', '/sensor/gripper/data'),
                ('/gripper/ctrl', '/sensor/gripper/ctrl'),
                ('/gripper/joint_state', '/sensor/gripper/joint_state'),
                ('/gripper/joint_state_ctrl', '/sensor/gripper/joint_state_ctrl'),
                ('/joint_state_info', '/joint_states'),
                ('/joint_state_gripper', '/joint_states_gripper'),
                ('/data_capture_status', '/data_tools_dataCapture/status'),
                ('/teleop_status', '/teleop_status'),
                ('/localization_status', '/pika_localization_status'),
                ('/arm_control_status', '/arm_control_status'),
            ],
            condition=con_sensor,
            respawn=True,
            output='screen'
        ),
        Node(
            package='sensor_tools',
            executable='serial_gripper_imu',
            name='gripper_serial_gripper_imu',
            parameters=[{'serial_port': gripper_serial_port,
                         'joint_name': gripper_joint_name,
                         'motor_current_limit': motor_current_limit,
                         'motor_current_redundancy': motor_current_redundancy,
                         'mit_mode': mit_mode,
                         'ctrl_rate': ctrl_rate}],
            remappings=[
                ('/imu/data', '/imu/data'),
                ('/gripper/data', '/gripper/gripper/data'),
                ('/gripper/ctrl', '/gripper/gripper/ctrl'),
                ('/gripper/joint_state', '/gripper/gripper/joint_state'),
                ('/gripper/joint_state_ctrl', '/sensor/gripper/joint_state'),
                ('/joint_state_info', '/joint_states_single'),
                ('/joint_state_gripper', '/joint_states_single_gripper'),
            ],
            condition=con_gripper,
            respawn=True,
            output='screen'
        )
    ])
