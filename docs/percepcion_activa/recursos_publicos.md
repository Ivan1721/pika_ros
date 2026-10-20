# Recursos públicos para la escena de percepción activa

Revisión del 20 de octubre de 2026. Reúne modelos de vegetación, generadores de escenas agrícolas,
datasets publicados con papers y material disponible sobre el sistema Pika, para pasar de la escena
de prueba actual (esferas y discos, ver [lazos_cinematica_nbv.md §5.6](lazos_cinematica_nbv.md#56-ejemplo-en-simulación-manzano))
a una escena agrícola realista.

**Licencias:** varios recursos no declaran licencia. Usarlos en investigación suele ser aceptable,
pero **antes de redistribuirlos o publicarlos dentro de este repo hay que pedir permiso a los
autores**. La columna "Licencia" dice lo que muestra cada página.

## 1. Plantas y escenas agrícolas para el simulador

| Recurso | Qué ofrece | Entorno | Licencia | Encaje con este proyecto |
|---|---|---|---|---|
| [LCAS/aoc_tomato_farm](https://github.com/LCAS/aoc_tomato_farm) | Generadores paramétricos de invernaderos y campos de **tomate con frutos**; cada planta se genera al azar (tallos, hojas, frutos). Parámetros: tamaño, filas, plantas por fila, luz | **ROS 2 Humble**; Gazebo Classic y Gazebo Sim; también Unity | Apache-2.0 | **El más directo:** mismo ROS 2 y mismo Gazebo que `pika_sim` |
| [azazdeaz/fields-ignition](https://github.com/azazdeaz/fields-ignition) | Script de Blender (`tomato_gen.py`) que genera tomateras; exporta SDF y un `markers.json` con la **posición de cada fruto** (ground truth) | ROS 1 Noetic + Ignition Dome | MIT | Reutilizar el generador de Blender y exportar las mallas a Gazebo Classic |
| [Helios / PyHelios](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2019.01185/text) (UC Davis) | Modelado procedural 3D de plantas y del ambiente, con API en C++ y Python; es la base de DAVIS-Ag | biblioteca independiente | código abierto | Plantas más realistas con parámetros: permitiría **fijar niveles de oclusión** (25–100 %, como el estudio YOLO) |
| [Romea/cropcraft](https://github.com/Romea/cropcraft) | Campos de cultivo desde YAML; Blender → archivo `.blend` y modelo de Gazebo; renderiza RGB y máscaras (cultivo, maleza, suelo) | Blender ≥ 4.0, Gazebo | Apache-2.0 | Cultivos en hilera; **no menciona frutales**. Útil para el entorno, no para la fruta |
| Bonn, Zaenker et al.: [view_motion_planner](https://github.com/Eruvae/view_motion_planner), [roi_viewpoint_planner](https://github.com/Eruvae/roi_viewpoint_planner) | Planners de NBV de fruta (GO-VMP, *Graph-based VMP*, del corpus) con un mundo de Gazebo de pimientos (`world23`, `trolley`) y brazo UR con cámara | ROS 1 (catkin) | no declarada | Referencia de método. El paquete de la escena (`ur_with_cam_gazebo`) **no aparece publicado**: pedirlo a los autores |
| [jrcuaranv/nbv_planning](https://github.com/jrcuaranv/nbv_planning) | NBV para mapeo semántico activo en horticultura; trae modelos de plantas para Gazebo (`install_models.sh`) | ROS Noetic | no declarada | Modelos listos para probar; el tipo de cultivo no está documentado |
| Burusa et al. (WUR, del corpus) | Sus tres papers de NBV en tomate usan **mallas comerciales Xfrog de tomate** ([cgtrader](https://www.cgtrader.com/3d-models/plant/other/xfrogplants-tomato)) | — | de pago | Para reproducir exactamente su escena |
| [Gazebo Plants](https://arxiv.org/abs/2402.02570) (2024) | Plugin de física de plantas deformables (varillas de Cosserat) | Gazebo | MPL 2.0, a pedido | Para que las hojas cedan al contacto (acercamiento en modo impedancia) |

## 2. Datasets publicados

| Dataset | Contenido | Uso aquí | Acceso |
|---|---|---|---|
| **[DAVIS-Ag](https://github.com/ctyeong/DAVIS-Ag)** (CASE 2024, del corpus) | 502K imágenes sintéticas 1280×720 de 632 escenas (fresa, tomate, vid en goblet), una o varias plantas. Cada vista trae máscara de instancia de los frutos, cajas, **pose de cámara y enlaces a las vistas vecinas por acción** (adelante, arriba, girar…) | **Benchmark offline de NBV:** probar las políticas A y B sin simulador, navegando el grafo de vistas | SharePoint de Kennesaw State; licencia no declarada; el código de los experimentos figura como "próximamente" |
| **[TomatoWUR](https://data.4tu.nl/datasets/e2c59841-4653-45de-a75e-4994b2766a2f)** (WUR, 2025) | 44 nubes de puntos de tomateras anotadas (hoja, tallo, tutor), imágenes de 15 cámaras, esqueletos y medidas manuales; código en [WUR-ABE/TomatoWUR](https://github.com/WUR-ABE/TomatoWUR) | Geometría **real** de tomateras: validar mapas 3D o derivar mallas | 4TU.ResearchData (DOI) |
| **[Pheno4D](https://www.ipb.uni-bonn.de/data/pheno4d/)** (Bonn, 2021) | Nubes de puntos de maíz y tomate en varias etapas de crecimiento, ~260 millones de puntos etiquetados | Variación por etapa de crecimiento (oclusión que cambia en el tiempo) | libre |
| **[Fuji-SfM](https://zenodo.org/record/3712808)** (UdL, 2020) | Manzanas Fuji reales: 288 imágenes con máscaras, 582 de una secuencia y la nube 3D de 11 árboles con la **posición real de cada manzana**; 6,43 GB | Fruta real ocluida en huerto, para validar detección y visibilidad | Zenodo; un dataset hermano del grupo es solo para investigación y educación: verificar |
| **[AgML](https://pypi.org/project/agml/)** (UC Davis) | Biblioteca Python que indexa datasets agrícolas públicos (el equipo habla de más de 275) y genera datos sintéticos con Helios | Un solo punto de entrada para datasets de fruta para el detector | pip |

## 3. Sistema Pika

**No encontré material público del Pika para simulación:**
- **Datasets grabados con Pika:** ninguno, ni en Hugging Face ni en arXiv. La búsqueda solo trae guías de uso de distribuidores ([OpenELAB](https://openelab.io/blogs/learn/how-to-collect-robot-demonstration-data-with-agilex-pika)). El dataset `DaMiTian/agilex_dataset` de Hugging Face está vacío.
- **CAD o URDF de la carcasa del Pika Gripper o del Sense:** no está publicado. AgileX dice en su [página de producto](https://global.agilex.ai/products/pika) que soporta URDF, pero no publica los archivos. Las tiendas dan las medidas (215 × 191 × 143 mm) y el peso (617–690 g, según la tienda). El `AgileX_Gripper.STEP` que circula es de la **pinza del Piper**, otro producto.

Por eso `pika_description` usa la malla de la pinza del Piper, y el `pika_tcp` queda ~5 cm más allá
de las garras dibujadas ([PIPER_PIKA.md §6](../../src/pika_description/docs/PIPER_PIKA.md)). Para
corregirlo, en orden:
1. **Pedir a AgileX** el STEP/URDF del Pika Gripper y del Sense (support@agilex.ai, el contacto del README).
2. **Escanear el gripper real** por fotogrametría o con la propia D405, y medir dónde cierran las garras (el TCP real).

## 4. Propuesta para la escena de NBV

1. **Escena (paso 3 de la hoja de ruta).** Reemplazar las esferas y discos por tomateras de `aoc_tomato_farm`, que corre en ROS 2 Humble con Gazebo Classic. Otra opción es exportar desde el generador de Blender de `fields-ignition`, que entrega la posición de cada fruto.
2. **Visibilidad real con mallas complejas.** El trazado de rayos contra discos ya no sirve con hojas reales. Un método directo en Gazebo: renderizar cada vista dos veces desde la misma cámara virtual, con y sin el follaje, y dividir los píxeles visibles del fruto por los del fruto completo. El fruto se separa con un color plano único.
3. **Niveles de oclusión controlados.** Con Helios/PyHelios se pueden generar plantas con densidad de hojas paramétrica, y fijar la oclusión en los rangos del estudio YOLO (25/50/70/75/100 %).
4. **Benchmark offline.** Evaluar las políticas A y B en DAVIS-Ag antes de gastar tiempo de simulación: su grafo de vistas reproduce el bucle "mirar → moverse".
5. **Validación con datos reales.** TomatoWUR y Pheno4D para la geometría de tomate; Fuji-SfM si el cultivo objetivo son manzanas.

**Cultivo:** la primera demo es con **manzanas** (decisión del 20-10-2026). La evaluación de otras
frutas está en [frutas_candidatas.md](frutas_candidatas.md).
