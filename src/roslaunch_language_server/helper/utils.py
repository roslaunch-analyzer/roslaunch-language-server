import os


def find_symlinks(target_path, search_folder):
    for root, dirs, files in os.walk(search_folder):
        for name in files + dirs:
            full_path = os.path.join(root, name)
            if os.path.islink(full_path):
                if os.readlink(full_path) == target_path:
                    return full_path
    return target_path
