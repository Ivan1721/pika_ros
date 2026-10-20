#!/usr/bin/env python3
# -*-coding:utf8-*-
# Calcula la compensacion de gravedad T_FF para test_piper_mit_impedance.py.
#
# En modo MIT cada motor aplica  tau = kp*(q_d - q) + kd*(0 - dq) + t_ref.
# Sin t_ref, el brazo solo se sostiene con el termino kp*(q_d - q): con kp
# bajo, J2/J3 se hunden hasta quedar apoyados en sus topes. Con
# t_ref = g(q_d), el torque de gravedad en la pose objetivo, el resorte kp
# solo tiene que vencer las perturbaciones (la mano que empuja).
#
# Lee TARGETS y KP de test_piper_mit_impedance.py, arma el URDF de Piper +
# gripper Pika (pika_description) y calcula g(q_d) con pinocchio. Tambien
# muestra cuanto se hundiria el brazo con y sin la compensacion.
#
# Requiere ROS (para xacro) y pinocchio: correrlo en la misma terminal que la
# teleop:
#   source ~/pika_ros/install/setup.bash && conda activate pika
#   python3 calcular_gravedad_mit.py            # solo muestra
#   python3 calcular_gravedad_mit.py --escribir # actualiza T_FF en el test
#
# Las masas del URDF son aproximadas (sobre todo la del gripper Pika): en el
# brazo real queda un error residual que se corrige con ESCALA_GRAVEDAD o
# midiendo el torque con el brazo quieto en la pose.
import argparse
import ast
import os
import re
import subprocess
import tempfile

import numpy as np
import pinocchio as pin

AQUI = os.path.dirname(os.path.abspath(__file__))
TEST = os.path.join(AQUI, 'test_piper_mit_impedance.py')
T_MAX = 8.0  # el protocolo MIT codifica t_ref en [-8, 8] N·m


def leer_lista(texto, nombre):
    m = re.search(rf'^{nombre}\s*=\s*(\[[^\]]*\])', texto, re.M)
    if not m:
        raise SystemExit(f'No encontre {nombre} en {TEST}')
    return [float(v) for v in ast.literal_eval(m.group(1))]


def modelo_urdf():
    xacro_file = subprocess.run(
        ['ros2', 'pkg', 'prefix', 'pika_description'], capture_output=True, text=True, check=True
    ).stdout.strip() + '/share/pika_description/urdf/pika_piper_standalone.urdf.xacro'
    urdf = subprocess.run(['xacro', xacro_file], capture_output=True, text=True, check=True).stdout
    with tempfile.NamedTemporaryFile('w', suffix='.urdf', delete=False) as f:
        f.write(urdf)
    modelo = pin.buildModelFromUrdf(f.name)
    os.unlink(f.name)
    return modelo


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--escribir', action='store_true', help='reescribe la linea T_FF del test')
    args = parser.parse_args()

    texto = open(TEST).read()
    q_d = np.array(leer_lista(texto, 'TARGETS'))
    kp = np.array(leer_lista(texto, 'KP'))

    modelo = modelo_urdf()
    datos = modelo.createData()
    iq = [modelo.joints[modelo.getJointId(f'joint{i}')].idx_q for i in range(1, 7)]
    iv = [modelo.joints[modelo.getJointId(f'joint{i}')].idx_v for i in range(1, 7)]
    lim_inf, lim_sup = modelo.lowerPositionLimit[iq], modelo.upperPositionLimit[iq]

    def gravedad(q6):
        q = pin.neutral(modelo)
        q[iq] = q6
        return pin.computeGeneralizedGravity(modelo, datos, q)[iv]

    def equilibrio(t_ff):
        # q tal que kp*(q_d - q) + t_ff = g(q), respetando los topes
        q = q_d.copy()
        for _ in range(3000):
            q_nuevo = np.clip(q_d - (gravedad(q) - t_ff) / kp, lim_inf, lim_sup)
            q = 0.8 * q + 0.2 * q_nuevo
        return q

    t_ff = gravedad(q_d)
    if np.any(np.abs(t_ff) > T_MAX):
        print(f'AVISO: algun |t_ff| supera {T_MAX} N·m y el protocolo MIT lo recortara')

    # Estabilidad: con t_ff constante, la gravedad actua como una rigidez
    # (dg/dq) que se suma al resorte kp. Si kp*I + dg/dq no es definida
    # positiva, q_d es un equilibrio inestable: el brazo se aleja solo.
    h = 1e-6
    rigidez_gravedad = np.column_stack(
        [(gravedad(q_d + h * e) - gravedad(q_d - h * e)) / (2 * h) for e in np.eye(6)])
    rigidez = np.diag(kp) + (rigidez_gravedad + rigidez_gravedad.T) / 2
    autovalores = np.linalg.eigvalsh(rigidez)

    print(f'TARGETS [rad]:           {np.round(q_d, 3).tolist()}')
    print(f'KP:                      {kp.tolist()}')
    print(f'g(q_d) [N·m]:            {np.round(t_ff, 3).tolist()}')
    print(f'hundimiento sin T_FF [°]: {np.round(np.degrees(q_d - equilibrio(np.zeros(6))), 1).tolist()}')
    print(f'hundimiento con T_FF [°]: {np.round(np.degrees(q_d - equilibrio(t_ff)), 1).tolist()}')
    print(f'autovalores de kp*I + dg/dq [N·m/rad]: {np.round(autovalores, 2).tolist()}')
    if autovalores.min() <= 0:
        print('AVISO: con estos KP la pose es INESTABLE aunque se compense la gravedad: '
              'el brazo se alejara de TARGETS. Sube KP en J2/J3.')
    else:
        print('Estable: el brazo vuelve a TARGETS despues de empujarlo.')

    linea = 'T_FF = [' + ', '.join(f'{v:.3f}' for v in t_ff) + ']  # joints 1-6, N·m'
    if args.escribir:
        nuevo, n = re.subn(r'^T_FF\s*=.*$', linea, texto, count=1, flags=re.M)
        if n != 1:
            raise SystemExit(f'No encontre la linea T_FF en {TEST}')
        open(TEST, 'w').write(nuevo)
        print(f'Escrito en {TEST}:\n  {linea}')
    else:
        print(f'Para el test:\n  {linea}')


if __name__ == '__main__':
    main()
