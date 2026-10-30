#!/usr/bin/env python3

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


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
            'use_sim_time': 'false',
            'autostart': 'true',
            'use_lifecycle_manager': 'false'
        }.items()
    )

    return LaunchDescription([
        slam_node
    ])
