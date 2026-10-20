# Piper + gripper Pika simulado en Gazebo, en lugar del brazo real.
#
# control:=teleop (por defecto) reemplaza a la Terminal 1 del Flujo A
# (start_sensor_gripper.bash + driver CAN). La Terminal 2 no cambia:
#   conda activate pika && ros2 launch pika_remote_piper teleop_rand_single_piper.launch.py sim:=true
#
# control:=mit emula el modo MIT (impedancia) de scripts/test_piper_mit_impedance.py:
# resorte kp y amortiguador kd en cada articulacion (Gazebo) + t_ref como esfuerzo
# (mit_emulador.py). No usa la teleop.
#
# Argumentos:
#   control:=teleop|mit
#   sense:=fake         marcador en RViz hace de Pika Sense (solo teleop; por defecto)
#   sense:=real         sin Sense falso; correr aparte bash scripts/start_single_sensor.bash
#   mit_script:=<ruta>  de donde se leen KP, KD, TARGETS, T_FF, ESCALA_GRAVEDAD
#   escala_gravedad:=X  pisa ESCALA_GRAVEDAD del script (0 = sin compensacion)
#   escena:=manzano     manzano de percepción activa (escena_manzano.py); escena:=ninguna, vacío
#   semilla:=N          semilla del follaje del manzano (por defecto 7, la de la documentación)
#   camaras:=false      sin la D405 ni la fisheye del gripper (Gazebo más liviano)
#   gui:=false          Gazebo sin ventana (solo gzserver)
#   rviz:=false         sin RViz
import ast
import os
import re
import xml.etree.ElementTree as ET

import xacro
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction,
                            RegisterEventHandler)
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

ARM_JOINTS = ['joint1', 'joint2', 'joint3', 'joint4', 'joint5', 'joint6']


def robot_description(camaras='true'):
    share_dir = get_package_share_directory('pika_sim')
    doc = xacro.process_file(os.path.join(share_dir, 'urdf', 'pika_piper_gazebo.urdf.xacro'),
                             mappings={'camaras': camaras})
    urdf = re.sub(r'<!--(.*?)-->', '', doc.toxml(), flags=re.DOTALL)
    # Gazebo Classic no resuelve package://; se reemplaza por la ruta instalada
    return re.sub(r'package://([^/]+)/',
                  lambda m: 'file://' + get_package_share_directory(m.group(1)) + '/', urdf)


def leer_mit(ruta):
    # Mismos valores que usa el script en el brazo real
    texto = open(ruta).read()
    valores = {}
    for nombre in ('KP', 'KD', 'TARGETS', 'T_FF', 'ESCALA_GRAVEDAD'):
        m = re.search(rf'^{nombre}\s*=\s*([^#\n]+)', texto, re.M)
        if not m:
            raise RuntimeError(f'No encontre {nombre} en {ruta}')
        valores[nombre] = ast.literal_eval(m.group(1).strip())
    return valores


def aplicar_mit(urdf, mit):
    # Resorte + amortiguador implicitos de Gazebo y mando por esfuerzo en joint1..6
    robot = ET.fromstring(urdf)
    for i, nombre in enumerate(ARM_JOINTS):
        joint = robot.find(f"joint[@name='{nombre}']")
        dinamica = joint.find('dynamics')
        if dinamica is None:
            dinamica = ET.SubElement(joint, 'dynamics')
        dinamica.set('damping', str(mit['KD'][i]))
        dinamica.set('friction', '0')

        gazebo = ET.SubElement(robot, 'gazebo', reference=nombre)
        ET.SubElement(gazebo, 'implicitSpringDamper').text = '1'
        ET.SubElement(gazebo, 'springReference').text = str(mit['TARGETS'][i])
        ET.SubElement(gazebo, 'springStiffness').text = str(mit['KP'][i])

        control = robot.find(f"ros2_control/joint[@name='{nombre}']")
        control.find('command_interface').set('name', 'effort')
    return ET.tostring(robot, encoding='unicode')


def launch_setup(context):
    share_dir = get_package_share_directory('pika_sim')
    gazebo_launch_dir = os.path.join(get_package_share_directory('gazebo_ros'), 'launch')
    modo = LaunchConfiguration('control').perform(context)

    urdf = robot_description(LaunchConfiguration('camaras').perform(context))
    nodos_modo = []
    if modo == 'mit':
        mit = leer_mit(os.path.expanduser(LaunchConfiguration('mit_script').perform(context)))
        escala = LaunchConfiguration('escala_gravedad').perform(context)
        escala = float(escala) if escala else float(mit['ESCALA_GRAVEDAD'])
        urdf = aplicar_mit(urdf, mit)
        controladores = ['joint_state_broadcaster', 'mit_ff_controller', 'gripper_controller']
        nodos_modo.append(Node(
            package='pika_sim',
            executable='mit_emulador.py',
            parameters=[{'kp': [float(v) for v in mit['KP']],
                         'targets': [float(v) for v in mit['TARGETS']],
                         't_ff': [float(v) for v in mit['T_FF']],
                         'escala_gravedad': escala}],
            output='screen',
        ))
    else:
        controladores = ['joint_state_broadcaster', 'arm_controller', 'gripper_controller']
        nodos_modo.append(Node(package='pika_sim', executable='piper_sim_bridge.py', output='screen'))
        if LaunchConfiguration('sense').perform(context) == 'fake':
            nodos_modo.append(Node(package='pika_sim', executable='fake_pika_sense.py', output='screen'))

    if LaunchConfiguration('camaras').perform(context) == 'true':
        # profundidad en 16UC1 mm, como el driver real de la D405
        nodos_modo.append(Node(package='pika_sim', executable='profundidad_mm.py', output='screen'))

    if LaunchConfiguration('escena').perform(context) == 'manzano':
        nodos_modo.append(Node(
            package='pika_sim',
            executable='escena_manzano.py',
            parameters=[{'semilla': int(LaunchConfiguration('semilla').perform(context))}],
            output='screen',
        ))

    description = {'robot_description': urdf}

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
        arguments=controladores + ['--controller-manager', '/controller_manager'],
        output='screen',
    )

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', os.path.join(share_dir, 'rviz', 'sim_piper_single.rviz')],
        parameters=[{'use_sim_time': True}],
        condition=IfCondition(LaunchConfiguration('rviz')),
        output='screen',
    )

    return [
        gzserver,
        gzclient,
        robot_state_publisher,
        spawn_entity,
        RegisterEventHandler(OnProcessExit(target_action=spawn_entity, on_exit=[controller_spawner])),
        *nodos_modo,
        rviz,
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('control', default_value='teleop', choices=['teleop', 'mit']),
        DeclareLaunchArgument('sense', default_value='fake', choices=['fake', 'real']),
        DeclareLaunchArgument('mit_script', default_value='~/pika_ros/scripts/test_piper_mit_impedance.py'),
        DeclareLaunchArgument('escala_gravedad', default_value=''),
        DeclareLaunchArgument('escena', default_value='ninguna', choices=['ninguna', 'manzano']),
        DeclareLaunchArgument('semilla', default_value='7'),
        DeclareLaunchArgument('camaras', default_value='true', choices=['true', 'false']),
        DeclareLaunchArgument('gui', default_value='true'),
        DeclareLaunchArgument('rviz', default_value='true'),
        OpaqueFunction(function=launch_setup),
    ])
