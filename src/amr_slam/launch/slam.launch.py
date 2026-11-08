#!/usr/bin/env python3

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():

    # File cau hinh cua robot
    slam_config = os.path.join(
        get_package_share_directory('amr_slam'),
        'config',
        'slam.yaml'
    )

    # Launch chinh thuc cua SLAM Toolbox
    slam_launch = os.path.join(
        get_package_share_directory('slam_toolbox'),
        'launch',
        'online_async_launch.py'
    )

    slam_node = IncludeLaunchDescription(PythonLaunchDescriptionSource(slam_launch),
        launch_arguments={
            'slam_params_file': slam_config,
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'autostart': 'true',
            'use_lifecycle_manager': 'false'
        }.items()
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Dùng clock mô phỏng khi chạy với Gazebo'
        ),
        slam_node
    ])
