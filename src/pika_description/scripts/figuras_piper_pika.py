#!/usr/bin/env python3
"""Figuras y medidas del Piper + gripper Pika, sacadas del URDF y de las mallas STL.

Genera en la carpeta de salida (por defecto src/pika_description/docs/figuras):
  fig_3d.png              vistas 3D: pose plegada (q = 0) y pose de referencia en L
  fig_lateral.png         vista lateral (X-Z) en la pose en L, con cotas de cada tramo
  fig_frontal.png         vista frontal (Y-Z) en la pose en L, con anchos
  fig_cadena.png          cadena de ejes: posición de cada articulación y desplazamiento entre ellas
  fig_articulaciones.png  las 7 libertades: cada articulación en su mínimo, referencia y máximo
  fig_alcance.png         espacio de trabajo del TCP (muestreo de posturas dentro de los límites)
  medidas.json            las medidas que aparecen en las figuras

Todo se calcula del modelo (pika_piper_standalone.urdf.xacro): si cambia el URDF, basta con
volver a correrlo. No necesita pinocchio; la cinemática directa recorre el URDF.

Uso (workspace compilado y cargado, sin conda; necesita matplotlib):
  source ~/pika_ros/install/setup.bash
  python3 ~/pika_ros/src/pika_description/scripts/figuras_piper_pika.py [carpeta_salida]
"""
import json
import os
import struct
import sys
import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use('Agg')  # dibujar a archivo, sin ventana
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import xacro  # noqa: E402
from ament_index_python.packages import get_package_share_directory  # noqa: E402
from matplotlib.collections import PolyCollection  # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(AQUI, '..', 'docs', 'figuras')

# Colores de AgileX, tomados de la foto oficial del Piper (img/piper_arm.png): base y
# articulaciones negras, eslabones gris grafito metalizado y anillos rojos. El rojo de la foto
# (#93353f) sale oscurecido por la luz; aquí se usa el mismo tono, más claro. La Pika es negro
# mate con rieles plateados.
SURF, INK, MUTED = '#fcfcfb', '#2b2b29', '#6b6a63'
C_NEGRO, C_GRAFITO = '#1d2124', '#55585c'   # Piper: base/articulaciones y eslabones
C_PIKA, C_PLATA = '#2b2c2e', '#a9acb0'      # gripper Pika y cámaras / rieles
C_ROJO, C_GRIS = '#c8323f', '#8a8d91'       # acento AgileX y serie secundaria
SERIES = [C_GRIS, C_ROJO]
ESLABONES_GRAFITO = ('link2', 'link3')      # brazo y antebrazo; el resto del Piper es negro
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'text.color': INK,
                     'axes.labelcolor': INK, 'xtick.color': MUTED, 'ytick.color': MUTED,
                     'axes.edgecolor': '#d6d5ce', 'figure.facecolor': SURF,
                     'axes.facecolor': SURF, 'savefig.facecolor': SURF})

ARM = ['joint1', 'joint2', 'joint3', 'joint4', 'joint5', 'joint6']
FUNCION = {'joint1': 'giro de la base', 'joint2': 'hombro', 'joint3': 'codo',
           'joint4': 'giro del antebrazo', 'joint5': 'flexión de la muñeca',
           'joint6': 'giro de la muñeca'}
# Pose de referencia en L: brazo vertical, antebrazo y herramienta horizontales hacia +X.
# Los ángulos se buscaron numéricamente sobre el URDF (ver docs/PIPER_PIKA.md).
Q_L = {'joint2': 1.4300, 'joint3': -1.2530, 'joint5': -0.0900}
Q_CERO = {}

URDF = xacro.process_file(os.path.join(get_package_share_directory('pika_description'), 'urdf',
                                       'pika_piper_standalone.urdf.xacro')).toxml()
ROOT = ET.fromstring(URDF)


def floats(text, default):
    return np.array([float(v) for v in text.split()]) if text else np.array(default, float)


def rpy_matrix(r, p, y):
    cr, sr, cp, sp, cy, sy = np.cos(r), np.sin(r), np.cos(p), np.sin(p), np.cos(y), np.sin(y)
    return np.array([[cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr],
                     [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr],
                     [-sp, cp * sr, cp * cr]])


def origin_of(el):
    o = el.find('origin')
    M = np.eye(4)
    M[:3, :3] = rpy_matrix(*floats(o.get('rpy') if o is not None else None, [0, 0, 0]))
    M[:3, 3] = floats(o.get('xyz') if o is not None else None, [0, 0, 0])
    return M


def axis_angle(axis, angle):
    a = axis / np.linalg.norm(axis)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + np.sin(angle) * K + (1 - np.cos(angle)) * K @ K


def load_stl(path):
    """Triángulos (N, 3, 3) de un STL binario o ASCII."""
    data = open(path, 'rb').read()
    if data[:5] == b'solid' and b'facet' in data[:300]:
        v = [list(map(float, ln.split()[1:])) for ln in data.decode().splitlines()
             if ln.strip().startswith('vertex')]
        return np.array(v).reshape(-1, 3, 3)
    n = struct.unpack('<I', data[80:84])[0]
    rec = np.dtype([('n', '<3f4'), ('v', '<9f4'), ('a', '<u2')])
    return np.frombuffer(data[84:84 + n * 50], dtype=rec)['v'].reshape(-1, 3, 3).astype(float)


def mesh_path(uri):
    pkg, rel = uri[len('package://'):].split('/', 1)
    return os.path.join(get_package_share_directory(pkg), rel)


# Geometría visual de cada link: lista de (transformación visual, triángulos en metros).
VISUALS = {}
for link in ROOT.findall('link'):
    for vis in link.findall('visual'):
        geo = vis.find('geometry')[0]
        if geo.tag != 'mesh':
            continue
        tris = load_stl(mesh_path(geo.get('filename'))) * floats(geo.get('scale'), [1, 1, 1])
        VISUALS.setdefault(link.get('name'), []).append((origin_of(vis), tris))

JOINTS = [dict(name=j.get('name'), type=j.get('type'), parent=j.find('parent').get('link'),
               child=j.find('child').get('link'), origin=origin_of(j),
               axis=floats(j.find('axis').get('xyz') if j.find('axis') is not None else None,
                           [1, 0, 0]),
               limit=(float(j.find('limit').get('lower')), float(j.find('limit').get('upper')))
               if j.find('limit') is not None else None)
          for j in ROOT.findall('joint')]
JOINT = {j['name']: j for j in JOINTS}


def world(q):
    """Pose de cada link en 'world' para los valores articulares q (dict nombre -> valor)."""
    T = {'world': np.eye(4)}
    changed = True
    while changed:
        changed = False
        for j in JOINTS:
            if j['parent'] in T and j['child'] not in T:
                M = np.eye(4)
                if j['type'] in ('revolute', 'continuous'):
                    M[:3, :3] = axis_angle(j['axis'], q.get(j['name'], 0.0))
                elif j['type'] == 'prismatic':
                    M[:3, 3] = j['axis'] * q.get(j['name'], 0.0)
                T[j['child']] = T[j['parent']] @ j['origin'] @ M
                changed = True
    return T


def joint_frames(q):
    """Origen y eje (en el mundo) de cada articulación móvil."""
    T = world(q)
    out = {}
    for j in JOINTS:
        if j['type'] in ('revolute', 'prismatic'):
            F = T[j['parent']] @ j['origin']
            out[j['name']] = (F[:3, 3], F[:3, :3] @ (j['axis'] / np.linalg.norm(j['axis'])))
    return out


def skeleton(q):
    """Puntos de la cadena: base, joint1..6, TCP."""
    T = world(q)
    fr = joint_frames(q)
    return np.array([T['base_link'][:3, 3]] + [fr[n][0] for n in ARM] + [T['pika_tcp'][:3, 3]])


def color_of(link):
    if link in ('pika_depth_link', 'pika_fisheye_link'):
        return C_PLATA
    if link.startswith('pika') or link == 'gripper_base':
        return C_PIKA
    if link in ESLABONES_GRAFITO:
        return C_GRAFITO
    return C_NEGRO


def placed(T, max_tris=None, seed=0):
    out = []
    rng = np.random.default_rng(seed)
    for link, items in VISUALS.items():
        for V, tris in items:
            if max_tris and len(tris) > max_tris:
                tris = tris[rng.choice(len(tris), max_tris, replace=False)]
            M = T[link] @ V
            out.append((link, tris @ M[:3, :3].T + M[:3, 3]))
    return out


def normals_of(t):
    n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
    return n / (np.linalg.norm(n, axis=1, keepdims=True) + 1e-12)


def shade(hex_color, normals, light, alpha=1.0):
    """Lambert + brillo especular, para que los tonos oscuros (negro, grafito) muestren la forma."""
    base = np.array(matplotlib.colors.to_rgb(hex_color))
    lam = np.clip(np.abs(normals @ light), 0, 1)
    rgb = base[None, :] * (0.5 + 0.5 * lam[:, None]) + 0.32 * lam[:, None] ** 6
    return np.c_[np.clip(rgb, 0, 1), np.full(len(rgb), alpha)]


def view_matrix(azim_deg, elev_deg):
    """Filas: derecha, arriba y hacia el observador, para una cámara en (azimut, elevación)."""
    a, e = np.radians(azim_deg), np.radians(elev_deg)
    toward = np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])
    right = np.cross([0, 0, 1], toward)
    right /= np.linalg.norm(right)
    up = np.cross(toward, right)
    return np.vstack([right, up, toward])


VIEWS = {'xz': np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float),   # lateral, mirando hacia +Y
         'yz': np.array([[0, 1, 0], [0, 0, 1], [1, 0, 0]], float),    # frontal, desde +X
         'xy': np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]], float)}    # planta, desde arriba


def render(ax, T, R, alpha=1.0, max_tris=None):
    """Proyecta las mallas con la matriz de vista R y pinta lo de atrás primero."""
    light = R[2] * 0.8 + R[1] * 0.35
    light /= np.linalg.norm(light)
    polys, cols, keys = [], [], []
    for link, t in placed(T, max_tris):
        polys.append(t @ R[:2].T)
        cols.append(shade(color_of(link), normals_of(t), light, alpha))
        keys.append((t @ R[2]).mean(1))
    order = np.argsort(np.concatenate(keys))
    ax.add_collection(PolyCollection(np.vstack(polys)[order], facecolors=np.vstack(cols)[order],
                                     edgecolors='none'))


def bounds(T, R):
    p = np.vstack([t.reshape(-1, 3) for _, t in placed(T)]) @ R.T
    return p.min(0), p.max(0)


def dim(ax, p0, p1, text, off, vertical=False):
    """Cota con flechas entre p0 y p1, desplazada 'off' (en metros)."""
    (x0, y0), (x1, y1) = p0, p1
    kw = dict(arrowstyle='<|-|>', color=INK, lw=0.9, mutation_scale=8, shrinkA=0, shrinkB=0)
    if vertical:
        ax.annotate('', (x0 + off, y0), (x0 + off, y1), arrowprops=kw)
        ax.plot([x0, x0 + off * 1.15], [y0, y0], color=MUTED, lw=0.5)
        ax.plot([x1, x0 + off * 1.15], [y1, y1], color=MUTED, lw=0.5)
        ax.text(x0 + off + (0.008 if off > 0 else -0.008), (y0 + y1) / 2, text, rotation=90,
                ha='left' if off > 0 else 'right', va='center', fontsize=9)
    else:
        ax.annotate('', (x0, y0 + off), (x1, y0 + off), arrowprops=kw)
        ax.plot([x0, x0], [y0, y0 + off * 1.15], color=MUTED, lw=0.5)
        ax.plot([x1, x1], [y1, y0 + off * 1.15], color=MUTED, lw=0.5)
        ax.text((x0 + x1) / 2, y0 + off + (0.008 if off > 0 else -0.008), text, ha='center',
                va='bottom' if off > 0 else 'top', fontsize=9)


def style(ax, title):
    ax.set_title(title, fontsize=11, loc='left')
    ax.grid(color='#ecebe5', lw=0.6)
    ax.set_axisbelow(True)


def axis_name(v):
    k = int(np.argmax(np.abs(v)))
    return ('+' if v[k] > 0 else '−') + 'XYZ'[k]


def fig_3d(medidas):
    fig, axes = plt.subplots(1, 2, figsize=(12, 6))
    for ax, (q, titulo) in zip(axes, [(Q_CERO, 'q = 0: pose plegada (reposo)'),
                                      (Q_L, 'Pose de referencia en L')]):
        R = view_matrix(-55, 22)
        T = world(q)
        render(ax, T, R)
        lo, hi = bounds(T, R)
        pad = 0.04
        ax.set_xlim(lo[0] - pad, hi[0] + pad)
        ax.set_ylim(lo[1] - pad, hi[1] + pad)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.text(0.0, 1.0, titulo, transform=ax.transAxes, fontsize=11, va='top')
        # ejes del mundo en la base
        for v, c, n in zip(np.eye(3), ['#c0392b', '#1e8449', '#2a78d6'], 'xyz'):
            p = (np.zeros(3), 0.08 * v)
            p2 = [pp @ R[:2].T for pp in p]
            ax.annotate('', p2[1], p2[0], arrowprops=dict(arrowstyle='-|>', color=c, lw=1.2))
            ax.text(*(p2[1] * 1.15), n, color=c, fontsize=9)
    fig.text(0.5, 0.02, 'Grafito y negro: brazo Piper. Negro mate: gripper Pika. Plata: D405 y fisheye. '
             'Ejes del mundo en la base: x rojo, y verde, z azul.', ha='center', color=MUTED,
             fontsize=9)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(os.path.join(OUT, 'fig_3d.png'), dpi=130)
    plt.close(fig)


def fig_vistas(medidas):
    T = world(Q_L)
    s = skeleton(Q_L)
    tcp, base = s[-1], s[0]
    j2, j3, j5, j6 = s[2], s[3], s[5], s[6]
    # Lateral X-Z con las cotas de cada tramo
    fig, ax = plt.subplots(figsize=(9, 6.5))
    render(ax, T, VIEWS['xz'])
    ax.plot(s[:, 0], s[:, 2], '-o', color=C_ROJO, lw=1.4, ms=4, mfc='white', zorder=5)
    lo, hi = bounds(T, VIEWS['xz'])
    dim(ax, (base[0], 0), (base[0], j2[2]), f'hombro {j2[2]:.3f} m', -0.07, vertical=True)
    dim(ax, (j2[0], j2[2]), (j3[0], j3[2]), f'brazo {np.linalg.norm(j3 - j2):.3f} m', -0.035,
        vertical=True)
    dim(ax, (j3[0], j3[2]), (j5[0], j5[2]), f'antebrazo {j5[0] - j3[0]:.3f} m', 0.07)
    dim(ax, (j5[0], j5[2]), (j6[0], j6[2]), f'{j6[0] - j5[0]:.3f}', 0.07)
    dim(ax, (j6[0], j6[2]), (tcp[0], tcp[2]), f'Pika → TCP {tcp[0] - j6[0]:.3f} m', 0.07)
    dim(ax, (base[0], 0), (tcp[0], 0), f'alcance horizontal del TCP {tcp[0] - base[0]:.3f} m',
        -0.06)
    dim(ax, (tcp[0], 0), (tcp[0], tcp[2]), f'TCP z = {tcp[2]:.3f} m', 0.05, vertical=True)
    ax.text(tcp[0] + 0.01, tcp[2] - 0.025, 'TCP (pika_tcp)', color=C_ROJO, fontsize=9)
    ax.axhline(0, color=MUTED, lw=0.8)
    ax.set_xlim(lo[0] - 0.12, hi[0] + 0.12)
    ax.set_ylim(-0.12, hi[1] + 0.1)
    ax.set_aspect('equal')
    ax.set_xlabel('X (m), adelante →')
    ax.set_ylabel('Z (m)')
    style(ax, f'Vista lateral (plano X-Z), pose en L: J2 {np.degrees(Q_L["joint2"]):.1f}°, '
              f'J3 {np.degrees(Q_L["joint3"]):.1f}°, J5 {np.degrees(Q_L["joint5"]):.1f}°')
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'fig_lateral.png'), dpi=130)
    plt.close(fig)
    medidas['pose_L'] = {k: round(v, 4) for k, v in Q_L.items()}
    medidas['tramos_m'] = {'base_a_hombro_z': round(float(j2[2]), 4),
                           'brazo_J2_J3': round(float(np.linalg.norm(j3 - j2)), 4),
                           'antebrazo_J3_J5': round(float(np.linalg.norm(j5 - j3)), 4),
                           'muneca_J5_J6': round(float(np.linalg.norm(j6 - j5)), 4),
                           'J6_a_TCP_pika': round(float(np.linalg.norm(tcp - j6)), 4)}
    medidas['tcp_en_pose_L_m'] = np.round(tcp, 4).tolist()

    # Frontal Y-Z: anchos de la base y del gripper
    fig, ax = plt.subplots(figsize=(6.5, 6.5))
    render(ax, T, VIEWS['yz'])
    base_pts = np.vstack([t.reshape(-1, 3) for l, t in placed(T) if l == 'base_link'])
    grip_pts = np.vstack([t.reshape(-1, 3) for l, t in placed(T) if l == 'gripper_base'])
    by, gy = (base_pts[:, 1].min(), base_pts[:, 1].max()), (grip_pts[:, 1].min(), grip_pts[:, 1].max())
    dim(ax, (by[0], 0), (by[1], 0), f'base {by[1] - by[0]:.3f} m', -0.05)
    dim(ax, (gy[0], grip_pts[:, 2].max()), (gy[1], grip_pts[:, 2].max()),
        f'gripper Pika {gy[1] - gy[0]:.3f} m', 0.05)
    lo, hi = bounds(T, VIEWS['yz'])
    ax.axhline(0, color=MUTED, lw=0.8)
    ax.set_xlim(lo[0] - 0.12, hi[0] + 0.12)
    ax.set_ylim(-0.1, hi[1] + 0.1)
    ax.set_aspect('equal')
    ax.set_xlabel('Y (m) →, izquierda del robot (visto de frente)')
    ax.set_ylabel('Z (m)')
    style(ax, 'Vista frontal (plano Y-Z), pose en L')
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'fig_frontal.png'), dpi=130)
    plt.close(fig)
    medidas['anchos_m'] = {'base': round(float(by[1] - by[0]), 4),
                           'gripper_pika': round(float(gy[1] - gy[0]), 4)}


def fig_cadena(medidas):
    fig, axes = plt.subplots(1, 2, figsize=(15, 6.5))
    tramos = {}
    for ax, (q, titulo) in zip(axes, [(Q_CERO, 'Cadena en q = 0 (plegado)'),
                                      (Q_L, 'Cadena en la pose en L')]):
        T = world(q)
        render(ax, T, VIEWS['xz'], alpha=0.18)
        s = skeleton(q)
        fr = joint_frames(q)
        ax.plot(s[:, 0], s[:, 2], '-', color=INK, lw=1.6, zorder=5)
        ax.scatter(s[1:-1, 0], s[1:-1, 2], s=42, color=C_GRAFITO, edgecolor='white', zorder=6)
        ax.scatter([s[-1, 0]], [s[-1, 2]], s=42, color=C_ROJO, edgecolor='white', zorder=6)
        nombres = ['base'] + ARM + ['TCP']
        filas = []
        for i in range(1, len(s)):
            d = s[i] - s[i - 1]
            filas.append(f'{nombres[i - 1]} → {nombres[i]}:  ΔX {d[0]:+.4f}  ΔZ {d[2]:+.4f}  '
                         f'|d| {np.linalg.norm(d):.4f} m')
            if q is Q_L:
                tramos[f'{nombres[i - 1]}->{nombres[i]}'] = np.round(d, 4).tolist()
        # J1/J2 y J4/J5 comparten origen: una sola etiqueta por punto
        grupos = []
        for n in ARM:
            p, a = fr[n]
            for g in grupos:
                if np.linalg.norm(g[0] - p) < 1e-3:
                    g[1].append(f'{n} ({axis_name(a)})')
                    break
            else:
                grupos.append((p, [f'{n} ({axis_name(a)})']))
        for k, (p, etiquetas) in enumerate(grupos):
            ax.annotate(' · '.join(etiquetas), (p[0], p[2]), xytext=(-8, 6 if k % 2 == 0 else -16),
                        textcoords='offset points', ha='right', fontsize=8.5,
                        bbox=dict(fc='white', ec='none', alpha=0.7, pad=1))
        ax.text(0.02, 0.02, '\n'.join(filas), transform=ax.transAxes, fontsize=8,
                family='DejaVu Sans Mono', va='bottom',
                bbox=dict(fc='white', ec='#d6d5ce', alpha=0.9))
        lo, hi = bounds(T, VIEWS['xz'])
        ax.set_xlim(min(lo[0], -0.35) - 0.05, max(hi[0], 0.55) + 0.05)
        ax.set_ylim(-0.32, max(hi[1], 0.5) + 0.05)
        ax.set_aspect('equal')
        ax.set_xlabel('X (m), adelante →')
        ax.set_ylabel('Z (m)')
        style(ax, titulo)
    fig.text(0.5, 0.01, 'Ejes en el mundo para cada pose. ΔY = 0 en todos los tramos con J1 = '
             'J4 = J6 = 0. TCP = pika_tcp (0,185 m desde la brida, eje de las garras).',
             ha='center', color=MUTED, fontsize=9)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(os.path.join(OUT, 'fig_cadena.png'), dpi=130)
    plt.close(fig)
    medidas['desplazamientos_pose_L_m'] = tramos


def fig_articulaciones(medidas):
    # Plano de dibujo de cada articulación: el que es perpendicular a su eje en la pose en L
    planos = {'joint1': 'xy', 'joint2': 'xz', 'joint3': 'xz', 'joint4': 'yz', 'joint5': 'xz',
              'joint6': 'yz'}
    fig, axes = plt.subplots(2, 4, figsize=(17, 9))
    libertades = {}
    for ax, n in zip(axes.flat, ARM):
        lo_, hi_ = JOINT[n]['limit']
        R = VIEWS[planos[n]]
        render(ax, world(Q_L), R, alpha=0.14, max_tris=2500)
        for valor, color, ls, etiqueta in [(lo_, SERIES[0], '--', f'mín {np.degrees(lo_):.0f}°'),
                                           (Q_L.get(n, 0.0), INK, '-', 'referencia'),
                                           (hi_, SERIES[1], '-.', f'máx {np.degrees(hi_):.0f}°')]:
            q = dict(Q_L)
            q[n] = valor
            T = world(q)
            pts = np.vstack([skeleton(q), T['pika_depth_link'][:3, 3]])
            p2 = pts @ R[:2].T
            ax.plot(p2[:-1, 0], p2[:-1, 1], ls, color=color, lw=1.6, label=etiqueta)
            ax.plot(*p2[-2], 'o', color=color, ms=4)
            ax.plot(*p2[-1], 's', color=color, ms=4)
            if n in ('joint4', 'joint6'):
                # el giro se ve en la cámara (cuadrado) alrededor del eje de la herramienta
                ax.plot([p2[-2, 0], p2[-1, 0]], [p2[-2, 1], p2[-1, 1]], ':', color=color, lw=1)
        p, a = joint_frames(Q_L)[n]
        pc = p @ R[:2].T
        ax.plot(*pc, 'o', color=C_ROJO, ms=7, zorder=7)
        ax.set_aspect('equal')
        if n in ('joint4', 'joint6'):
            # Giros alrededor del eje del antebrazo / herramienta: se mira a lo largo del eje,
            # con zoom en la muñeca, y se dibuja el arco que recorre la D405.
            arco = []
            for v in np.linspace(lo_, hi_, 60):
                q = dict(Q_L)
                q[n] = v
                arco.append(world(q)['pika_depth_link'][:3, 3] @ R[:2].T)
            arco = np.array(arco)
            ax.plot(arco[:, 0], arco[:, 1], '-', color=MUTED, lw=1, zorder=4)
            ax.set_xlim(pc[0] - 0.11, pc[0] + 0.11)
            ax.set_ylim(pc[1] - 0.11, pc[1] + 0.11)
        else:
            ax.autoscale_view()
            x0, x1 = ax.get_xlim()
            y0, y1 = ax.get_ylim()
            m = 0.06
            ax.set_xlim(x0 - m, x1 + m)
            ax.set_ylim(y0 - m, y1 + m)
        ax.legend(fontsize=8, loc='lower right', frameon=False)
        ax.set_xticks([])
        ax.set_yticks([])
        style(ax, f'{n} · {FUNCION[n]}\nrotacional, rango [{np.degrees(lo_):.0f}°, '
                  f'{np.degrees(hi_):.0f}°] = {np.degrees(hi_ - lo_):.0f}°')
        libertades[n] = {'tipo': 'rotacional', 'funcion': FUNCION[n],
                         'rango_rad': [lo_, hi_], 'rango_grados': [round(np.degrees(lo_), 1),
                                                                   round(np.degrees(hi_), 1)],
                         'eje_en_pose_L': axis_name(a)}
    # Gripper: dos garras prismáticas
    ax = axes.flat[6]
    jl = JOINT['pika_jaw_left_joint']['limit']
    R = VIEWS['xy']
    for valor, alpha in [(jl[1], 0.35), (0.0, 1.0)]:
        q = dict(Q_L)
        q['pika_jaw_left_joint'], q['pika_jaw_right_joint'] = valor, -valor
        render(ax, world(q), R, alpha=alpha)
    centro = world(Q_L)['gripper_base'][:3, 3] @ R[:2].T
    ax.set_xlim(centro[0] - 0.05, centro[0] + 0.20)
    ax.set_ylim(centro[1] - 0.09, centro[1] + 0.09)
    ax.set_aspect('equal')
    ax.text(0.02, 0.04, f'opaco: cerrado (0 mm)\ntranslúcido: abierto ({2 * jl[1] * 1000:.0f} mm)',
            transform=ax.transAxes, fontsize=8.5, color=MUTED)
    ax.set_xticks([])
    ax.set_yticks([])
    style(ax, f'Gripper Pika · 2 garras prismáticas\n0–{jl[1] * 1000:.0f} mm cada una '
              f'(apertura 0–{2 * jl[1] * 1000:.0f} mm), vista desde arriba')
    libertades['gripper'] = {'tipo': '2 prismáticas (en espejo)', 'por_garra_m': list(jl),
                             'apertura_total_m': [0.0, 2 * jl[1]]}
    # Resumen
    ax = axes.flat[7]
    ax.axis('off')
    filas = [f'{n}  {FUNCION[n]:<20s} [{np.degrees(JOINT[n]["limit"][0]):5.0f}°, '
             f'{np.degrees(JOINT[n]["limit"][1]):4.0f}°]' for n in ARM]
    ax.text(0, 0.95, '6 GDL rotacionales + pinza\n\n' + '\n'.join(filas) +
            f'\n\npinza: 0–{2 * jl[1] * 1000:.0f} mm de apertura\n\n'
            'Línea llena: pose en L. Rayas: mínimo.\nPunto-raya: máximo. Círculo: TCP.\n'
            'Cuadrado: D405. Punto rojo: la\narticulación que se mueve. Gris (J4,\n'
            'J6): arco que recorre la D405.\n\n'
            'Solo cinemática: algunos extremos\n(p. ej. J2 a 180°) chocarían con la\n'
            'base o el piso.',
            va='top', fontsize=9, family='DejaVu Sans Mono')
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'fig_articulaciones.png'), dpi=120)
    plt.close(fig)
    medidas['libertades'] = libertades


def fig_alcance(medidas, n=40000):
    rng = np.random.default_rng(1)
    lims = np.array([JOINT[nm]['limit'] for nm in ARM])
    Q = rng.uniform(lims[:, 0], lims[:, 1], size=(n, 6))
    P = np.array([world(dict(zip(ARM, q)))['pika_tcp'][:3, 3] for q in Q])
    hombro = skeleton(Q_CERO)[2]
    r = np.hypot(P[:, 0], P[:, 1])
    d_hombro = np.linalg.norm(P - hombro, axis=1)
    fig, axes = plt.subplots(1, 2, figsize=(14, 6.2))
    ax = axes[0]
    signo = np.where(P[:, 0] >= 0, 1, -1)
    ax.scatter(signo * r, P[:, 2], s=1, alpha=0.08, color=C_GRAFITO, rasterized=True)
    render(ax, world(Q_L), VIEWS['xz'], alpha=0.5, max_tris=4000)
    ax.plot(*hombro[[0, 2]], 'o', color=C_ROJO, ms=7)
    rmax = d_hombro.max()
    t = np.linspace(0, 2 * np.pi, 200)
    ax.plot(hombro[0] + rmax * np.cos(t), hombro[2] + rmax * np.sin(t), '--', color=C_ROJO, lw=1)
    ax.text(hombro[0] + rmax * 0.72, hombro[2] + rmax * 0.72,
            f'máx. desde el hombro\n{rmax:.3f} m', color=C_ROJO, fontsize=9)
    ax.axhline(0, color=MUTED, lw=0.8)
    ax.set_aspect('equal')
    ax.set_xlabel('distancia horizontal al eje de la base, con signo de X (m)')
    ax.set_ylabel('Z (m)')
    style(ax, f'Alcance del TCP, corte lateral ({n} posturas al azar dentro de los límites)')
    ax = axes[1]
    ax.scatter(P[:, 0], P[:, 1], s=1, alpha=0.08, color=C_GRAFITO, rasterized=True)
    lo_, hi_ = JOINT['joint1']['limit']
    for ang, txt in [(lo_, f'J1 mín {np.degrees(lo_):.0f}°'), (hi_, f'J1 máx {np.degrees(hi_):.0f}°')]:
        ax.plot([0, 0.7 * np.cos(ang)], [0, 0.7 * np.sin(ang)], '--', color=C_ROJO, lw=1)
        ax.text(0.72 * np.cos(ang), 0.72 * np.sin(ang), txt, color=C_ROJO, fontsize=9,
                ha='center')
    ax.plot(0, 0, 'o', color=INK)
    ax.set_aspect('equal')
    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    style(ax, 'Alcance del TCP, vista desde arriba (sector que cubre J1)')
    fig.text(0.5, 0.01, 'Sin revisar choques entre eslabones ni con el piso: es la envolvente '
             'cinemática. Círculo rojo: hombro (joint2).', ha='center', color=MUTED,
             fontsize=9)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(os.path.join(OUT, 'fig_alcance.png'), dpi=120)
    plt.close(fig)
    medidas['alcance_tcp_m'] = {'max_desde_hombro': round(float(rmax), 4),
                                'max_horizontal_desde_eje_base': round(float(r.max()), 4),
                                'z_min': round(float(P[:, 2].min()), 4),
                                'z_max': round(float(P[:, 2].max()), 4),
                                'muestras': n}


def main():
    os.makedirs(OUT, exist_ok=True)
    medidas = {'modelo': 'pika_description/urdf/pika_piper_standalone.urdf.xacro',
               'tcp': 'pika_tcp', 'nota': 'generado por scripts/figuras_piper_pika.py'}
    for f in (fig_3d, fig_vistas, fig_cadena, fig_articulaciones, fig_alcance):
        f(medidas)
        print(f'{f.__name__}: listo', flush=True)
    with open(os.path.join(OUT, 'medidas.json'), 'w') as fh:
        json.dump(medidas, fh, indent=1, ensure_ascii=False)
    print(f'Figuras y medidas en {os.path.abspath(OUT)}')


if __name__ == '__main__':
    main()
