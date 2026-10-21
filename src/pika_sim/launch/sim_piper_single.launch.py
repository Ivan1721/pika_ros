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
#   arbol:=helios       manzano realista de Helios en vez de primitivas (generar antes con
#                       scripts/generar_manzano_helios.py); ruta_helios:=<carpeta> elige cuál
#   densidad:=media     con arbol:=helios: muro frutal con más fruta en racimos y más follaje (o alta)
#   luz:=atardecer      iluminación: dia, atardecer, contraluz, nublado, noche_fria, noche_calida
#   fondo:=blanco       para renders: fondo blanco o croma (magenta #FF00FF), sin suelo ni sombras
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


# Iluminación del mundo (luz:=...). Colores RGB; las direcciones son hacia dónde viaja la luz.
# El robot mira hacia +x: un sol con dirección +x ilumina el árbol de frente, uno con −x lo deja a
# contraluz. Los focos de noche van en la plataforma, a los lados del brazo, apuntando a la fruta.
LUCES = {
    'dia': dict(ambiente='0.40 0.40 0.40', fondo='0.70 0.80 0.92', sol='0.85 0.85 0.82',
                dir_sol='-0.5 0.1 -0.9', sombras=True),
    'atardecer': dict(ambiente='0.42 0.34 0.28', fondo='0.96 0.72 0.50', sol='1.00 0.72 0.42',
                      dir_sol='0.80 0.40 -0.35', sombras=True),
    'contraluz': dict(ambiente='0.36 0.34 0.32', fondo='0.98 0.90 0.75', sol='1.00 0.90 0.72',
                      dir_sol='-0.85 0.20 -0.40', sombras=True),
    'nublado': dict(ambiente='0.55 0.58 0.65', fondo='0.75 0.78 0.83', sol='0.50 0.55 0.65',
                    dir_sol='-0.2 0.1 -1.0', sombras=False),
    'noche_fria': dict(ambiente='0.06 0.06 0.08', fondo='0.02 0.02 0.04', sol='0.04 0.05 0.08',
                       dir_sol='-0.3 0.2 -1.0', sombras=False, focos='0.43 0.46 0.50'),   # LED ~6500 K
    'noche_calida': dict(ambiente='0.06 0.06 0.08', fondo='0.02 0.02 0.04', sol='0.04 0.05 0.08',
                         dir_sol='-0.3 0.2 -1.0', sombras=False, focos='0.50 0.38 0.25'),  # LED ~3000 K
}


FONDOS = {'blanco': '1 1 1', 'croma': '1 0 1'}   # croma: magenta puro #FF00FF, para recortar


def mundo(luz, fondo='natural'):
    """Escribe el mundo de Gazebo con la iluminación y el fondo pedidos y devuelve su ruta.
    Con fondo blanco o croma: sin suelo, sin sombras y fondo de un solo color (para renders)."""
    l = dict(LUCES[luz])
    if fondo != 'natural':
        l.update(fondo=FONDOS[fondo], sombras=False)
    focos = ''
    if 'focos' in l:
        for i, (y, z) in enumerate([(0.45, 0.45), (-0.45, 0.45), (0.0, 0.75)]):
            d = [0.55 - (-0.1), 0.0 - y, 0.30 - z]
            focos += (f'<light type="spot" name="foco{i}"><pose>-0.1 {y} {z} 0 0 0</pose>'
                      f'<diffuse>{l["focos"]} 1</diffuse><specular>0.3 0.3 0.3 1</specular>'
                      f'<attenuation><range>6</range><constant>0.8</constant><linear>0.3</linear>'
                      f'<quadratic>0.1</quadratic></attenuation><direction>{d[0]} {d[1]} {d[2]}</direction>'
                      f'<spot><inner_angle>0.35</inner_angle><outer_angle>0.9</outer_angle><falloff>1.0</falloff></spot>'
                      f'<cast_shadows>false</cast_shadows></light>')
    sdf = (f'<?xml version="1.0"?><sdf version="1.6"><world name="default">'
           f'<scene><ambient>{l["ambiente"]} 1</ambient><background>{l["fondo"]} 1</background>'
           f'<shadows>{str(l["sombras"]).lower()}</shadows></scene>'
           f'<light type="directional" name="sun"><cast_shadows>{str(l["sombras"]).lower()}</cast_shadows>'
           f'<pose>0 0 10 0 0 0</pose><diffuse>{l["sol"]} 1</diffuse><specular>0.2 0.2 0.2 1</specular>'
           f'<attenuation><range>1000</range><constant>0.9</constant><linear>0.01</linear><quadratic>0.001</quadratic>'
           f'</attenuation><direction>{l["dir_sol"]}</direction></light>{focos}'
           + ('<include><uri>model://ground_plane</uri></include>' if fondo == 'natural' else '')
           + '</world></sdf>')
    carpeta = os.path.expanduser('~/.cache/pika_sim/mundos')
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, f'huerto_{luz}_{fondo}.world')
    with open(ruta, 'w') as f:
        f.write(sdf)
    return ruta


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

    ruta_helios = LaunchConfiguration('ruta_helios').perform(context)
    if not ruta_helios:                                    # el muro frutal por defecto, con la densidad pedida
        densidad = LaunchConfiguration('densidad').perform(context)
        ruta_helios = '~/.cache/pika_sim/manzanos/apple_fruitingwall_e640_s7' + ('' if densidad == 'base' else f'_{densidad}')
    if LaunchConfiguration('escena').perform(context) == 'manzano':
        nodos_modo.append(Node(
            package='pika_sim',
            executable='escena_manzano.py',
            parameters=[{'semilla': int(LaunchConfiguration('semilla').perform(context)),
                         'modelo': LaunchConfiguration('arbol').perform(context),
                         'ruta_helios': ruta_helios,
                         'suelo': LaunchConfiguration('fondo').perform(context) == 'natural'}],
            output='screen',
        ))

    description = {'robot_description': urdf}

    gzserver = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(gazebo_launch_dir, 'gzserver.launch.py')),
        launch_arguments={'world': mundo(LaunchConfiguration('luz').perform(context),
                                         LaunchConfiguration('fondo').perform(context))}.items())
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
        DeclareLaunchArgument('arbol', default_value='primitivas', choices=['primitivas', 'helios']),
        DeclareLaunchArgument('ruta_helios', default_value=''),
        DeclareLaunchArgument('camaras', default_value='true', choices=['true', 'false']),
        DeclareLaunchArgument('luz', default_value='dia', choices=list(LUCES)),
        DeclareLaunchArgument('fondo', default_value='natural', choices=['natural', 'blanco', 'croma']),
        DeclareLaunchArgument('densidad', default_value='base', choices=['base', 'media', 'alta']),
        DeclareLaunchArgument('gui', default_value='true'),
        DeclareLaunchArgument('rviz', default_value='true'),
        OpaqueFunction(function=launch_setup),
    ])
