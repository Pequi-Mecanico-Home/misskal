from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction
from launch.conditions import UnlessCondition
from launch.substitutions import Command, FindExecutable, PathJoinSubstitution, LaunchConfiguration
from launch_ros.actions import Node, PushRosNamespace
from launch_ros.substitutions import FindPackageShare
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():

    # Configs
    config_jackal_ekf = PathJoinSubstitution(
        [FindPackageShare('jackal_control'),
         'config',
         'localization.yaml'],
    )

    config_imu_filter = PathJoinSubstitution(
        [FindPackageShare('jackal_control'),
         'config',
         'imu_filter.yaml'],
    )

    config_jackal_velocity_controller = PathJoinSubstitution(
        [FindPackageShare('jackal_control'),
        'config',
        'control.yaml'],
    )

    # Launch Arguments

    robot_description_command_arg = DeclareLaunchArgument(
        'robot_description_command',
        default_value=[
            PathJoinSubstitution([FindExecutable(name='xacro')]),
            ' ',
            PathJoinSubstitution(
                [FindPackageShare('jackal_description'), 'urdf', 'jackal.urdf.xacro']
            )
        ]
    )

    is_sim = LaunchConfiguration('is_sim', default=False)

    is_sim_arg = DeclareLaunchArgument(
        'is_sim',
        default_value=is_sim)


    # Localization
    localization_group_action = GroupAction([
        PushRosNamespace(
                    namespace='misskal'),

        # Extended Kalman Filter
        Node(
            package='robot_localization',
            executable='ekf_node',
            name='ekf_node',
            output='screen',
            parameters=[config_jackal_ekf, {'use_sim_time': True if is_sim else False}],
        ),

        # Madgwick Filter
        Node(
            package='imu_filter_madgwick',
            executable='imu_filter_madgwick_node',
            name='imu_filter_node',
            output='screen',
            parameters=[config_imu_filter]
        )
    ])

    # ROS2 Controllers
    control_group_action = GroupAction([
        # ROS2 Control
        Node(
            namespace='misskal',
            package='controller_manager',
            executable='ros2_control_node',
            parameters=[config_jackal_velocity_controller, {'use_sim_time': True if is_sim else False}],
            output={
                'stdout': 'screen',
                'stderr': 'screen',
            },
            remappings=[
            ("~/robot_description", "robot_description")],
            condition=UnlessCondition(is_sim)
        ),

        # Joint State Broadcaster
        Node(
            namespace='misskal',
            package='controller_manager',
            executable='spawner',
            arguments=['joint_state_broadcaster', '--controller-manager-timeout', '300'],
            output='screen',
        ),

        # Velocity Controller
        Node(
            namespace='misskal',
            package='controller_manager',
            executable='spawner',
            arguments=['jackal_velocity_controller', '--controller-manager-timeout', '300'],
            output='screen',
        )
    ])

    ld = LaunchDescription()
    ld.add_action(robot_description_command_arg)
    ld.add_action(is_sim_arg)
    ld.add_action(localization_group_action)
    ld.add_action(control_group_action)
    return ld
