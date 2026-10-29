import os

from ament_index_python.packages import (get_package_share_directory)

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    config = os.path.join(
        get_package_share_directory('amr_lidar'),
        'config',
        'lidar.yaml'
    )

    return LaunchDescription([
        Node(
            package='sllidar_ros2',
            executable='sllidar_node',
            name='sllidar_node',
            output='screen',
            parameters=[config],
            remappings=[
                ('scan', '/scan')
            ]
        )
    ])
