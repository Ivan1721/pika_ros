# Frutas candidatas para la percepción activa

Evaluación del 20 de octubre de 2026. **La primera demo es con manzanas** (ver
[lazos_cinematica_nbv.md §5.6](lazos_cinematica_nbv.md#56-ejemplo-en-simulación-manzano)). Este
documento ordena otras frutas para más adelante, según lo que permite el sistema y lo que hay
disponible.

## 1. Restricciones del sistema

| Restricción | Valor | Efecto |
|---|---|---|
| Apertura de la pinza Pika | 0–70 mm entre garras | Frutas de más de ~65 mm de diámetro no se pueden tomar de lado a lado |
| Alcance del Piper | ~0,63 m (0,81 m del hombro al TCP con la Pika) | La fruta tiene que quedar a la altura de la plataforma; el motor Hydronit reubica la base, pero no la eleva varios metros |
| Mirar hacia arriba | En la demo, las vistas desde abajo (elevación −15°) y las muy laterales quedan fuera del límite de ±70° de J5 | Cultivos donde la fruta cuelga **sobre** el robot (pérgola) son difíciles |
| D405 | 7–50 cm, 87° × 58° | Funciona bien de cerca: frutas chicas o medianas vistas a 15–35 cm |
| Carga del Piper | 1,5 kg | Ninguna fruta individual es problema |

## 2. Comparación

| Fruta | Tamaño típico | Oclusión dominante | Encaje con Piper + Pika | Recursos públicos | En el corpus |
|---|---|---|---|---|---|
| **Manzana** (demo actual) | 65–85 mm | hojas y otras manzanas | Bien para percepción; **para cosechar, al límite de la pinza** (≤ 70 mm) | [Fuji-SfM](https://zenodo.org/record/3712808) (manzanas reales con nube 3D y posición de cada fruto); escena propia en `pika_sim` | *Autonomous Apple Fruitlet Sizing with NBV* (2024), *Execution-Aware NBV … apple perception* (2026), *Active view planning for counting apples* (2017), y otros 3 de detección y cosecha de manzana |
| **Tomate** (racimo o cherry) | 20–70 mm | hojas, tallos, frutos del mismo racimo | Muy bien: invernadero a altura de trabajo, frutos dentro de la pinza | **Los más completos:** [aoc_tomato_farm](https://github.com/LCAS/aoc_tomato_farm) (ROS 2 + Gazebo), [fields-ignition](https://github.com/azazdeaz/fields-ignition), [TomatoWUR](https://data.4tu.nl/datasets/e2c59841-4653-45de-a75e-4994b2766a2f), [Pheno4D](https://www.ipb.uni-bonn.de/data/pheno4d/), [DAVIS-Ag](https://github.com/ctyeong/DAVIS-Ag) | El grupo más grande: Burusa et al. (3 papers de NBV), *Adaptive Viewpoint Selection for Tomato Truss Localization* (2025), *Active perception … tomatoes hidden within clusters* (2026), *Best-View Pedicel Localization … Cherry Tomatoes* (2026) |
| **Pimentón** | 70–100 mm | hojas; pedúnculo oculto | Bien para percepción; **grande para la pinza** | Planners de Bonn (pimiento en Gazebo, escena no publicada) | *Viewpoint Planning for Fruit Size and Position Estimation* (2021), *Graph-Based VMP*, GO-VMP, *HortiBot* (2024), 2 de dirección de aproximación |
| **Uva de mesa** | racimo; baya 15–25 mm | hojas sobre el racimo; pedúnculo | Bien: se corta el pedúnculo, no se toma la baya; parronal a altura de trabajo | [DAVIS-Ag](https://github.com/ctyeong/DAVIS-Ag) (vid en goblet) | *View Planning for Grape Harvesting … under Occlusion* (2024) y su versión con DRL (2025), *Active Perception for Grapevine …* (2026), *DRL-enhanced 3D detection of occluded stems …* (2024) |
| **Frutilla** | 25–40 mm | hojas; fruta cerca del suelo | Cabe en la pinza; exige trabajar muy bajo | [DAVIS-Ag](https://github.com/ctyeong/DAVIS-Ag) (frutilla) | Review de cosecha de frutilla (2026) |
| **Pera** | 60–80 mm | hojas | Como la manzana | — | Review de robots para cosechar pera (2025) |
| **Cereza** | 20–28 mm | hojas; racimos de 2–4 | Cabe en la pinza; pedúnculo delicado | — | — (solo cherry tomato) |
| **Mandarina y limón** | 50–70 mm | hojas densas | Cabe al límite; árbol bajo o mediano | — | *AI-driven adaptive grasping … citrus harvesting* (2025) |
| **Naranja** | 70–90 mm | hojas densas | Grande para la pinza | — | (el mismo paper de cítricos) |
| **Arándano** | 10–15 mm | racimos densos | Demasiado chico para tomarlo de a uno; percepción muy fina | — | — |
| **Palta** | 70–100 mm | hojas grandes | Grande para la pinza; árboles altos, fuera del alcance | GS-NBV usa un palto en Gazebo | *GS-NBV … Avocado Harvesting under Occlusions* (2025) |
| **Kiwi** | 45–55 mm | hojas sobre la fruta | Cabe en la pinza, pero **cuelga de una pérgola sobre el robot**: hay que mirar hacia arriba, lo que la muñeca no permite | — | — |

Los tamaños son rangos típicos de la fruta comercial, como orientación; no son mediciones de este
proyecto.

**Modelos 3D:** la biblioteca de plantas de Helios, ya integrada para la manzana (`arbol:=helios`
en `pika_sim`), trae también tomate, tomate cherry, vid (VSP y Wye), pimentón, frutilla, olivo,
almendro, nogal y pistacho. Pasar a otra fruta es, en principio, cambiar el modelo en
`generar_manzano_helios.py`, que hoy acepta solo los dos de manzano
([recursos_publicos.md §1b](recursos_publicos.md#1b-árboles-completos-hojas-ramas-y-frutos-en-3d-revisión-del-20-10-2026-segunda-parte)).

## 3. Recomendación

1. **Manzana: la demo actual.** Hay buena base en el corpus (sobre todo NBV de huerto) y Fuji-SfM para validar con datos reales. Para cosechar, la apertura de 70 mm queda justa con manzanas grandes; para la **percepción**, que es el foco del survey, no hay problema.
2. **Tomate: la opción con más respaldo.** Tiene el mayor número de papers comparables de NBV, un generador de escenas listo para ROS 2 Humble + Gazebo y datasets de geometría real. Si el grupo prioriza comparar con el estado del arte, es la mejor siguiente fruta.
3. **Uva de mesa y pimentón.** Tienen buen respaldo en el corpus. Con la uva se corta el pedúnculo, así que no la limita la apertura de la pinza.
4. **Más adelante, con trabajo extra:**
   - cereza y arándano: frutas chicas en racimos; necesitan percepción fina;
   - mandarina, limón y pera: parecidas a la manzana, pero con pocos recursos públicos.
5. **No recomendadas con este brazo y esta pinza:**
   - **palta y naranja,** por tamaño y altura;
   - **kiwi,** porque exige vistas desde abajo que la muñeca del Piper no alcanza en la demo.

Para todas: el estudio YOLO de oclusión (rangos de visibilidad 25–100 %) se entrenó con fruta real. Al
pasar a otra fruta hay que revisar si el detector la cubre o hay que reentrenarlo. En simulación, el
etiquetado automático desde la geometría conocida sirve para eso
([recursos_publicos.md §4](recursos_publicos.md#4-propuesta-para-la-escena-de-nbv)).
