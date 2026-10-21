# Plan de migración a Next-Best-View

Plan del 21 de octubre de 2026 para llevar el trabajo de investigación de `pika_ros` (fork público
de AgileX) a un repositorio propio y privado, `Ivan1721/Next-Best-View`. Todavía no se ha ejecutado.

## 1. Objetivo y criterio

- **Next-Best-View (privado):** todo lo propio de la investigación: simulación, modelo del robot, percepción activa, informes, figuras, herramientas, modelos 3D y, más adelante, Docker.
- **pika_ros (fork público):** vuelve a ser solo el fork de AgileX con los ajustes de hardware de esta máquina, para seguir sincronizando con AgileX sin conflictos.
- **Criterio para cada archivo:** si lo escribimos nosotros o es material que nos pasó AgileX para la investigación, va a Next-Best-View. Si es código de AgileX, o un ajuste a ese código para que funcione el hardware, se queda en `pika_ros` y Next-Best-View lo usa como dependencia.

Estado de partida, verificado el 21-10-2026:
- Next-Best-View existe, es accesible por SSH y está vacío.
- La rama `sim-gazebo` de `pika_ros` tiene 151 archivos cambiados respecto de AgileX, en 74 commits. 29 de ellos no están en `pika-custom-ros2`.
- La identidad de git de la máquina es `Your Name <you@example.com>`: así quedaron firmados 72 commits.
- No están instalados `git filter-repo` ni Git LFS. Docker sí (29.9).

## 2. Qué va a dónde

| Contenido actual en `pika_ros` | Destino | Nota |
|---|---|---|
| `src/pika_sim/` | NBV `src/pika_sim/` | Paquete ROS 2 completo |
| `src/pika_description/` (incluye `meshes/agilex/`, `agilex/`, `docs/`) | NBV `src/pika_description/` | Las mallas quedan dentro del paquete (`package://pika_description/...`); 18 MB de STL a Git LFS |
| `docs/percepcion_activa/` (con `img/` y `img/modelos/`) | NBV `docs/percepcion_activa/` | 8,7 MB de imágenes |
| `docs/estado_del_proyecto.md`, `docs/README.md` | NBV `docs/` | El mapa se rehace con las rutas nuevas |
| `docs/arquitectura/`, `docs/energia/` | NBV `docs/` | Diagramas, generador, inventario y presupuesto |
| `docs/manuales/Manual.md` | NBV `docs/manuales/` | Guía propia; actualizar rutas `~/pika_ros` donde corresponda |
| `docs/manuales/` (PDF y manual EN), `docs/datasheets/`, `docs/calibracion/` | NBV `docs/agilex/` | Material oficial de AgileX, de consulta |
| `docs/presentaciones/` | NBV `docs/presentaciones/` | |
| `scripts/calcular_gravedad_mit.py`, `scripts/test_piper_mit_impedance.py`, `scripts/capture_bundle.py` | NBV `tools/` | Herramientas propias; usan el SDK del Piper y la cinemática de `pika_description` |
| Generadores de figuras y escenas (`generar_manzano_helios.py`, `render_camara.py`, `galeria_oclusion.py`, `panel_*.py`, `figuras_piper_pika.py`, `generar_diagrama.py`) | se quedan donde están dentro de cada paquete o carpeta | Moverlos a `tools/` rompería los `ros2 run`; se listan en el README |
| `scripts/setup_*.bash`, `scripts/start_*.bash`, `scripts/setup_device.py` (modificados) | **quedan en `pika_ros`** | Son de la máquina y del hardware (seriales, puertos USB) |
| `src/sensor_tools/` (launch y README modificados) | **quedan en `pika_ros`** | Driver de AgileX |
| `src/PikaAnyArm` (fork propio, con `sim:=true` e `index_name`) | **queda como repo propio**; NBV lo usa como dependencia | |
| `src/data_tools`, `src/data_msgs`, `src/realsense-ros` | **quedan en `pika_ros`** | Código de AgileX e Intel |
| `install/` (`pika_locator`, `libsurvive`, solo binarios) | **queda en `~/pika_ros`** | No se puede recompilar; el NBV lo usa como capa base |
| `AGENTS.md`, `CLAUDE.md` | se escriben unos nuevos para NBV | Los de `pika_ros` se acortan a lo del fork |
| `README.md`, `README_es.md`, `README_zh.md` | quedan en `pika_ros` | Textos de AgileX |
| `gripper/*.png` (raíz), `.vscode/settings.json`, `scripts/setup_device(original).py` | **se borran** | Restos sin uso |
| `~/.cache/pika_sim/` (árboles de Helios generados) | no se versiona | Texturas LGPL; se regeneran con el script |
| `figuras_fuente/gazebo/` en ActivePerceptionArms | queda allá | Pertenece al survey |

## 3. Estructura de Next-Best-View

```
Next-Best-View/
  README.md                 mapa de todo (hereda el de docs/README.md)
  AGENTS.md, CLAUDE.md      convenciones y guía para agentes
  dependencias.repos        repos que se bajan con vcs import, fijados por commit
  src/
    pika_sim/               simulación en Gazebo
    pika_description/       URDF del Piper con la Pika (modelo de AgileX)
    (nbv_planner/)          el planner, cuando exista
  tools/                    herramientas sueltas: MIT, gravedad, capturas
  docs/
    estado_del_proyecto.md
    percepcion_activa/  arquitectura/  energia/  manuales/  presentaciones/
    agilex/                 manuales, hojas de datos y guías oficiales
  docker/                   (fase 7)
  .gitattributes            Git LFS para *.STL, *.stl, *.dae, *.pdf, *.pptx, *.docx
```

**Espacio de trabajo: dos capas.** `~/pika_ros` sigue igual, como capa base: drivers, binarios del
localizador y PikaAnyArm. Next-Best-View se compila en su propio espacio de trabajo y se monta
encima:

```bash
mkdir -p ~/nbv_ws/src && cd ~/nbv_ws/src && git clone git@github.com:Ivan1721/Next-Best-View.git
source ~/pika_ros/install/setup.bash          # capa base
cd ~/nbv_ws && colcon build && source install/setup.bash
```

Es lo que menos rompe: `install/` de `pika_ros` tiene binarios que no se pueden rehacer, y los
`start_*.bash` siguen funcionando. `dependencias.repos` documenta qué commit de cada dependencia se
probó, para poder rearmar todo en otra máquina o en Docker.

## 4. Decisiones antes de empezar

| # | Decisión | Propuesta |
|---|---|---|
| 1 | ¿Conservar el historial de lo que se mueve? | **Sí**, con `git filter-repo`: quedan los 74 commits que tocaron esos archivos |
| 2 | ¿Corregir el autor `Your Name`? | **Sí**, con un `.mailmap` al filtrar. Falta definir el nombre y el correo que aparecerán; propuesta: el nombre completo y el correo *noreply* de GitHub |
| 3 | ¿Git LFS para las mallas y los PDF? | **Sí**: son binarios grandes que pueden cambiar. Las imágenes chicas (JPG, PNG de documentos) quedan en git normal |
| 4 | ¿Qué hacer con `sim-gazebo` en `pika_ros`? | Marcarla con la etiqueta `archivo-sim-gazebo` y borrar la rama; no unirla a `pika-custom-ros2` |
| 5 | ¿Borrar de `pika_ros` lo que se movió? | En `pika-custom-ros2`, sí: de lo migrado, ahí solo están `pika_description` (versión vieja) y `docs/energia`, `docs/manuales`, `docs/presentaciones`, `docs/calibracion`, `docs/datasheets`; se quitan en un commit con una nota que apunte al repo nuevo. `pika_sim` y `percepcion_activa` solo existen en `sim-gazebo`. El historial público no se reescribe |
| 6 | ¿Nombre de la rama principal del NBV? | `main` |

## 5. Fases

### Fase 0 — Preparación (15 min)
1. Instalar `git-filter-repo` (`pip install --user git-filter-repo`) y Git LFS (`sudo apt install git-lfs`, luego `git lfs install`).
2. Configurar la identidad de git de la máquina (decisión 2).
3. En `pika_ros`: verificar que no queden cambios sin subir, crear la etiqueta `pre-migracion-nbv` en `sim-gazebo` y subirla. Es el punto de retorno.

### Fase 1 — Extraer con historial (30 min)
1. Clonar `pika_ros` en una carpeta temporal y ubicarse en `sim-gazebo`.
2. Correr `git filter-repo` con las rutas de la tabla de la sección 2 (`--path`), los cambios de ubicación (`--path-rename docs/manuales/agilex-piper-user-manual.pdf:docs/agilex/...`, `scripts/calcular_gravedad_mit.py:tools/...`, etc.) y el `.mailmap`.
3. Revisar el resultado: `git log --stat`, que no aparezca nada de AgileX fuera de lo listado, y que no haya restos (`gripper/`, `.vscode`).
4. Pasar las mallas y los PDF a LFS con `git lfs migrate import --include="*.STL,*.stl,*.dae,*.pdf,*.pptx,*.docx" --everything`.

### Fase 2 — Ordenar y subir (30 min)
1. Agregar `README.md`, `AGENTS.md`, `CLAUDE.md`, `dependencias.repos` y `.gitattributes`.
2. Rehacer el mapa de documentación con las rutas nuevas (el script de anclas que ya existe).
3. Subir a `main` del NBV: `git remote add origin git@github.com:Ivan1721/Next-Best-View.git && git push -u origin main`.

### Fase 3 — Rutas y enlaces internos (45 min)
1. Cambiar las 14 referencias a `~/pika_ros/...` en `src/` y `docs/` por las nuevas. El caso delicado es el valor por defecto de `mit_script` en el launch de `pika_sim`, que apunta a `~/pika_ros/scripts/test_piper_mit_impedance.py`.
2. Cambiar los enlaces a `github.com/Ivan1721/pika_ros/blob/sim-gazebo/...` (las STL de §2.4 del informe, entre otros) por rutas relativas del NBV.
3. Volver a verificar todos los enlaces y anclas con el script de verificación.

### Fase 4 — Compilar y probar (45 min)
1. `~/nbv_ws`: compilar sobre la capa base de `~/pika_ros`.
2. Antes de compilar, sacar `pika_sim` y `pika_description` de `~/pika_ros` (o compilar `~/pika_ros` sin ellos), para que no haya dos paquetes con el mismo nombre en la capa base y la de arriba.
3. Pruebas, todas sin el robot salvo la última:
   - `ros2 launch pika_sim sim_piper_single.launch.py gui:=false rviz:=false escena:=manzano arbol:=helios` y la demo de NBV: tiene que dar los mismos números del informe (4 de 20, 69 %, 39 %);
   - la galería de oclusión en una luz;
   - `display_pika_piper.launch.py` y las figuras de `PIPER_PIKA.md`;
   - `calcular_gravedad_mit.py` desde `tools/`: el mismo `T_FF`;
   - con los dos Sense conectados: `start_multi_sensor.bash` y la simulación con `lado:=_l`.

### Fase 5 — Limpiar pika_ros (20 min)
1. Etiquetar `archivo-sim-gazebo` y borrar la rama `sim-gazebo` en GitHub y en local.
2. En `pika-custom-ros2`: quitar `pika_description` y los documentos que se movieron (decisión 5), y borrar los restos sin uso. Dejar en `docs/README.md` una nota de que la investigación sigue en un repo privado.
3. Acortar `AGENTS.md` y `CLAUDE.md` a lo que es del fork: hardware, sincronización con AgileX y flujos.

### Fase 6 — Referencias externas (20 min)
1. **ActivePerceptionArms:** enlaces a `pika_ros/sim-gazebo` en el README, `pedidos_figuras.md` y el proyecto de tesis.
2. **Portafolio:** la tarjeta de `pika_ros` en `proyectos.html` sigue válida (el repo sigue público); agregar el NBV solo si se hace público.
3. **Memoria del asistente** y `CLAUDE.md` de las otras máquinas: rutas nuevas y rol de cada repo.

### Fase 7 — Docker (más adelante)
- Imagen base `osrf/ros:humble-desktop-full`, con `gazebo_ros_pkgs`, `ros2_control`, RealSense, Python (numpy, scipy, Pillow) y el entorno de Helios.
- GPU con `nvidia-container-toolkit` para que Gazebo y las cámaras rindan como en la máquina (sección de consumo del informe).
- Para el hardware: dispositivos `/dev/ttyUSB5x`, `/dev/video5x`, el `hidraw` del Vive y los CAN, con las reglas udev en el anfitrión.
- Los binarios de `pika_locator` se copian desde `source/install.zip` de `pika_ros` al construir la imagen.

## 6. Riesgos y cómo cubrirlos

| Riesgo | Cobertura |
|---|---|
| Perder algo al filtrar | La etiqueta `pre-migracion-nbv` y la rama `sim-gazebo` siguen hasta terminar la fase 4 |
| Paquetes duplicados entre las dos capas | Fase 4, paso 2 |
| Enlaces rotos en documentos | Script de verificación de enlaces y anclas (ya existe) |
| Material de AgileX publicado | El NBV es privado; en `pika_ros` ya se publicó con autorización, y se deja de agregar ahí |
| El sitio o la tesis apuntan a rutas viejas | Fase 6 |
| Otra máquina (Windows) con clones viejos | Actualizar su `CLAUDE.md` y volver a clonar el NBV |

## 7. Tiempo estimado

Fases 0 a 6: unas 3,5 horas en una sesión. Fase 7, aparte.
