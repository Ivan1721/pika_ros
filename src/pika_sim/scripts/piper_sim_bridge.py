#!/usr/bin/env python3
# -*-coding:utf8-*-
# Puente entre la cadena de teleop (pika_remote_piper) y el Piper simulado.
#
# Reemplaza al driver CAN (piper_single_ctrl) con el mismo contrato de topics
# que usa start_single_piper.launch.py:
#   entrada  /joint_states_gripper{index}  JointState, 6 joints [rad] + apertura de pinza [m]
#   salida   /joint_states_single{index}   JointState, mismo formato que /puppet/joint_left
#                                          del driver (nombres joint0..joint6)
#
# Hacia Gazebo manda posiciones a los JointGroupPositionController y lee el estado
# de /joint_state_broadcaster/joint_states, reordenandolo por nombre: Gazebo no
# publica las articulaciones en orden 1..6 y piper_FK.py / piper_IK.py leen
# position[:6] asumiendo ese orden.
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Float64MultiArray

ARM_JOINTS = ['joint1', 'joint2', 'joint3', 'joint4', 'joint5', 'joint6']
JAW_LEFT = 'pika_jaw_left_joint'
JAW_RIGHT = 'pika_jaw_right_joint'
# Nombres que publica piper_ctrl_single_node.py en /puppet/joint_left
DRIVER_NAMES = ['joint0', 'joint1', 'joint2', 'joint3', 'joint4', 'joint5', 'joint6']


class PiperSimBridge(Node):
    def __init__(self):
        super().__init__('piper_sim_bridge')
        self.declare_parameter('index_name', '')
        self.declare_parameter('jaw_max', 0.035)  # limite de cada garra en el URDF [m]
        index_name = self.get_parameter('index_name').get_parameter_value().string_value
        self.jaw_max = self.get_parameter('jaw_max').get_parameter_value().double_value

        self.arm_cmd_pub = self.create_publisher(Float64MultiArray, '/arm_controller/commands', 1)
        self.gripper_cmd_pub = self.create_publisher(Float64MultiArray, '/gripper_controller/commands', 1)
        self.feedback_pub = self.create_publisher(JointState, f'/joint_states_single{index_name}', 1)

        self.create_subscription(JointState, f'/joint_states_gripper{index_name}', self.cmd_callback, 1)
        self.create_subscription(JointState, '/joint_state_broadcaster/joint_states', self.sim_state_callback, 1)

        self.warned_short_cmd = False
        self.get_logger().info(
            f'Puente listo: /joint_states_gripper{index_name} -> Gazebo -> /joint_states_single{index_name}')

    def cmd_callback(self, msg):
        if len(msg.position) < 6:
            if not self.warned_short_cmd:
                self.get_logger().warn(f'Comando con {len(msg.position)} posiciones, se esperan 6 o 7; se ignora')
                self.warned_short_cmd = True
            return
        self.arm_cmd_pub.publish(Float64MultiArray(data=[float(p) for p in msg.position[:6]]))

        if len(msg.position) >= 7:
            # Igual que el driver real: apertura total en metros, sin signo
            jaw = min(max(abs(msg.position[6]) / 2.0, 0.0), self.jaw_max)
            self.gripper_cmd_pub.publish(Float64MultiArray(data=[jaw, -jaw]))

    def sim_state_callback(self, msg):
        position = dict(zip(msg.name, msg.position))
        velocity = dict(zip(msg.name, msg.velocity)) if len(msg.velocity) == len(msg.name) else {}
        if not all(j in position for j in ARM_JOINTS):
            return

        opening = position.get(JAW_LEFT, 0.0) - position.get(JAW_RIGHT, 0.0)
        feedback = JointState()
        feedback.header.stamp = self.get_clock().now().to_msg()
        feedback.name = DRIVER_NAMES
        feedback.position = [position[j] for j in ARM_JOINTS] + [opening]
        feedback.velocity = [velocity.get(j, 0.0) for j in ARM_JOINTS] + [0.0]
        feedback.effort = [0.0] * 7
        self.feedback_pub.publish(feedback)


def main():
    rclpy.init()
    node = PiperSimBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
