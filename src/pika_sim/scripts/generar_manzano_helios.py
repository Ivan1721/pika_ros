#!/usr/bin/env python3
# -*-coding:utf8-*-
# Genera un manzano realista para pika_sim con Helios (PlantArchitecture, UC Davis) y lo exporta
# en mallas que Gazebo Classic carga directamente.
#
# Helios arma la planta completa: tronco, ramas con sus horquetas, pecíolos, hojas, pedúnculos y
# manzanas, con texturas fotográficas de corteza, hoja y fruto. Este script:
#   - recorta cada hoja a la silueta de la foto de hoja de manzano: Helios la dibuja como un
#     rectángulo curvo con transparencia, y la cámara de profundidad de Gazebo no respeta la
#     transparencia (vería rectángulos)
#   - escribe madera.obj (tronco, ramas, pecíolos y pedúnculos), hojas.obj y frutas.obj, con sus .mtl
#     y texturas
#   - escribe verdad.json (centro y radio de cada manzana, en el marco del árbol) y
#     triangulos.npz para el planner: hojas y madera (visibilidad por trazado de rayos) y solo
#     tronco y ramas (choques: pecíolos y pedúnculos ceden)
#
# Necesita PyHelios (MIT; el núcleo de Helios y sus texturas son LGPL-2.1). Va en un entorno
# virtual aparte, sin ROS, porque trae sus propias bibliotecas:
#   python3 -m venv ~/.venvs/helios && ~/.venvs/helios/bin/pip install pyhelios3d pillow
#   env -u PYTHONPATH ~/.venvs/helios/bin/python -I generar_manzano_helios.py --modelo apple_fruitingwall
#       [--densidad base|media|alta] [--flor P --cuaja P --racimo N --brote P --hoja F]
#
# Modelos: apple_fruitingwall (muro frutal en espaldera, el sistema de los huertos pensados para
# cosecha robótica; por defecto) y apple (árbol libre). La edad en días fija la fenología: hacia
# los 450 días el árbol está en reposo invernal, sin hojas.
import argparse
import json
import os
import shutil

import numpy as np
from PIL import Image


def silueta_hoja(png, n=24, encoger=0.985):
    """Contorno de la hoja en coordenadas UV (estrellado desde el centroide de la máscara)."""
    a = np.asarray(Image.open(png).convert('RGBA'))[..., 3] > 128
    alto, ancho = a.shape
    ys, xs = np.nonzero(a)
    cx, cy = xs.mean(), ys.mean()
    puntos = []
    for t in np.linspace(0, 2 * np.pi, n, endpoint=False):
        d = np.array([np.cos(t), np.sin(t)])
        r = np.arange(0, max(alto, ancho), 0.5)
        x, y = cx + r * d[0], cy + r * d[1]
        ok = (x >= 0) & (x < ancho) & (y >= 0) & (y < alto)
        r, x, y = r[ok], x[ok].astype(int), y[ok].astype(int)
        dentro = np.nonzero(a[y, x])[0]
        rmax = r[dentro[-1]] if len(dentro) else 0.0
        puntos.append((cx + encoger * rmax * d[0], cy + encoger * rmax * d[1]))
    p = np.array(puntos)
    centro = np.array([cx / ancho, 1.0 - cy / alto])
    return centro, np.c_[p[:, 0] / ancho, 1.0 - p[:, 1] / alto]   # v de OBJ: 0 abajo


def malla_silueta(centro, borde):
    """Triangulación de la silueta: centro, anillo interior (mitad) y borde."""
    n = len(borde)
    interior = centro + 0.5 * (borde - centro)
    uv = np.vstack([centro, interior, borde])
    tris = []
    for i in range(n):
        j = (i + 1) % n
        tris.append((0, 1 + i, 1 + j))
        tris.append((1 + i, 1 + n + i, 1 + n + j))
        tris.append((1 + i, 1 + n + j, 1 + j))
    return uv, np.array(tris)


def uv_a_3d(uv_pts, uv_tris, xyz_tris):
    """Lleva puntos UV a 3D con la interpolación lineal por triángulos de la hoja de Helios."""
    out = np.zeros((len(uv_pts), 3))
    for k, p in enumerate(uv_pts):
        mejor, peor_min = None, -np.inf
        for (a, b, c), (A, B, C) in zip(uv_tris, xyz_tris):
            m = np.array([[b[0] - a[0], c[0] - a[0]], [b[1] - a[1], c[1] - a[1]]])
            if abs(np.linalg.det(m)) < 1e-12:
                continue
            s, t = np.linalg.solve(m, p - a)
            w = np.array([1 - s - t, s, t])
            if w.min() > peor_min:                       # el triángulo que mejor lo contiene
                peor_min, mejor = w.min(), w @ np.array([A, B, C])
        out[k] = mejor
    return out


class Obj:
    """Escritor mínimo de OBJ con UV y varios materiales."""

    def __init__(self):
        self.v, self.vt, self.caras = [], [], {}

    def agregar(self, material, xyz, uv, tris):
        base_v, base_t = len(self.v), len(self.vt)
        self.v.extend(map(tuple, xyz))
        self.vt.extend(map(tuple, uv))
        self.caras.setdefault(material, []).extend(
            tuple((base_v + i + 1, base_t + i + 1) for i in t) for t in tris)

    def escribir(self, ruta, mtl):
        with open(ruta, 'w') as f:
            f.write(f'mtllib {mtl}\n')
            f.writelines(f'v {x:.5f} {y:.5f} {z:.5f}\n' for x, y, z in self.v)
            f.writelines(f'vt {u:.4f} {v:.4f}\n' for u, v in self.vt)
            for material, caras in self.caras.items():
                f.write(f'usemtl {material}\n')
                f.writelines('f ' + ' '.join(f'{a}/{b}' for a, b in c) + '\n' for c in caras)


def escribir_mtl(ruta, materiales):
    with open(ruta, 'w') as f:
        for nombre, m in materiales.items():
            f.write(f'newmtl {nombre}\nKa {m["kd"]}\nKd {m["kd"]}\nKs 0.05 0.05 0.05\nillum 2\n')
            if m.get('textura'):
                f.write(f'map_Kd {m["textura"]}\n')


# Densidad de fruta y follaje: parámetros de los brotes de Helios (lateral, proleptic...)
#   flor    probabilidad de que una yema floral brote          (Helios: 0,3)
#   cuaja   probabilidad de que una flor cuaje en fruto         (Helios: 0,3)
#   racimo  flores por pedúnculo: manzanas juntas en un dardo   (Helios: 1)
#   brote   probabilidad mínima de brotación vegetativa: más brotes, más hojas (Helios: 0,1)
#   hoja    factor sobre el tamaño de la hoja                   (Helios: 1,0)
DENSIDADES = {
    'base': dict(flor=0.3, cuaja=0.3, racimo=1, brote=0.1, hoja=1.0),
    'media': dict(flor=0.5, cuaja=0.45, racimo=2, brote=0.25, hoja=1.1),
    'alta': dict(flor=0.7, cuaja=0.6, racimo=3, brote=0.4, hoja=1.2),
}


def aplicar_densidad(pa, d):
    for lab in pa.listShootTypeLabels():
        p = pa.getCurrentShootParameters(lab)
        inf = p['phytomer_parameters']['inflorescence']
        p['flower_bud_break_probability']['parameters'] = [d['flor']]
        p['fruit_set_probability']['parameters'] = [d['cuaja']]
        inf['flowers_per_peduncle']['parameters'] = [float(d['racimo'])]
        p['vegetative_bud_break_probability_min']['parameters'] = [d['brote']]
        escala = p['phytomer_parameters']['leaf']['prototype_scale']['parameters']
        p['phytomer_parameters']['leaf']['prototype_scale']['parameters'] = [escala[0] * d['hoja']]
        pa.defineShootType(lab, p)


def separar(centros, radios, rng, holgura=0.003, max_desp=0.06, iters=400):
    """Helios pone las manzanas de un mismo dardo casi en el mismo punto, y con mucha fruta se
    interpenetran. Las separa como esferas que se empujan, sin alejarlas más de max_desp de donde
    nacieron, y ralea (quita) las que igual no caben. Devuelve los centros nuevos y cuáles quedan."""
    anclas, c = centros.copy(), centros.copy()
    n = len(c)
    req = radios[:, None] + radios[None] + holgura
    for _ in range(iters):
        d = c[:, None] - c[None]
        dist = np.linalg.norm(d, axis=2)
        np.fill_diagonal(dist, np.inf)
        choque = dist < req
        if not choque.any():
            break
        juntas = dist < 1e-6                                  # mismo punto: dirección al azar
        if juntas.any():
            d[juntas] = rng.normal(size=(int(juntas.sum()), 3))
            dist[juntas] = np.linalg.norm(d[juntas], axis=1)
        empuje = np.where(choque, (req - dist) / 2, 0.0)[..., None] * d / dist[..., None]
        c += 0.6 * empuje.sum(1)
        desp = c - anclas
        largo = np.linalg.norm(desp, axis=1, keepdims=True)
        c = anclas + desp * np.minimum(1.0, max_desp / np.maximum(largo, 1e-9))
    quedan = np.ones(n, bool)
    dist = np.linalg.norm(c[:, None] - c[None], axis=2)
    np.fill_diagonal(dist, np.inf)
    choque = dist < req - 0.002
    while True:                                               # raleo: la que más choca, primero
        cuenta = (choque & quedan[None] & quedan[:, None]).sum(1)
        if cuenta.max() == 0:
            break
        quedan[np.argmax(cuenta)] = False
    return c, quedan


def tubo(p0, p1, radio, lados=6):
    """Triángulos de un cilindro entre p0 y p1 (el pedúnculo de una manzana que se movió)."""
    eje = p1 - p0
    eje = eje / np.linalg.norm(eje)
    u = np.cross(eje, [0, 0, 1] if abs(eje[2]) < 0.9 else [1, 0, 0])
    u /= np.linalg.norm(u)
    v = np.cross(eje, u)
    ang = np.linspace(0, 2 * np.pi, lados, endpoint=False)
    anillo = radio * (np.cos(ang)[:, None] * u + np.sin(ang)[:, None] * v)
    a, b = p0 + anillo, p1 + anillo
    tris = []
    for i in range(lados):
        j = (i + 1) % lados
        tris += [(a[i], b[i], b[j]), (a[i], b[j], a[j])]
    return np.array(tris)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--modelo', default='apple_fruitingwall', choices=['apple_fruitingwall', 'apple'])
    ap.add_argument('--edad', type=float, default=640, help='días; ~450 es reposo invernal')
    ap.add_argument('--semilla', type=int, default=7)
    ap.add_argument('--salida', default=os.path.expanduser('~/.cache/pika_sim/manzanos'))
    ap.add_argument('--densidad', default='base', choices=list(DENSIDADES),
                    help='fruta y follaje: base (la de Helios), media o alta')
    for k, ayuda in [('flor', 'brotación floral'), ('cuaja', 'cuaja de frutos'), ('racimo', 'flores por pedúnculo'),
                     ('brote', 'brotación vegetativa mínima'), ('hoja', 'factor de tamaño de hoja')]:
        ap.add_argument(f'--{k}', type=float, default=None, help=f'{ayuda}; pisa el de --densidad')
    args = ap.parse_args()

    from pyhelios import Context, PlantArchitecture
    from pyhelios.types import vec3

    c = Context()
    c.seedRandomGenerator(args.semilla)
    pa = PlantArchitecture(c)
    pa.disableMessages()
    pa.loadPlantModelFromLibrary(args.modelo)
    densidad = dict(DENSIDADES[args.densidad])
    propios = {k: getattr(args, k) for k in densidad if getattr(args, k) is not None}
    densidad.update(propios)
    if args.densidad != 'base' or propios:
        aplicar_densidad(pa, densidad)
    pid = pa.buildPlantInstanceFromLibrary(vec3(0, 0, 0), args.edad)
    nombre = f'{args.modelo}_e{int(args.edad)}_s{args.semilla}'
    if args.densidad != 'base':
        nombre += f'_{args.densidad}'
    if propios:
        nombre += '_' + '_'.join(f'{k}{v:g}' for k, v in sorted(propios.items()))
    rng = np.random.default_rng(args.semilla)
    destino = os.path.join(args.salida, nombre)
    os.makedirs(destino, exist_ok=True)

    def tri(u):
        return np.array([[p.x, p.y, p.z] for p in c.getPrimitiveVertices(u)])

    def uv(u):
        return np.array([[p.x, p.y] for p in c.getPrimitiveTextureUV(u)])

    texturas = {}

    def textura(u):
        ruta = c.getPrimitiveTextureFile(u)
        if not ruta:
            return None
        texturas[os.path.basename(ruta)] = ruta
        return os.path.basename(ruta)

    # ── Madera: entrenudos (corteza con textura), pecíolos y pedúnculos ──
    madera, tris_madera, tris_ramas, vert_pedunculos = Obj(), [], [], []
    for grupo, material in [(pa.getAllInternodeUUIDs(), 'corteza'), (pa.getAllPetioleUUIDs(), 'peciolo'),
                            (pa.getAllPeduncleUUIDs(), 'pedunculo')]:
        for u in grupo:
            t = tri(u)
            if len(t) != 3:
                continue
            coords = uv(u) if (material == 'corteza' and textura(u)) else np.zeros((3, 2))
            madera.agregar(material, t, coords if len(coords) == 3 else np.zeros((3, 2)), [(0, 1, 2)])
            tris_madera.append(t)
            if material == 'corteza':
                tris_ramas.append(t)
            elif material == 'pedunculo':
                vert_pedunculos.extend(t)

    # ── Hojas: cada una recortada a la silueta de la foto ──
    hojas, tris_hojas, centros_hoja = Obj(), [], []
    png_hoja = None
    for o in pa.getPlantLeafObjectIDs(pid):
        uus = c.getObjectPrimitiveUUIDs(o)
        if png_hoja is None:
            png_hoja = c.getPrimitiveTextureFile(uus[0])
            centro, borde = silueta_hoja(png_hoja)
            uv_hoja, tris_hoja = malla_silueta(centro, borde)
            textura(uus[0])
        xyz = uv_a_3d(uv_hoja, [uv(u) for u in uus], [tri(u) for u in uus])
        hojas.agregar('hoja', xyz, uv_hoja, tris_hoja)
        tris_hojas.extend(xyz[tris_hoja])
        centros_hoja.append(xyz[0])
    hojas.escribir(os.path.join(destino, 'hojas.obj'), 'hojas.mtl')
    escribir_mtl(os.path.join(destino, 'hojas.mtl'),
                 {'hoja': {'kd': '0.55 0.75 0.45', 'textura': os.path.basename(png_hoja)}})

    # ── Manzanas: separadas para que no se interpenetren, con pedúnculo nuevo si se movieron ──
    objetos, centros, radios = [], [], []
    for o in pa.getPlantFruitObjectIDs(pid):
        uus = c.getObjectPrimitiveUUIDs(o)
        lo, hi = c.getObjectBoundingBox(o)
        objetos.append(uus)
        centros.append([(lo.x + hi.x) / 2, (lo.y + hi.y) / 2, (lo.z + hi.z) / 2])
        radios.append(float(np.mean([hi.x - lo.x, hi.y - lo.y, hi.z - lo.z])) / 2)
    centros, radios = np.array(centros), np.array(radios)
    nuevos, quedan = separar(centros, radios, rng) if len(centros) else (centros, np.ones(0, bool))
    vert_pedunculos = np.array(vert_pedunculos) if vert_pedunculos else np.zeros((0, 3))
    frutas, verdad_frutas, movidas = Obj(), [], 0
    for uus, c0, c1, r, ok in zip(objetos, centros, nuevos, radios, quedan):
        if not ok:
            continue
        desp = c1 - c0
        for u in uus:
            textura(u)
            frutas.agregar('manzana', tri(u) + desp, uv(u), [(0, 1, 2)])
        if np.linalg.norm(desp) > 0.003:
            movidas += 1
            # el pedúnculo original termina cerca de donde estaba la manzana: se prolonga hasta la nueva
            cerca = np.linalg.norm(vert_pedunculos - c0, axis=1) if len(vert_pedunculos) else np.zeros(0)
            inicio = vert_pedunculos[np.argmin(cerca)] if len(cerca) and cerca.min() < r + 0.03 else c0 + [0, 0, r]
            hacia = inicio - c1
            fin = c1 + r * 0.9 * hacia / max(np.linalg.norm(hacia), 1e-9)
            if np.linalg.norm(fin - inicio) > 0.002:
                for t in tubo(inicio, fin, 0.0015):
                    madera.agregar('pedunculo', t, np.zeros((3, 2)), [(0, 1, 2)])
                    tris_madera.append(t)
        verdad_frutas.append({'centro': [round(float(v), 4) for v in c1], 'radio': round(r, 4)})
    madera.escribir(os.path.join(destino, 'madera.obj'), 'madera.mtl')
    escribir_mtl(os.path.join(destino, 'madera.mtl'), {
        'corteza': {'kd': '0.55 0.45 0.35', 'textura': 'AppleBark.jpg'},
        'peciolo': {'kd': '0.45 0.55 0.20'}, 'pedunculo': {'kd': '0.40 0.30 0.18'}})
    frutas.escribir(os.path.join(destino, 'frutas.obj'), 'frutas.mtl')
    escribir_mtl(os.path.join(destino, 'frutas.mtl'), {'manzana': {'kd': '0.9 0.9 0.9', 'textura': 'AppleFruit.jpg'}})

    for base, ruta in texturas.items():
        shutil.copy(ruta, os.path.join(destino, base))
    np.savez_compressed(os.path.join(destino, 'triangulos.npz'),
                        hojas=np.array(tris_hojas, np.float32), madera=np.array(tris_madera, np.float32),
                        ramas=np.array(tris_ramas, np.float32))
    caja = c.getDomainBoundingBox()
    verdad = {'generador': 'Helios PlantArchitecture (pyhelios3d)', 'modelo': args.modelo, 'edad_dias': args.edad,
              'semilla': args.semilla, 'marco': 'arbol (base del tronco en el origen, z arriba)',
              'densidad': {'nombre': args.densidad, **densidad},
              'manzanas_de_helios': int(len(centros)), 'separadas': movidas, 'raleadas': int((~quedan).sum()),
              'caja': [[caja[0].x, caja[0].y], [caja[1].x, caja[1].y], [caja[2].x, caja[2].y]],
              'altura': round(pa.getPlantHeight(pid), 3), 'n_hojas': len(centros_hoja),
              'triangulos': {'madera': len(tris_madera), 'hojas': len(tris_hojas),
                             'frutas': sum(len(v) for v in frutas.caras.values())},
              'manzanas': verdad_frutas,
              'mallas': {'madera': 'madera.obj', 'hojas': 'hojas.obj', 'frutas': 'frutas.obj'}}
    with open(os.path.join(destino, 'verdad.json'), 'w') as f:
        json.dump(verdad, f, indent=1, ensure_ascii=False)
    print(f'{destino}: {len(verdad_frutas)} manzanas ({movidas} separadas, {verdad["raleadas"]} raleadas de '
          f'{len(centros)}), {len(centros_hoja)} hojas, altura {verdad["altura"]} m, triángulos {verdad["triangulos"]}')


if __name__ == '__main__':
    main()
