#!/usr/bin/env python3
# -*-coding:utf8-*-
# Render de alta resolución de la simulación con una cámara virtual de Gazebo, para figuras.
#
# Más limpio que una captura de gzclient: la imagen no depende del tamaño de la ventana, y cada
# render queda anotado en un camaras.json (posición, punto mirado, campo visual, resolución, pose
# del brazo y datos de la escena) para poder repetirlo.
#
#   ros2 run pika_sim render_camara.py --salida G1.png --pos -0.7 0.8 0.8 --mira 0.35 0 0.25 \
#       --hfov 0.9 --res 3000x2000 [--q j1 j2 j3 j4 j5 j6] [--pinza 0.047] [--fruta x y z r] \
#       [--escena '{"luz": "dia", "fondo": "blanco"}']
#
# --q y --pinza mueven el brazo antes de la foto (posición directa, modo teleop de pika_sim).
# --fruta pone una esfera ámbar (#EDA100) como fruta. Con --hfov chico y la cámara lejos, la
# vista se acerca a una ortográfica.
import argparse
import json
import math
import os
import time

import numpy as np
import rclpy
from gazebo_msgs.srv import DeleteEntity, SpawnEntity
from PIL import Image as PILImage
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Float64MultiArray

AMBAR = '0.929 0.631 0.0 1'


def rpy_mirando(pos, mira):
    d = np.asarray(mira, float) - np.asarray(pos, float)
    return 0.0, -math.atan2(d[2], math.hypot(d[0], d[1])), math.atan2(d[1], d[0])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--salida', required=True)
    ap.add_argument('--pos', type=float, nargs=3, required=True)
    ap.add_argument('--mira', type=float, nargs=3, required=True)
    ap.add_argument('--hfov', type=float, default=1.0)
    ap.add_argument('--res', default='1920x1280')
    ap.add_argument('--q', type=float, nargs=6)
    ap.add_argument('--pinza', type=float, help='apertura de cada garra [m] (0 a 0,047)')
    ap.add_argument('--fruta', type=float, nargs=4, metavar=('X', 'Y', 'Z', 'R'))
    ap.add_argument('--escena', default='{}', help='JSON con datos de la escena para camaras.json')
    ap.add_argument('--etiqueta', default='')
    args, _ = ap.parse_known_args()
    ancho, alto = (int(v) for v in args.res.lower().split('x'))
    os.makedirs(os.path.dirname(os.path.abspath(args.salida)), exist_ok=True)

    rclpy.init()
    nodo = Node('render_camara')
    spawn = nodo.create_client(SpawnEntity, '/spawn_entity')
    borrar = nodo.create_client(DeleteEntity, '/delete_entity')
    spawn.wait_for_service(timeout_sec=30)
    borrar.wait_for_service(timeout_sec=30)

    def llamar(cli, req):
        fut = cli.call_async(req)
        rclpy.spin_until_future_complete(nodo, fut, timeout_sec=30)
        return fut.result()

    if args.q is not None or args.pinza is not None:
        brazo = nodo.create_publisher(Float64MultiArray, '/arm_controller/commands', 1)
        pinza = nodo.create_publisher(Float64MultiArray, '/gripper_controller/commands', 1)
        for _ in range(30):
            if args.q is not None:
                brazo.publish(Float64MultiArray(data=[float(v) for v in args.q]))
            if args.pinza is not None:
                pinza.publish(Float64MultiArray(data=[args.pinza, -args.pinza]))
            rclpy.spin_once(nodo, timeout_sec=0.1)
        time.sleep(3.0)
    if args.fruta:
        x, y, z, r = args.fruta
        llamar(borrar, DeleteEntity.Request(name='render_fruta'))
        llamar(spawn, SpawnEntity.Request(name='render_fruta', xml=(
            f'<?xml version="1.0"?><sdf version="1.6"><model name="render_fruta"><static>true</static>'
            f'<link name="l"><pose>{x} {y} {z} 0 0 0</pose><visual name="v"><geometry><sphere><radius>{r}</radius>'
            f'</sphere></geometry><material><ambient>{AMBAR}</ambient><diffuse>{AMBAR}</diffuse></material>'
            f'</visual></link></model></sdf>')))

    nombre = f'render_cam_{os.getpid()}'
    rr, pp, yy = rpy_mirando(args.pos, args.mira)
    x, y, z = args.pos
    sdf = (f'<?xml version="1.0"?><sdf version="1.6"><model name="{nombre}"><static>true</static>'
           f'<link name="l"><pose>{x} {y} {z} {rr} {pp} {yy}</pose><sensor name="s" type="camera">'
           f'<update_rate>2</update_rate><camera><horizontal_fov>{args.hfov}</horizontal_fov>'
           f'<image><width>{ancho}</width><height>{alto}</height><format>R8G8B8</format></image>'
           f'<clip><near>0.01</near><far>30</far></clip></camera>'
           f'<plugin name="p" filename="libgazebo_ros_camera.so"><ros><namespace>/{nombre}</namespace></ros>'
           f'<camera_name>cam</camera_name></plugin></sensor></link></model></sdf>')
    llamar(spawn, SpawnEntity.Request(name=nombre, xml=sdf))
    llegadas = []
    sub = nodo.create_subscription(Image, f'/{nombre}/cam/image_raw', llegadas.append, 1)
    t0 = time.time()
    while len(llegadas) < 3 and time.time() - t0 < 60:        # la tercera: escena ya asentada
        rclpy.spin_once(nodo, timeout_sec=0.2)
    nodo.destroy_subscription(sub)
    llamar(borrar, DeleteEntity.Request(name=nombre))
    if not llegadas:
        nodo.get_logger().error('sin imagen de la cámara de render')
        raise SystemExit(1)
    m = llegadas[-1]
    PILImage.frombytes('RGB', (m.width, m.height), bytes(m.data)).save(args.salida)

    # anotación para repetir el render
    ruta_json = os.path.join(os.path.dirname(os.path.abspath(args.salida)), 'camaras.json')
    try:
        registro = json.load(open(ruta_json))
    except (OSError, ValueError):
        registro = {}
    registro[os.path.basename(args.salida)] = {
        'etiqueta': args.etiqueta, 'escena': json.loads(args.escena),
        'camara': {'posicion_m': list(args.pos), 'mira_a_m': list(args.mira),
                   'rpy_rad': [round(rr, 5), round(pp, 5), round(yy, 5)], 'hfov_rad': args.hfov,
                   'resolucion_px': [ancho, alto]},
        'brazo_q_rad': list(args.q) if args.q is not None else None, 'pinza_m': args.pinza,
        'fruta_xyzr_m': list(args.fruta) if args.fruta else None,
        'generado': time.strftime('%Y-%m-%d %H:%M:%S')}
    with open(ruta_json, 'w') as f:
        json.dump(registro, f, indent=1, ensure_ascii=False)
    nodo.get_logger().info(f'{args.salida}: {m.width}×{m.height}')
    nodo.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
