cmake_minimum_required(VERSION 3.8)
project(amr_odometry)

find_package(ament_cmake REQUIRED)

install(PROGRAMS
  amr_odometry/odometry.py
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY launch config
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
