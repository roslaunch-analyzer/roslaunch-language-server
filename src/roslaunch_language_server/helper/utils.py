import os
from typing import Optional


def find_symlinks(target_path: str, search_folder: str) -> Optional[str]:
    """
    Search for symbolic links in a given folder that point to the specified target path.

    Parameters:
    target_path (str): The path that the symbolic links should point to.
    search_folder (str): The folder to search for symbolic links.

    Returns:
    Optional[str]: The full path of the first symbolic link found that points to the target path,
                   or None if no such symbolic link is found.
    """
    for root, dirs, files in os.walk(search_folder):
        for name in files + dirs:
            full_path = os.path.join(root, name)
            if os.path.islink(full_path):  # Check if the path is a symbolic link
                if (
                    os.readlink(full_path) == target_path
                ):  # Check if the symbolic link points to the target path
                    return full_path
    return None  # Return None if no matching symbolic link is found
