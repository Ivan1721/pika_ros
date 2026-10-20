#!/usr/bin/env python3
# -*-coding:utf8-*-
# Escena de demostración de next-best-view en pika_sim: fruta ocluida por hojas, vistas
# candidatas en un casquete y el Piper llevado a la mejor vista alcanzable. Toma capturas con
# cámaras virtuales de Gazebo para documentación (no es todavía el planner del paso 4).
#
# Qué calcula, sin datos inventados:
#   - visibilidad de cada candidata: fracción de la superficie de la fruta (mirando a la cámara)
#     cuyo rayo hasta la cámara no cruza ninguna hoja (geometría conocida = política B ideal)
#   - alcanzabilidad: IK de la D405 (posición + eje óptico hacia la fruta) sobre el URDF que
#     publica robot_state_publisher; se acepta con error < 5 mm y < 3°, y |J5| > 10° (fuera
#     de la singularidad de muñeca)
# Supuesto: la D405 mira a lo largo de +Z de gripper_base (eje de la herramienta).
#
# Uso, con la simulación corriendo (sin conda):
#   ros2 launch pika_sim sim_piper_single.launch.py gui:=false rviz:=false
#   ros2 run pika_sim escena_nbv_demo.py --salida ~/pika_ros/docs/percepcion_activa/img
import argparse
import json
import math
import os
import time
import xml.etree.ElementTree as ET

import numpy as np
import rclpy
from gazebo_msgs.srv import SpawnEntity
from PIL import Image as PILImage
from rcl_interfaces.srv import GetParameters
from rclpy.node import Node
from scipy.optimize import least_squares
from sensor_msgs.msg import Image
from std_msgs.msg import Float64MultiArray

ARM = ['joint1', 'joint2', 'joint3', 'joint4', 'joint5', 'joint6']

# ── Escena (metros, marco del mundo = base del Piper) ──
FRUTA = np.array([0.55, 0.0, 0.30])
R_FRUTA = 0.04
# Hojas: discos (centro, normal, radio) entre el robot y la fruta, que tapan la vista frontal
HOJAS = [((0.485, 0.020, 0.315), (1.0, 0.15, 0.25), 0.050),
         ((0.490, -0.035, 0.285), (1.0, -0.25, -0.10), 0.045),
         ((0.525, 0.000, 0.355), (0.45, 0.0, 1.0), 0.045)]
RAMA = ((0.62, 0.0, 0.0), (0.62, 0.0, 0.42), 0.012)          # tallo vertical detrás de la fruta
# Candidatas: casquete de radio R alrededor de la fruta, del lado del robot
R_VISTA = 0.22
ELEVACIONES = [-15, 10, 35, 60]
AZIMUTS = [-50, -25, 0, 25, 50]                                # respecto de la dirección fruta → robot


# ── Cinemática directa sobre el URDF ──
def rpy(r, p, y):
    cr, sr, cp, sp, cy, sy = np.cos(r), np.sin(r), np.cos(p), np.sin(p), np.cos(y), np.sin(y)
    return np.array([[cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr],
                     [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr],
                     [-sp, cp * sr, cp * cr]])


def eje_angulo(a, t):
    a = a / np.linalg.norm(a)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + np.sin(t) * K + (1 - np.cos(t)) * K @ K


class Cinematica:
    def __init__(self, urdf):
        raiz = ET.fromstring(urdf)
        self.juntas = []
        self.limites = {}
        for j in raiz.findall('joint'):
            o = j.find('origin')
            M = np.eye(4)
            if o is not None:
                M[:3, :3] = rpy(*[float(v) for v in (o.get('rpy') or '0 0 0').split()])
                M[:3, 3] = [float(v) for v in (o.get('xyz') or '0 0 0').split()]
            eje = j.find('axis')
            self.juntas.append((j.get('name'), j.get('type'), j.find('parent').get('link'),
                                j.find('child').get('link'), M,
                                np.array([float(v) for v in eje.get('xyz').split()]) if eje is not None
                                else np.array([1.0, 0, 0])))
            lim = j.find('limit')
            if lim is not None:
                self.limites[j.get('name')] = (float(lim.get('lower')), float(lim.get('upper')))

    def poses(self, q):
        T = {'world': np.eye(4)}
        cambio = True
        while cambio:
            cambio = False
            for nombre, tipo, padre, hijo, M, eje in self.juntas:
                if padre in T and hijo not in T:
                    J = np.eye(4)
                    if tipo == 'revolute':
                        J[:3, :3] = eje_angulo(eje, q.get(nombre, 0.0))
                    T[hijo] = T[padre] @ M @ J
                    cambio = True
        return T

    def camara(self, q6):
        T = self.poses(dict(zip(ARM, q6)))
        return T['pika_depth_link'][:3, 3], T['gripper_base'][:3, 2]

    def ik_camara(self, c, d, semillas):
        lo = np.array([self.limites[n][0] for n in ARM])
        hi = np.array([self.limites[n][1] for n in ARM])

        def residuo(q):
            p, z = self.camara(q)
            return np.r_[p - c, 0.3 * (z - d), 0.002 * q]

        mejor = None
        for s in semillas:
            r = least_squares(residuo, np.clip(s, lo + 1e-3, hi - 1e-3), bounds=(lo, hi))
            p, z = self.camara(r.x)
            err_p = np.linalg.norm(p - c)
            err_a = math.degrees(math.acos(np.clip(z @ d, -1, 1)))
            if mejor is None or err_p + err_a / 100 < mejor[1] + mejor[2] / 100:
                mejor = (r.x, err_p, err_a)
        return mejor


# ── Visibilidad por trazado de rayos contra las hojas ──
def visibilidad(c, n=600, seed=0):
    rng = np.random.default_rng(seed)
    v = rng.normal(size=(n, 3))
    v /= np.linalg.norm(v, axis=1, keepdims=True)
    pts = FRUTA + R_FRUTA * v
    hacia = (c - pts)
    frente = (v * hacia).sum(1) > 0
    visibles = 0
    for p, ok in zip(pts, frente):
        if not ok:
            continue
        tapado = False
        for centro, normal, radio in HOJAS:
            centro, normal = np.array(centro), np.array(normal) / np.linalg.norm(normal)
            den = normal @ (c - p)
            if abs(den) < 1e-9:
                continue
            t = normal @ (centro - p) / den
            if 0 < t < 1 and np.linalg.norm(p + t * (c - p) - centro) < radio:
                tapado = True
                break
        visibles += not tapado
    return visibles / max(1, frente.sum())


def candidatas():
    base = math.atan2(-FRUTA[1], -FRUTA[0])     # dirección fruta → robot
    out = []
    for e in ELEVACIONES:
        for a in AZIMUTS:
            az, el = base + math.radians(a), math.radians(e)
            c = FRUTA + R_VISTA * np.array([math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)])
            out.append({'elevacion': e, 'azimut': a, 'c': c, 'd': (FRUTA - c) / np.linalg.norm(FRUTA - c)})
    return out


# ── SDF ──
def pose_mirando(origen, objetivo):
    """roll pitch yaw de un marco cuyo +X apunta de origen a objetivo (cámaras de Gazebo)."""
    d = np.array(objetivo) - np.array(origen)
    yaw = math.atan2(d[1], d[0])
    pitch = -math.atan2(d[2], math.hypot(d[0], d[1]))
    return f'{origen[0]} {origen[1]} {origen[2]} 0 {pitch} {yaw}'


def material(rgba):
    return f'<material><ambient>{rgba}</ambient><diffuse>{rgba}</diffuse></material>'


def cilindro_entre(nombre, p0, p1, radio, rgba, sombra=True):
    p0, p1 = np.array(p0), np.array(p1)
    d = p1 - p0
    largo = np.linalg.norm(d)
    z = d / largo
    pitch = math.acos(np.clip(z[2], -1, 1))
    yaw = math.atan2(z[1], z[0])
    m = (p0 + p1) / 2
    return (f'<link name="{nombre}"><pose>{m[0]} {m[1]} {m[2]} 0 {pitch} {yaw}</pose><visual name="v">'
            f'<cast_shadows>{str(sombra).lower()}</cast_shadows><geometry><cylinder><radius>{radio}</radius><length>{largo}</length></cylinder></geometry>'
            f'{material(rgba)}</visual></link>')


def disco(nombre, centro, normal, radio, rgba):
    n = np.array(normal) / np.linalg.norm(normal)
    pitch = math.acos(np.clip(n[2], -1, 1))
    yaw = math.atan2(n[1], n[0])
    return (f'<link name="{nombre}"><pose>{centro[0]} {centro[1]} {centro[2]} 0 {pitch} {yaw}</pose>'
            f'<visual name="v"><geometry><cylinder><radius>{radio}</radius><length>0.004</length></cylinder>'
            f'</geometry>{material(rgba)}</visual></link>')


def esfera(nombre, c, radio, rgba, sombra=True):
    return (f'<link name="{nombre}"><pose>{c[0]} {c[1]} {c[2]} 0 0 0</pose><visual name="v">'
            f'<cast_shadows>{str(sombra).lower()}</cast_shadows>'
            f'<geometry><sphere><radius>{radio}</radius></sphere></geometry>{material(rgba)}</visual></link>')


def sdf_modelo(nombre, links):
    return f'<?xml version="1.0"?><sdf version="1.6"><model name="{nombre}"><static>true</static>{links}</model></sdf>'


def sdf_camara(nombre, pose, hfov, ancho, alto):
    return (f'<?xml version="1.0"?><sdf version="1.6"><model name="{nombre}"><static>true</static>'
            f'<link name="l"><pose>{pose}</pose><sensor name="s" type="camera"><update_rate>5</update_rate>'
            f'<camera><horizontal_fov>{hfov}</horizontal_fov><image><width>{ancho}</width><height>{alto}</height>'
            f'<format>R8G8B8</format></image><clip><near>0.02</near><far>20</far></clip></camera>'
            f'<plugin name="p" filename="libgazebo_ros_camera.so"><ros><namespace>/{nombre}</namespace></ros>'
            f'<camera_name>cam</camera_name></plugin></sensor></link></model></sdf>')


def color_visibilidad(v, alcanzable):
    """Inalcanzable: gris claro. Alcanzable: de grafito (nada visible) a rojo AgileX (todo visible)."""
    if not alcanzable:
        return '0.80 0.80 0.78 1'
    grafito, rojo = np.array([0.33, 0.35, 0.36]), np.array([0.85, 0.12, 0.18])
    c = grafito + (rojo - grafito) * min(1.0, v / 0.6)
    return f'{c[0]:.3f} {c[1]:.3f} {c[2]:.3f} 1'


class Demo(Node):
    def __init__(self):
        super().__init__('escena_nbv_demo')
        self.spawn = self.create_client(SpawnEntity, '/spawn_entity')
        self.arm = self.create_publisher(Float64MultiArray, '/arm_controller/commands', 1)
        self.grip = self.create_publisher(Float64MultiArray, '/gripper_controller/commands', 1)

    def urdf(self):
        cli = self.create_client(GetParameters, '/robot_state_publisher/get_parameters')
        cli.wait_for_service(timeout_sec=10)
        fut = cli.call_async(GetParameters.Request(names=['robot_description']))
        rclpy.spin_until_future_complete(self, fut, timeout_sec=10)
        return fut.result().values[0].string_value

    def spawnear(self, nombre, xml):
        self.spawn.wait_for_service(timeout_sec=10)
        fut = self.spawn.call_async(SpawnEntity.Request(name=nombre, xml=xml))
        rclpy.spin_until_future_complete(self, fut, timeout_sec=20)
        self.get_logger().info(f'{nombre}: {fut.result().status_message}')

    def foto(self, nombre, ruta, timeout=20.0):
        llegada = {}
        sub = self.create_subscription(Image, f'/{nombre}/cam/image_raw', lambda m: llegada.setdefault('m', m), 1)
        t0 = time.time()
        while 'm' not in llegada and time.time() - t0 < timeout:
            rclpy.spin_once(self, timeout_sec=0.2)
        self.destroy_subscription(sub)
        if 'm' not in llegada:
            self.get_logger().error(f'sin imagen de {nombre}')
            return False
        m = llegada['m']
        PILImage.frombytes('RGB', (m.width, m.height), bytes(m.data)).save(ruta)
        self.get_logger().info(f'guardada {ruta}')
        return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--salida', default=os.path.expanduser('~/pika_ros/docs/percepcion_activa/img'))
    args, _ = ap.parse_known_args()
    os.makedirs(args.salida, exist_ok=True)

    rclpy.init()
    node = Demo()
    kin = Cinematica(node.urdf())

    # 1. Candidatas: visibilidad y alcanzabilidad
    semillas = [np.array([0, 1.4, -1.25, 0, 0.6, 0]), np.array([0, 1.0, -1.6, 0, 0.9, 0]),
                np.array([0, 1.8, -1.0, 0, 0.3, 0]), np.array([0, 1.2, -1.4, 0.4, 0.7, 0]),
                np.array([0, 1.2, -1.4, -0.4, 0.7, 0]), np.array([0, 0.8, -0.8, 0, -0.6, 0])]
    cands = candidatas()
    for k in cands:
        k['visibilidad'] = visibilidad(k['c'])
        j1 = math.atan2(k['c'][1], k['c'][0])
        q, ep, ea = kin.ik_camara(k['c'], k['d'], [s + np.r_[j1, 0, 0, 0, 0, 0] for s in semillas])
        k.update(q=q, error_pos_mm=ep * 1000, error_ang_deg=ea)
        k['alcanzable'] = bool(ep < 0.005 and ea < 3.0 and abs(q[4]) > math.radians(10))
    alcanzables = [k for k in cands if k['alcanzable']]
    mejor = max(alcanzables, key=lambda k: k['visibilidad'])
    frontal = min(cands, key=lambda k: abs(k['elevacion'] - 10) + abs(k['azimut']))
    node.get_logger().info(f'{len(alcanzables)}/{len(cands)} alcanzables; mejor: elev {mejor["elevacion"]}°, '
                           f'azim {mejor["azimut"]}°, visibilidad {mejor["visibilidad"]:.0%}; '
                           f'frontal: {frontal["visibilidad"]:.0%}')

    # 2. Escena: rama, fruta y hojas (solo visuales, sin colisión)
    links = cilindro_entre('rama', RAMA[0], RAMA[1], RAMA[2], '0.42 0.30 0.20 1')
    links += cilindro_entre('pedunculo', (0.62, 0.0, 0.36), FRUTA + [0.0, 0.0, R_FRUTA * 0.8], 0.004, '0.42 0.30 0.20 1')
    links += esfera('fruta', FRUTA, R_FRUTA, '0.80 0.12 0.10 1')
    for i, (c, n, r) in enumerate(HOJAS):
        links += disco(f'hoja{i}', c, n, r, '0.20 0.55 0.18 1')
    node.spawnear('escena_fruta', sdf_modelo('escena_fruta', links))

    # 3. Lo que vería la cámara desde la vista frontal y desde la elegida (brazo plegado y sin
    #    marcadores, para que solo se vea la oclusión por las hojas)
    for _ in range(20):
        node.arm.publish(Float64MultiArray(data=[0.0] * 6))
        rclpy.spin_once(node, timeout_sec=0.1)
    time.sleep(3.0)
    node.spawnear('cam_frontal', sdf_camara('cam_frontal', pose_mirando(frontal['c'], FRUTA), 1.52, 848, 480))
    node.spawnear('cam_elegida', sdf_camara('cam_elegida', pose_mirando(mejor['c'], FRUTA), 1.52, 848, 480))
    time.sleep(2.0)
    node.foto('cam_frontal', os.path.join(args.salida, 'nbv_vista_frontal.png'))
    node.foto('cam_elegida', os.path.join(args.salida, 'nbv_vista_elegida.png'))

    # 4. Candidatas y brazo en la mejor vista (pinza abierta), y la foto de la escena completa
    vis = ''
    for i, k in enumerate(cands):
        col = color_visibilidad(k['visibilidad'], k['alcanzable'])
        radio = 0.018 if k is mejor else (0.011 if k['alcanzable'] else 0.007)
        grosor = 0.0035 if k is mejor else (0.0020 if k['alcanzable'] else 0.0012)
        vis += esfera(f'c{i}', k['c'], radio, col, sombra=False)
        vis += cilindro_entre(f'r{i}', k['c'], k['c'] + (R_VISTA - 0.06) * k['d'], grosor, col, sombra=False)
    node.spawnear('vistas_candidatas', sdf_modelo('vistas_candidatas', vis))
    for _ in range(20):
        node.arm.publish(Float64MultiArray(data=[float(v) for v in mejor['q']]))
        node.grip.publish(Float64MultiArray(data=[0.03, -0.03]))
        rclpy.spin_once(node, timeout_sec=0.1)
    time.sleep(3.0)
    node.spawnear('cam_escena', sdf_camara('cam_escena', pose_mirando((0.18, -1.05, 0.78), (0.38, 0.0, 0.26)), 0.85, 1600, 1000))
    time.sleep(2.0)
    node.foto('cam_escena', os.path.join(args.salida, 'nbv_escena.png'))

    resumen = {'fruta': FRUTA.tolist(), 'radio_fruta': R_FRUTA, 'radio_casquete': R_VISTA,
               'candidatas': [{'elevacion': k['elevacion'], 'azimut': k['azimut'],
                               'visibilidad': round(k['visibilidad'], 3), 'alcanzable': k['alcanzable'],
                               'error_pos_mm': round(k['error_pos_mm'], 2),
                               'error_ang_deg': round(k['error_ang_deg'], 2),
                               'q': [round(float(v), 4) for v in k['q']]} for k in cands],
               'mejor': {'elevacion': mejor['elevacion'], 'azimut': mejor['azimut'],
                         'visibilidad': round(mejor['visibilidad'], 3)},
               'frontal': {'elevacion': frontal['elevacion'], 'azimut': frontal['azimut'],
                           'visibilidad': round(frontal['visibilidad'], 3)}}
    with open(os.path.join(args.salida, 'nbv_escena.json'), 'w') as f:
        json.dump(resumen, f, indent=1, ensure_ascii=False)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
