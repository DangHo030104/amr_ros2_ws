import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def include_launch(package_name, launch_file):
    path = os.path.join(
        get_package_share_directory(package_name),
        'launch',
        launch_file
    )
    return IncludeLaunchDescription(PythonLaunchDescriptionSource(path))


def generate_launch_description():
    return LaunchDescription([
        include_launch('amr_description', 'description.launch.py'),
        include_launch('amr_serial_bridge', 'serial_bridge.launch.py'),
        include_launch('amr_odometry', 'odometry.launch.py'),
        include_launch('amr_lidar', 'lidar.launch.py')
    ])
