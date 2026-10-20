cmake_minimum_required(VERSION 3.5)
project(pika_sim)

find_package(ament_cmake REQUIRED)

install(
  DIRECTORY urdf launch config rviz
  DESTINATION share/${PROJECT_NAME}
)

install(PROGRAMS
  scripts/piper_sim_bridge.py
  scripts/fake_pika_sense.py
  scripts/mit_emulador.py
  scripts/escena_nbv_demo.py
  scripts/escena_manzano.py
  scripts/profundidad_mm.py
  scripts/panel_nbv.py
  scripts/galeria_oclusion.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
