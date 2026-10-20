#!/usr/bin/env python3
# -*-coding:utf8-*-
# Compara variantes de la escena (iluminación o densidad) en una figura: una columna por variante,
# con la escena completa arriba y lo que ve la D405 del gripper abajo.
#
# Uso: panel_variantes.py <salida.png> <título> <carpeta>:<rótulo> [<carpeta>:<rótulo> ...]
# Cada carpeta es la --salida de una corrida de escena_nbv_demo.py con el manzano de Helios.
import json
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
from PIL import Image  # noqa: E402

MUTED = '#666666'


def main():
    salida, titulo, variantes = sys.argv[1], sys.argv[2], [a.split(':', 1) for a in sys.argv[3:]]
    n = len(variantes)
    fig, ejes = plt.subplots(2, n, figsize=(3.3 * n, 5.4), gridspec_kw={'height_ratios': [1.0, 1.2]})
    if n == 1:
        ejes = ejes.reshape(2, 1)
    for k, (carpeta, rotulo) in enumerate(variantes):
        d = json.load(open(os.path.join(carpeta, 'nbv_helios_escena.json')))
        escena = Image.open(os.path.join(carpeta, 'nbv_helios_escena.png'))
        ancho, alto = escena.size
        escena = escena.crop((int(ancho * 0.12), 0, ancho, int(alto * 0.85)))     # brazo y árbol
        ejes[0, k].imshow(escena)
        ejes[0, k].set_title(rotulo, fontsize=11, loc='left')
        ejes[1, k].imshow(Image.open(os.path.join(carpeta, 'nbv_helios_d405_color.png')))
        ejes[1, k].set_xlabel(f'D405 en la mejor vista: {d["mejor"]["visibilidad"]:.0%} visible',
                              fontsize=9, color=MUTED)
        for e in ejes[:, k]:
            e.set_xticks([])
            e.set_yticks([])
    fig.suptitle(titulo, x=0.01, ha='left', fontsize=12)
    fig.tight_layout()
    fig.savefig(salida, dpi=110, bbox_inches='tight')
    print(f'Listo: {salida}')


if __name__ == '__main__':
    main()
