import os
from typing import Text

from launch import LaunchContext
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import AnyLaunchDescriptionSource
from ros2launch.api.api import get_share_file_path_from_package, parse_launch_arguments

from .tree import IncludeLaunchDescriptionNode


def command2tree(launch_command: Text) -> IncludeLaunchDescriptionNode:

    argv = launch_command.replace("ros2 launch ", "").split(" ")

    if os.path.isfile(argv[0]):
        launch_file_path = argv[0]
        launch_file_arguments = parse_launch_arguments(argv[1:])
    else:
        package_name = argv[0]
        launch_file_name = argv[1]

        launch_file_path = get_share_file_path_from_package(
            package_name=package_name, file_name=launch_file_name
        )
        launch_file_arguments = parse_launch_arguments(argv[2:])

    entity = IncludeLaunchDescription(
        AnyLaunchDescriptionSource(launch_file_path),
        launch_arguments=launch_file_arguments,
    )

    context = LaunchContext(argv=launch_file_arguments)

    return IncludeLaunchDescriptionNode(entity=entity, context=context)
