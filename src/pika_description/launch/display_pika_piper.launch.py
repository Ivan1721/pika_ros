import os
import xacro

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def launch_setup(context, *args, **kwargs):
    pkg = get_package_share_directory('pika_description')
    gripper_val = LaunchConfiguration('gripper').perform(context)

    urdf_path = os.path.join(pkg, 'urdf/pika_piper_standalone.urdf.xacro')
    doc = xacro.parse(open(urdf_path))
    xacro.process_doc(doc, mappings={'gripper': gripper_val})
    robot_description = {'robot_description': doc.toxml()}

    rviz_config = os.path.join(pkg, 'rviz/pika_piper.rviz')

    return [
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[robot_description],
            output='screen',
        ),
        Node(
            package='joint_state_publisher_gui',
            executable='joint_state_publisher_gui',
            parameters=[robot_description],
            output='screen',
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config],
            output='screen',
        ),
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            name='gripper',
            default_value='pika',
            description='Gripper a montar en link6 del Piper (pika | ...)',
        ),
        OpaqueFunction(function=launch_setup),
    ])
