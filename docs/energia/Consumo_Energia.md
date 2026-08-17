# Consumo de energía por componente — Pika + Piper (pika_ros)

Este documento reúne el consumo eléctrico de cada componente físico usado en el proyecto. Los datos se clasifican por su origen, porque no todos tienen el mismo nivel de certeza:

| Marca | Significado |
| --- | --- |
| ✅ **Oficial** | Tomado directamente de la hoja de datos Pika (`[Externo] Hoja de datos del producto Pika beta (CN).md`) incluida en este repositorio. |
| 📘 **Fabricante** | Especificación pública del fabricante del componente (Intel, HTC, AgileX), no está documentada dentro de este repo. |
| 🧮 **Estimado** | Calculado o inferido a partir de datos parciales (p. ej. límites de corriente en el firmware) porque no existe una cifra oficial publicada. Recomendado verificar con un medidor USB/multímetro si se necesita precisión. |

---

## 1. Tabla resumen

| Componente | Alimentación | Consumo típico | Consumo pico | Origen |
| --- | --- | --- | --- | --- |
| Pika Station (base de localización) | 12 V (batería 12 V/10 Ah o adaptador 220 V AC) | **3 W** | — | ✅ Oficial |
| Etiqueta de posicionamiento (tracker, en Pika Sense) | Batería interna, recarga por USB | ~0.4–0.5 W (9 h de autonomía) | — | 🧮 Estimado (autonomía oficial ✅, capacidad de batería no publicada) |
| Cámara de profundidad Intel RealSense D405 (×1 por Sense/Gripper) | USB 3.1 Type-C (bus-powered) | ~2.5 W | ~3.5 W | 📘 Fabricante (Intel) |
| Cámara fisheye USB (×1 por Sense/Gripper) | USB (bus-powered) | ~1.5–2.5 W | ~3 W | 🧮 Estimado (módulo UVC genérico) |
| IMU + codificador de posición del gripper | Integrado en la placa del Sense/Gripper, vía Type-C | <0.5 W | — | 🧮 Estimado |
| Motor de la pinza (Pika Gripper) | 24 V DC vía conector XT30(PB) | ~2–7 W (sujeción) | **24 W** (límite de firmware: 1000 mA @ 24 V) | ✅ Oficial (conector/voltaje) + 🧮 Estimado (consumo real) |
| **Brazo robótico Piper** (6 GDL, teleoperación) | 24 V DC (mín. 24 V, máx. 26 V) | **≤ 40 W** (potencia integral) | **≤ 120 W** (potencia máx.) | ✅ Oficial (`agilex-piper-user-manual.pdf`) |
| Pinza de dos dedos del Piper (follower gripper, opcional) | 24 V DC | ≤30 W (potencia integral) | ≤50 W (potencia máx.) | ✅ Oficial (mismo manual) |
| Palanca/gripper maestro (leader teaching device, opcional) | 24 V DC | ≤30 W (potencia integral) | ≤50 W (potencia máx.) | ✅ Oficial (mismo manual) |
| Adaptador USB-CAN (gs_usb) | USB bus-powered | ~1–2.5 W | — | 🧮 Estimado |
| Receptor USB inalámbrico (dongle del tracker) | USB bus-powered | <0.5 W | — | 🧮 Estimado |

---

## 2. Detalle por módulo

### 2.1 Pika Station (base de localización / lighthouse)
Dato **oficial** de la hoja de datos del producto (sección 1.3):

- Voltaje de trabajo: **12 V**
- Batería: **12 V @ 10 Ah** (≈ 120 Wh)
- Consumo típico: **3 W**
- Autonomía: **30 h** con batería completa
- Alimentación alterna: adaptador HTC 220 V AC (uso en interiores, sin batería)

> Nota de consistencia: 120 Wh ÷ 3 W ≈ 40 h teóricas; la cifra oficial de 30 h ya contempla pérdidas de conversión/reserva de batería, es coherente.

Este módulo corresponde a la estación de seguimiento óptico (equivalente a un lighthouse HTC Vive Gen 2, según el log de arranque de `pika_locator`: `Detected LH gen 2 system`).

### 2.2 Pika Sense (unidad de captura portátil)
No hay una cifra total de consumo publicada para todo el conjunto. Se alimenta de dos formas distintas:

- **Etiqueta de posicionamiento (tracker superior)**: batería propia, recarga independiente por su puerto dedicado. Autonomía oficial: **9 h**. Sin capacidad de batería publicada, por lo que el consumo medio (~0.4–0.5 W) es una estimación basada en trackers ópticos similares (baterías de Li-ion ~1000 mAh).
- **Resto de sensores** (cámara D405, cámara fisheye, codificador del gripper, IMU): se alimentan vía el cable Type-C desde el equipo de cómputo (laptop, mini PC de la mochila, o el host que corre `sensor_tools`). No tienen batería propia ni cifra de consumo publicada por AgileX.

### 2.3 Pika Gripper (unidad ejecutora)
- Conector de potencia: **XT30(PB)**, línea de **24 V DC** dedicada al motor sin escobillas de la pinza (dato ✅ oficial, tabla de pines de la sección 1.6.2).
- El firmware (`sensor_tools`) limita la corriente del motor a **1000 mA** por defecto (parámetro `motor_current_limit`, en [open_multi_gripper.launch.py:33](../../src/sensor_tools/launch/open_multi_gripper.launch.py#L33) y equivalentes) → **24 W pico** a 24 V.
- En reposo/sujeción estática el consumo real es mucho menor (~2–7 W estimado), ya que el motor solo corrige posición.
- Cámaras y sensores del Gripper (mismas que en Sense) se alimentan vía Type-C, mismas estimaciones que en 2.2.

### 2.4 Cámara Intel RealSense D405
Dato de fabricante (Intel), no está en la documentación de AgileX:
- Alimentación: bus USB 3.1 Gen 1 Type-C, sin entrada de alimentación separada.
- Consumo típico publicado por Intel para la familia D400 de factor reducido: **~2.5 W** en operación (color + profundidad activos), picos cercanos a 3.5 W durante el arranque de stream.

### 2.5 Cámara fisheye USB
No se identifica una marca/modelo específico en el repositorio (se referencia genéricamente como cámara USB fisheye ~200°, ver `usb_camera.py`). El consumo de módulos UVC USB de esta clase (sensor + lente + controlador) típicamente ronda **1.5–2.5 W**; es una estimación, no una cifra certificada.

### 2.6 Brazo robótico Piper (PikaAnyArm)
Especificaciones **oficiales** tomadas de `agilex-piper-user-manual.pdf` (sección 5, "Technical Specifications"):

| Parámetro | Valor |
| --- | --- |
| Voltaje de alimentación | DC 24 V (mín. 24 V, máx. 26 V) |
| Potencia máxima | **≤ 120 W** |
| Potencia integral (uso normal/continuo) | **≤ 40 W** |
| Carga útil (payload) | 1.5 kg |
| Peso del brazo | 4.2 kg |
| Repetibilidad | ±0.1 mm |
| Radio de trabajo | 626.75 mm |
| Comunicación | CAN |
| Nota de la corriente de carga si se usa un cargador no estándar | entrada ≤ 26 V, corriente ≥ 10 A |

El manual aclara que estos son resultados de prueba de AgileX en un entorno controlado; el consumo real puede variar según el uso.

**Accesorios opcionales del Piper** (no forman parte de este workspace de `pika_ros`, pero sí del ecosistema del brazo si se usan):
- Pinza de dos dedos (follower gripper): 24 V DC, ≤30 W integral / ≤50 W máx.
- Dispositivo de enseñanza / gripper maestro (leader teaching device): 24 V DC, ≤30 W integral / ≤50 W máx.

> Nota: en este proyecto, la teleoperación usa `piper_single_ctrl` para leer/escribir el estado del brazo vía CAN — la pinza física que se mueve es la del **Pika Gripper** (sección 2.3), no el follower gripper opcional de AgileX. Esta tabla se incluye por si en el futuro se usa el gripper nativo del Piper.

### 2.7 Periféricos USB auxiliares
- Adaptador USB–CAN (`gs_usb`, usado por `can_config.sh` para `can_left`/`can_right`): bus-powered, bajo consumo (~1–2.5 W estimado).
- Receptor USB inalámbrico del tracker (dongle de la etiqueta de posicionamiento): bus-powered, consumo mínimo (<0.5 W estimado).

---

## 3. Presupuesto energético por configuración

Suma aproximada de los componentes activos en cada modo de uso descrito en `CLAUDE.md` / `Manual.md`. Los rangos reflejan reposo→uso activo.

| Configuración | Componentes | Consumo aproximado |
| --- | --- | --- |
| `single_pika` (1 Sense + 1 Station) | Sense (D405+fisheye+IMU ~4–5 W vía USB del host) + tracker (~0.5 W) + Station (3 W) | **~7.5–8.5 W** (sin contar el host) |
| `multi_pika` (2 Sense + 2 Station) | 2× Sense + 2× tracker + 2× Station | **~15–17 W** (sin contar el host) |
| Teleoperación 1 brazo (Sense + Station + Gripper + Piper) | Sense (~5 W) + Station (3 W) + Gripper Pika (2–24 W) + Piper (≤40 W integral, ≤120 W pico) | **~10–50 W típico, hasta ~152 W en pico** |
| Teleoperación 2 brazos (`teleop_rand_multi_piper`) | 2× (Sense + Station + Gripper Pika + Piper) | **~20–100 W típico, hasta ~304 W en pico** |

El equipo de cómputo (laptop o mini PC que ejecuta ROS 2, `colcon`, y los nodos) no está incluido: su consumo depende del hardware del usuario (típicamente 15–65 W en un mini PC tipo NUC, o 30–120 W en una laptop con GPU bajo carga) y no es un componente "Pika" del datasheet.

---

## 4. Limitaciones de este documento

- La **Pika Station** y el **brazo Piper** (incluyendo sus accesorios opcionales de pinza/enseñanza) tienen cifras de consumo oficiales, tomadas de las hojas de datos de AgileX incluidas en este repositorio.
- El resto de valores (cámaras D405/fisheye, IMU, consumo real del motor de la pinza Pika, periféricos USB) son estimaciones basadas en especificaciones típicas de fabricante o límites de firmware, **no mediciones directas de este hardware**.
- Para cifras de precisión (dimensionar una batería portátil o fuente de alimentación, por ejemplo), se recomienda medir con un multímetro/medidor USB en línea durante la operación real de captura y teleoperación.

## 5. Fuentes

- `[Externo] Hoja de datos del producto Pika beta (CN).md` (incluido en este repositorio) — Pika Sense, Pika Gripper, Pika Station.
- `agilex-piper-user-manual.pdf` (incluido en este repositorio) — brazo Piper y sus accesorios opcionales.
- Especificaciones públicas de Intel (RealSense D400 series) y estimaciones para el resto de periféricos USB genéricos, sin documentación oficial en este proyecto.
