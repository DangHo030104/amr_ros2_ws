import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    odometry_config = os.path.join(
        get_package_share_directory('amr_odometry'),
        'config',
        'odometry.yaml'
    )
    ekf_config = os.path.join(
        get_package_share_directory('amr_odometry'),
        'config',
        'ekf.yaml'
    )
    return LaunchDescription([
        Node(
            package='amr_odometry',
            executable='odometry.py',
            name='odometry',
            output='screen',
            parameters=[odometry_config]
        ),
        Node(
            package='robot_localization',
            executable='ekf_node',
            name='ekf_filter_node',
            output='screen',
            parameters=[ekf_config],
            remappings=[('odometry/filtered', 'odom')]
        )
    ])
