from typing import List, Optional

from launch import Action
from launch.launch_context import LaunchContext
from launch.launch_description import LaunchDescriptionEntity


def visit(
    self: Action, context: LaunchContext
) -> Optional[List[LaunchDescriptionEntity]]:
    """Override visit from LaunchDescriptionEntity so that it executes."""
    if self.condition is None or self.condition.evaluate(context):
        return self.execute(context)
    return None


def apply_action_patch():
    Action.visit = visit
