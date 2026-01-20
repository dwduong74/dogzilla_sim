import os

import launch_ros
from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    IncludeLaunchDescription,
    SetEnvironmentVariable,
    RegisterEventHandler,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch.event_handlers import OnProcessExit


def generate_launch_description():

    use_sim_time = LaunchConfiguration("use_sim_time")
    description_path = LaunchConfiguration("description_path")
    robot_name = LaunchConfiguration("robot_name")

    config_pkg_share = launch_ros.substitutions.FindPackageShare(
        package="dogzilla_config"
    ).find("dogzilla_config")
    descr_pkg_share = launch_ros.substitutions.FindPackageShare(
        package="dogzilla_description"
    ).find("dogzilla_description")

    joints_config = os.path.join(config_pkg_share, "config/joints/joints.yaml")
    ros_control_config = os.path.join(
        config_pkg_share, "config/ros_control/ros_control.yaml"
    )
    gait_config = os.path.join(config_pkg_share, "config/gait/gait.yaml")
    links_config = os.path.join(config_pkg_share, "config/links/links.yaml")
    default_model_path = os.path.join(descr_pkg_share, "xacro/dogzilla.xacro")

    # Use SDF world file for Ignition Fortress
    default_world_path = os.path.join(config_pkg_share, "worlds/default.sdf")

    declare_use_sim_time = DeclareLaunchArgument(
        "use_sim_time",
        default_value="true",
        description="Use simulation (Gazebo) clock if true",
    )
    declare_rviz = DeclareLaunchArgument(
        "rviz", default_value="false", description="Launch rviz"
    )
    declare_robot_name = DeclareLaunchArgument(
        "robot_name", default_value="dogzilla", description="Robot name"
    )
    declare_lite = DeclareLaunchArgument(
        "lite", default_value="false", description="Lite"
    )
    declare_ros_control_file = DeclareLaunchArgument(
        "ros_control_file",
        default_value=ros_control_config,
        description="Ros control config path",
    )
    declare_gazebo_world = DeclareLaunchArgument(
        "world", default_value=default_world_path, description="Gazebo world name"
    )

    declare_gui = DeclareLaunchArgument(
        "gui", default_value="true", description="Use gui"
    )
    declare_world_init_x = DeclareLaunchArgument("world_init_x", default_value="0.0")
    declare_world_init_y = DeclareLaunchArgument("world_init_y", default_value="0.0")
    declare_world_init_z = DeclareLaunchArgument("world_init_z", default_value="0.15")
    declare_world_init_heading = DeclareLaunchArgument(
        "world_init_heading", default_value="0.0"
    )

    # Set Gazebo system plugin path for ros2_control
    gz_plugin_path = SetEnvironmentVariable(
        name='GZ_SIM_SYSTEM_PLUGIN_PATH',
        value='/opt/ros/humble/lib'
    )

    # Set Ignition resource path for models
    ign_resource_path = SetEnvironmentVariable(
        name='IGN_GAZEBO_RESOURCE_PATH',
        value=[
            os.path.join(config_pkg_share, 'worlds'), ':',
            '/usr/share/ignition/ignition-gazebo6/worlds'
        ]
    )

    # Launch Champ Bringup (Robot State Publisher, Joint State Publisher, etc.)
    bringup_ld = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("champ_bringup"),
                "launch",
                "bringup.launch.py",
            )
        ),
        launch_arguments={
            "description_path": default_model_path,
            "joints_map_path": joints_config,
            "links_map_path": links_config,
            "gait_config_path": gait_config,
            "use_sim_time": LaunchConfiguration("use_sim_time"),
            "robot_name": LaunchConfiguration("robot_name"),
            "gazebo": "true",
            "lite": LaunchConfiguration("lite"),
            "rviz": LaunchConfiguration("rviz"),
            "joint_controller_topic": "joint_group_effort_controller/joint_trajectory",
            "hardware_connected": "false",
            "publish_foot_contacts": "false",
            "close_loop_odom": "true",
        }.items(),
    )

    # Start Ignition Gazebo
    start_ignition_cmd = ExecuteProcess(
        cmd=['ign', 'gazebo', '-r', LaunchConfiguration("world")],
        output='screen',
    )

    # Spawn Robot in Ignition
    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', robot_name,
            '-allow_renaming', 'true',
            '-topic', '/robot_description',
            '-x', LaunchConfiguration("world_init_x"),
            '-y', LaunchConfiguration("world_init_y"),
            '-z', LaunchConfiguration("world_init_z"),
            '-Y', LaunchConfiguration("world_init_heading"),
        ],
        output='screen',
    )

    # ROS GZ Bridges
    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=['/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock'],
        output='screen',
    )

    # Load Joint Group Effort Controller
    load_joint_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_group_effort_controller", "--controller-manager", "/controller_manager"],
        output="screen",
    )

    # Load Joint State Broadcaster
    load_joint_state_broadcaster = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_states_controller", "--controller-manager", "/controller_manager"],
        output="screen",
    )

    return LaunchDescription(
        [
            gz_plugin_path,
            ign_resource_path,
            declare_use_sim_time,
            declare_rviz,
            declare_robot_name,
            declare_lite,
            declare_ros_control_file,
            declare_gazebo_world,
            declare_gui,
            declare_world_init_x,
            declare_world_init_y,
            declare_world_init_z,
            declare_world_init_heading,

            start_ignition_cmd,
            bringup_ld,
            spawn_robot,
            clock_bridge,

            RegisterEventHandler(
                event_handler=OnProcessExit(
                    target_action=spawn_robot,
                    on_exit=[load_joint_state_broadcaster],
                )
            ),
            RegisterEventHandler(
                event_handler=OnProcessExit(
                    target_action=load_joint_state_broadcaster,
                    on_exit=[load_joint_controller],
                )
            ),
        ]
    )
