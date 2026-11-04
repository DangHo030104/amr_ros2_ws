import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    # Dùng launch chuẩn của Nav2 để quản lý AMCL, map server, planner, controller, behavior server và lifecycle.
    nav2_launch = os.path.join(
        get_package_share_directory('nav2_bringup'),
        'launch',
        'bringup_launch.py'
    )

    # File cấu hình riêng đã được điều chỉnh theo robot AMR thực tế.
    params_file = os.path.join(
        get_package_share_directory('amr_navigation'),
        'config',
        'nav2.yaml'
    )

    return LaunchDescription([
        # Khai báo tham số đầu vào cho launch file, yêu cầu người dùng cung cấp đường dẫn tới file YAML của bản đồ đã lưu.
        # VD: ros2 launch amr_navigation navigation.launch.py \
        #     map:=/duong/dan/lab_map.yaml
        DeclareLaunchArgument(
            'map',
            description='Đường dẫn tuyệt đối tới file YAML của bản đồ đã lưu'
        ),

        # Nạp launch file chuẩn của Nav2, truyền các tham số cần thiết.
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(nav2_launch),
            launch_arguments={
                'map': LaunchConfiguration('map'),
                'params_file': params_file,         # Nạp cấu hình nav2.yaml 
                'use_sim_time': 'false',
                'autostart': 'true',                # Auto khởi chạy các node Nav2 (Lifecycle Node) khi launch
                'slam': 'false',                    # Không chạy SLAM Toolbox, dùng Localization
                'use_composition': 'true',          # Chạy các node Nav2 trong component container (giảm tải CPU)
                'use_respawn': 'false'              # Không tự khởi động lại tiến trình Nav2 khi lỗi
            }.items()
        )
    ])
