import os
import pathlib
from typing import Optional

import launch
import launch_ros
from launch.substitutions import LaunchConfiguration
from launch_ros.parameter_descriptions import ParameterFile as ParameterFileDescription
from launch_ros.parameters_type import (
    ParameterDescription,
    ParameterFile,
    Parameters,
    ParameterValue,
    Substitution,
)


def find_linked_path(path: str) -> str:
    """Find the linked path of a given path. If the path is not a link, return the path itself."""
    if os.path.islink(path):
        linked_path = os.readlink(path)
        return find_linked_path(linked_path)
    else:
        return path


def serialize_text_substitution(text_substitution: Substitution):
    if isinstance(text_substitution, LaunchConfiguration):
        return "".join(
            [
                serialize_text_substitution(substitution)
                for substitution in text_substitution._LaunchConfiguration__variable_name
            ]
        )
    if isinstance(text_substitution, launch.substitutions.TextSubstitution):
        text: str = text_substitution._TextSubstitution__text
    return text


def handle_parameter_value(value: ParameterValue):
    from launch_ros.parameters_type import (
        ParameterValueDescription,
        Sequence,
        Substitution,
        _SingleValueType,
    )

    if isinstance(value, ParameterValueDescription):
        return value._ParameterValue__evaluated_parameter_value
    if isinstance(value, Sequence):
        if isinstance(value[0], Substitution):
            return "".join(
                [serialize_text_substitution(substitution) for substitution in value]
            )
        else:
            return [handle_parameter_value(sub_value) for sub_value in value]
    if isinstance(value, _SingleValueType):
        return value


def handle_parameter_file(parameter_file: ParameterFile):
    if (
        type(parameter_file) is pathlib.Path
        or isinstance(parameter_file, str)
        or isinstance(parameter_file, os.PathLike)
    ):
        string_path = find_linked_path(str(parameter_file))
        return string_path
    if type(parameter_file) is ParameterFileDescription:
        return handle_parameter_file(parameter_file.param_file)
    return "".join(
        [serialize_text_substitution(substitution) for substitution in parameter_file]
    )


def serialize_parameters(parameters: Optional[Parameters]):
    if parameters is None:
        return {}
    output_dictionary = dict()
    for parameter in parameters:
        if type(parameter) is ParameterFile:
            parameter_list = output_dictionary.get("__param_files", [])
            parameter_list.append(handle_parameter_file(parameter))
            output_dictionary["__param_files"] = parameter_list
        if type(parameter) is ParameterDescription:
            continue
        if type(parameter) is dict:
            for key in parameter.keys():
                # key: ParameterName = Sequence[Substitution]
                key_name = serialize_text_substitution(key[0])
                value: ParameterValue = parameter[key]
                serialized_value = handle_parameter_value(value)
                output_dictionary[key_name] = serialized_value

    return output_dictionary


def _make_entity_serializable(entity: launch.LaunchDescriptionEntity):
    import re

    d = {}
    d["type"] = entity.__class__.__name__
    if type(entity) is launch.actions.IncludeLaunchDescription:
        d["package"] = re.search(
            r"install/([^/]+)/share/\1", entity._get_launch_file()
        ).group(1)
        d["file_name"] = entity._get_launch_file().split("/")[-1]
        d["full_path"] = find_linked_path(entity._get_launch_file())

    if type(entity) is launch.actions.GroupAction:
        d["scoped"] = entity._GroupAction__scoped
        d["forwarding"] = entity._GroupAction__forwarding

    if type(entity) is launch_ros.actions.ComposableNodeContainer:
        d["package"] = entity.node_package
        d["executable"] = entity.node_executable
        d["namespace"] = entity._Node__expanded_node_namespace.replace(
            launch_ros.actions.Node.UNSPECIFIED_NODE_NAMESPACE, "/"
        )
        d["name"] = entity._Node__expanded_node_name
        d["parameters"] = serialize_parameters(entity._Node__parameters)
        d["remappings"] = entity._Node__expanded_remappings

    if type(entity) is launch_ros.actions.LoadComposableNodes:
        d["target_container"] = entity._LoadComposableNodes__final_target_container_name

    if type(entity) is launch_ros.descriptions.ComposableNode:
        d["package"] = entity.package
        d["plugin"] = entity.node_plugin
        d["namespace"] = entity.node_namespace
        d["name"] = entity.node_name
        d["parameters"] = serialize_parameters(entity._ComposableNode__parameters)

    if type(entity) is launch_ros.actions.Node:
        d["package"] = entity.node_package
        d["executable"] = entity.node_executable
        d["namespace"] = entity._Node__expanded_node_namespace.replace(
            launch_ros.actions.Node.UNSPECIFIED_NODE_NAMESPACE, "/"
        )
        d["name"] = entity._Node__expanded_node_name
        d["parameters"] = serialize_parameters(entity._Node__parameters)

    if isinstance(entity, launch.actions.OpaqueFunction):
        d["name"] = entity.name

    return d


def make_entity_tree_serializable(tree: dict | object, context: launch.LaunchContext):
    if not isinstance(tree, dict):
        return _make_entity_serializable(tree)

    d = {}
    d["entity"] = _make_entity_serializable(tree["entity"])
    if isinstance(tree["children"], list):
        d["children"] = [
            make_entity_tree_serializable(child, context) for child in tree["children"]
        ]

    return d
