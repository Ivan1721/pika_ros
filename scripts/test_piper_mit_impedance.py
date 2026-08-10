#!/usr/bin/env python3
# -*-coding:utf8-*-
# Prueba de modo MIT (control de impedancia) en los 6 joints del brazo
# Piper, usando piper_sdk directo -- sin ROS2 de por medio.
#
# Requiere: piper_sdk instalado o disponible via PYTHONPATH.
# En esta maquina esta clonado en ~/piper_sdk (fuera de este repo);
# ajusta PIPER_SDK_PATH abajo si tu instalacion esta en otro lugar,
# o simplemente instalalo con `pip3 install piper_sdk`.
#
# El brazo se mantiene atraido hacia TARGETS (en radianes) con las
# ganancias KP/KD. Empuja el brazo con la mano y sueltalo para sentir
# el efecto resorte. Ctrl+C para detener en cualquier momento.
#
# Uso:
#   python3 test_piper_mit_impedance.py [can_left|can_right|can0]
import os
import sys
import time

PIPER_SDK_PATH = os.path.expanduser("~/piper_sdk")
if PIPER_SDK_PATH not in sys.path:
    sys.path.insert(0, PIPER_SDK_PATH)
from piper_sdk import *

CAN_PORT = sys.argv[1] if len(sys.argv) > 1 else "can_left"
DURATION_S = 30
HZ = 100
KP = 5
KD = 0.8

# Posicion objetivo (radianes) para cada joint 1-6. Por defecto: home
# (todos en 0). Se puede reemplazar por una posicion capturada a mano,
# por ejemplo via el GUI de sliders de start_single_piper_rviz.launch.py
# + GetArmJointMsgs() del brazo, convertida de 0.001 grados a radianes.
TARGETS = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]  # joints 1-6

# Nota: J3 tiene su "home" (0 rad) en el borde de su rango [-2.967, 0] --
# alli no hay margen mecanico para ceder en una direccion. Si pruebas J3
# especificamente, usa un valor a la mitad de su rango (ej. -1.4) para
# sentir el efecto resorte en ambos sentidos.

if __name__ == "__main__":
    piper = C_PiperInterface_V2(CAN_PORT)
    piper.ConnectPort()
    while not piper.EnablePiper():
        time.sleep(0.01)
    print(f"Brazo habilitado en {CAN_PORT}. Modo MIT hacia {TARGETS} durante {DURATION_S}s.")
    print("Muevelo con la mano y sueltalo para sentir el efecto resorte. Ctrl+C para detener antes.")
    print("Aviso: al terminar (tiempo agotado o Ctrl+C), el brazo puede perder sujecion activa de golpe.")

    period = 1.0 / HZ
    start = time.time()
    try:
        while time.time() - start < DURATION_S:
            piper.ModeCtrl(0x01, 0x04, 0, 0xAD)
            for motor in range(1, 7):
                piper.JointMitCtrl(motor, TARGETS[motor - 1], 0.0, KP, KD, 0.0)
            time.sleep(period)
    except KeyboardInterrupt:
        pass
    print("Prueba terminada.")
