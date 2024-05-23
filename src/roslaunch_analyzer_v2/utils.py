import os


def find_linked_path(path: str) -> str:
    """Find the linked path of a given path. If the path is not a link, return the path itself."""
    if os.path.islink(path):
        linked_path = os.readlink(path)
        return find_linked_path(linked_path)
    else:
        return path
