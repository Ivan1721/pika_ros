#!/usr/bin/env python3
# -*-coding:utf8-*-
# Sustituto del Pika Sense + tracker Vive para teleoperar sin hardware.
#
# Hace lo mismo que el nodo serial_gripper_imu del Sense en open_sensor_gripper.launch.py:
#   - publica la pose de la mano en /pika_pose{index} (aqui, desde un marcador
#     interactivo 6-DoF en RViz en lugar del tracker Vive)
#   - mezcla la salida de piper_IK.py (/joint_states{index}) con la apertura de
#     la pinza y la publica en /joint_states_gripper{index}
#   - llama a /teleop_trigger{index} para iniciar/detener la teleop (el doble
#     click del Sense); en RViz: click derecho sobre el marcador
#
# La apertura tambien se puede fijar por topic, util para pruebas sin RViz:
#   ros2 topic pub --once /fake_pika_sense/gripper_opening std_msgs/msg/Float64 "{data: 0.05}"
import copy

import rclpy

from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from geometry_msgs.msg import Pose, PoseStamped
from sensor_msgs.msg import JointState
from std_msgs.msg import Float64
from std_srvs.srv import Trigger
from visualization_msgs.msg import InteractiveMarker, InteractiveMarkerControl, Marker
from interactive_markers import InteractiveMarkerServer, MenuHandler

MARKER_NAME = 'pika_sense'
# Partes del Sense en el marco de su base_link (pika_sensor_description de AgileX), con las garras en reposo
SENSE_MALLAS = [('base_link.STL', (0.0, 0.0, 0.0)), ('left_hand_link.STL', (0.0175, 0.0356, -0.0185)),
                ('right_hand_link.STL', (0.0175, -0.0356, -0.0185))]
GRIPPER_PRESETS = [('Pinza: abrir', 0.094), ('Pinza: media', 0.047), ('Pinza: cerrar', 0.0)]   # Pika: 0-94 mm


class FakePikaSense(Node):
    def __init__(self):
        super().__init__('fake_pika_sense')
        self.declare_parameter('index_name', '')
        self.declare_parameter('frame_id', 'world')
        self.declare_parameter('rate', 100.0)  # Hz de /pika_pose
        self.declare_parameter('gripper_opening', 0.094)  # apertura inicial [m]
        self.declare_parameter('initial_xyz', [0.3, 0.0, 0.3])
        index_name = self.get_parameter('index_name').get_parameter_value().string_value
        self.frame_id = self.get_parameter('frame_id').get_parameter_value().string_value
        rate = self.get_parameter('rate').get_parameter_value().double_value
        self.gripper_opening = self.get_parameter('gripper_opening').get_parameter_value().double_value
        xyz = self.get_parameter('initial_xyz').get_parameter_value().double_array_value

        self.pose = Pose()
        self.pose.position.x, self.pose.position.y, self.pose.position.z = xyz
        self.pose.orientation.w = 1.0

        self.pose_pub = self.create_publisher(PoseStamped, f'/pika_pose{index_name}', 1)
        self.merged_pub = self.create_publisher(JointState, f'/joint_states_gripper{index_name}', 1)
        self.create_subscription(JointState, f'/joint_states{index_name}', self.ik_joint_callback, 1)
        self.create_subscription(Float64, '~/gripper_opening', self.gripper_opening_callback, 1)
        self.trigger_client = self.create_client(Trigger, f'/teleop_trigger{index_name}')
        self.create_timer(1.0 / rate, self.publish_pose)

        self.server = InteractiveMarkerServer(self, 'fake_pika_sense')
        self.menu = MenuHandler()
        self.menu.insert('Teleop: iniciar / detener', callback=self.trigger_callback)
        for label, opening in GRIPPER_PRESETS:
            self.menu.insert(label, callback=lambda feedback, o=opening: self.set_gripper(o))
        self.server.insert(self.make_marker(), feedback_callback=self.marker_callback)
        self.menu.apply(self.server, MARKER_NAME)
        self.server.applyChanges()

        self.get_logger().info(
            f'Sense falso listo: /pika_pose{index_name}, /joint_states_gripper{index_name}; '
            f'click derecho sobre el marcador en RViz para teleop/pinza')

    def make_marker(self):
        marker = InteractiveMarker()
        marker.header.frame_id = self.frame_id
        marker.name = MARKER_NAME
        marker.description = 'Pika Sense (simulado)'
        marker.scale = 0.15
        marker.pose = copy.deepcopy(self.pose)

        # Malla del Pika Sense de AgileX (cuerpo y garras), girada 180° en Y para que su eje de
        # herramienta quede en +Z como el del gripper, y centrada en el marcador
        body_control = InteractiveMarkerControl(interaction_mode=InteractiveMarkerControl.MENU, always_visible=True)
        for malla, (x, y, z) in SENSE_MALLAS:
            parte = Marker(type=Marker.MESH_RESOURCE, mesh_resource=f'package://pika_description/meshes/agilex/sense/{malla}')
            parte.scale.x = parte.scale.y = parte.scale.z = 1.0
            parte.pose.position.x, parte.pose.position.y, parte.pose.position.z = -x - 0.048, y, -z + 0.052
            parte.pose.orientation.y, parte.pose.orientation.w = 1.0, 0.0
            parte.color.r, parte.color.g, parte.color.b, parte.color.a = 0.9, 0.5, 0.1, 0.9
            body_control.markers.append(parte)
        marker.controls.append(body_control)

        for name, (w, x, y, z) in {'x': (1.0, 1.0, 0.0, 0.0), 'y': (1.0, 0.0, 0.0, 1.0), 'z': (1.0, 0.0, 1.0, 0.0)}.items():
            for mode, prefix in ((InteractiveMarkerControl.ROTATE_AXIS, 'rotate_'), (InteractiveMarkerControl.MOVE_AXIS, 'move_')):
                control = InteractiveMarkerControl(name=prefix + name, interaction_mode=mode)
                control.orientation.w, control.orientation.x = w, x
                control.orientation.y, control.orientation.z = y, z
                marker.controls.append(control)
        return marker

    def marker_callback(self, feedback):
        self.pose = feedback.pose

    def publish_pose(self):
        msg = PoseStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.frame_id
        msg.pose = self.pose
        self.pose_pub.publish(msg)

    def ik_joint_callback(self, msg):
        # Igual que jointStateInfoHandler en serial_gripper_imu.cpp
        merged = copy.deepcopy(msg)
        merged.position = list(merged.position[:6]) + [0.0] * max(0, 6 - len(merged.position))
        merged.position.append(self.gripper_opening)
        self.merged_pub.publish(merged)

    def set_gripper(self, opening):
        self.gripper_opening = opening
        self.get_logger().info(f'Apertura de pinza: {opening:.3f} m')

    def gripper_opening_callback(self, msg):
        self.set_gripper(msg.data)

    def trigger_callback(self, feedback):
        if not self.trigger_client.service_is_ready():
            self.get_logger().warn('/teleop_trigger no disponible: lanza teleop_rand_single_piper.launch.py')
            return
        future = self.trigger_client.call_async(Trigger.Request())
        future.add_done_callback(
            lambda f: self.get_logger().info(f'teleop_trigger -> {f.result().message or f.result().success}'))


def main():
    rclpy.init()
    node = FakePikaSense()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
