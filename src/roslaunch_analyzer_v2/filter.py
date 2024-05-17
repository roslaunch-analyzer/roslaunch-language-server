import launch
import launch_ros
from rclpy.logging import get_logger

logger = get_logger("launch2json")

container_classes = (
    launch.actions.GroupAction,
    launch.actions.IncludeLaunchDescription,
    launch.actions.OpaqueFunction,
    launch.LaunchDescription,
)

ignore_container_classes = (
    launch.actions.OpaqueFunction,
    launch.LaunchDescription,
)

ignore_classes = (
    launch_ros.actions.PushRosNamespace,
    launch_ros.actions.SetParameter,
    launch_ros.actions.SetRemap,
    launch.actions.DeclareLaunchArgument,
    launch.actions.PopEnvironment,
    launch.actions.PopLaunchConfigurations,
    launch.actions.PushEnvironment,
    launch.actions.PushLaunchConfigurations,
    launch.actions.SetLaunchConfiguration,
)

SubtreeType = (
    dict
    | list
    | launch.LaunchDescriptionEntity
    | launch_ros.descriptions.ComposableNode
)


def _process_tree(tree: SubtreeType, func):
    if isinstance(tree, dict):
        tree["children"] = _process_tree(tree["children"], func)
        return func(tree)
    elif isinstance(tree, list):
        return [filtered for e in tree if (filtered := _process_tree(e, func))]
    else:
        return func(tree)


def _remove_invalid_nodes(tree: SubtreeType):
    if isinstance(tree, launch.LaunchDescriptionEntity):
        if isinstance(tree, ignore_classes) or isinstance(tree, container_classes):
            return None
    return tree


def _remove_unnecessary_containers(tree: SubtreeType):
    if isinstance(tree, dict):
        extend_items = []
        remove_items = []

        for child in tree["children"]:
            if isinstance(child, dict) and isinstance(
                child["entity"], ignore_container_classes
            ):
                extend_items.extend(child["children"])
                remove_items.append(child)

        tree["children"].extend(extend_items)
        for remove_item in remove_items:
            tree["children"].remove(remove_item)

    return tree


def _remove_empty_containers(tree: SubtreeType):
    if isinstance(tree, dict):
        if isinstance(tree["entity"], container_classes) and not tree["children"]:
            return None
    return tree


def filter_entity_tree(tree: dict):
    tree = _process_tree(tree.copy(), _remove_invalid_nodes)
    tree = _process_tree(tree.copy(), _remove_unnecessary_containers)
    tree = _process_tree(tree.copy(), _remove_empty_containers)
    # tree = remove_one_member_group(tree.copy()) # TODO
    return tree
