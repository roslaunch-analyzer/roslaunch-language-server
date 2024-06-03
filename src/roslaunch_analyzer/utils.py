import os
import re
from typing import Optional


def resolve_symlink(path: str) -> str:
    """
    Recursively resolve the target of a symbolic link.

    Args:
        path: The path to resolve.

    Returns:
        The resolved path.
    """
    if os.path.islink(path):
        linked_path = os.readlink(path)
        return resolve_symlink(linked_path)
    return path


def extract_package_name(launch_file_path: str) -> Optional[str]:
    """
    Extract the package name from the launch file path.

    Args:
        launch_file_path: The path to the launch file.

    Returns:
        The package name if found, otherwise None.
    """
    match = re.search(
        r"install/(?P<package_name>[^/]+)/share/(?P=package_name)",
        launch_file_path,
    )
    return match.group("package_name") if match else None
