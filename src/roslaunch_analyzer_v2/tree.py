import itertools
from typing import Any, Dict, List, Optional

from launch import LaunchContext, LaunchDescription, LaunchDescriptionEntity
from launch.actions import (
    DeclareLaunchArgument,
    GroupAction,
    IncludeLaunchDescription,
    OpaqueFunction,
    PopEnvironment,
    PopLaunchConfigurations,
    PushEnvironment,
    PushLaunchConfigurations,
    SetLaunchConfiguration,
)
from launch.utilities import normalize_to_list_of_substitutions, perform_substitutions
from launch_ros.actions import (
    ComposableNodeContainer,
    LoadComposableNodes,
    Node,
    PushRosNamespace,
    SetParameter,
    SetRemap,
)
from launch_ros.descriptions import ComposableNode

from .parameter import serialize_parameters
from .utils import find_linked_path, specify_package_from_launch_file_path


class LaunchTreeNodeRegistry:
    """
    Registry for mapping launch actions to their corresponding tree node classes.
    """

    __tree_nodes: Dict[type, Any] = {}

    @classmethod
    def register(cls, action_cls=None):
        """
        Decorator to register a tree node class for a specific launch action.

        Args:
            action_cls: The launch action class to register.
        """

        def decorator(node_cls):
            cls.__tree_nodes[action_cls] = node_cls
            return node_cls

        return decorator

    @classmethod
    def get_node(cls, entity, context):
        """
        Get the registered tree node for a given entity.

        Args:
            entity: The launch entity.
            context: The launch context.

        Returns:
            The corresponding tree node or None if not registered.
        """
        node_cls = cls.__tree_nodes.get(type(entity))
        return node_cls(entity, context) if node_cls else None


def _to_string(context, substitutions):
    """
    Convert substitutions to their string representation.

    Args:
        context: The launch context.
        substitutions: The substitutions to perform.

    Returns:
        The string representation of the substitutions.
    """
    if substitutions is None:
        substitutions = ""
    return perform_substitutions(
        context, normalize_to_list_of_substitutions(substitutions)
    )


class LaunchTreeNode:
    """
    Base class for representing a node in the launch description tree.
    """

    entity: LaunchDescriptionEntity

    def __init__(self, entity: LaunchDescriptionEntity, context: LaunchContext):
        self.entity = entity
        self.context = context
        self.children = []

    def _make_children(self, sub_entities: Optional[List[LaunchDescriptionEntity]]):
        """
        Create child nodes for the given sub-entities.

        Args:
            sub_entities: The list of sub-entities.

        Returns:
            A list of child nodes.
        """
        if sub_entities is None:
            return []

        return [
            child.build()
            for entity in sub_entities
            if (child := LaunchTreeNodeRegistry.get_node(entity, self.context))
        ]

    def build(self):
        """
        Build the tree node and its children by visiting the entity.

        Returns:
            The built tree node.
        """
        try:
            sub_entities = self.entity.visit(self.context)
        except Exception as e:
            print(f"Error in {self.entity.__class__}: {e}")
            return
        self.children = self._make_children(sub_entities)
        return self

    def _serialize_children(self):
        """
        Serialize the child nodes.

        Returns:
            A list of serialized child nodes.
        """
        return list(
            itertools.chain.from_iterable(child._serialize() for child in self.children)
        )

    def _serialize(self):
        """
        Serialize the node.

        Returns:
            A serialized representation of the node.
        """
        raise NotImplementedError()

    def serialize(self):
        """
        Serialize the node and return the first element of the serialized result.

        Returns:
            The first element of the serialized result.
        """
        return self._serialize()[0]


class IgnoredNode(LaunchTreeNode):
    """
    Node that is ignored in the serialization process.
    """

    def _serialize(self):
        return []


class SplicedNode(LaunchTreeNode):
    """
    Node that splices its children directly into the serialized output.
    """

    def _serialize(self):
        return self._serialize_children()


@LaunchTreeNodeRegistry.register(action_cls=LaunchDescription)
class LaunchDescriptionNode(SplicedNode):
    """Node representing a LaunchDescription."""

    pass


@LaunchTreeNodeRegistry.register(action_cls=DeclareLaunchArgument)
class DeclareLaunchArgumentNode(IgnoredNode):
    """Node representing a DeclareLaunchArgument."""

    pass


@LaunchTreeNodeRegistry.register(action_cls=PopEnvironment)
class PopEnvironmentNode(IgnoredNode):
    """Node representing a PopEnvironment."""

    pass


@LaunchTreeNodeRegistry.register(action_cls=PopLaunchConfigurations)
class PopLaunchConfigurationsNode(IgnoredNode):
    """Node representing a PopLaunchConfigurations."""

    pass


@LaunchTreeNodeRegistry.register(action_cls=PushEnvironment)
class PushEnvironmentNode(IgnoredNode):
    """Node representing a PushEnvironment."""

    pass


@LaunchTreeNodeRegistry.register(action_cls=PushLaunchConfigurations)
class PushLaunchConfigurationsNode(IgnoredNode):
    """Node representing a PushLaunchConfigurations."""

    pass


@LaunchTreeNodeRegistry.register(action_cls=SetLaunchConfiguration)
class SetLaunchConfigurationNode(IgnoredNode):
    """Node representing a SetLaunchConfiguration."""

    pass


@LaunchTreeNodeRegistry.register(action_cls=OpaqueFunction)
class OpaqueFunctionNode(SplicedNode):
    """Node representing an OpaqueFunction."""

    pass


@LaunchTreeNodeRegistry.register(action_cls=PushRosNamespace)
class PushRosNamespaceNode(IgnoredNode):
    """Node representing a PushRosNamespace."""

    pass


@LaunchTreeNodeRegistry.register(action_cls=SetParameter)
class SetParameterNode(IgnoredNode):
    """Node representing a SetParameter."""

    pass


@LaunchTreeNodeRegistry.register(action_cls=SetRemap)
class SetRemapNode(IgnoredNode):
    """Node representing a SetRemap."""

    pass


@LaunchTreeNodeRegistry.register(action_cls=GroupAction)
class GroupActionNode(LaunchTreeNode):
    """Node representing a GroupAction."""

    entity: GroupAction

    def _serialize(self):
        children = self._serialize_children()
        if not children:
            return []
        return [
            {
                "type": "GroupAction",
                "scoped": self.entity._GroupAction__scoped,
                "forwarding": self.entity._GroupAction__forwarding,
                "children": children,
            }
        ]


@LaunchTreeNodeRegistry.register(action_cls=IncludeLaunchDescription)
class IncludeLaunchDescriptionNode(LaunchTreeNode):
    """Node representing an IncludeLaunchDescription."""

    entity: IncludeLaunchDescription

    def _serialize(self):
        return [
            {
                "type": "IncludeLaunchDescription",
                "path": find_linked_path(self.entity._get_launch_file()),
                "package": specify_package_from_launch_file_path(
                    self.entity._get_launch_file()
                ),
                "children": self._serialize_children(),
            }
        ]


@LaunchTreeNodeRegistry.register(action_cls=Node)
class NodeNode(LaunchTreeNode):
    """Node representing a Node."""

    entity: Node

    def _serialize(self):
        return [
            {
                "type": "Node",
                "package": _to_string(self.context, self.entity.node_package),
                "executable": _to_string(self.context, self.entity.node_executable),
                "name": _to_string(self.context, self.entity.node_name),
                "namespace": _to_string(
                    self.context, self.entity.expanded_node_namespace
                ),
                "parameters": serialize_parameters(self.entity._Node__parameters),
                "children": self._serialize_children(),
            }
        ]


@LaunchTreeNodeRegistry.register(action_cls=ComposableNodeContainer)
class ComposableNodeContainerNode(LaunchTreeNode):
    """Node representing a ComposableNodeContainer."""

    entity: ComposableNodeContainer

    def _serialize(self):
        return [
            {
                "type": "ComposableNodeContainer",
                "package": _to_string(self.context, self.entity.node_package),
                "executable": _to_string(self.context, self.entity.node_executable),
                "name": _to_string(self.context, self.entity.node_name),
                "namespace": _to_string(
                    self.context, self.entity.expanded_node_namespace
                ),
                "parameters": serialize_parameters(self.entity._Node__parameters),
                "children": self._serialize_children(),
            }
        ]


@LaunchTreeNodeRegistry.register(action_cls=LoadComposableNodes)
class LoadComposableNodesNode(LaunchTreeNode):
    """Node representing a LoadComposableNodes."""

    entity: LoadComposableNodes

    def __serialize_composable_node(self, entity: ComposableNode):
        """
        Serialize a ComposableNode entity.

        Args:
            entity: The ComposableNode entity.

        Returns:
            A serialized representation of the ComposableNode.
        """
        return {
            "package": _to_string(self.context, entity.package),
            "plugin": _to_string(self.context, entity.node_plugin),
            "namespace": _to_string(self.context, entity.node_namespace),
            "name": _to_string(self.context, entity.node_name),
            "parameters": serialize_parameters(entity._ComposableNode__parameters),
        }

    def _serialize(self):
        return [
            {
                "type": "LoadComposableNodes",
                "target_container": self.entity._LoadComposableNodes__final_target_container_name,
                "loaded_nodes": [
                    self.__serialize_composable_node(entity)
                    for entity in self.entity._LoadComposableNodes__composable_node_descriptions
                ],
            }
        ]
