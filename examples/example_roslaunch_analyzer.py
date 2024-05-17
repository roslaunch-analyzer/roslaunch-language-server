import json

from roslaunch_analyzer import analyse_launch_structure

launch_command = "ros2 launch autoware_launch planning_simulator.launch.xml"

serializable_tree = analyse_launch_structure(launch_command)

print(json.dumps(serializable_tree, indent=2))
