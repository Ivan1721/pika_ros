#!/usr/bin/env python3
# -*-coding:utf8-*-
# Convierte la profundidad de la D405 simulada al formato del driver real de RealSense.
#
# Gazebo publica 32FC1 en metros (/gripper/camera/depth_sim/image_raw). El driver real publica
# 16UC1 en milímetros, y data_tools (dataCapture.cpp) convierte con cv_bridge a 16UC1 sin
# reescalar: con metros en float guardaría 0 y 1. Este nodo publica
# /gripper/camera/aligned_depth_to_color/image_raw en 16UC1 mm, con 0 donde no hay dato
# (igual que la cámara real), y deja todo lo demás igual.
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image


class ProfundidadMm(Node):
    def __init__(self):
        super().__init__('profundidad_mm')
        self.declare_parameter('entrada', '/gripper/camera/depth_sim/image_raw')
        self.declare_parameter('salida', '/gripper/camera/aligned_depth_to_color/image_raw')
        self.pub = self.create_publisher(Image, self.get_parameter('salida').value, 5)
        self.create_subscription(Image, self.get_parameter('entrada').value, self.convertir,
                                 qos_profile_sensor_data)

    def convertir(self, m):
        if m.encoding != '32FC1':
            self.get_logger().error(f'esperaba 32FC1 y llegó {m.encoding}', throttle_duration_sec=5.0)
            return
        z = np.frombuffer(bytes(m.data), dtype=np.float32).reshape(m.height, m.width)
        mm = np.where(np.isfinite(z) & (z > 0), np.round(z * 1000.0), 0.0)
        out = Image(header=m.header, height=m.height, width=m.width, encoding='16UC1', is_bigendian=0,
                    step=m.width * 2, data=np.clip(mm, 0, 65535).astype(np.uint16).tobytes())
        self.pub.publish(out)


def main():
    rclpy.init()
    nodo = ProfundidadMm()
    try:
        rclpy.spin(nodo)
    except KeyboardInterrupt:
        pass
    finally:
        nodo.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
