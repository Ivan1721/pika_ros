#!/usr/bin/env python3
# -*-coding:utf8-*-
# Escena de demostración de next-best-view en pika_sim: fruta ocluida por hojas, vistas
# candidatas en un casquete y el Piper llevado a la mejor vista alcanzable. Toma capturas con
# cámaras virtuales de Gazebo para documentación (no es todavía el planner del paso 4).
#
# Qué calcula, sin datos inventados:
#   - visibilidad de cada candidata: fracción de la fruta que vería la cámara (puntos repartidos
#     sobre el disco que ocupa en la imagen) cuyo rayo hasta la cámara no cruza ninguna hoja
#     (geometría conocida = política B ideal)
#   - alcanzabilidad: IK de la D405 (posición + eje óptico hacia la fruta) sobre el URDF que
#     publica robot_state_publisher; se acepta con error < 5 mm y < 3°, y |J5| > 10° (fuera
#     de la singularidad de muñeca)
# Supuesto: la D405 mira a lo largo de +Z de gripper_base (eje de la herramienta).
#
# Escenas (--escena):
#   manzano (por defecto)  tronco, ramas, follaje aleatorio con semilla fija y varias manzanas; la
#                          manzana objetivo queda detrás de un racimo de hojas
#   prueba                 una fruta, tres hojas en disco y un tallo (la primera escena de prueba)
# En la visibilidad cuentan las hojas y las otras frutas; ramas y tronco no. Con el manzano de Helios
# (lanzado con escena:=manzano arbol:=helios) se trazan rayos contra los triángulos reales de hojas
# y madera, y los archivos salen con el prefijo nbv_helios.
#
# Uso, con la simulación corriendo (sin conda); con escena:=manzano la demo usa ese árbol
# (/escena/verdad) en vez de spawnear el suyo, y guarda lo que ven la D405 y la fisheye del gripper:
#   ros2 launch pika_sim sim_piper_single.launch.py gui:=false rviz:=false escena:=manzano
#   ros2 run pika_sim escena_nbv_demo.py [--escena manzano|prueba] [--semilla N] [--radio R] [--despeje D] \
#       --salida ~/pika_ros/docs/percepcion_activa/img
import argparse
import json
import math
import os
import time
import xml.etree.ElementTree as ET

import numpy as np
import rclpy
from gazebo_msgs.srv import DeleteEntity, SpawnEntity
from PIL import Image as PILImage
from rcl_interfaces.srv import GetParameters
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile
from scipy.optimize import least_squares
from sensor_msgs.msg import Image
from std_msgs.msg import Float64MultiArray, String

import escena_manzano

ARM = ['joint1', 'joint2', 'joint3', 'joint4', 'joint5', 'joint6']

# ── Escena (metros, marco del mundo = base del Piper) ──
FRUTA = np.array([0.55, 0.0, 0.30])
R_FRUTA = 0.04
# Hojas: discos (centro, normal, radio) entre el robot y la fruta, que tapan la vista frontal
HOJAS = [((0.485, 0.020, 0.315), (1.0, 0.15, 0.25), 0.050),
         ((0.490, -0.035, 0.285), (1.0, -0.25, -0.10), 0.045),
         ((0.525, 0.000, 0.355), (0.45, 0.0, 1.0), 0.045)]
RAMA = ((0.62, 0.0, 0.0), (0.62, 0.0, 0.42), 0.012)          # tallo vertical detrás de la fruta
RAMAS = [RAMA, ((0.62, 0.0, 0.36), tuple(FRUTA + [0.0, 0.0, R_FRUTA * 0.8]), 0.004)]   # + pedúnculo
OTRAS = []                                                    # otras frutas: (centro, radio)
TRIS = None                                                   # manzano de Helios: triángulos de hojas y madera
MADERA = None                                                 # manzano de Helios: vértices de tronco y ramas
DESPEJE = 0.03                                                # distancia mínima de cámara y garras a la madera
MODELO = 'primitivas'
COLOR_FRUTA, COLOR_HOJA, COLOR_MADERA = '0.80 0.12 0.10 1', '0.20 0.55 0.18 1', '0.42 0.30 0.20 1'
# Candidatas: casquete de radio R alrededor de la fruta, del lado del robot
R_VISTA = 0.22
ELEVACIONES = [-15, 10, 35, 60]
AZIMUTS = [-50, -25, 0, 25, 50]                                # respecto de la dirección fruta → robot


def usar_escena(verdad):
    """Toma la escena del manzano (dict de /escena/verdad o de escena_manzano.generar)."""
    global FRUTA, R_FRUTA, HOJAS, RAMAS, OTRAS, COLOR_FRUTA, COLOR_HOJA, TRIS, MODELO, MADERA
    manzanas = verdad['manzanas']
    objetivo = next(m for m in manzanas if m['objetivo'])
    FRUTA, R_FRUTA = np.array(objetivo['centro']), objetivo['radio']
    OTRAS = [(np.array(m['centro']), m['radio']) for m in manzanas if not m['objetivo']]
    HOJAS = [(tuple(h['centro']), tuple(h['normal']), h['radio']) for h in verdad['hojas']]
    RAMAS = [(tuple(r['p0']), tuple(r['p1']), r['radio']) for r in verdad['ramas']]
    COLOR_FRUTA, COLOR_HOJA = escena_manzano.COLOR_FRUTA, escena_manzano.COLOR_HOJA
    MODELO = verdad.get('modelo', 'primitivas')
    if MODELO == 'helios':                                    # hojas y ramas reales: triángulos
        datos = np.load(verdad['triangulos'])
        tris = np.concatenate([datos['hojas'], datos['madera']]).astype(float)
        R, t = np.array(verdad['arbol_a_world']['R']), np.array(verdad['arbol_a_world']['t'])
        TRIS = tris @ R.T + t
        # choques solo contra tronco y ramas: pecíolos y pedúnculos ceden
        madera = datos['ramas' if 'ramas' in datos else 'madera'].astype(float) @ R.T + t   # (N, 3, 3)
        madera = madera[np.linalg.norm(madera.mean(1) - FRUTA, axis=1) < 0.6]
        # puntos sobre cada triángulo (malla baricéntrica de paso 1/4): los tubos de las ramas
        # tienen triángulos largos y sus vértices solos no bastan para medir la distancia
        w = np.array([(i, j, 4 - i - j) for i in range(5) for j in range(5 - i)], float) / 4
        MADERA = np.einsum('kb,nbd->nkd', w, madera).reshape(-1, 3)
        OTRAS = [(c, r) for c, r in OTRAS if np.linalg.norm(c - FRUTA) < 1.0]   # las cercanas bastan


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
    if TRIS is not None:
        return escena_manzano.fraccion_visible(FRUTA, R_FRUTA, c, TRIS, OTRAS, n=n, seed=seed)
    # primitivas: hojas en disco y otras frutas; mismo muestreo de la fruta que con Helios
    pts = escena_manzano.muestras_fruta(FRUTA, R_FRUTA, c, n, seed)
    visibles = 0
    for p in pts:
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
        for centro, radio in ([] if tapado else OTRAS):         # otras frutas por delante
            d = c - p
            f = p - centro
            b, cc = f @ d, f @ f - radio ** 2
            disc = b * b - (d @ d) * cc
            if disc > 0 and 0 < (-b - math.sqrt(disc)) / (d @ d) < 1:
                tapado = True
                break
        visibles += not tapado
    return visibles / max(1, len(pts))


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


material = escena_manzano._material
cilindro_entre, disco, esfera = escena_manzano.cilindro_entre, escena_manzano.disco, escena_manzano.esfera
sdf_modelo = escena_manzano.sdf_modelo


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
        self.borrar = self.create_client(DeleteEntity, '/delete_entity')
        self.arm = self.create_publisher(Float64MultiArray, '/arm_controller/commands', 1)
        self.grip = self.create_publisher(Float64MultiArray, '/gripper_controller/commands', 1)

    def urdf(self):
        cli = self.create_client(GetParameters, '/robot_state_publisher/get_parameters')
        cli.wait_for_service(timeout_sec=10)
        fut = cli.call_async(GetParameters.Request(names=['robot_description']))
        rclpy.spin_until_future_complete(self, fut, timeout_sec=10)
        return fut.result().values[0].string_value

    def quitar(self, nombre):
        if self.borrar.wait_for_service(timeout_sec=2):
            fut = self.borrar.call_async(DeleteEntity.Request(name=nombre))
            rclpy.spin_until_future_complete(self, fut, timeout_sec=10)

    def spawnear(self, nombre, xml):
        self.spawn.wait_for_service(timeout_sec=10)
        self.quitar(nombre)                                       # de una corrida anterior
        fut = self.spawn.call_async(SpawnEntity.Request(name=nombre, xml=xml))
        rclpy.spin_until_future_complete(self, fut, timeout_sec=20)
        self.get_logger().info(f'{nombre}: {fut.result().status_message}')

    def esperar(self, tipo, topic, timeout, qos=1):
        llegada = {}
        sub = self.create_subscription(tipo, topic, lambda m: llegada.setdefault('m', m), qos)
        t0 = time.time()
        while 'm' not in llegada and time.time() - t0 < timeout:
            rclpy.spin_once(self, timeout_sec=0.2)
        self.destroy_subscription(sub)
        return llegada.get('m')

    def verdad(self):
        qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        m = self.esperar(String, '/escena/verdad', 3.0, qos)
        return json.loads(m.data) if m else None

    def camara_gripper(self, base):
        """Color y profundidad de la D405 simulada del gripper (si la simulación tiene cámaras)."""
        color = self.esperar(Image, '/gripper/camera/color/image_raw', 10.0)
        prof = self.esperar(Image, '/gripper/camera/aligned_depth_to_color/image_raw', 10.0)
        if color is None or prof is None:
            self.get_logger().warn('sin imagen de la D405 del gripper (¿camaras:=false?)')
            return
        PILImage.frombytes('RGB', (color.width, color.height), bytes(color.data)).save(base + '_color.png')
        ojo = self.esperar(Image, '/gripper/camera_fisheye/color/image_raw', 10.0)
        if ojo is not None:
            PILImage.frombytes('RGB', (ojo.width, ojo.height), bytes(ojo.data)).save(
                base.replace('_d405', '_fisheye') + '.png')
        if prof.encoding == '16UC1':                                 # mm, como la D405 real
            z = np.frombuffer(bytes(prof.data), dtype=np.uint16).reshape(prof.height, prof.width) / 1000.0
        else:
            z = np.frombuffer(bytes(prof.data), dtype=np.float32).reshape(prof.height, prof.width)
        validos = np.isfinite(z) & (z > 0)
        cerca, lejos = 0.07, 0.5                                     # rango útil de la D405
        t = np.clip((np.where(validos, z, lejos) - cerca) / (lejos - cerca), 0, 1)
        paleta = np.array([[253, 231, 37], [94, 201, 98], [33, 145, 140], [59, 82, 139], [68, 1, 84]], float)
        x = t * (len(paleta) - 1)                                   # cerca amarillo, lejos morado
        k = np.minimum(x.astype(int), len(paleta) - 2)
        f = (x - k)[..., None]
        rgb = ((1 - f) * paleta[k] + f * paleta[k + 1]).astype(np.uint8)
        rgb[~validos | (z > lejos)] = 0
        PILImage.fromarray(rgb).save(base + '_profundidad.png')
        en_rango = validos & (z <= lejos)
        self.get_logger().info(f'D405: {en_rango.mean():.0%} de píxeles con profundidad en 7–50 cm; '
                               f'mediana {np.median(z[en_rango]) if en_rango.any() else float("nan"):.3f} m')

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
    global R_VISTA, DESPEJE, MADERA
    ap = argparse.ArgumentParser()
    ap.add_argument('--salida', default=os.path.expanduser('~/pika_ros/docs/percepcion_activa/img'))
    ap.add_argument('--escena', choices=['manzano', 'prueba'], default='manzano')
    ap.add_argument('--semilla', type=int, default=7)
    ap.add_argument('--radio', type=float, default=None,
                    help='radio del casquete de vistas (m); 0,22 con primitivas y 0,30 con Helios')
    ap.add_argument('--despeje', type=float, default=DESPEJE,
                    help='distancia mínima de cámara y garras a tronco y ramas (m), solo con Helios')
    args, _ = ap.parse_known_args()
    os.makedirs(args.salida, exist_ok=True)
    prefijo = 'nbv' if args.escena == 'prueba' else f'nbv_{args.escena}'
    corrida = os.getpid()             # cámaras con nombre propio: así la demo se puede repetir

    rclpy.init()
    node = Demo()
    escena_lanzada = False
    if args.escena == 'manzano':
        # Si la simulación se lanzó con escena:=manzano, se usa ese árbol (su verdad del terreno);
        # si no, se genera aquí con la semilla pedida y se spawnea en el paso 2.
        verdad = node.verdad()
        escena_lanzada = verdad is not None
        if escena_lanzada:
            args.semilla = verdad['semilla']
            node.get_logger().info(f'uso el manzano de /escena/verdad (semilla {args.semilla})')
        else:
            verdad = json.loads(escena_manzano.verdad_json(escena_manzano.generar(args.semilla)))
        usar_escena(verdad)
        if MODELO == 'helios':
            prefijo = 'nbv_helios'
    # las garras de la Pika llegan ~15 cm por delante de la D405: en un árbol real, con 0,22 m casi
    # todas las vistas meten las garras entre las ramas, junto al dardo de la manzana
    R_VISTA = args.radio or (0.30 if MODELO == 'helios' else 0.22)
    DESPEJE = args.despeje
    if MADERA is not None:                                    # madera cerca del nuevo casquete
        MADERA = MADERA[np.linalg.norm(MADERA - FRUTA, axis=1) < R_VISTA + 0.2]
    kin = Cinematica(node.urdf())
    for viejo in ('vistas_candidatas', 'escena_fruta'):          # marcadores de una corrida anterior
        node.quitar(viejo)

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
        if MADERA is not None:
            # la cámara y las garras (sus puntas, ~15 cm por delante) no pueden atravesar tronco ni ramas
            tramo = k['c'] + np.linspace(0, 0.15, 8)[:, None] * k['d']
            k['despeje_mm'] = float(np.min(np.linalg.norm(MADERA[None] - tramo[:, None], axis=2))) * 1000
            k['choca_madera'] = k['despeje_mm'] < DESPEJE * 1000
            k['alcanzable'] = k['alcanzable'] and not k['choca_madera']
    alcanzables = [k for k in cands if k['alcanzable']]
    if MADERA is not None:
        node.get_logger().info(f"{sum(k.get('choca_madera', False) for k in cands)} candidatas descartadas por chocar con la madera")
    mejor = max(alcanzables, key=lambda k: k['visibilidad'])
    frontal = min(cands, key=lambda k: abs(k['elevacion'] - 10) + abs(k['azimut']))
    node.get_logger().info(f'{len(alcanzables)}/{len(cands)} alcanzables; mejor: elev {mejor["elevacion"]}°, '
                           f'azim {mejor["azimut"]}°, visibilidad {mejor["visibilidad"]:.0%}; '
                           f'frontal: {frontal["visibilidad"]:.0%}')

    # 2. Escena: ramas, frutas y hojas (solo visuales, sin colisión)
    links = ''.join(cilindro_entre(f'rama{i}', a, b, r, COLOR_MADERA) for i, (a, b, r) in enumerate(RAMAS))
    links += esfera('fruta', FRUTA, R_FRUTA, COLOR_FRUTA)
    links += ''.join(esfera(f'otra{i}', c, r, COLOR_FRUTA) for i, (c, r) in enumerate(OTRAS))
    for i, (c, n, r) in enumerate(HOJAS):
        links += disco(f'hoja{i}', c, n, r, COLOR_HOJA)
    if not escena_lanzada:
        node.spawnear('escena_fruta', sdf_modelo('escena_fruta', links))

    # 3. Lo que vería la cámara desde la vista frontal y desde la elegida (brazo plegado y sin
    #    marcadores, para que solo se vea la oclusión por las hojas)
    for _ in range(20):
        node.arm.publish(Float64MultiArray(data=[0.0] * 6))
        rclpy.spin_once(node, timeout_sec=0.1)
    time.sleep(3.0)
    node.spawnear(f'cam_frontal_{corrida}', sdf_camara(f'cam_frontal_{corrida}', pose_mirando(frontal['c'], FRUTA), 1.52, 848, 480))
    node.spawnear(f'cam_elegida_{corrida}', sdf_camara(f'cam_elegida_{corrida}', pose_mirando(mejor['c'], FRUTA), 1.52, 848, 480))
    time.sleep(2.0)
    node.foto(f'cam_frontal_{corrida}', os.path.join(args.salida, f'{prefijo}_vista_frontal.png'))
    node.foto(f'cam_elegida_{corrida}', os.path.join(args.salida, f'{prefijo}_vista_elegida.png'))

    # 4. Brazo en la mejor vista (pinza abierta): lo que ven las cámaras del gripper, antes de
    #    poner los marcadores de las candidatas
    for _ in range(20):
        node.arm.publish(Float64MultiArray(data=[float(v) for v in mejor['q']]))
        node.grip.publish(Float64MultiArray(data=[0.047, -0.047]))
        rclpy.spin_once(node, timeout_sec=0.1)
    time.sleep(3.0)
    node.camara_gripper(os.path.join(args.salida, f'{prefijo}_d405'))

    # 5. Candidatas coloreadas por visibilidad y la foto de la escena completa
    vis = ''
    for i, k in enumerate(cands):
        col = color_visibilidad(k['visibilidad'], k['alcanzable'])
        radio = 0.018 if k is mejor else (0.011 if k['alcanzable'] else 0.007)
        grosor = 0.0035 if k is mejor else (0.0020 if k['alcanzable'] else 0.0012)
        vis += esfera(f'c{i}', k['c'], radio, col, sombra=False)
        vis += cilindro_entre(f'r{i}', k['c'], k['c'] + (R_VISTA - 0.06) * k['d'], grosor, col, sombra=False)
    node.spawnear('vistas_candidatas', sdf_modelo('vistas_candidatas', vis))
    time.sleep(1.0)
    node.spawnear(f'cam_escena_{corrida}', sdf_camara(f'cam_escena_{corrida}', pose_mirando((0.18, -1.05, 0.78), (0.38, 0.0, 0.26)), 0.85, 1600, 1000))
    time.sleep(2.0)
    node.foto(f'cam_escena_{corrida}', os.path.join(args.salida, f'{prefijo}_escena.png'))

    resumen = {'escena': args.escena, 'modelo': MODELO, 'semilla': args.semilla,
               'hojas': len(HOJAS) if TRIS is None else 'triángulos de Helios', 'fruta': FRUTA.tolist(), 'radio_fruta': R_FRUTA, 'radio_casquete': R_VISTA,
               'candidatas': [{'elevacion': k['elevacion'], 'azimut': k['azimut'],
                               'visibilidad': round(k['visibilidad'], 3), 'alcanzable': k['alcanzable'],
                               'error_pos_mm': round(k['error_pos_mm'], 2),
                               'error_ang_deg': round(k['error_ang_deg'], 2),
                               'q': [round(float(v), 4) for v in k['q']],
                               **({'despeje_mm': round(k['despeje_mm'], 1), 'choca_madera': bool(k['choca_madera'])}
                                  if 'despeje_mm' in k else {})} for k in cands],
               'mejor': {'elevacion': mejor['elevacion'], 'azimut': mejor['azimut'],
                         'visibilidad': round(mejor['visibilidad'], 3)},
               'frontal': {'elevacion': frontal['elevacion'], 'azimut': frontal['azimut'],
                           'visibilidad': round(frontal['visibilidad'], 3)}}
    with open(os.path.join(args.salida, f'{prefijo}_escena.json'), 'w') as f:
        json.dump(resumen, f, indent=1, ensure_ascii=False)
    for n in ('cam_frontal', 'cam_elegida', 'cam_escena'):        # las cámaras auxiliares no quedan
        node.quitar(f'{n}_{corrida}')
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
