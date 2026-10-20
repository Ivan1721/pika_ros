#!/usr/bin/env python3
# -*-coding:utf8-*-
# Galería de oclusión: manzanas del árbol de Helios vistas con distinto nivel de visibilidad.
#
# capturar (con la simulación corriendo, escena:=manzano arbol:=helios):
#   1. Toma las manzanas del árbol que quedan al alcance del Piper y, para cada una, vistas en un
#      casquete de 0,30 m del lado del robot (las mismas que usaría el NBV).
#   2. Calcula la visibilidad de cada par manzana–vista trazando rayos contra hojas, madera y otras
#      manzanas de toda la hilera, y elige un ejemplo por franja de visibilidad.
#   3. Fotografía cada ejemplo con una cámara virtual con el campo visual de la D405 (87°, 640×480).
#   4. Verifica la visibilidad en la imagen: pone una esfera magenta emisiva sobre la manzana (6 % más grande),
#      vuelve a fotografiar y cuenta los píxeles que cambiaron. La fracción visible en la imagen es
#      esos píxeles sobre el área del disco proyectado de la manzana.
#   La selección depende solo de la geometría y la semilla: repetida con otra luz:=..., da los
#   mismos ejemplos, así que se pueden comparar iluminaciones.
#
#     ros2 run pika_sim galeria_oclusion.py capturar --salida <carpeta>
#
# panel: arma la figura con una fila por franja de visibilidad y una columna por corrida (luz).
# validacion: dispersión de la visibilidad por rayos contra la medida en la imagen.
#
#     python3 galeria_oclusion.py panel|validacion <salida.png> <carpeta>:<rótulo> [<carpeta>:<rótulo> ...]
import json
import math
import os
import sys
import time

import numpy as np

FRANJAS = [(0.0, 0.10), (0.10, 0.30), (0.30, 0.50), (0.50, 0.70), (0.70, 0.90), (0.90, 1.01)]
HFOV, ANCHO, ALTO = 1.518, 640, 480                      # D405
R_VISTA = 0.30
ELEVACIONES, AZIMUTS = [-15, 10, 35], [-40, -20, 0, 20, 40]


def vistas(fruta):
    """Vistas en el casquete, del lado del robot (−x), apuntando a la fruta."""
    out = []
    for e in ELEVACIONES:
        for a in AZIMUTS:
            az, el = math.pi + math.radians(a), math.radians(e)
            c = fruta + R_VISTA * np.array([math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)])
            out.append((e, a, c))
    return out


def proyectar(camara, fruta, radio):
    """Centro (px) y radio (px) del disco de la fruta en la imagen de una cámara que la mira."""
    f = (ANCHO / 2) / math.tan(HFOV / 2)
    d = np.linalg.norm(fruta - camara)
    rho = f * radio / math.sqrt(max(d * d - radio * radio, 1e-9))
    return (ANCHO / 2, ALTO / 2), rho


def capturar(argv):
    import argparse

    import rclpy
    from gazebo_msgs.srv import DeleteEntity, SpawnEntity
    from PIL import Image as PILImage
    from rclpy.node import Node
    from rclpy.qos import DurabilityPolicy, QoSProfile
    from sensor_msgs.msg import Image
    from std_msgs.msg import String

    import escena_manzano as em
    from escena_nbv_demo import pose_mirando, sdf_camara

    ap = argparse.ArgumentParser()
    ap.add_argument('--salida', required=True)
    ap.add_argument('--semilla', type=int, default=3)
    ap.add_argument('--max_frutas', type=int, default=60)
    args, _ = ap.parse_known_args(argv)
    os.makedirs(args.salida, exist_ok=True)

    rclpy.init()
    nodo = Node('galeria_oclusion')

    def esperar(tipo, topic, timeout, qos=1, saltar=0):
        llegadas = []
        sub = nodo.create_subscription(tipo, topic, llegadas.append, qos)
        t0 = time.time()
        while len(llegadas) <= saltar and time.time() - t0 < timeout:
            rclpy.spin_once(nodo, timeout_sec=0.1)
        nodo.destroy_subscription(sub)
        return llegadas[-1] if len(llegadas) > saltar else None

    spawn = nodo.create_client(SpawnEntity, '/spawn_entity')
    borrar = nodo.create_client(DeleteEntity, '/delete_entity')
    spawn.wait_for_service(timeout_sec=30)
    borrar.wait_for_service(timeout_sec=30)

    def llamar(cli, req):
        fut = cli.call_async(req)
        rclpy.spin_until_future_complete(nodo, fut, timeout_sec=30)
        return fut.result()

    qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
    m = esperar(String, '/escena/verdad', 10.0, qos)
    if m is None:
        sys.exit('sin /escena/verdad: lanzar con escena:=manzano arbol:=helios')
    verdad = json.loads(m.data)
    if verdad.get('modelo') != 'helios':
        sys.exit('la galería necesita el árbol de Helios (arbol:=helios)')
    tris = em.triangulos_verdad(verdad)
    manzanas = [(np.array(f['centro']), f['radio']) for f in verdad['manzanas']]

    # 1–2. pares manzana–vista y su visibilidad (rayos), un ejemplo por franja
    rng = np.random.default_rng(args.semilla)
    # al alcance y sobre la cubierta de la plataforma (z > 0,1 m: las vistas bajas siguen sobre ella;
    # la plataforma no está en el modelo de rayos)
    al_alcance = [i for i, (c, _) in enumerate(manzanas) if abs(c[1]) < 0.45 and 0.10 < c[2] < 0.75 and 0.35 < c[0] < 0.8]
    elegidas = sorted(rng.choice(al_alcance, size=min(args.max_frutas, len(al_alcance)), replace=False).tolist())
    pares = []
    for i in elegidas:
        c, r = manzanas[i]
        otras = [(cj, rj) for j, (cj, rj) in enumerate(manzanas) if j != i and np.linalg.norm(cj - c) < 0.8]
        for e, a, cam in vistas(c):
            pares.append({'i': i, 'elev': e, 'azim': a, 'cam': cam,
                          'vis': em.fraccion_visible(c, r, cam, tris, otras, n=200, seed=1)})
    nodo.get_logger().info(f'{len(elegidas)} manzanas al alcance, {len(pares)} pares manzana–vista evaluados')
    ejemplos = []
    for lo, hi in FRANJAS:
        usadas = {e['i'] for e in ejemplos}
        cand = sorted((p for p in pares if lo <= p['vis'] < hi and p['i'] not in usadas),
                      key=lambda p: abs(p['vis'] - (lo + min(hi, 1.0)) / 2))
        for p in cand[:5]:                                  # confirma con más rayos
            c, r = manzanas[p['i']]
            otras = [(cj, rj) for j, (cj, rj) in enumerate(manzanas) if j != p['i'] and np.linalg.norm(cj - c) < 0.8]
            v = em.fraccion_visible(c, r, p['cam'], tris, otras, n=1000, seed=2)
            if lo <= v < hi:
                ejemplos.append(dict(p, vis=v, franja=[lo, min(hi, 1.0)]))
                break

    # 3–4. fotos con y sin la esfera de verificación
    corrida = os.getpid()
    resultados = []
    for k, ej in enumerate(ejemplos):
        c, r = manzanas[ej['i']]
        nombre = f'gal_cam_{corrida}_{k}'
        llamar(spawn, SpawnEntity.Request(name=nombre, xml=sdf_camara(nombre, pose_mirando(ej['cam'], c), HFOV, ANCHO, ALTO)))
        img = esperar(Image, f'/{nombre}/cam/image_raw', 20.0, saltar=2)
        marca = (f'<?xml version="1.0"?><sdf version="1.6"><model name="gal_marca"><static>true</static>'
                 f'<link name="l"><pose>{c[0]} {c[1]} {c[2]} 0 0 0</pose><visual name="v"><cast_shadows>false</cast_shadows>'
                 f'<geometry><sphere><radius>{r * 1.06}</radius></sphere></geometry><material><ambient>1 0 1 1</ambient>'
                 f'<diffuse>1 0 1 1</diffuse><emissive>1 0 1 1</emissive></material></visual></link></model></sdf>')
        llamar(spawn, SpawnEntity.Request(name='gal_marca', xml=marca))
        img_m = esperar(Image, f'/{nombre}/cam/image_raw', 20.0, saltar=4)
        llamar(borrar, DeleteEntity.Request(name='gal_marca'))
        llamar(borrar, DeleteEntity.Request(name=nombre))
        if img is None or img_m is None:
            nodo.get_logger().error(f'sin imagen para el ejemplo {k}')
            continue
        a = np.frombuffer(bytes(img.data), np.uint8).reshape(ALTO, ANCHO, 3).astype(int)
        b = np.frombuffer(bytes(img_m.data), np.uint8).reshape(ALTO, ANCHO, 3).astype(int)
        # la esfera es 6 % más grande que la manzana: la malla de Helios no es una esfera perfecta y
        # donde sobresale taparía a una esfera del mismo radio (falsos huecos en la máscara)
        (cx, cy), rho = proyectar(ej['cam'], c, r * 1.06)
        yy, xx = np.mgrid[0:ALTO, 0:ANCHO]
        cerca = (xx - cx) ** 2 + (yy - cy) ** 2 < (1.15 * rho) ** 2
        cambio = (np.abs(b - a).sum(2) > 60) & cerca
        vis_img = float(cambio.sum() / (math.pi * rho * rho))
        base = os.path.join(args.salida, f'oclusion_{k}')
        PILImage.fromarray(a.astype(np.uint8)).save(base + '.png')
        PILImage.fromarray((cambio * 255).astype(np.uint8)).save(base + '_mascara.png')
        resultados.append({'k': k, 'manzana': ej['i'], 'centro': np.round(c, 4).tolist(), 'radio': r,
                           'elevacion': ej['elev'], 'azimut': ej['azim'], 'franja': ej['franja'],
                           'camara': np.round(ej['cam'], 4).tolist(),
                           'visibilidad_rayos': round(ej['vis'], 3), 'visibilidad_imagen': round(min(vis_img, 1.0), 3),
                           'centro_px': [cx, cy], 'radio_px': round(rho, 1), 'imagen': os.path.basename(base) + '.png'})
        nodo.get_logger().info(f'franja {ej["franja"]}: manzana {ej["i"]}, rayos {ej["vis"]:.0%}, imagen {vis_img:.0%}')
    with open(os.path.join(args.salida, 'oclusion.json'), 'w') as f:
        json.dump({'casquete_m': R_VISTA, 'pares_evaluados': len(pares), 'ejemplos': resultados}, f, indent=1)
    nodo.destroy_node()
    rclpy.shutdown()


def panel(argv):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle
    from PIL import Image

    mascara = '--mascara' in argv
    argv = [a for a in argv if a != '--mascara']
    salida, corridas = argv[0], [a.split(':', 1) for a in argv[1:]]
    if mascara:                     # columna extra: lo que midió la imagen en la primera corrida
        corridas.append((corridas[0][0], 'visible en la imagen\n(' + corridas[0][1] + ')', True))
    corridas = [c if len(c) == 3 else (c[0], c[1], False) for c in corridas]
    datos = [json.load(open(os.path.join(d, 'oclusion.json'))) for d, _, _ in corridas]
    filas = len(datos[0]['ejemplos'])
    fig, ejes = plt.subplots(filas, len(corridas), figsize=(2.3 * len(corridas) + 1.2, 2.3 * filas))
    ejes = np.atleast_2d(ejes)
    for j, ((carpeta, rotulo, es_mascara), d) in enumerate(zip(corridas, datos)):
        for i, ej in enumerate(d['ejemplos']):
            ax = ejes[i, j]
            img = np.asarray(Image.open(os.path.join(carpeta, ej['imagen'])))
            if es_mascara:
                m = np.asarray(Image.open(os.path.join(carpeta, ej['imagen'].replace('.png', '_mascara.png')))) > 0
                img = img.copy()
                img[m] = (0.35 * img[m] + np.array([165, 0, 165])).astype(np.uint8)
            cx, cy = ej['centro_px']
            lado = max(2.6 * ej['radio_px'], 60)
            x0, x1 = int(max(cx - lado, 0)), int(min(cx + lado, ANCHO))
            y0, y1 = int(max(cy - lado, 0)), int(min(cy + lado, ALTO))
            ax.imshow(img[y0:y1, x0:x1])
            ax.add_patch(Circle((cx - x0, cy - y0), ej['radio_px'], fill=False, ls='--', lw=1.2, ec='#ffd23f'))
            ax.set_xticks([])
            ax.set_yticks([])
            if i == 0:
                ax.set_title(rotulo, fontsize=11)
            if j == 0:
                lo, hi = ej['franja']
                ax.set_ylabel(f'{lo:.0%}–{hi:.0%}', fontsize=10)
            ax.set_xlabel(f'rayos {ej["visibilidad_rayos"]:.0%} · imagen {ej["visibilidad_imagen"]:.0%}', fontsize=8, color='#555555')
    fig.suptitle('Visibilidad de la manzana objetivo (círculo) por franja, con distintas luces', x=0.01, ha='left', fontsize=12)
    fig.tight_layout()
    fig.savefig(salida, dpi=80, bbox_inches='tight')
    print(f'Listo: {salida}')


def validacion(argv):
    """Dispersión visibilidad por rayos contra visibilidad medida en la imagen, todas las corridas."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    salida, corridas = argv[0], [a.split(':', 1) for a in argv[1:]]
    fig, ax = plt.subplots(figsize=(4.6, 4.4))
    errores, puntos = [], []
    for carpeta, rotulo in corridas:
        ej = json.load(open(os.path.join(carpeta, 'oclusion.json')))['ejemplos']
        x = [e['visibilidad_rayos'] * 100 for e in ej]
        y = [e['visibilidad_imagen'] * 100 for e in ej]
        errores += [abs(a - b) for a, b in zip(x, y)]
        puntos.append([(round(a, 1), round(b, 1)) for a, b in zip(x, y)])
        ax.scatter(x, y, s=22, label=rotulo, alpha=0.85)
    ax.plot([0, 100], [0, 100], color='#888888', lw=1, ls='--')
    ax.set_xlabel('visibilidad por trazado de rayos (%)')
    ax.set_ylabel('visibilidad medida en la imagen (%)')
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    iguales = all(p == puntos[0] for p in puntos)
    nota = ';\nlas luces dan los mismos puntos' if len(corridas) > 1 and iguales else ''
    ax.set_title(f'Error medio {np.mean(errores):.1f} puntos, máximo {np.max(errores):.1f} (n = {len(errores)}{nota})',
                 fontsize=9, loc='left')
    ax.legend(fontsize=8, loc='upper left')
    fig.tight_layout()
    fig.savefig(salida, dpi=120)
    print(f'Listo: {salida} (error medio {np.mean(errores):.1f}, máximo {np.max(errores):.1f}, n={len(errores)})')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'panel':
        panel(sys.argv[2:])
    elif len(sys.argv) > 1 and sys.argv[1] == 'validacion':
        validacion(sys.argv[2:])
    elif len(sys.argv) > 1 and sys.argv[1] == 'capturar':
        capturar(sys.argv[2:])
    else:
        sys.exit(__doc__ if __doc__ else 'uso: galeria_oclusion.py capturar|panel ...')
