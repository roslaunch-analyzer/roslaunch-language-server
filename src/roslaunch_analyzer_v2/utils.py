import os
import re
from typing import Optional


def find_linked_path(path: str) -> str:
    if os.path.islink(path):
        linked_path = os.readlink(path)
        return find_linked_path(linked_path)
    else:
        return path


def specify_package_from_launch_file_path(launch_file_path: str) -> Optional[str]:
    match = re.search(
        r"install/(?P<package_name>[^/]+)/share/(?P=package_name)",
        launch_file_path,
    )

    return match.group("package_name") if match else None
