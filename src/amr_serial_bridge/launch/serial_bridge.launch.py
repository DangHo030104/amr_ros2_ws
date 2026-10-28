from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import (
    get_package_share_directory
)
import os


def generate_launch_description():

    config = os.path.join(
        get_package_share_directory(
            'amr_serial_bridge'
        ),
        'config',
        'serial_bridge.yaml'
    )

    return LaunchDescription([
        Node(
            package='amr_serial_bridge',
            executable='serial_bridge.py',
            name='serial_bridge',
            output='screen',
            parameters=[config]
        )
    ])
