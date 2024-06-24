import dataclasses
import os
import re
from typing import Dict, Text

from launch import LaunchContext
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import AnyLaunchDescriptionSource
from ros2launch.api.api import get_share_file_path_from_package, parse_launch_arguments

from .tree import IncludeLaunchDescriptionNode


@dataclasses.dataclass
class LaunchCommand:
    """
    Data class to store the launch command details.

    Attributes:
        path (Text): The path to the launch file.
        arguments (Dict[Text, Text]): The launch arguments as key-value pairs.
    """

    path: Text
    arguments: Dict[Text, Text]


def parse_command_line(launch_command_line: Text) -> LaunchCommand:
    """
    Parse the command line to extract the launch command details.

    Args:
        launch_command_line (Text): The full command line string.

    Returns:
        LaunchCommand: An instance of LaunchCommand containing the parsed path and arguments.
    """
    command_line_body = re.sub(r"^ros2\s+launch\s+", "", launch_command_line)
    args = command_line_body.split()
    if os.path.isfile(args[0]):
        return LaunchCommand(path=args[0], arguments=parse_launch_arguments(args[1:]))
    else:
        package_name = args[0]
        launch_file_name = args[1]
        launch_file_path = get_share_file_path_from_package(
            package_name=package_name, file_name=launch_file_name
        )
        return LaunchCommand(
            path=launch_file_path, arguments=parse_launch_arguments(args[2:])
        )


def command_to_tree(command: LaunchCommand) -> IncludeLaunchDescriptionNode:
    """
    Convert a LaunchCommand to an IncludeLaunchDescriptionNode.

    Args:
        command (LaunchCommand): The launch command to convert.

    Returns:
        IncludeLaunchDescriptionNode: The corresponding IncludeLaunchDescriptionNode.
    """
    entity = IncludeLaunchDescription(
        AnyLaunchDescriptionSource(command.path),
        launch_arguments=command.arguments,
    )

    context = LaunchContext(argv=command.arguments)

    return IncludeLaunchDescriptionNode(entity=entity, context=context)
