import json
import os

from roslaunch_analyzer import command_to_tree, parse_command_line

command = parse_command_line(
    "ros2  launch   autoware_launch autoware.launch.xml  "
    "  map_path:=$HOME/autoware_map/sample-map-planning/"
)

tree = command_to_tree(command)

tree.build()

os.makedirs("log", exist_ok=True)

with open("log/example_roslaunch_analyzer.json", "w") as f:
    f.write(json.dumps(tree._serialize(), indent=2))
