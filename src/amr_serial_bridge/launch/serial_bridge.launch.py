# Khởi chạy Node serial_bridge và tự động nạp các tham số cấu hình từ file serial_bridge.yaml

import os
from launch import LaunchDescription    # Class dùng để chứa list actions mà ROS 2 cần thực hiện khi chạy file Launch
from launch_ros.actions import Node     # Node ở đây là một hành động khởi chạy Node ROS 2

# Tự động tìm đường dẫn đến thư mục share, giúp ROS 2 tự tìm package trong các môi trường đã source phù hợp
from ament_index_python.packages import (get_package_share_directory)


def generate_launch_description():

    # Ghép các thành phần đường dẫn
    # VD: /home/black/amr_ros2_ws/install/amr_serial_bridge/share/amr_serial_bridge/config/serial_bridge.yaml
    config = os.path.join(
        get_package_share_directory('amr_serial_bridge'),
        'config',
        'serial_bridge.yaml'
    )

    return LaunchDescription([
        Node(
            package='amr_serial_bridge',
            executable='serial_bridge.py',
            name='serial_bridge',
            output='screen',                    # Cho phép hiển thị log của node trên màn hình terminal
            parameters=[config]                 # Nạp các tham số cấu hình từ file serial_bridge.yaml vào Node
        )
    ])
