import json

from roslaunch_analyzer import analyse_launch_structure

launch_command = "ros2 launch autoware_launch autoware.launch.xml map_path:=$HOME/autoware_map/sample-map-planning/ vehicle_model:=sample_"

serializable_tree = analyse_launch_structure(launch_command)

# print(json.dumps(serializable_tree, indent=2))
