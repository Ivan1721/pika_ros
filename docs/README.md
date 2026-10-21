# Mapa de la documentación de pika_ros

Punto de entrada único: desde aquí se llega a **todos** los documentos del repositorio y a sus
secciones principales. Están agrupados por para qué sirven; un mismo documento puede aparecer en
más de un grupo.

**Si es tu primera vez:** lee [el estado del proyecto](estado_del_proyecto.md) (hardware, software, datos, estado,
algoritmos y caminos) y después el [Manual](manuales/Manual.md) para instalar y operar.

## ¿Qué necesitas?

| Quiero… | Ir a |
|---|---|
| Entender el proyecto completo | [estado_del_proyecto.md](estado_del_proyecto.md) |
| Instalar el workspace desde cero | [Manual, instalación](manuales/Manual.md#1-instalar-ros-2-humble) (pasos 1–8) |
| Conectar Sense y Gripper por primera vez (reglas USB) | [Manual §9](manuales/Manual.md#9-vincular-dispositivos-usb-primera-vez) |
| Calibrar las estaciones Vive | [Manual §10](manuales/Manual.md#10-despliegue-y-calibración-de-pika-station) · [guía de AgileX](calibracion/Pika%20Tracker%20and%20Sense%20Setup%20&%20Calibration.md) |
| Elegir qué flujo usar | [Tabla rápida de flujos](manuales/Manual.md#tabla-rápida--qué-flujo-necesito) |
| Teleoperar el Piper con el Sense | [Flujo A](manuales/Manual.md#flujo-a--teleoperación-pika--un-piper-1-brazo--1-gripper) · [A+ (dos brazos)](manuales/Manual.md#flujo-a--teleoperación-pika--dos-pipers-2-brazos--2-grippers) |
| Probar el modo MIT (impedancia) | [Manual B.3](manuales/Manual.md#b3--prueba-de-impedancia-modo-mit) · [el lazo de impedancia](percepcion_activa/lazos_cinematica_nbv.md#4-lazo-de-impedancia-modo-mit) |
| Simular sin el robot | [pika_sim](../src/pika_sim/README.md) · [Flujo D+](manuales/Manual.md#d--teleoperación-simulada-piper--gripper-pika-sin-hardware) |
| Usar un Sense real con Gazebo | [pika_sim: con los dos Sense](../src/pika_sim/README.md#con-los-dos-sense-conectados) |
| Leer o grabar los datos de los sensores | [topics y ejemplos](estado_del_proyecto.md#3-acceso-a-los-datos-de-los-sensores) · [Flujo E](manuales/Manual.md#flujo-e--pipeline-de-datos-captura--hdf5--lerobot) |
| Saber cómo se conecta y alimenta todo | [arquitectura](arquitectura/README.md) · [energía](energia/Consumo_Energia.md) |
| Medidas y cinemática del brazo con la pinza | [PIPER_PIKA.md](../src/pika_description/docs/PIPER_PIKA.md) |
| Escenarios agrícolas, oclusión y figuras | [informe de escenarios](percepcion_activa/escenarios_simulacion.md) |
| Ver los modelos 3D de la simulación | [§2.4 Modelos 3D](percepcion_activa/escenarios_simulacion.md#24-modelos-3d-de-la-simulación) |
| Algoritmos posibles (visión, NBV, IK, MoveIt…) | [§6](estado_del_proyecto.md#6-algoritmos-posibles-por-área) |
| Qué falta y qué sigue | [estado actual](estado_del_proyecto.md#5-estado-actual) · [caminos](estado_del_proyecto.md#9-caminos-posibles) · [hoja de ruta](percepcion_activa/README.md#6-hoja-de-ruta) |
| Resolver un problema | [problemas frecuentes](manuales/Manual.md#problemas-frecuentes) · [problemas conocidos del software](manuales/Manual.md#problemas-conocidos-del-software) |
| Plan para pasar la investigación al repo privado Next-Best-View | [plan_migracion_next_best_view.md](plan_migracion_next_best_view.md) |
| Reglas para trabajar en el repo (commits, estilo) | [AGENTS.md](../AGENTS.md) |

## 1. Visión general

| Documento | Qué tiene | Secciones |
|---|---|---|
| [estado_del_proyecto.md](estado_del_proyecto.md) | Revisión completa del proyecto (21-10-2026) | [Hardware](estado_del_proyecto.md#1-hardware) · [Software y aplicación](estado_del_proyecto.md#2-software-y-aplicación) · [Acceso a los datos de los sensores](estado_del_proyecto.md#3-acceso-a-los-datos-de-los-sensores) · [Trabajo realizado](estado_del_proyecto.md#4-trabajo-realizado) · [Estado actual](estado_del_proyecto.md#5-estado-actual) · [Algoritmos posibles por área](estado_del_proyecto.md#6-algoritmos-posibles-por-área) · [Limitaciones](estado_del_proyecto.md#7-limitaciones) · [Innovaciones y estado del arte](estado_del_proyecto.md#8-innovaciones-y-estado-del-arte) · [Caminos posibles](estado_del_proyecto.md#9-caminos-posibles) |
| [README.md](../README.md) · [README_es.md](../README_es.md) · [README_zh.md](../README_zh.md) | Presentación del producto Pika (texto original de AgileX, EN / ES / ZH) | — |
| [AGENTS.md](../AGENTS.md) | Convenciones de código, documentación y commits del fork | — |
| `CLAUDE.md` | Guía para Claude Code; está en `.gitignore` y solo existe en la máquina de desarrollo | — |

## 2. Instalación y operación

| Documento | Qué tiene | Secciones |
|---|---|---|
| [Manual.md](manuales/Manual.md) | Guía principal en español: instalación, conexión de dispositivos, calibración, CAN y los flujos de uso | [Instalar ROS 2 Humble](manuales/Manual.md#1-instalar-ros-2-humble) · [Vincular dispositivos USB (primera vez)](manuales/Manual.md#9-vincular-dispositivos-usb-primera-vez) · [Despliegue y calibración de Pika Station](manuales/Manual.md#10-despliegue-y-calibración-de-pika-station) · [Configurar CAN bus (brazo Piper)](manuales/Manual.md#11-configurar-can-bus-brazo-piper) · [Flujo A — Teleoperación Pika + Un Piper (1 brazo + 1 gripper)](manuales/Manual.md#flujo-a--teleoperación-pika--un-piper-1-brazo--1-gripper) · [Flujo A+ — Teleoperación Pika + Dos Pipers (2 brazos + 2 grippers)](manuales/Manual.md#flujo-a--teleoperación-pika--dos-pipers-2-brazos--2-grippers) · [Flujo B — Solo control del brazo Piper (con RViz)](manuales/Manual.md#flujo-b--solo-control-del-brazo-piper-con-rviz) · [Flujo C — Captura de cámaras y joints del robot](manuales/Manual.md#flujo-c--captura-de-cámaras-y-joints-del-robot) · [Flujo D — Simulación Gazebo del brazo Piper](manuales/Manual.md#flujo-d--simulación-gazebo-del-brazo-piper) · [Flujo E — Pipeline de datos (captura → HDF5 → LeRobot)](manuales/Manual.md#flujo-e--pipeline-de-datos-captura--hdf5--lerobot) · [Problemas frecuentes](manuales/Manual.md#problemas-frecuentes) |
| [Pika Tracker and Sense Setup & Calibration.md](calibracion/Pika%20Tracker%20and%20Sense%20Setup%20&%20Calibration.md) | Guía de AgileX: estaciones base, tracker y verificación en RViz (EN) | [Base Station Hardware Deployment](calibracion/Pika%20Tracker%20and%20Sense%20Setup%20&%20Calibration.md#12-base-station-hardware-deployment) · [Positioning Base Station Calibration](calibracion/Pika%20Tracker%20and%20Sense%20Setup%20&%20Calibration.md#13-positioning-base-station-calibration) · [Check Sense TF Coordinate Stability in RViz](calibracion/Pika%20Tracker%20and%20Sense%20Setup%20&%20Calibration.md#22-check-sense-tf-coordinate-stability-in-rviz) |
| [Pika Product User Manual (EN)](manuales/Pika%20Product%20User%20Manual%20beta%20%28EN%29%20ROS2.md) | Manual oficial del producto Pika para ROS 2 | — |
| [agilex-piper-user-manual.pdf](manuales/agilex-piper-user-manual.pdf) | Manual oficial del brazo Piper (PDF) | — |
| [sensor_tools/README.md](../src/sensor_tools/README.md) | Launch files y topics del hardware Pika | [Launch files](../src/sensor_tools/README.md#launch-files) · [Main topics (single Sense)](../src/sensor_tools/README.md#main-topics-single-sense) |

## 3. Hardware

| Documento | Qué tiene | Secciones |
|---|---|---|
| [arquitectura/README.md](arquitectura/README.md) | Alimentación y comunicaciones (bimanual y plataforma de un brazo), con diagramas | [Versión de un brazo: plataforma remolcable](arquitectura/README.md#versión-de-un-brazo-plataforma-remolcable) · [Alimentación](arquitectura/README.md#1-alimentación) · [Enlaces de comunicación](arquitectura/README.md#2-enlaces-de-comunicación) · [Topología USB propuesta (montaje bimanual)](arquitectura/README.md#3-topología-usb-propuesta-montaje-bimanual) · [Qué está verificado y qué no](arquitectura/README.md#4-qué-está-verificado-y-qué-no) |
| [Consumo_Energia.md](energia/Consumo_Energia.md) | Consumo por componente, batería, inversor y autonomía de la plataforma | [Tabla resumen](energia/Consumo_Energia.md#1-tabla-resumen) · [Presupuesto energético por configuración](energia/Consumo_Energia.md#3-presupuesto-energético-por-configuración) · [Plataforma del remolque (batería e inversor)](energia/Consumo_Energia.md#4-plataforma-del-remolque-batería-e-inversor) |
| [Hoja de datos Pika (ES)](datasheets/Hoja%20de%20datos%20del%20producto%20Pika%20beta%20%28ES%29.md) · [(CN)](datasheets/Hoja%20de%20datos%20del%20producto%20Pika%20beta%20%28CN%29.md) | Especificaciones oficiales del Sense, el Gripper y la Station | — |
| [PIPER_PIKA.md](../src/pika_description/docs/PIPER_PIKA.md) | Medidas, grados de libertad, alcance y modelo del gripper de AgileX | [Resumen](../src/pika_description/docs/PIPER_PIKA.md#1-resumen) · [Medidas](../src/pika_description/docs/PIPER_PIKA.md#3-medidas) · [Grados de libertad](../src/pika_description/docs/PIPER_PIKA.md#4-grados-de-libertad) · [Alcance](../src/pika_description/docs/PIPER_PIKA.md#5-alcance) · [Modelo del gripper Pika](../src/pika_description/docs/PIPER_PIKA.md#6-modelo-del-gripper-pika) · [Observaciones para el robot real](../src/pika_description/docs/PIPER_PIKA.md#7-observaciones-para-el-robot-real) |
| [agilex/README.md](../src/pika_description/agilex/README.md) | Archivos que envió AgileX (URDF, mallas, planos) y su procedencia | — |

## 4. Simulación

| Documento | Qué tiene | Secciones |
|---|---|---|
| [pika_sim/README.md](../src/pika_sim/README.md) | Cómo lanzar la simulación y todos sus argumentos | [Uso](../src/pika_sim/README.md#uso) · [Con los dos Sense conectados](../src/pika_sim/README.md#con-los-dos-sense-conectados) · [Modo MIT (impedancia)](../src/pika_sim/README.md#modo-mit-impedancia) · [Argumentos](../src/pika_sim/README.md#argumentos) · [Cámaras del gripper](../src/pika_sim/README.md#cámaras-del-gripper) · [Escenario agrícola: manzano](../src/pika_sim/README.md#escenario-agrícola-manzano) · [Manzano realista (Helios)](../src/pika_sim/README.md#manzano-realista-helios) · [Iluminación](../src/pika_sim/README.md#iluminación) · [Modelos 3D](../src/pika_sim/README.md#modelos-3d) · [Renders para figuras](../src/pika_sim/README.md#renders-para-figuras) · [Consumo de recursos](../src/pika_sim/README.md#consumo-de-recursos) · [Escena de demostración de NBV](../src/pika_sim/README.md#escena-de-demostración-de-nbv) · [Pendiente](../src/pika_sim/README.md#pendiente) |
| [escenarios_simulacion.md](percepcion_activa/escenarios_simulacion.md) | Informe de los escenarios: árboles, densidades, luces, NBV, oclusión, modelos 3D y consumo | [Resumen](percepcion_activa/escenarios_simulacion.md#resumen) · [Escenarios](percepcion_activa/escenarios_simulacion.md#2-escenarios) · [2.4 Modelos 3D de la simulación](percepcion_activa/escenarios_simulacion.md#24-modelos-3d-de-la-simulación) · [NBV en cada escenario](percepcion_activa/escenarios_simulacion.md#3-nbv-en-cada-escenario) · [Oclusión: manzanas con distinto nivel de visibilidad](percepcion_activa/escenarios_simulacion.md#4-oclusión-manzanas-con-distinto-nivel-de-visibilidad) · [Consumo de recursos](percepcion_activa/escenarios_simulacion.md#6-consumo-de-recursos) · [Cómo reproducirlo](percepcion_activa/escenarios_simulacion.md#7-cómo-reproducirlo) |
| [pika_description/README.md](../src/pika_description/README.md) | URDF del Piper con la Pika: estructura, marcos y cómo visualizarlo | [Estructura del modelo](../src/pika_description/README.md#estructura-del-modelo) · [Posiciones de referencia (desde `gripper_base`)](../src/pika_description/README.md#posiciones-de-referencia-desde-gripper_base) · [Marco de coordenadas](../src/pika_description/README.md#marco-de-coordenadas) · [Lanzar visualización](../src/pika_description/README.md#lanzar-visualización) · [Integrar en otro URDF](../src/pika_description/README.md#integrar-en-otro-urdf) |

## 5. Percepción activa e investigación

| Documento | Qué tiene | Secciones |
|---|---|---|
| [percepcion_activa/README.md](percepcion_activa/README.md) | Cómo se conectan pika_ros, Milo y ActivePerceptionArms; decisiones y hoja de ruta | [Los tres repositorios](percepcion_activa/README.md#1-los-tres-repositorios) · [Milo como punto intermedio](percepcion_activa/README.md#2-milo-como-punto-intermedio) · [Decisiones tomadas](percepcion_activa/README.md#3-decisiones-tomadas) · [Estado actual](percepcion_activa/README.md#4-estado-actual) · [Contrato común por robot](percepcion_activa/README.md#5-contrato-común-por-robot) · [Hoja de ruta](percepcion_activa/README.md#6-hoja-de-ruta) · [Cómo retomar el trabajo](percepcion_activa/README.md#7-cómo-retomar-el-trabajo) |
| [lazos_cinematica_nbv.md](percepcion_activa/lazos_cinematica_nbv.md) | Lazos de control, cinemática, IK, impedancia y cómo se genera el NBV | [Panorama: lazos anidados](percepcion_activa/lazos_cinematica_nbv.md#1-panorama-lazos-anidados) · [Cinemática](percepcion_activa/lazos_cinematica_nbv.md#2-cinemática) · [Lazo de teleoperación (Flujo A y D+)](percepcion_activa/lazos_cinematica_nbv.md#3-lazo-de-teleoperación-flujo-a-y-d) · [Lazo de impedancia (modo MIT)](percepcion_activa/lazos_cinematica_nbv.md#4-lazo-de-impedancia-modo-mit) · [Cómo se generaría el NBV en Piper + Pika](percepcion_activa/lazos_cinematica_nbv.md#5-cómo-se-generaría-el-nbv-en-piper--pika) · [Qué falta, en orden](percepcion_activa/lazos_cinematica_nbv.md#6-qué-falta-en-orden) |
| [recursos_publicos.md](percepcion_activa/recursos_publicos.md) | Modelos de plantas, escenas agrícolas, datasets y material del Pika | [Plantas y escenas agrícolas para el simulador](percepcion_activa/recursos_publicos.md#1-plantas-y-escenas-agrícolas-para-el-simulador) · [Árboles completos, hojas, ramas y frutos en 3D (revisión del 20-10-2026, segunda parte)](percepcion_activa/recursos_publicos.md#1b-árboles-completos-hojas-ramas-y-frutos-en-3d-revisión-del-20-10-2026-segunda-parte) · [Datasets publicados](percepcion_activa/recursos_publicos.md#2-datasets-publicados) · [Propuesta para la escena de NBV](percepcion_activa/recursos_publicos.md#4-propuesta-para-la-escena-de-nbv) |
| [frutas_candidatas.md](percepcion_activa/frutas_candidatas.md) | Qué frutas encajan con el Piper y la pinza Pika | [Restricciones del sistema](percepcion_activa/frutas_candidatas.md#1-restricciones-del-sistema) · [Comparación](percepcion_activa/frutas_candidatas.md#2-comparación) · [Recomendación](percepcion_activa/frutas_candidatas.md#3-recomendación) |
| ActivePerceptionArms (repo privado) | Revisión sistemática del estado del arte, proyecto de tesis y figuras | — |
| [milo_ws, rama `brazo`](https://github.com/Ivan1721/milo_ws/tree/brazo) | Milo: plantillas de MoveIt, OctoMap y cámara en la pinza | — |

## 6. Paquetes de terceros (submódulos y código incluido)

| Documento | Qué tiene |
|---|---|
| [PikaAnyArm/README.md](https://github.com/Ivan1721/PikaAnyArm/blob/pika-custom-ros2/README.md) | Teleoperación de brazos con el Pika (fork propio, rama `pika-custom-ros2`) |
| [piper_ros/README(复件).md](https://github.com/Ivan1721/PikaAnyArm/blob/pika-custom-ros2/piper/piper_ros/README(%E5%A4%8D%E4%BB%B6).md) | Driver ROS 2 del brazo Piper |
| [data_tools/README.md](https://github.com/agilexrobotics/data_tools/blob/ros2/README.md) | Captura, sincronización y conversión de datos (AgileX) |
| [data_msgs/README.md](https://github.com/agilexrobotics/data_msgs/blob/ros2/README.md) | Mensajes propios del kit Pika (AgileX) |
| [realsense-ros/README.md](../src/realsense-ros/README.md) | Driver ROS 2 de las cámaras RealSense (Intel); sus otros documentos están en la misma carpeta |

Fuente oficial de AgileX para todo el kit Pika: [portal de documentación en Yuque](https://agilexsupport.yuque.com/staff-hso6mo/peoot3/rcrola7ogxquhivi).
La presentación de las contribuciones de este fork está en [presentaciones/](presentaciones/).
