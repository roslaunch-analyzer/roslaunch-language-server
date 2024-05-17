import json

from launch import LaunchContext, LaunchDescription, LaunchDescriptionEntity
from launch.actions import IncludeLaunchDescription


class LaunchTreeNode:

    print("LaunchStrucuteNode")

    action_to_node: dict = {}

    def __init__(self, name, parent):
        self.name = name
        self.parent = parent
        self.children = []

    def add_child(self, child):
        self.children.append(child)

    def __str__(self):
        return self.name

    def __dict__(self):
        raise NotImplementedError()

    def visit(self): ...


class IncludeLaunchDescriptionNode(LaunchTreeNode):
    def __init__(self, entity: IncludeLaunchDescription, context: LaunchContext):

        self.entity = entity
        self.context = context

    def visit(self):
        try:
            sub_entities = self.entity.visit(self.context)
        except Exception as e:
            print(f"error in {self.entity.__class__}: {e}")


x = IncludeLaunchDescriptionNode("entity")
print(LaunchTreeNode.action_to_node)
