from roslaunch_analyzer_v2.command import command2tree

tree = command2tree(
    "ros2 launch autoware_launch planning_simulator.launch.xml "
    "map_path:=$HOME/autoware_map/sample-map-planning/ "
    "vehicle_model:=sample_vehicle"
)

tree.build()
