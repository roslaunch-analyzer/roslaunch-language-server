import asyncio
import itertools

# import json
import logging
from typing import List  # , Text, Tuple

from launch import (  # LaunchContext,; LaunchDescriptionEntity,; Action,
    LaunchDescription,
    LaunchService,
)
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

# from roslaunch_analyzer_v2.utils import find_linked_path

_REGISTERD_LAUNCH_TREE_NODE = {}


def register_entity(tree_node_cls=None, action_cls=None):
    def actual_decorator(cls):
        global _REGISTERD_LAUNCH_TREE_NODE
        _REGISTERD_LAUNCH_TREE_NODE[action_cls] = cls
        return cls

    return actual_decorator


def get_registerd_launch_tree_node(entity, service):
    global _REGISTERD_LAUNCH_TREE_NODE
    if type(entity) not in _REGISTERD_LAUNCH_TREE_NODE:
        return None
    return _REGISTERD_LAUNCH_TREE_NODE[type(entity)](entity, service)


class LaunchTreeNode:

    def __init__(self, entity: IncludeLaunchDescription, service: LaunchService):
        self.entity = entity
        self.service = service
        self.children = []

    def spliced(self):
        yield self

    def _build_preprocess(self):
        self.__loop = asyncio.get_event_loop()
        self.service.context._set_asyncio_loop(self.__loop)

    def _build_postprocess(self):
        tasks = asyncio.all_tasks(self.__loop)
        list(map(lambda task: task.cancel(), tasks))
        logging.root.setLevel(logging.CRITICAL)
        self.__loop.create_task(self.service.run_async())
        self.__loop.run_until_complete(asyncio.sleep(0))
        shutdown_task = self.__loop.create_task(self.service.shutdown())
        self.__loop.run_until_complete(shutdown_task)
        logging.root.setLevel(logging.INFO)

    def build(self, is_root=True):
        if is_root:
            self._build_preprocess()

        try:
            sub_entities = self.entity.visit(self.service.context)
        except Exception as e:
            print(f"error in {self.entity.__class__}: {e}")
            return

        if sub_entities is None:
            return

        global _REGISTERD_LAUNCH_TREE_NODE

        self.children: List[LaunchTreeNode] = [  # children before building
            child
            for entity in sub_entities
            if (child := get_registerd_launch_tree_node(entity, self.service))
        ]

        self.children = [  # children after building
            child for c in self.children if (child := c.build(is_root=False))
        ]

        # splice the children
        self.children = list(
            itertools.chain(*[child.spliced() for child in self.children])
        )

        for child in self.children:
            print(child.__class__.__name__)

        if is_root:
            self._build_postprocess()

        return self


def _to_string(context, substitutions):

    if substitutions is None:
        substitutions = ""

    return perform_substitutions(
        context, normalize_to_list_of_substitutions(substitutions)
    )


class SplicedNode(LaunchTreeNode):
    def spliced(self):
        yield from self.children


class IgnoredIfChildrenIsEmptyNode(LaunchTreeNode):
    def build(self, is_root=True):
        super().build(is_root)
        if len(self.children) == 0:
            return None


class IgnoredNode(LaunchTreeNode):
    def build(self, is_root=True):
        try:
            self.entity.visit(self.service.context)
        except Exception as e:
            print(f"error in {self.entity.__class__}: {e}")
        return None


class ActionNode(LaunchTreeNode):
    def build(self, is_root=True):
        if self.entity.condition is not None and not self.entity.condition.evaluate(
            self.service.context
        ):
            return
        return super().build(is_root)


@register_entity(action_cls=LaunchDescription)
class LaunchDescriptionNode(SplicedNode): ...


@register_entity(action_cls=DeclareLaunchArgument)
class DeclareLaunchArgumentNode(IgnoredNode):
    pass


@register_entity(action_cls=PopEnvironment)
class PopEnvironmentNode(IgnoredNode):
    pass  # Implement the specific logic for PopEnvironmentNode here


@register_entity(action_cls=PopLaunchConfigurations)
class PopLaunchConfigurationsNode(IgnoredNode):
    pass  # Implement the specific logic for PopLaunchConfigurationsNode here


@register_entity(action_cls=PushEnvironment)
class PushEnvironmentNode(IgnoredNode):
    pass  # Implement the specific logic for PushEnvironmentNode here


@register_entity(action_cls=PushLaunchConfigurations)
class PushLaunchConfigurationsNode(ActionNode):
    pass  # Implement the specific logic for PushLaunchConfigurationsNode here


@register_entity(action_cls=SetLaunchConfiguration)
class SetLaunchConfigurationNode(ActionNode):
    pass  # Implement the specific logic for SetLaunchConfigurationNode here


@register_entity(action_cls=GroupAction)
class GroupActionNode(ActionNode):
    pass  # Implement the specific logic for GroupActionNode here


@register_entity(action_cls=IncludeLaunchDescription)
class IncludeLaunchDescriptionNode(ActionNode):
    pass  # Implement the specific logic for IncludeLaunchDescriptionNode here


@register_entity(action_cls=OpaqueFunction)
class OpaqueFunctionNode(SplicedNode):
    pass  # Implement the specific logic for OpaqueFunctionNode here


@register_entity(action_cls=PushRosNamespace)
class PushRosNamespaceNode(ActionNode):
    pass  # Implement the specific logic for PushRosNamespaceNode here


@register_entity(action_cls=SetParameter)
class SetParameterNode(ActionNode):
    pass  # Implement the specific logic for SetParameterNode here


@register_entity(action_cls=SetRemap)
class SetRemapNode(ActionNode):
    pass  # Implement the specific logic for SetRemapNode here


@register_entity(action_cls=Node)
class NodeNode(ActionNode):
    def build(self, is_root=False):

        assert is_root is False  # This node should not be root

        try:
            self.entity.visit(self.service.context)
        except Exception as e:
            print(f"error in {self.entity.__class__}: {e}")

        self.entity._Node__package = _to_string(
            self.service.context, self.entity._Node__package
        )
        self.entity._Node__node_executable = _to_string(
            self.service.context, self.entity._Node__node_executable
        )

        return self


@register_entity(action_cls=ComposableNodeContainer)
class ComposableNodeContainerNode(NodeNode):
    pass


@register_entity(action_cls=LoadComposableNodes)
class LoadComposableNodesNode(ActionNode):
    def build(self, is_root=False):

        assert is_root is False  # This node should not be root

        try:
            self.entity.visit(self.service.context)
        except Exception as e:
            print(f"error in {self.entity.__class__}: {e}")

        def make_composable_node(n):
            n._ComposableNode__package = _to_string(self.service.context, n.package)
            n._ComposableNode__node_plugin = _to_string(
                self.service.context, n.node_plugin
            )
            n._ComposableNode__node_namespace = _to_string(
                self.service.context, n.node_namespace
            )
            n._ComposableNode__node_name = _to_string(self.service.context, n.node_name)
            return n

        self.children: List[LaunchTreeNode] = [
            ComposableNodeContainerNode(make_composable_node(entity), self.service)
            for entity in self.entity._LoadComposableNodes__composable_node_descriptions
        ]

        return self
