#!/usr/bin/env python3

import subprocess
import re
import os
import cv2
import time

def run_command(command):
    """Ejecuta un comando y retorna su salida"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    except Exception as e:
        print(f"Error al ejecutar comando: {str(e)}")
        return None


def get_device_info():
    """Obtiene información del dispositivo"""
    # Ejecuta comando rs-enumerate-devices
    rs_output = run_command("rs-enumerate-devices -s")
    if not rs_output:
        print("No se puede obtener datos de la cámara de profundidad")
        return None, None

    # Analiza salida para obtener número de serie
    serial_match = re.search(r'Intel RealSense D405\s+(\d+)', rs_output)
    if not serial_match:
        print("No se puede obtener datos de la cámara de profundidad")
        return None, None
    serial_number = serial_match.group(1)

    # Ejecuta comando udevadm
    ls_output = run_command("ls /dev | grep ttyUSB | grep -v ttyUSB50 | grep -v ttyUSB51 | grep -v ttyUSB60 | grep -v ttyUSB61")
    count = ls_output.count("tty")
    if count > 1:
        print("Asegúrate de que la máquina solo tenga un dispositivo USB serial conectado")
        return None, None
    udev_output = run_command(f"udevadm info /dev/{ls_output} | grep DEVPATH")
    if not udev_output:
        print("No se puede obtener datos del puerto serial")
        return None, None

    # Analiza la ruta USB
    usb_path = udev_output[:udev_output.find(ls_output)][:-1]  # Obtiene formato como 1-13.2.4:1.0
    usb_path = usb_path[usb_path.rfind("/")+1:]
    print("Buscando cámara fisheye, presiona 's' cuando aparezca, presiona 'q' si no es fisheye (¡presiona en la ventana de imagen, no en la terminal!)")
    video_path = None
    cv2.setLogLevel(0)
    for i in range(50):
        cap = cv2.VideoCapture(i)
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        cap.set(cv2.CAP_PROP_FOURCC, fourcc)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        key = None
        if cap.isOpened():
            # print("puerto:", "/dev/video"+str(i))
            while True:
                ret, frame = cap.read()
                cv2.imshow("/dev/video"+str(i), frame)
                key = cv2.waitKey(1)
                if key & 0xFF == ord('q'):
                    break
                elif key & 0xFF == ord('s'):
                    break
        cv2.destroyAllWindows()
        if key is not None and key & 0xFF == ord('s'):
            video_path = 'video' + str(i)
            break
    cv2.destroyAllWindows()
    if video_path is None:
        print("No se puede obtener datos de la cámara fisheye")
        return None, None
    udev_output = run_command(f"udevadm info /dev/{video_path} | grep DEVPATH")
    video_path = udev_output[:udev_output.find("video")][:-1]  # Obtiene formato como 1-13.2.4:1.0
    video_path = video_path[video_path.rfind("/")+1:]

    return serial_number, usb_path, video_path


def generate_setup_bash(left_info, right_info, select):
    if select == "1":
        path = "setup_multi_sensor.bash"
        usb_num1 = 50
        usb_num2 = 51
        name1 = "sensor_"
        name2 = "sensor_"
        to1 = ">"
        to2 = ">>"
    if select == "2":
        path = "setup_multi_gripper.bash"
        usb_num1 = 60
        usb_num2 = 61
        name1 = "gripper_"
        name2 = "gripper_"
        to1 = ">"
        to2 = ">>"
    if select == "3":
        path = "setup_sensor_gripper.bash"
        usb_num1 = 50
        usb_num2 = 60
        name1 = "sensor_"
        name2 = "gripper_"
        to1 = ">"
        to2 = ">"
    """Genera el archivo setup.bash"""
    content = f"""
#/bin/bash

sudo sh -c 'echo "ACTION==\\"add\\", KERNELS==\\"{left_info[1]}\\", SUBSYSTEMS==\\"usb\\", MODE:=\\"0777\\", SYMLINK+=\\"ttyUSB{usb_num1}\\"" {to1} /etc/udev/rules.d/{name1}serial.rules'
sudo sh -c 'echo "ACTION==\\"add\\", KERNELS==\\"{right_info[1]}\\", SUBSYSTEMS==\\"usb\\", MODE:=\\"0777\\", SYMLINK+=\\"ttyUSB{usb_num2}\\"" {to2} /etc/udev/rules.d/{name2}serial.rules'

sudo sh -c 'echo "ACTION==\\"add\\", KERNEL==\\"video[0,2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36,38,40,42,44,46,48]*\\", KERNELS==\\"{left_info[2]}\\", SUBSYSTEMS==\\"usb\\", MODE:=\\"0777\\", SYMLINK+=\\"video{usb_num1}\\"" {to1} /etc/udev/rules.d/{name1}fisheye.rules'
sudo sh -c 'echo "ACTION==\\"add\\", KERNEL==\\"video[0,2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36,38,40,42,44,46,48]*\\", KERNELS==\\"{right_info[2]}\\", SUBSYSTEMS==\\"usb\\", MODE:=\\"0777\\", SYMLINK+=\\"video{usb_num2}\\"" {to2} /etc/udev/rules.d/{name2}fisheye.rules'

sudo udevadm control --reload-rules && sudo service udev restart && sudo udevadm trigger
               """
    with open(path, "w") as f:
        f.write(content)
    os.chmod(path, 0o755)


def generate_start_bash(left_info, right_info, select):
    if select == "1":
        path = "start_multi_sensor.bash"
        usb_num1 = 50
        usb_num2 = 51
        content = f"""
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
camera_fps=30
camera_width=640
camera_height=480
l_depth_camera_no={left_info[0]}
r_depth_camera_no={right_info[0]}

l_serial_port=/dev/ttyUSB{usb_num1}
r_serial_port=/dev/ttyUSB{usb_num2}
sudo chmod a+rw /dev/ttyUSB*
l_fisheye_port={usb_num1}
r_fisheye_port={usb_num2}
sudo chmod a+rw /dev/video*

source /opt/ros/humble/setup.bash && cd $SCRIPT_DIR/../install/sensor_tools/share/sensor_tools/scripts/ && chmod 777 usb_camera.py
if [ -n "$1" ]; then
    source $SCRIPT_DIR/../install/setup.bash && ros2 launch sensor_tools open_multi_sensor.launch.py l_depth_camera_no:=_$l_depth_camera_no r_depth_camera_no:=_$r_depth_camera_no l_serial_port:=$l_serial_port r_serial_port:=$r_serial_port l_fisheye_port:=$l_fisheye_port r_fisheye_port:=$r_fisheye_port camera_fps:=$camera_fps camera_width:=$camera_width camera_height:=$camera_height camera_profile:=$camera_width,$camera_height,$camera_fps name:=$1 name_index:=$1_
else
    source $SCRIPT_DIR/../install/setup.bash && ros2 launch sensor_tools open_multi_sensor.launch.py l_depth_camera_no:=_$l_depth_camera_no r_depth_camera_no:=_$r_depth_camera_no l_serial_port:=$l_serial_port r_serial_port:=$r_serial_port l_fisheye_port:=$l_fisheye_port r_fisheye_port:=$r_fisheye_port camera_fps:=$camera_fps camera_width:=$camera_width camera_height:=$camera_height camera_profile:=$camera_width,$camera_height,$camera_fps
fi
                """
    if select == "2":
        path = "start_multi_gripper.bash"
        usb_num1 = 60
        usb_num2 = 61
        content = f"""
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
camera_fps=30
camera_width=640
camera_height=480
l_depth_camera_no={left_info[0]}
r_depth_camera_no={right_info[0]}

l_serial_port=/dev/ttyUSB{usb_num1}
r_serial_port=/dev/ttyUSB{usb_num2}
sudo chmod a+rw /dev/ttyUSB*
l_fisheye_port={usb_num1}
r_fisheye_port={usb_num2}
sudo chmod a+rw /dev/video*

source /opt/ros/humble/setup.bash && cd $SCRIPT_DIR/../install/sensor_tools/share/sensor_tools/scripts/ && chmod 777 usb_camera.py
if [ -n "$1" ]; then
    source $SCRIPT_DIR/../install/setup.bash && ros2 launch sensor_tools open_multi_gripper.launch.py l_depth_camera_no:=_$l_depth_camera_no r_depth_camera_no:=_$r_depth_camera_no l_serial_port:=$l_serial_port r_serial_port:=$r_serial_port l_fisheye_port:=$l_fisheye_port r_fisheye_port:=$r_fisheye_port camera_fps:=$camera_fps camera_width:=$camera_width camera_height:=$camera_height camera_profile:=$camera_width,$camera_height,$camera_fps name:=$1 name_index:=$1_
else
    source $SCRIPT_DIR/../install/setup.bash && ros2 launch sensor_tools open_multi_gripper.launch.py l_depth_camera_no:=_$l_depth_camera_no r_depth_camera_no:=_$r_depth_camera_no l_serial_port:=$l_serial_port r_serial_port:=$r_serial_port l_fisheye_port:=$l_fisheye_port r_fisheye_port:=$r_fisheye_port camera_fps:=$camera_fps camera_width:=$camera_width camera_height:=$camera_height camera_profile:=$camera_width,$camera_height,$camera_fps
fi
                """
    if select == "3":
        path = "start_sensor_gripper.bash"
        usb_num1 = 50
        usb_num2 = 60
        content = f"""
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
camera_fps=30
camera_width=640
camera_height=480
sensor_depth_camera_no={left_info[0]}
gripper_depth_camera_no={right_info[0]}

sensor_serial_port=/dev/ttyUSB{usb_num1}
gripper_serial_port=/dev/ttyUSB{usb_num2}
sudo chmod a+rw /dev/ttyUSB*
sensor_fisheye_port={usb_num1}
gripper_fisheye_port={usb_num2}
sudo chmod a+rw /dev/video*

source /opt/ros/humble/setup.bash && cd $SCRIPT_DIR/../install/sensor_tools/share/sensor_tools/scripts/ && chmod 777 usb_camera.py
source $SCRIPT_DIR/../install/setup.bash && ros2 launch sensor_tools open_sensor_gripper.launch.py sensor_depth_camera_no:=_$sensor_depth_camera_no gripper_depth_camera_no:=_$gripper_depth_camera_no sensor_serial_port:=$sensor_serial_port gripper_serial_port:=$gripper_serial_port sensor_fisheye_port:=$sensor_fisheye_port gripper_fisheye_port:=$gripper_fisheye_port camera_fps:=$camera_fps camera_width:=$camera_width camera_height:=$camera_height camera_profile:=$camera_width,$camera_height,$camera_fps
                """
    with open(path, "w") as f:
        f.write(content)
    os.chmod(path, 0o755)


def main():
    print("=== Herramienta de configuración Pika ===")
    select = None
    while True:
        select = input("Selecciona configuración:\n1. Dos sensores Pika (pinzas de mano)\n2. Dos pinzas Pika (montadas en brazo robótico)\n3. Un sensor Pika y una pinza Pika\nIngresa tu opción: ")
        if select == "1":
            device1 = "izquierdo"
            device2 = "derecho"
            break
        if select == "2":
            device1 = "izquierdo"
            device2 = "derecho"
            break
        if select == "3":
            device1 = "sensor"
            device2 = "pinza"
            break
        else:
            print("Por favor ingresa 1, 2 o 3")
            continue

    print(f"Por favor conecta el dispositivo {device1}, luego presiona Enter...")
    input()
    print(f"Obteniendo información del dispositivo {device1}...")
    while True:
        left_info = get_device_info()
        if not left_info[0]:
            print(f"No se puede obtener información del dispositivo {device1}, verifica la conexión, luego presiona Enter...")
            input()
        else:
            break
    print(f"Información del dispositivo {device1}: {left_info[0]} {left_info[1]} {left_info[2]}")


    print(f"Por favor desconecta el dispositivo {device1}, conecta el dispositivo {device2} (en un puerto USB diferente, no puedes cambiar de puerto después), luego presiona Enter...")
    input()
    print(f"Obteniendo información del dispositivo {device2}...")
    while True:
        right_info = get_device_info()
        if not right_info[0]:
            print(f"No se puede obtener información del dispositivo {device2}, verifica la conexión, luego presiona Enter...")
            input()
        else:
            break
    print(f"Información del dispositivo {device2}: {right_info[0]} {right_info[1]} {right_info[2]}")

    # Genera archivos de configuración
    print("Generando archivos de configuración...")
    generate_setup_bash(left_info, right_info, select)
    generate_start_bash(left_info, right_info, select)
    setup_path = "setup_multi_sensor.bash" if select=="1" else ("setup_multi_gripper.bash" if select=="2" else "setup_sensor_gripper.bash")
    start_path = "start_multi_sensor.bash" if select=="1" else ("start_multi_gripper.bash" if select=="2" else "start_sensor_gripper.bash")
    print("¡Configuración completada! Archivos generados:")
    print(f"1. {setup_path}")
    print(f"2. {start_path}")
    print(f"Ejecutando {setup_path}")
    run_command(f"bash {setup_path}")
    print("Ejecución completada.")
    while True:
        if select == "1":
            print("Por favor DESCONECTA ambos sensores Pika y RECONECTA los dos (izquierdo y derecho) en sus puertos USB respectivos. Luego presiona Enter para verificar si se vincularon correctamente...")
        elif select == "2":
            print("Por favor DESCONECTA ambas pinzas Pika y RECONECTA las dos (izquierda y derecha) en sus puertos USB respectivos. Luego presiona Enter para verificar si se vincularon correctamente...")
        else:  # select == "3"
            print("Por favor DESCONECTA el sensor y la pinza Pika y RECONECTA ambos dispositivos en sus puertos USB respectivos. Luego presiona Enter para verificar si se vincularon correctamente...")
        input()
        print("Esperando...")
        time.sleep(5)
        video_list = run_command("ls /dev | grep video")
        usb_list = run_command("ls /dev | grep ttyUSB")
        if (select == "1" or select == "3") and video_list.find("50") < 0:
            print("No se encuentra cámara fisheye del sensor (izquierdo)")
            continue
        if (select == "1") and video_list.find("51") < 0:
            print("No se encuentra cámara fisheye del sensor (derecho)")
            continue
        if (select == "2" or select == "3") and video_list.find("60") < 0:
            print("No se encuentra cámara fisheye de la pinza (izquierda)")
            continue
        if (select == "2") and video_list.find("61") < 0:
            print("No se encuentra cámara fisheye de la pinza (derecha)")
            continue
        if (select == "1" or select == "3") and usb_list.find("50") < 0:
            print("No se encuentra puerto serial del sensor (izquierdo)")
            continue
        if (select == "1") and usb_list.find("51") < 0:
            print("No se encuentra puerto serial del sensor (derecho)")
            continue
        if (select == "2" or select == "3") and usb_list.find("60") < 0:
            print("No se encuentra puerto serial de la pinza (izquierda)")
            continue
        if (select == "2") and usb_list.find("61") < 0:
            print("No se encuentra puerto serial de la pinza (derecha)")
            continue
        break
    print("¡Vinculación exitosa! Método para iniciar los dispositivos:")
    print(f"2. Luego ejecuta: bash {start_path}")


if __name__ == "__main__":
    main()
