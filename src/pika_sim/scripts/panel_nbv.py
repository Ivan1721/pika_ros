#!/usr/bin/env python3
# -*-coding:utf8-*-
# Arma una figura con las capturas de escena_nbv_demo.py: (a) la escena en Gazebo con las vistas
# candidatas, (b) lo que ve la cámara desde la vista frontal y (c) desde la vista elegida.
# Los números salen de nbv_escena.json. No necesita ROS.
#
# Uso:
#   python3 panel_nbv.py [carpeta]      # por defecto ~/pika_ros/docs/percepcion_activa/img
import json
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

CARPETA = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser('~/pika_ros/docs/percepcion_activa/img')
INK, MUTED, SURF = '#2b2b29', '#6b6a63', '#fcfcfb'
ROJO, GRAFITO, GRIS = '#d91f2e', '#55595c', '#cccbc7'


def main():
    d = json.load(open(os.path.join(CARPETA, 'nbv_escena.json')))
    n = len(d['candidatas'])
    alc = sum(k['alcanzable'] for k in d['candidatas'])
    m, f = d['mejor'], d['frontal']
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11, 'text.color': INK,
                         'figure.facecolor': SURF})
    fig = plt.figure(figsize=(13.2, 5.6))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.81, 1], wspace=0.03, hspace=0.16)

    ax = ax_escena = fig.add_subplot(gs[:, 0])
    ax.imshow(plt.imread(os.path.join(CARPETA, 'nbv_escena.png')))
    ax.set_anchor('E')
    ax.set_title(f'(a) Escena en Gazebo: {n} vistas candidatas a {d["radio_casquete"]:.2f} m de la fruta; '
                 f'{alc} alcanzables', loc='left', fontsize=12)
    ax.axis('off')
    ax.legend(handles=[
        Line2D([], [], marker='o', ls='-', color=ROJO, ms=11, lw=2.5, label=f'elegida (visibilidad {m["visibilidad"]:.0%})'),
        Line2D([], [], marker='o', ls='-', color=ROJO, ms=7, lw=1.5, alpha=0.75, label='alcanzable, mucha visibilidad'),
        Line2D([], [], marker='o', ls='-', color=GRAFITO, ms=7, lw=1.5, label='alcanzable, poca visibilidad'),
        Line2D([], [], marker='o', ls='-', color=GRIS, ms=5, lw=1, label='no alcanzable (|J5| > 70° o error de IK)')],
        loc='lower right', fontsize=10, framealpha=0.92)

    for fila, (archivo, titulo) in enumerate([
            ('nbv_vista_frontal.png', f'(b) Vista frontal (elev. {f["elevacion"]}°, azim. {f["azimut"]}°): '
                                      f'{f["visibilidad"]:.0%} de la fruta visible'),
            ('nbv_vista_elegida.png', f'(c) Vista elegida (elev. {m["elevacion"]}°, azim. {m["azimut"]}°): '
                                      f'{m["visibilidad"]:.0%} visible')]):
        ax = fig.add_subplot(gs[fila, 1])
        ax.imshow(plt.imread(os.path.join(CARPETA, archivo)))
        ax.set_anchor('W')
        ax.set_title(titulo, loc='left', fontsize=11)
        ax.axis('off')

    fig.canvas.draw()  # aplica el aspecto de las imágenes para conocer el borde real de (a)
    fig.text(ax_escena.get_position().x0, 0.015, 'Piper + Pika en pika_sim. Visibilidad: fracción de la cara de la fruta hacia la cámara '
             'sin hojas en el camino\n(trazado de rayos sobre la geometría). Vistas (b) y (c): cámara virtual con el '
             'campo visual de la D405 (87°), sin el brazo.', fontsize=9, color=MUTED)
    salida = os.path.join(CARPETA, 'nbv_escena_panel.png')
    fig.savefig(salida, dpi=130, bbox_inches='tight')
    print(f'Listo: {salida}')


if __name__ == '__main__':
    main()
