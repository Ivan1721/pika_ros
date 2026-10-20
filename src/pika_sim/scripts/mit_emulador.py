#!/usr/bin/env python3
# -*-coding:utf8-*-
# Emulador del modo MIT (control de impedancia) del Piper en Gazebo.
#
# En el brazo real cada motor aplica
#   tau = kp*(q_d - q) + kd*(0 - dq) + t_ref
# En pika_sim (control:=mit) los dos primeros terminos los integra Gazebo
# como un resorte + amortiguador implicitos en cada articulacion (estables
# aunque la muneca tenga inercias minimas). Este nodo agrega el tercero:
# manda t_ref = escala_gravedad * t_ff por /mit_ff_controller/commands.
#
# Los valores (kp, kd, q_d, t_ff, escala) salen de
# scripts/test_piper_mit_impedance.py: sim_piper_single.launch.py los lee y
# los pasa como parametros, asi la simulacion prueba lo mismo que el script.
#
# Perturbacion: torque extra por articulacion, como empujar con la mano.
# La desviacion en equilibrio deberia ser perturbacion / kp:
#   ros2 topic pub --once /mit_emulador/perturbacion std_msgs/msg/Float64MultiArray \
#     "{data: [0, 1.0, 0, 0, 0, 0]}"
import math

import rclpy

from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Float64MultiArray

JOINTS = ['joint1', 'joint2', 'joint3', 'joint4', 'joint5', 'joint6']
T_MAX = 8.0  # el protocolo MIT codifica t_ref en [-8, 8] N·m


class MitEmulador(Node):
    def __init__(self):
        super().__init__('mit_emulador')
        self.declare_parameter('kp', [0.0] * 6)
        self.declare_parameter('targets', [0.0] * 6)
        self.declare_parameter('t_ff', [0.0] * 6)
        self.declare_parameter('escala_gravedad', 1.0)
        self.kp = list(self.get_parameter('kp').get_parameter_value().double_array_value)
        self.targets = list(self.get_parameter('targets').get_parameter_value().double_array_value)
        t_ff = self.get_parameter('t_ff').get_parameter_value().double_array_value
        escala = self.get_parameter('escala_gravedad').get_parameter_value().double_value
        self.t_ref = [escala * t for t in t_ff]
        self.perturbacion = [0.0] * 6
        self.q = None

        self.ff_pub = self.create_publisher(Float64MultiArray, '/mit_ff_controller/commands', 1)
        self.create_subscription(JointState, '/joint_state_broadcaster/joint_states', self.estado_callback, 1)
        self.create_subscription(Float64MultiArray, '~/perturbacion', self.perturbacion_callback, 1)
        self.create_timer(0.1, self.publicar)
        self.create_timer(2.0, self.reportar)
        self.get_logger().info(
            f'MIT emulado: q_d={self.targets} kp={self.kp} t_ref={[round(t, 3) for t in self.t_ref]} '
            f'(escala_gravedad {escala})')

    def estado_callback(self, msg):
        posicion = dict(zip(msg.name, msg.position))
        if all(j in posicion for j in JOINTS):
            self.q = [posicion[j] for j in JOINTS]

    def perturbacion_callback(self, msg):
        if len(msg.data) != 6:
            self.get_logger().warn('La perturbacion necesita 6 valores (N·m por articulacion)')
            return
        self.perturbacion = list(msg.data)
        esperado = [p / k if k > 0 else float('nan') for p, k in zip(self.perturbacion, self.kp)]
        self.get_logger().info(
            f'Perturbacion {self.perturbacion} N·m; desviacion esperada '
            f'{[round(math.degrees(e), 1) for e in esperado]} grados')

    def publicar(self):
        tau = [max(-T_MAX, min(T_MAX, t)) + p for t, p in zip(self.t_ref, self.perturbacion)]
        self.ff_pub.publish(Float64MultiArray(data=tau))

    def reportar(self):
        if self.q is None:
            return
        error = [math.degrees(q - qd) for q, qd in zip(self.q, self.targets)]
        self.get_logger().info(f'q - q_d [grados]: {[round(e, 1) for e in error]}')


def main():
    rclpy.init()
    node = MitEmulador()
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
