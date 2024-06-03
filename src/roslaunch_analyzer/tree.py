import itertools
from typing import Any, Dict, List, Optional

from launch import Action, LaunchContext, LaunchDescription, LaunchDescriptionEntity
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
from .utils import extract_package_name, resolve_symlink


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
    def get_node(cls, entity, context) -> Optional["LaunchTreeNode"]:
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


def to_string(context: LaunchContext, substitutions: Any) -> str:
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
        self.children: List[LaunchTreeNode] = []

    def complete_entity_info(self):
        """
        Complete any additional information required for the entity.
        """
        pass

    def build_children(
        self, sub_entities: Optional[List[LaunchDescriptionEntity]]
    ) -> List["LaunchTreeNode"]:
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
            built_child
            for entity in sub_entities
            if (child := LaunchTreeNodeRegistry.get_node(entity, self.context))
            if (built_child := child.build())
        ]

    def build(self) -> Optional["LaunchTreeNode"]:
        """
        Build the tree node and its children by visiting the entity.

        Returns:
            The built tree node or None if the entity's condition evaluates to False.
        """
        if isinstance(self.entity, Action):
            if (
                self.entity.condition is not None
                and not self.entity.condition.evaluate(self.context)
            ):
                return None

        try:
            sub_entities = self.entity.visit(self.context)
        except Exception as e:
            print(f"Error in {self.entity.__class__}: {e}")
            return None

        self.complete_entity_info()
        self.children = self.build_children(sub_entities)
        return self

    def serialize_children(self) -> List[Dict[str, Any]]:
        """
        Serialize the child nodes.

        Returns:
            A list of serialized child nodes.
        """
        return list(
            itertools.chain.from_iterable(child._serialize() for child in self.children)
        )

    def serialize(self) -> Dict[str, Any]:
        """
        Serialize the node and return the first element of the serialized result.

        Returns:
            The serialized representation of the node.
        """
        return self._serialize()[0]

    def _serialize(self) -> List[Dict[str, Any]]:
        """
        Serialize the node.

        Returns:
            A serialized representation of the node.
        """
        raise NotImplementedError()


class IgnoredNode(LaunchTreeNode):
    """
    Node that is ignored in the serialization process.
    """

    def _serialize(self) -> List[Dict[str, Any]]:
        return []


class SplicedNode(LaunchTreeNode):
    """
    Node that splices its children directly into the serialized output.
    """

    def _serialize(self) -> List[Dict[str, Any]]:
        return self.serialize_children()


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

    def complete_entity_info(self):
        """
        Complete any additional information required for the entity.
        """
        self.scoped: bool = self.entity._GroupAction__scoped
        self.forwarding: bool = self.entity._GroupAction__forwarding

    def _serialize(self) -> List[Dict[str, Any]]:
        children = self.serialize_children()
        if not children:
            return []
        return [
            {
                "type": "GroupAction",
                "scoped": self.scoped,
                "forwarding": self.forwarding,
                "children": children,
            }
        ]


@LaunchTreeNodeRegistry.register(action_cls=IncludeLaunchDescription)
class IncludeLaunchDescriptionNode(LaunchTreeNode):
    """Node representing an IncludeLaunchDescription."""

    entity: IncludeLaunchDescription

    def complete_entity_info(self):
        """
        Complete any additional information required for the entity.
        """
        self.package: Optional[str] = extract_package_name(
            self.entity._get_launch_file()
        )
        self.path: str = resolve_symlink(self.entity._get_launch_file())

    def _serialize(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "IncludeLaunchDescription",
                "path": self.path,
                "package": self.package,
                "children": self.serialize_children(),
            }
        ]


@LaunchTreeNodeRegistry.register(action_cls=Node)
class NodeNode(LaunchTreeNode):
    """Node representing a Node."""

    entity: Node

    def complete_entity_info(self):
        """
        Complete any additional information required for the entity.
        """
        self.package: str = to_string(self.context, self.entity.node_package)
        self.executable: str = to_string(self.context, self.entity.node_executable)
        self.namespace: str = to_string(
            self.context, self.entity.expanded_node_namespace
        )
        self.name: str = to_string(self.context, self.entity.node_name)
        self.parameters = serialize_parameters(self.entity._Node__parameters)

    def _serialize(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "Node",
                "package": self.package,
                "executable": self.executable,
                "name": self.name,
                "namespace": self.namespace,
                "parameters": self.parameters,
                "children": self.serialize_children(),
            }
        ]


@LaunchTreeNodeRegistry.register(action_cls=ComposableNodeContainer)
class ComposableNodeContainerNode(LaunchTreeNode):
    """Node representing a ComposableNodeContainer."""

    entity: ComposableNodeContainer

    def complete_entity_info(self):
        """
        Complete any additional information required for the entity.
        """
        self.package: str = to_string(self.context, self.entity.node_package)
        self.executable: str = to_string(self.context, self.entity.node_executable)
        self.namespace: str = to_string(
            self.context, self.entity.expanded_node_namespace
        )
        self.name: str = to_string(self.context, self.entity.node_name)
        self.parameters = serialize_parameters(self.entity._Node__parameters)

    def _serialize(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "ComposableNodeContainer",
                "package": self.package,
                "executable": self.executable,
                "name": self.name,
                "namespace": self.namespace,
                "parameters": self.parameters,
                "children": self.serialize_children(),
            }
        ]


@LaunchTreeNodeRegistry.register(action_cls=LoadComposableNodes)
class LoadComposableNodesNode(LaunchTreeNode):
    """Node representing a LoadComposableNodes."""

    entity: LoadComposableNodes

    def serialize_composable_node(self, entity: ComposableNode) -> Dict[str, Any]:
        """
        Serialize a ComposableNode entity.

        Args:
            entity: The ComposableNode entity.

        Returns:
            A serialized representation of the ComposableNode.
        """
        return {
            "package": to_string(self.context, entity.package),
            "plugin": to_string(self.context, entity.node_plugin),
            "namespace": to_string(self.context, entity.node_namespace),
            "name": to_string(self.context, entity.node_name),
            "parameters": serialize_parameters(entity._ComposableNode__parameters),
        }

    def complete_entity_info(self):
        """
        Complete any additional information required for the entity.
        """
        self.target_container: str = (
            self.entity._LoadComposableNodes__final_target_container_name
        )
        self.loaded_nodes = [
            self.serialize_composable_node(entity)
            for entity in self.entity._LoadComposableNodes__composable_node_descriptions
        ]

    def _serialize(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "LoadComposableNodes",
                "target_container": self.target_container,
                "loaded_nodes": self.loaded_nodes,
            }
        ]
