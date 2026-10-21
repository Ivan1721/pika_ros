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
| [Helios / PyHelios](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2019.01185/text) (UC Davis) | Modelado procedural 3D de plantas y del ambiente, con API en C++ y Python; es la base de DAVIS-Ag | biblioteca independiente | código abierto | **Integrado en `pika_sim`** (§1b). Permite **fijar niveles de oclusión** (25–100 %, como el estudio YOLO) |
| [Romea/cropcraft](https://github.com/Romea/cropcraft) | Campos de cultivo desde YAML; Blender → archivo `.blend` y modelo de Gazebo; renderiza RGB y máscaras (cultivo, maleza, suelo) | Blender ≥ 4.0, Gazebo | Apache-2.0 | Cultivos en hilera; **no menciona frutales**. Útil para el entorno, no para la fruta |
| Bonn, Zaenker et al.: [view_motion_planner](https://github.com/Eruvae/view_motion_planner), [roi_viewpoint_planner](https://github.com/Eruvae/roi_viewpoint_planner) | Planners de NBV de fruta (GO-VMP, *Graph-based VMP*, del corpus) con un mundo de Gazebo de pimientos (`world23`, `trolley`) y brazo UR con cámara | ROS 1 (catkin) | no declarada | Referencia de método. El paquete de la escena (`ur_with_cam_gazebo`) **no aparece publicado**: pedirlo a los autores |
| [jrcuaranv/nbv_planning](https://github.com/jrcuaranv/nbv_planning) | NBV para mapeo semántico activo en horticultura; trae modelos de plantas para Gazebo (`install_models.sh`) | ROS Noetic | no declarada | Modelos listos para probar; el tipo de cultivo no está documentado |
| Burusa et al. (WUR, del corpus) | Sus tres papers de NBV en tomate usan **mallas comerciales Xfrog de tomate** ([cgtrader](https://www.cgtrader.com/3d-models/plant/other/xfrogplants-tomato)) | — | de pago | Para reproducir exactamente su escena |
| [Gazebo Plants](https://arxiv.org/abs/2402.02570) (2024) | Plugin de física de plantas deformables (varillas de Cosserat) | Gazebo | MPL 2.0, a pedido | Para que las hojas cedan al contacto (acercamiento en modo impedancia) |

## 1b. Árboles completos, hojas, ramas y frutos en 3D (revisión del 20-10-2026, segunda parte)

Búsqueda de modelos 3D y bases de datos CAD de manzanos, con hojas y horquetas, que se puedan
correr en Gazebo. **El primero de la tabla ya está integrado en `pika_sim`** (`arbol:=helios`, ver
[src/pika_sim/README.md](../../src/pika_sim/README.md#manzano-realista-helios)).

| Recurso | Qué ofrece | Formato | Licencia | Encaje |
|---|---|---|---|---|
| **[Helios / PyHelios](https://github.com/PlantSimulationLab/PyHelios)** (UC Davis) | Biblioteca de 31 plantas procedurales con fenología: `apple`, `apple_fruitingwall` (muro frutal), y también `almond`, `olive`, `walnut`, `pistachio`, `grapevine_VSP` y `grapevine_Wye`, `tomato`, `cherrytomato`, `capsicum`, `strawberry`, entre otras. Árbol completo: tronco, ramas con horquetas, pecíolos, hojas, pedúnculos y frutos, con texturas fotográficas | exporta OBJ con MTL y texturas; da los objetos por órgano (hoja, fruto, entrenudo) | PyHelios MIT; núcleo y texturas LGPL-2.1 | **Integrado.** `pip install pyhelios3d`, sin ROS. Semilla y edad reproducibles; unos 20 s por árbol |
| [Apple Tree de Klas Karlsson](https://hub.qgis.org/wavefronts/7/) (QGIS Hub) | Árbol low poly con esferas rojas como frutas | Wavefront OBJ (según la URL) | CC0 | Fondo de hilera liviano; sin hojas individuales |
| [Apple Tree de venturon](https://venturon.itch.io/apple-tree) (itch.io) | Manzano low poly, solo colores de material | GLB, FBX | CC0 | Fondo; habría que convertirlo a OBJ o DAE |
| [Apple Kraken / ROSConDemo](https://github.com/o3de/ROSConDemo) (O3DE) | Huerto de manzanos con hileras y miles de manzanas, y un robot cosechador, en ROS 2 Humble | assets de O3DE | varias (Apache-2.0, MIT, CC BY 4.0 y CC BY-NC 4.0, según el archivo) | Referencia de escena de huerto; los assets son para O3DE, no Gazebo |
| [kubja/gazebo-vegetation](https://github.com/kubja/gazebo-vegetation) | 10 árboles y 5 arbustos para Gazebo, mallas de free3d.com | paquete ROS 1 | no declarada | No trae frutales |
| [Forest3D](https://github.com/vlordier/Forest3D) | Convierte assets de Blender a modelos y mundos SDF de Gazebo | Blender → SDF | ver repo | Camino si se consigue un `.blend` de manzano |
| TurboSquid, free3d, RenderHub, Xfrog ([cgtrader](https://www.cgtrader.com/3d-models/plant/other/xfrogplants-tomato)) | Manzanos y frutales de alto detalle | OBJ, FBX | gratis con licencia poco clara, o de pago | Solo si se necesita fotorrealismo de catálogo |

**Bases de datos de árboles reales** (para validar la geometría o construir árboles medidos):

| Dataset | Contenido | Formato | Licencia |
|---|---|---|---|
| **BRANCH3D** ([DiffTS, ICCV 2025](https://github.com/PRBonn/DiffTS), Bonn) | 280 manzanos de huerto escaneados con láser 10 veces en la temporada, con su **esqueleto de ramas de referencia** por fecha: la oclusión crece con el follaje | nubes de puntos y esqueletos | no declarada |
| [Real2Sim branch completion](https://github.com/suptimq/Real-Sim_3D_Branch_Completion) (Cornell, 2024) | Ramas de manzano simuladas (L-Py y Fusion 360) y 106 ramas reales medidas | ver repo | MIT |
| [synthetic-trees](https://github.com/uc-vision/synthetic-trees) (U. Canterbury) | Nubes de puntos sintéticas de manzano, cerezo y pino, con y sin hojas, con esqueletos | `.npz` | MIT |
| [CearLab Tree-Models-Library](https://github.com/CearLab/Tree-Models-Library) | ~20 árboles frutales reales de huerto como primitivas (ramas y frutos) | MATLAB `.txt` | MIT |
| [Manzanas y huerto en 3D](https://zenodo.org/records/15635995) (Zenodo, 2025) | 100 manzanas escaneadas en alta resolución y alineadas, más un escaneo láser de huerto (1,5 GB) y videos de dron | nubes de puntos, LAZ, MOV | CC BY 4.0 |
| [AppleQSM](https://www.sciencedirect.com/science/article/pii/S2643651524002620) y [BranchMatch](https://github.com/NingWang1999/BranchMatch) | Arquitectura de manzanos en espaldera desde nubes de puntos; escaneos de árboles en reposo | nubes de puntos | ver cada uno |

**Pendiente para más realismo:**
- reemplazar la malla de manzana de Helios por una de las 100 manzanas escaneadas de Zenodo;
- comparar la arquitectura del muro de Helios con BRANCH3D, que está medido en un huerto real;
- probar otras frutas candidatas con los modelos de Helios: tomate, uva, pimentón y frutilla.

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
- **CAD o URDF de la carcasa del Pika Gripper o del Sense:** no está publicado. AgileX dice en su [página de producto](https://global.agilex.ai/products/pika) que soporta URDF, pero no publica los archivos.

**Actualización del 20-10-2026:** a pedido nuestro, el soporte de AgileX envió los URDF y las
mallas del Pika Gripper y del Sense, los STEP de ambos y dos planos con medidas. Están integrados
en `pika_description` ([PIPER_PIKA.md §6](../../src/pika_description/docs/PIPER_PIKA.md#6-modelo-del-gripper-pika)).
AgileX autorizó publicarlos en este repositorio.

## 4. Propuesta para la escena de NBV

1. **Escena (paso 3 de la hoja de ruta).** ✅ Para manzanas, hecho con Helios (§1b). Para tomate, la opción directa sigue siendo `aoc_tomato_farm`, que corre en ROS 2 Humble con Gazebo Classic; Helios también trae tomateras.
2. **Visibilidad real con mallas complejas.** ✅ La demo ya traza rayos contra los triángulos de hojas y madera del árbol de Helios (Möller–Trumbore, en numpy). Complemento posible: en Gazebo, renderizar cada vista dos veces desde la misma cámara virtual, con y sin el follaje, y dividir los píxeles visibles del fruto por los del fruto completo. El fruto se separa con un color plano único.
3. **Niveles de oclusión controlados.** Con Helios se pueden generar plantas con densidad de hojas paramétrica, y fijar la oclusión en los rangos del estudio YOLO (25/50/70/75/100 %). El nodo de la escena ya elige la manzana objetivo por su visibilidad de frente (parámetro `visibilidad_frontal`); falta barrer los niveles.
4. **Benchmark offline.** Evaluar las políticas A y B en DAVIS-Ag antes de gastar tiempo de simulación: su grafo de vistas reproduce el bucle "mirar → moverse".
5. **Validación con datos reales.** TomatoWUR y Pheno4D para la geometría de tomate; Fuji-SfM si el cultivo objetivo son manzanas.

**Cultivo:** la primera demo es con **manzanas** (decisión del 20-10-2026). La evaluación de otras
frutas está en [frutas_candidatas.md](frutas_candidatas.md).
