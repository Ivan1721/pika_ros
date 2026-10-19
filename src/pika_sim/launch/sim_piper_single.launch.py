# Piper + gripper Pika simulado en Gazebo, en lugar del brazo real.
#
# Reemplaza a la Terminal 1 del Flujo A (start_sensor_gripper.bash + driver CAN).
# La Terminal 2 no cambia:
#   conda activate pika && ros2 launch pika_remote_piper teleop_rand_single_piper.launch.py
#
# Argumentos:
#   sense:=fake  marcador en RViz hace de Pika Sense (por defecto)
#   sense:=real  sin Sense falso; correr aparte bash scripts/start_single_sensor.bash
#   gui:=false   Gazebo sin ventana (solo gzserver)
#   rviz:=false  sin RViz
import os
import re

import xacro
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, RegisterEventHandler
from launch.conditions import IfCondition, LaunchConfigurationEquals
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def robot_description():
    share_dir = get_package_share_directory('pika_sim')
    doc = xacro.process_file(os.path.join(share_dir, 'urdf', 'pika_piper_gazebo.urdf.xacro'))
    urdf = re.sub(r'<!--(.*?)-->', '', doc.toxml(), flags=re.DOTALL)
    # Gazebo Classic no resuelve package://; se reemplaza por la ruta instalada
    return re.sub(r'package://([^/]+)/',
                  lambda m: 'file://' + get_package_share_directory(m.group(1)) + '/', urdf)


def generate_launch_description():
    share_dir = get_package_share_directory('pika_sim')
    gazebo_launch_dir = os.path.join(get_package_share_directory('gazebo_ros'), 'launch')
    description = {'robot_description': robot_description()}

    declared_arguments = [
        DeclareLaunchArgument('sense', default_value='fake', choices=['fake', 'real']),
        DeclareLaunchArgument('gui', default_value='true'),
        DeclareLaunchArgument('rviz', default_value='true'),
    ]

    gzserver = IncludeLaunchDescription(PythonLaunchDescriptionSource(os.path.join(gazebo_launch_dir, 'gzserver.launch.py')))
    gzclient = IncludeLaunchDescription(PythonLaunchDescriptionSource(os.path.join(gazebo_launch_dir, 'gzclient.launch.py')),
                                        condition=IfCondition(LaunchConfiguration('gui')))

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[description, {'use_sim_time': True}],
        remappings=[('/joint_states', '/joint_state_broadcaster/joint_states')],
        output='screen',
    )

    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=['-entity', 'pika_piper', '-topic', 'robot_description'],
        output='screen',
    )

    controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster', 'arm_controller', 'gripper_controller',
                   '--controller-manager', '/controller_manager'],
        output='screen',
    )

    bridge = Node(
        package='pika_sim',
        executable='piper_sim_bridge.py',
        output='screen',
    )

    fake_sense = Node(
        package='pika_sim',
        executable='fake_pika_sense.py',
        output='screen',
        condition=LaunchConfigurationEquals('sense', 'fake'),
    )

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', os.path.join(share_dir, 'rviz', 'sim_piper_single.rviz')],
        parameters=[{'use_sim_time': True}],
        condition=IfCondition(LaunchConfiguration('rviz')),
        output='screen',
    )

    return LaunchDescription(declared_arguments + [
        gzserver,
        gzclient,
        robot_state_publisher,
        spawn_entity,
        RegisterEventHandler(OnProcessExit(target_action=spawn_entity, on_exit=[controller_spawner])),
        bridge,
        fake_sense,
        rviz,
    ])
