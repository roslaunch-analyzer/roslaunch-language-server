import json
import os
from roslaunch_analyzer import get_arguments_of_launch_file, parse_command_line


command = parse_command_line(
    "ros2 launch autoware_launch autoware.launch.xml"
)

arguments = get_arguments_of_launch_file(command.path)

os.makedirs("log", exist_ok=True)

with open("log/example_get_arguments_of_launch_file.json", "w") as f:
    f.write(json.dumps(arguments, indent=2))
