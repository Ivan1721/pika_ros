#!/usr/bin/env python3
# -*-coding:utf8-*-
# Escenario agrícola para la percepción activa: un manzano frente al Piper.
#
# Dos modelos (parámetro modelo):
#   primitivas  manzano simplificado (cilindros, discos como hojas, esferas), generado aquí
#   helios      manzano realista de Helios (generar_manzano_helios.py): tronco y ramas con sus
#               horquetas, hojas con la silueta real, manzanas con textura. Por defecto, un muro
#               frutal en espaldera, con un árbol vecino a cada lado de la hilera
#
# Como módulo lo usa escena_nbv_demo.py: generar(), cargar_helios(), fraccion_visible() y los
# ayudantes de SDF.
#
# Como nodo (lo lanza sim_piper_single.launch.py con escena:=manzano):
#   - spawnea el árbol en Gazebo (solo visuales, sin colisión: el brazo atraviesa las hojas)
#   - con helios, pone el robot sobre una plataforma: cambia el suelo de Gazebo por uno de huerto
#     a la altura de la plataforma, por debajo de la base del Piper
#   - publica la verdad del terreno para el planner y para RViz, con QoS transient local:
#       /escena/frutas      visualization_msgs/MarkerArray (manzanas; la objetivo en amarillo)
#       /escena/verdad      std_msgs/String con JSON: manzanas (centro, radio, objetivo) en el
#                           marco world; con primitivas, hojas y ramas; con helios, la ruta de los
#                           triángulos de hojas y madera y la transformación árbol → world
#
# Parámetros: modelo (primitivas), semilla (7), n_manzanas (4), densidad_hojas (16 por rama),
# objetivo_ocluida (true), ruta_helios (carpeta de generar_manzano_helios.py), visibilidad_frontal
# (0.3: con helios se elige como objetivo la manzana alcanzable cuya vista de frente se acerque más
# a esa visibilidad), vecinos (1 árbol a cada lado de la hilera).
import json
import math
import os

import numpy as np

COLOR_FRUTA, COLOR_HOJA, COLOR_MADERA = '0.70 0.09 0.09 1', '0.15 0.42 0.13 1', '0.42 0.30 0.20 1'
OBJETIVO = np.array([0.55, 0.0, 0.30])            # dentro del alcance útil de la D405 del Piper
R_MANZANA = 0.038                                   # manzana de ~7,5 cm
R_VISTA = 0.22                                      # distancia de las vistas a la fruta
RUTA_HELIOS = os.path.expanduser('~/.cache/pika_sim/manzanos/apple_fruitingwall_e640_s7')


def generar(semilla=7, n_manzanas=4, densidad_hojas=16, objetivo_ocluida=True):
    """Manzano reproducible. Devuelve un dict con frutas [(centro, radio, objetivo)], hojas
    [(centro, normal, radio)] y ramas [(p0, p1, radio)], en el marco del mundo (base del Piper)."""
    rng = np.random.default_rng(semilla)
    tronco = ((0.74, 0.0, 0.0), (0.74, 0.0, 0.46), 0.035)
    ramas = [((0.74, 0.0, 0.33), (0.565, 0.0, 0.36), 0.010),        # rama de la manzana objetivo
             ((0.74, 0.0, 0.30), (0.58, 0.13, 0.36), 0.012),
             ((0.74, 0.0, 0.36), (0.60, -0.14, 0.42), 0.012),
             ((0.74, 0.0, 0.22), (0.58, 0.07, 0.22), 0.010),
             ((0.74, 0.0, 0.42), (0.64, 0.03, 0.52), 0.010)]
    pedunculo = ((0.565, 0.0, 0.36), tuple(OBJETIVO + [0.0, 0.0, R_MANZANA * 0.85]), 0.004)
    otras = [(np.array([0.585, 0.135, 0.32]), 0.036), (np.array([0.605, -0.14, 0.38]), 0.037),
             (np.array([0.585, 0.075, 0.185]), 0.035), (np.array([0.63, 0.04, 0.47]), 0.034),
             (np.array([0.60, -0.10, 0.25]), 0.036)]
    frutas = [(OBJETIVO.copy(), R_MANZANA, True)] + [(c, r, False) for c, r in otras[:max(0, n_manzanas - 1)]]

    def libre(p):
        return all(np.linalg.norm(p - c) > r + 0.012 for c, r, _ in frutas)

    hojas = []
    for a, b, _ in ramas:                                             # follaje a lo largo de las ramas
        a, b = np.array(a), np.array(b)
        for _ in range(densidad_hojas):
            p = a + rng.uniform(0.25, 1.0) * (b - a) + rng.normal(0, 0.03, 3)
            if libre(p):
                hojas.append((tuple(p), tuple(rng.normal(size=3)), float(rng.uniform(0.024, 0.032))))
    if objetivo_ocluida:                                              # racimo delante de la objetivo
        for _ in range(10):
            p = OBJETIVO + np.r_[-rng.uniform(0.055, 0.085), rng.uniform(-0.045, 0.045), rng.uniform(-0.04, 0.025)]
            if libre(p):
                hojas.append((tuple(p), (1.0, rng.normal(0, 0.35), rng.normal(0, 0.35)),
                              float(rng.uniform(0.026, 0.032))))
    return {'modelo': 'primitivas', 'semilla': semilla, 'frutas': frutas, 'hojas': hojas,
            'ramas': [tronco] + ramas + [pedunculo]}


# ── Visibilidad por trazado de rayos contra triángulos (hojas y madera) y esferas (otras frutas) ──
def _corta(o, d, tris, eps=1e-9):
    """Para cada rayo o + t·d con t en (0, 1), ¿cruza algún triángulo? (Möller–Trumbore)."""
    if len(tris) == 0:
        return np.zeros(len(o), bool)
    v0, e1, e2 = tris[:, 0], tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0]
    tapado = np.zeros(len(o), bool)
    for i in range(0, len(o), 64):
        oo, dd = o[i:i + 64, None, :], d[i:i + 64, None, :]
        p = np.cross(dd, e2[None])
        det = (e1[None] * p).sum(-1)
        inv = 1.0 / np.where(np.abs(det) < eps, np.nan, det)
        s = oo - v0[None]
        u = (s * p).sum(-1) * inv
        q = np.cross(s, e1[None])
        v = (dd * q).sum(-1) * inv
        t = (e2[None] * q).sum(-1) * inv
        hit = (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-4) & (t < 1)
        tapado[i:i + 64] = hit.any(1)
    return tapado


def fraccion_visible(centro, radio, camara, tris, esferas=(), n=600, seed=0):
    """Fracción de la cara de la fruta que mira a la cámara cuyo rayo hasta la cámara no cruza
    ningún triángulo ni otra fruta."""
    rng = np.random.default_rng(seed)
    v = rng.normal(size=(n, 3))
    v /= np.linalg.norm(v, axis=1, keepdims=True)
    pts = np.asarray(centro) + radio * v
    d = np.asarray(camara) - pts
    frente = (v * d).sum(1) > 0
    pts, d = pts[frente], d[frente]
    if len(pts) == 0:
        return 0.0
    # solo los triángulos cerca del segmento fruta–cámara
    medio, largo = (np.asarray(centro) + np.asarray(camara)) / 2, np.linalg.norm(np.asarray(camara) - centro)
    if len(tris):
        cerca = np.linalg.norm(tris.mean(1) - medio, axis=1) < largo / 2 + radio + 0.05
        tris = tris[cerca]
    tapado = _corta(pts, d, tris)
    for c, r in esferas:                                      # otras frutas por delante
        f = pts - c
        b, cc, a = (f * d).sum(1), (f * f).sum(1) - r ** 2, (d * d).sum(1)
        disc = b * b - a * cc
        t = (-b - np.sqrt(np.maximum(disc, 0))) / a
        tapado |= (disc > 0) & (t > 0) & (t < 1)
    return float(1.0 - tapado.mean())


# ── Manzano de Helios ──
def rot_z(yaw):
    c, s = math.cos(yaw), math.sin(yaw)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def cargar_helios(ruta=RUTA_HELIOS, visibilidad_frontal=0.3, vecinos=1, objetivo=OBJETIVO):
    """Ubica el árbol de Helios para que una manzana quede en `objetivo` (frente al Piper) y la
    hilera corra a lo largo de y. Elige como objetivo la manzana cuya vista de frente, a R_VISTA
    desde el lado del robot, tenga la visibilidad más cercana a `visibilidad_frontal`, entre las
    que dejan la plataforma a una altura razonable (0,4–1,4 m)."""
    with open(os.path.join(ruta, 'verdad.json')) as f:
        v = json.load(f)
    datos = np.load(os.path.join(ruta, 'triangulos.npz'))
    tris_local = np.concatenate([datos['hojas'], datos['madera']]).astype(float)
    frutas_local = [(np.array(m['centro']), m['radio']) for m in v['manzanas']]
    if v['modelo'] == 'apple':
        # árbol libre: se gira para que la manzana elegida mire al robot (−x)
        giro = lambda c: math.pi - math.atan2(c[1], c[0])   # noqa: E731
    else:
        giro = lambda c: 0.0                                 # noqa: E731  muro: ya está en el plano y–z
    mejor = None
    for i, (c, r) in enumerate(frutas_local):
        altura = c[2] - objetivo[2]
        if not 0.4 <= altura <= 1.4:
            continue
        R = rot_z(giro(c))
        cw = R @ c
        # lado del robot: con el muro, el de x negativa o positiva, el que deje la fruta más afuera
        signo = 1.0 if v['modelo'] == 'apple' or cw[0] <= 0 else -1.0
        if signo < 0:
            R = rot_z(math.pi) @ R
        t = objetivo - R @ c
        tris = tris_local @ R.T + t
        esferas = [(R @ cj + t, rj) for j, (cj, rj) in enumerate(frutas_local) if j != i]
        vis = fraccion_visible(objetivo, r, objetivo - [R_VISTA, 0, 0], tris, esferas, n=300)
        if mejor is None or abs(vis - visibilidad_frontal) < abs(mejor['vis'] - visibilidad_frontal):
            mejor = {'i': i, 'R': R, 't': t, 'vis': vis}
    if mejor is None:
        raise RuntimeError(f'ninguna manzana de {ruta} deja la plataforma entre 0,4 y 1,4 m')
    R, t = mejor['R'], mejor['t']
    yaw = math.atan2(R[1, 0], R[0, 0])
    largo = v['caja'][1][1] - v['caja'][1][0]                       # largo del árbol a lo largo de y
    poses = [(t + [0, k * largo, 0], yaw) for k in range(-vecinos, vecinos + 1)]
    frutas = []
    for k, (tk, _) in enumerate(poses):
        for j, (c, r) in enumerate(frutas_local):
            frutas.append((R @ c + tk, r, k == vecinos and j == mejor['i']))
    return {'modelo': 'helios', 'semilla': v['semilla'], 'ruta': ruta, 'helios': v, 'frutas': frutas,
            'hojas': [], 'ramas': [], 'poses': poses, 'R': R, 't': t,
            'altura_plataforma': float(-t[2]), 'visibilidad_frontal': mejor['vis']}


def triangulos_mundo(escena):
    """Triángulos de hojas y madera del árbol central de helios, en el marco world."""
    datos = np.load(os.path.join(escena['ruta'], 'triangulos.npz'))
    tris = np.concatenate([datos['hojas'], datos['madera']]).astype(float)
    return tris @ np.asarray(escena['R']).T + np.asarray(escena['t'])


# ── SDF (solo visuales) ──
def _material(rgba):
    return f'<material><ambient>{rgba}</ambient><diffuse>{rgba}</diffuse></material>'


def cilindro_entre(nombre, p0, p1, radio, rgba, sombra=True):
    p0, p1 = np.array(p0, float), np.array(p1, float)
    d = p1 - p0
    largo = np.linalg.norm(d)
    z = d / largo
    pitch, yaw = math.acos(np.clip(z[2], -1, 1)), math.atan2(z[1], z[0])
    m = (p0 + p1) / 2
    return (f'<link name="{nombre}"><pose>{m[0]} {m[1]} {m[2]} 0 {pitch} {yaw}</pose><visual name="v">'
            f'<cast_shadows>{str(sombra).lower()}</cast_shadows><geometry><cylinder><radius>{radio}</radius>'
            f'<length>{largo}</length></cylinder></geometry>{_material(rgba)}</visual></link>')


def disco(nombre, centro, normal, radio, rgba):
    n = np.array(normal, float) / np.linalg.norm(normal)
    pitch, yaw = math.acos(np.clip(n[2], -1, 1)), math.atan2(n[1], n[0])
    return (f'<link name="{nombre}"><pose>{centro[0]} {centro[1]} {centro[2]} 0 {pitch} {yaw}</pose>'
            f'<visual name="v"><geometry><cylinder><radius>{radio}</radius><length>0.004</length></cylinder>'
            f'</geometry>{_material(rgba)}</visual></link>')


def esfera(nombre, c, radio, rgba, sombra=True):
    return (f'<link name="{nombre}"><pose>{c[0]} {c[1]} {c[2]} 0 0 0</pose><visual name="v">'
            f'<cast_shadows>{str(sombra).lower()}</cast_shadows><geometry><sphere><radius>{radio}</radius>'
            f'</sphere></geometry>{_material(rgba)}</visual></link>')


def caja(nombre, centro, tam, rgba, colision=False):
    geo = f'<geometry><box><size>{tam[0]} {tam[1]} {tam[2]}</size></box></geometry>'
    col = f'<collision name="c">{geo}</collision>' if colision else ''
    return (f'<link name="{nombre}"><pose>{centro[0]} {centro[1]} {centro[2]} 0 0 0</pose>{col}'
            f'<visual name="v">{geo}{_material(rgba)}</visual></link>')


def sdf_modelo(nombre, links):
    return f'<?xml version="1.0"?><sdf version="1.6"><model name="{nombre}"><static>true</static>{links}</model></sdf>'


def sdf_escena(escena, nombre='manzano'):
    if escena['modelo'] == 'helios':
        links = ''
        for k, (t, yaw) in enumerate(escena['poses']):
            for parte, archivo in escena['helios']['mallas'].items():
                uri = 'file://' + os.path.join(escena['ruta'], archivo)
                links += (f'<link name="{parte}{k}"><pose>{t[0]} {t[1]} {t[2]} 0 0 {yaw}</pose><visual name="v">'
                          f'<geometry><mesh><uri>{uri}</uri></mesh></geometry></visual></link>')
        return sdf_modelo(nombre, links)
    links = ''.join(cilindro_entre(f'rama{i}', a, b, r, COLOR_MADERA) for i, (a, b, r) in enumerate(escena['ramas']))
    links += ''.join(esfera(f'manzana{i}', c, r, COLOR_FRUTA) for i, (c, r, _) in enumerate(escena['frutas']))
    links += ''.join(disco(f'hoja{i}', c, n, r, COLOR_HOJA) for i, (c, n, r) in enumerate(escena['hojas']))
    return sdf_modelo(nombre, links)


def sdf_huerto(altura):
    """Suelo de huerto a `altura` bajo la base del Piper y la plataforma remolcable donde va."""
    links = caja('suelo', (0, 0, -altura - 0.05), (30, 30, 0.1), '0.36 0.30 0.22 1', colision=True)
    links += caja('cubierta', (-0.15, 0, -0.04), (1.0, 0.7, 0.08), '0.25 0.25 0.27 1')
    for i, (x, y) in enumerate([(-0.6, -0.3), (-0.6, 0.3), (0.3, -0.3), (0.3, 0.3)]):
        links += caja(f'pata{i}', (x, y, -(altura + 0.08) / 2), (0.06, 0.06, altura - 0.08), '0.20 0.20 0.22 1')
    return sdf_modelo('huerto', links)


def verdad_json(escena):
    d = {'semilla': escena['semilla'], 'marco': 'world', 'modelo': escena['modelo'],
         'manzanas': [{'centro': [round(float(v), 4) for v in c], 'radio': r, 'objetivo': o}
                      for c, r, o in escena['frutas']],
         'hojas': [{'centro': [round(float(v), 4) for v in c], 'normal': [round(float(v), 4) for v in n],
                    'radio': round(r, 4)} for c, n, r in escena['hojas']],
         'ramas': [{'p0': list(a), 'p1': list(b), 'radio': r} for a, b, r in escena['ramas']]}
    if escena['modelo'] == 'helios':
        d.update({'ruta': escena['ruta'], 'helios': {k: escena['helios'][k] for k in ('modelo', 'edad_dias', 'semilla')},
                  'triangulos': os.path.join(escena['ruta'], 'triangulos.npz'),
                  'arbol_a_world': {'R': np.round(escena['R'], 6).tolist(), 't': np.round(escena['t'], 4).tolist()},
                  'altura_plataforma': round(escena['altura_plataforma'], 3),
                  'visibilidad_frontal': round(escena['visibilidad_frontal'], 3)})
    return json.dumps(d)


def main():
    import rclpy
    from rclpy.executors import ExternalShutdownException
    from gazebo_msgs.srv import DeleteEntity, SpawnEntity
    from rclpy.node import Node
    from rclpy.qos import DurabilityPolicy, QoSProfile
    from std_msgs.msg import String
    from visualization_msgs.msg import Marker, MarkerArray

    class EscenaManzano(Node):
        def __init__(self):
            super().__init__('escena_manzano')
            self.declare_parameter('modelo', 'primitivas')
            self.declare_parameter('semilla', 7)
            self.declare_parameter('n_manzanas', 4)
            self.declare_parameter('densidad_hojas', 16)
            self.declare_parameter('objetivo_ocluida', True)
            self.declare_parameter('ruta_helios', RUTA_HELIOS)
            self.declare_parameter('visibilidad_frontal', 0.3)
            self.declare_parameter('vecinos', 1)
            g = lambda n: self.get_parameter(n).value  # noqa: E731
            if g('modelo') == 'helios':
                self.escena = cargar_helios(os.path.expanduser(g('ruta_helios')), g('visibilidad_frontal'), g('vecinos'))
            else:
                self.escena = generar(g('semilla'), g('n_manzanas'), g('densidad_hojas'), g('objetivo_ocluida'))
            qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
            self.pub_marcas = self.create_publisher(MarkerArray, '/escena/frutas', qos)
            self.pub_verdad = self.create_publisher(String, '/escena/verdad', qos)

        def llamar(self, cli, req, timeout=60.0):
            fut = cli.call_async(req)
            rclpy.spin_until_future_complete(self, fut, timeout_sec=timeout)
            return fut.result()

        def spawnear(self):
            cli = self.create_client(SpawnEntity, '/spawn_entity')
            if not cli.wait_for_service(timeout_sec=60.0):
                self.get_logger().error('/spawn_entity no disponible: ¿está corriendo Gazebo?')
                return False
            e = self.escena
            if e['modelo'] == 'helios':
                borrar = self.create_client(DeleteEntity, '/delete_entity')
                if borrar.wait_for_service(timeout_sec=10.0):
                    self.llamar(borrar, DeleteEntity.Request(name='ground_plane'))
                self.llamar(cli, SpawnEntity.Request(name='huerto', xml=sdf_huerto(e['altura_plataforma'])))
            res = self.llamar(cli, SpawnEntity.Request(name='manzano', xml=sdf_escena(e)), timeout=120.0)
            ok = res is not None and res.success
            if e['modelo'] == 'helios':
                h = e['helios']
                self.get_logger().info(
                    f'manzano Helios {h["modelo"]} ({h["edad_dias"]:.0f} días, semilla {h["semilla"]}) con '
                    f'{len(e["poses"]) - 1} vecinos: {len(e["frutas"])} manzanas; plataforma a '
                    f'{e["altura_plataforma"]:.2f} m; objetivo con {e["visibilidad_frontal"]:.0%} visible de frente; '
                    f'spawn {"ok" if ok else "FALLÓ"}')
            else:
                self.get_logger().info(f'manzano (semilla {e["semilla"]}): {len(e["frutas"])} manzanas, '
                                       f'{len(e["hojas"])} hojas; spawn {"ok" if ok else "FALLÓ"}')
            return ok

        def publicar(self):
            marcas = MarkerArray()
            for i, (c, r, objetivo) in enumerate(self.escena['frutas']):
                m = Marker(type=Marker.SPHERE, action=Marker.ADD, id=i, ns='manzanas')
                m.header.frame_id = 'world'
                m.pose.position.x, m.pose.position.y, m.pose.position.z = (float(v) for v in c)
                m.pose.orientation.w = 1.0
                m.scale.x = m.scale.y = m.scale.z = 2 * r
                m.color.a = 0.6
                m.color.r, m.color.g, m.color.b = (0.95, 0.75, 0.10) if objetivo else (0.78, 0.20, 0.25)
                marcas.markers.append(m)
            self.pub_marcas.publish(marcas)
            self.pub_verdad.publish(String(data=verdad_json(self.escena)))

    rclpy.init()
    nodo = EscenaManzano()
    nodo.spawnear()
    nodo.publicar()
    try:
        rclpy.spin(nodo)                     # sigue vivo para servir la verdad (transient local)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        nodo.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
