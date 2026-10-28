cmake_minimum_required(VERSION 3.8)
project(amr_serial_bridge)

find_package(ament_cmake REQUIRED)
find_package(rclpy REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(std_msgs REQUIRED)

install(
  PROGRAMS
    amr_serial_bridge/serial_bridge.py
    amr_serial_bridge/serial_protocol.py
  DESTINATION lib/${PROJECT_NAME}
)

install(
  DIRECTORY
    launch
    config
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
