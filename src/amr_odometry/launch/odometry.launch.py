import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    config = os.path.join(
        get_package_share_directory('amr_odometry'),
        'config',
        'odometry.yaml'
    )

    return LaunchDescription([
        Node(
            package='amr_odometry',
            executable='odometry.py',
            name='odometry',
            output='screen',
            parameters=[config]
        )
    ])
