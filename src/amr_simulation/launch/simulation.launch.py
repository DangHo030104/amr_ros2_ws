import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    simulation_share = get_package_share_directory('amr_simulation')
    description_share = get_package_share_directory('amr_description')
    gazebo_share = get_package_share_directory('gazebo_ros')

    xacro_file = os.path.join(description_share, 'urdf', 'amr.urdf.xacro')
    default_world = os.path.join(simulation_share, 'worlds', 'test_world.world')
    rviz_config = os.path.join(simulation_share, 'rviz', 'simulation.rviz')

    robot_description = ParameterValue(
        Command(['xacro ', xacro_file, ' use_gazebo:=true']),
        value_type=str
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gazebo_share, 'launch', 'gazebo.launch.py')
        ),
        launch_arguments={
            'world': LaunchConfiguration('world'),
            'gui': LaunchConfiguration('gui')
        }.items()
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': True
        }]
    )

    spawn_robot = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        output='screen',
        arguments=[
            '-topic', 'robot_description',
            '-entity', 'amr_robot',
            '-x', LaunchConfiguration('x'),
            '-y', LaunchConfiguration('y'),
            '-z', '0.0325',
            '-Y', LaunchConfiguration('yaw')
        ]
    )

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        output='screen',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': True}],
        condition=IfCondition(LaunchConfiguration('rviz'))
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'world',
            default_value=default_world,
            description='Đường dẫn tới Gazebo world'
        ),
        DeclareLaunchArgument(
            'gui',
            default_value='true',
            description='Hiển thị giao diện Gazebo'
        ),
        DeclareLaunchArgument(
            'rviz',
            default_value='true',
            description='Khởi động RViz với fixed frame odom'
        ),
        DeclareLaunchArgument('x', default_value='0.0'),
        DeclareLaunchArgument('y', default_value='0.0'),
        DeclareLaunchArgument('yaw', default_value='0.0'),
        robot_state_publisher,
        gazebo,
        spawn_robot,
        rviz
    ])
