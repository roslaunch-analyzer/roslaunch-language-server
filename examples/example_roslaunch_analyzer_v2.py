import json

from roslaunch_analyzer_v2 import launch_command

tree = launch_command.parse("ros2 launch examples_rclcpp_minimal publisher.launch.py")

tree.visit()

print(json.dumps(tree))
