#!/usr/bin/env python3
# -*-coding:utf8-*-
# Escenario agrícola para la percepción activa: un manzano simplificado frente al Piper.
#
# Como módulo, generar() devuelve la geometría (tronco, ramas, hojas y manzanas) a partir de una
# semilla: la misma semilla da siempre el mismo árbol. Lo usan este nodo y escena_nbv_demo.py.
#
# Como nodo (lo lanza sim_piper_single.launch.py con escena:=manzano):
#   - spawnea el manzano en Gazebo (solo visuales, sin colisión: el brazo atraviesa las hojas)
#   - publica la verdad del terreno para el planner y para RViz, con QoS transient local:
#       /escena/frutas      visualization_msgs/MarkerArray (manzanas; la objetivo en otro color)
#       /escena/verdad      std_msgs/String con JSON: manzanas (centro, radio, objetivo), hojas y ramas
#
# Parámetros: semilla (7), n_manzanas (4), densidad_hojas (16 por rama), objetivo_ocluida (true).
import json
import math

import numpy as np

COLOR_FRUTA, COLOR_HOJA, COLOR_MADERA = '0.70 0.09 0.09 1', '0.15 0.42 0.13 1', '0.42 0.30 0.20 1'
OBJETIVO = np.array([0.55, 0.0, 0.30])            # dentro del alcance útil de la D405 del Piper
R_MANZANA = 0.038                                   # manzana de ~7,5 cm


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
    return {'semilla': semilla, 'frutas': frutas, 'hojas': hojas,
            'ramas': [tronco] + ramas + [pedunculo]}


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


def sdf_modelo(nombre, links):
    return f'<?xml version="1.0"?><sdf version="1.6"><model name="{nombre}"><static>true</static>{links}</model></sdf>'


def sdf_escena(escena, nombre='manzano'):
    links = ''.join(cilindro_entre(f'rama{i}', a, b, r, COLOR_MADERA) for i, (a, b, r) in enumerate(escena['ramas']))
    links += ''.join(esfera(f'manzana{i}', c, r, COLOR_FRUTA) for i, (c, r, _) in enumerate(escena['frutas']))
    links += ''.join(disco(f'hoja{i}', c, n, r, COLOR_HOJA) for i, (c, n, r) in enumerate(escena['hojas']))
    return sdf_modelo(nombre, links)


def verdad_json(escena):
    return json.dumps({
        'semilla': escena['semilla'], 'marco': 'world',
        'manzanas': [{'centro': [round(float(v), 4) for v in c], 'radio': r, 'objetivo': o}
                     for c, r, o in escena['frutas']],
        'hojas': [{'centro': [round(float(v), 4) for v in c], 'normal': [round(float(v), 4) for v in n],
                   'radio': round(r, 4)} for c, n, r in escena['hojas']],
        'ramas': [{'p0': list(a), 'p1': list(b), 'radio': r} for a, b, r in escena['ramas']]})


def main():
    import rclpy
    from gazebo_msgs.srv import SpawnEntity
    from rclpy.node import Node
    from rclpy.qos import DurabilityPolicy, QoSProfile
    from std_msgs.msg import String
    from visualization_msgs.msg import Marker, MarkerArray

    class EscenaManzano(Node):
        def __init__(self):
            super().__init__('escena_manzano')
            self.declare_parameter('semilla', 7)
            self.declare_parameter('n_manzanas', 4)
            self.declare_parameter('densidad_hojas', 16)
            self.declare_parameter('objetivo_ocluida', True)
            g = lambda n: self.get_parameter(n).value  # noqa: E731
            self.escena = generar(g('semilla'), g('n_manzanas'), g('densidad_hojas'), g('objetivo_ocluida'))
            qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
            self.pub_marcas = self.create_publisher(MarkerArray, '/escena/frutas', qos)
            self.pub_verdad = self.create_publisher(String, '/escena/verdad', qos)

        def spawnear(self):
            cli = self.create_client(SpawnEntity, '/spawn_entity')
            if not cli.wait_for_service(timeout_sec=60.0):
                self.get_logger().error('/spawn_entity no disponible: ¿está corriendo Gazebo?')
                return False
            fut = cli.call_async(SpawnEntity.Request(name='manzano', xml=sdf_escena(self.escena)))
            rclpy.spin_until_future_complete(self, fut, timeout_sec=30.0)
            ok = fut.result() is not None and fut.result().success
            self.get_logger().info(f'manzano (semilla {self.escena["semilla"]}): {len(self.escena["frutas"])} '
                                   f'manzanas, {len(self.escena["hojas"])} hojas; spawn {"ok" if ok else "FALLÓ"}')
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
    except KeyboardInterrupt:
        pass
    finally:
        nodo.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
