#!/usr/bin/env python3
"""Genera arquitectura_comunicaciones.png y .svg desde arquitectura_comunicaciones.dot.

El enrutado ortogonal de Graphviz (flechas con codos) trata cualquier nodo como obstáculo, así
que las franjas de fondo de cada capa no pueden estar en el mismo dibujo. Se dibuja en dos
pasadas con el mismo marco (los nodos invisibles esquina_inf / esquina_sup) y se superponen:
  fondo  = encabezado + sección FRANJAS, flechas rectas
  frente = todo menos FRANJAS, flechas ortogonales, fondo transparente

Uso (desde cualquier carpeta; necesita Graphviz y Pillow):
  python3 docs/arquitectura/generar_diagrama.py
"""
import os
import re
import subprocess
import tempfile

from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
FUENTE = os.path.join(AQUI, 'arquitectura_comunicaciones.dot')
SALIDA = os.path.join(AQUI, 'arquitectura_comunicaciones')
DPI = 100


def partes(texto):
    ini = texto.index('  // FRANJAS')
    fin = texto.index('  // FIN FRANJAS')
    fondo = texto[:fin].replace('splines=ortho', 'splines=false') + '}\n'
    frente = (texto[:ini] + texto[fin:]).replace('bgcolor="#fcfcfb"', 'bgcolor="transparent"')
    # El título se dibuja solo en el fondo. En el frente queda transparente, para que las dos
    # pasadas tengan exactamente el mismo tamaño.
    titulo = frente.index('label=<<B>Pika + Piper')
    fin_titulo = frente.index('labelloc=t];', titulo)
    frente = (frente[:titulo] + frente[titulo:fin_titulo].replace('COLOR="#6b6a63"', 'COLOR="transparent"')
              + 'labelloc=t, fontcolor="transparent"];' + frente[fin_titulo + len('labelloc=t];'):])
    return fondo, frente


def render(dot, formato, salida):
    with tempfile.NamedTemporaryFile('w', suffix='.dot', delete=False) as f:
        f.write(dot)
    subprocess.run(['neato', '-n2', f'-T{formato}', f'-Gdpi={DPI}', f.name, '-o', salida],
                   check=True)
    os.unlink(f.name)


def main():
    fondo, frente = partes(open(FUENTE).read())
    with tempfile.TemporaryDirectory() as tmp:
        # PNG: superposición de las dos pasadas
        render(fondo, 'png', f'{tmp}/fondo.png')
        render(frente, 'png', f'{tmp}/frente.png')
        a = Image.open(f'{tmp}/fondo.png').convert('RGBA')
        b = Image.open(f'{tmp}/frente.png').convert('RGBA')
        if a.size != b.size:
            raise SystemExit(f'Las dos pasadas tienen distinto tamaño: {a.size} vs {b.size}')
        Image.alpha_composite(a, b).convert('RGB').save(SALIDA + '.png')

        # SVG: los grupos del frente se insertan dentro del dibujo del fondo
        render(fondo, 'svg', f'{tmp}/fondo.svg')
        render(frente, 'svg', f'{tmp}/frente.svg')
        svg_fondo = open(f'{tmp}/fondo.svg').read()
        svg_frente = open(f'{tmp}/frente.svg').read()
        g_ini = svg_frente.index('<g id="graph0"')
        cuerpo = svg_frente[svg_frente.index('>', g_ini) + 1:svg_frente.rindex('</g>')]
        cuerpo = re.sub(r'id="(node|edge)(\d+)"', r'id="frente_\1\2"', cuerpo)
        cierre = svg_fondo.rindex('</g>')
        open(SALIDA + '.svg', 'w').write(svg_fondo[:cierre] + cuerpo + svg_fondo[cierre:])
    print(f'Listo: {SALIDA}.png y .svg')


if __name__ == '__main__':
    main()
