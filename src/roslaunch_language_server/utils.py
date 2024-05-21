import os

from ament_index_python.packages import get_packages_with_prefixes

all_ros_packages = list(get_packages_with_prefixes().keys())

all_env_vars = list(os.environ.keys())
