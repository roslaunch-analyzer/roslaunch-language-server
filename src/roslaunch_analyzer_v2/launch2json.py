import os
from dataclasses import dataclass
from typing import List, Text, Tuple

from launch import LaunchService
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import AnyLaunchDescriptionSource
from rclpy.logging import get_logger

# import launchcmd
from ros2launch.api.api import get_share_file_path_from_package, parse_launch_arguments

from roslaunch_analyzer.filter import filter_entity_tree
from roslaunch_analyzer.parser import create_entity_tree
from roslaunch_analyzer.serialization import make_entity_tree_serializable

logger = get_logger("launch2json")


@dataclass
class LaunchCommandInfo:
    launch_file_path: Text
    launch_arguments: List[Tuple[Text, Text]]

    @classmethod
    def from_command(cls, launch_command: Text):
        argv = launch_command.replace("ros2 launch ", "").split(" ")

        if os.path.isfile(argv[0]):  # If the first argument is a file path
            launch_file_path = argv[0]
            return cls(
                launch_file_path=launch_file_path,
                launch_arguments=parse_launch_arguments(argv[1:]),
            )
        else:  # If the first argument is a package name
            package_name = argv[0]
            launch_file_name = argv[1]
            launch_arguments = parse_launch_arguments(argv[2:])

            return cls(
                launch_file_path=get_share_file_path_from_package(
                    package_name=package_name, file_name=launch_file_name
                ),
                launch_arguments=launch_arguments,
            )


def get_entity_and_launch_service(launch_info: LaunchCommandInfo):
    root_entity = IncludeLaunchDescription(
        AnyLaunchDescriptionSource(launch_info.launch_file_path),
        launch_arguments=launch_info.launch_arguments,
    )

    launch_service = LaunchService(argv=launch_info.launch_arguments)

    return root_entity, launch_service


def analyse_launch_structure(launch_command: Text):
    launch_info = LaunchCommandInfo.from_command(launch_command)
    root_entity, launch_service = get_entity_and_launch_service(launch_info)
    raw_tree = create_entity_tree(root_entity, launch_service)
    filtered_tree = filter_entity_tree(raw_tree.copy())
    serializable_tree = make_entity_tree_serializable(
        filtered_tree, launch_service.context
    )
    return serializable_tree


if __name__ == "__main__":
    import json

    launch_command = "ros2 launch autoware_launch planning_simulator.launch.xml"
    serializable_tree = analyse_launch_structure(launch_command)
    print(json.dumps(serializable_tree, indent=1))
