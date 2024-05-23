import json

from roslaunch_analyzer import analyse_launch_structure

import re


pattern1 = re.compile(r"\s*^ros2\s+launch\s+(?P<package_name>\w*)\s+(?P<launch_file_name>[a-zA-Z0-9_.\-]*)(\s+\w*\:\=\w*)")

# launch_command = "ros2 launch autoware_launch autoware.launch.xml map_path:=$HOME/autoware_map/sample-map-planning/ vehicle_model:=sample_vehicle"
launch_command = "ros2 launch autoware_launch logging_simulator.launch.xml map_path:=HOME/workspace/training/2f_map vehicle_model:=logiee_st_c sensor_model:=logiee_st_c_sensor localization:=false perception:=true planning:=false control:=false vehicle:=false sensing:=false rviz:=false"

match = re.match(pattern1, launch_command)

if match:
    print("Matched")
    print(match.groups())
else:
    print("Not matched")

# serializable_tree = analyse_launch_structure(launch_command)

# print(json.dumps(serializable_tree, indent=2))
