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
# el efecto resorte. Cada motor aplica
#   tau = KP*(TARGETS - q) + KD*(0 - dq) + T_FF
# donde T_FF es el torque de gravedad en TARGETS (compensacion de
# gravedad). Sin T_FF, con KP bajos J2/J3 no sostienen el peso y el
# brazo cae a sus topes (J2=0, J3=0, la pose plegada).
#
# T_FF se calcula desde el URDF con calcular_gravedad_mit.py: hay que
# recalcularlo cada vez que cambien TARGETS o lo montado en la pinza.
#
# Comportamiento, duracion, frecuencia de envio, llamada de modo y
# manejo de salida siguen la misma logica que el demo original del SDK
# (V2_piper_ctrl_joint_mit.py): un envio por iteracion + sleep(1),
# bucle infinito (sin limite de tiempo), MotionCtrl_2, y sin capturar
# KeyboardInterrupt -- Ctrl+C corta el script de golpe, no hay salida
# limpia ni mensaje final.
#
# Uso:
#   python3 test_piper_mit_impedance.py [can_left|can_right|can0]
import os
import re
import sys
import time

PIPER_SDK_PATH = os.path.expanduser("~/piper_sdk")
if PIPER_SDK_PATH not in sys.path:
    sys.path.insert(0, PIPER_SDK_PATH)
from piper_sdk import *

CAN_PORT = sys.argv[1] if len(sys.argv) > 1 else "can_left"

# Ganancias por joint (1-6). Cada joint puede tener su propia rigidez
# (kp) y amortiguacion (kd) -- JointMitCtrl las acepta por llamada, no
# hay que usar el mismo valor para los 6. Por ejemplo, J2/J3 (los que
# mas peso del brazo sostienen contra la gravedad) pueden llevar un kp
# mas alto para no hundirse, mientras J4-J6 (muneca, mas livianos)
# pueden ir mas sueltos.
# J2/J3 no pueden bajar de ~8: la gravedad actua como una rigidez negativa
# de hasta -5.2 N·m/rad en esta pose, y con KP=5 la pose es un equilibrio
# inestable aunque se compense con T_FF (el brazo se aleja solo). Con 20/15
# es estable y cede ~4 grados por cada N·m de empuje en J2 (verificado en
# pika_sim control:=mit). calcular_gravedad_mit.py revisa esta condicion.
KP = [5.0, 20.0, 15.0, 5.0, 5.0, 5.0]  # joints 1-6
KD = [0.8, 0.8, 0.8, 0.8, 0.8, 0.8]  # joints 1-6

# Posicion objetivo (radianes) para cada joint 1-6.
# J1=0.0deg J2=14.61deg J3=-40.45deg J4=0.0deg J5=25.32deg J6=16.21deg
# (Reemplaza a la pose capturada antes con los sliders de
# start_single_piper_rviz.launch.py: J2=23.35 J3=-47.824 J4=-3.779
# J5=37.395 J6=20.146 grados.)
TARGETS = [0.0, 0.255, -0.706, 0.00, 0.442, 0.283]  # joints 1-6

# Compensacion de gravedad: torque de gravedad en TARGETS segun el URDF de
# Piper + gripper Pika. Generado por calcular_gravedad_mit.py --escribir.
T_FF = [-0.000, 2.721, -4.320, -0.020, -1.042, -0.013]  # joints 1-6, N·m

# Fraccion de T_FF que se aplica. 0.0 reproduce el demo original del SDK
# (sin compensacion). La primera vez en el brazo real empieza con 0.5 para
# confirmar que el signo de T_FF levanta el brazo en vez de empujarlo hacia
# abajo, y sube a 1.0 despues.
ESCALA_GRAVEDAD = 1.0

# Firmware minimo para el modo MIT (move_mode 0x04 "MOVE M", segun la
# documentacion de MotionCtrl_2 en piper_sdk).
FIRMWARE_MINIMO = (1, 5, 2)


def revisar_firmware(piper):
    # ConnectPort ya pide la version; la respuesta tarda unos milisegundos
    for _ in range(40):
        version = piper.GetPiperFirmwareVersion()
        if version != -0x4AF:
            break
        piper.SearchPiperFirmwareVersion()
        time.sleep(0.025)
    else:
        print("Aviso: no se pudo leer la version de firmware; se sigue igual.", flush=True)
        return
    m = re.search(r"V(\d+)\.(\d+)-(\d+)", version)
    if m and tuple(int(v) for v in m.groups()) < FIRMWARE_MINIMO:
        print(f"Aviso: firmware {version} es anterior a V1.5-2; el modo MIT puede no funcionar.", flush=True)
    else:
        print(f"Firmware: {version}", flush=True)

# Nota: J3 tiene su "home" (0 rad) en el borde de su rango [-2.967, 0] --
# alli no hay margen mecanico para ceder en una direccion. Si pruebas J3
# especificamente, usa un valor a la mitad de su rango (ej. -1.4) para
# sentir el efecto resorte en ambos sentidos.

if __name__ == "__main__":
    piper = C_PiperInterface_V2(CAN_PORT)
    piper.ConnectPort()
    revisar_firmware(piper)
    while not piper.EnablePiper():
        time.sleep(0.01)
    print(f"Brazo habilitado en {CAN_PORT}. Modo MIT hacia {TARGETS} (bucle infinito).", flush=True)
    print("Muevelo con la mano y sueltalo para sentir el efecto resorte. Ctrl+C para cortar.", flush=True)
    print("Aviso: al cortar con Ctrl+C, el brazo puede perder sujecion activa de golpe.", flush=True)
    print(f"Compensacion de gravedad: {ESCALA_GRAVEDAD:.0%} de T_FF = {T_FF} N·m", flush=True)

    while True:
        piper.MotionCtrl_2(0x01, 0x04, 0, 0xAD)
        for motor in range(1, 7):
            piper.JointMitCtrl(motor, TARGETS[motor - 1], 0.0, KP[motor - 1], KD[motor - 1],
                               ESCALA_GRAVEDAD * T_FF[motor - 1])
        time.sleep(1)