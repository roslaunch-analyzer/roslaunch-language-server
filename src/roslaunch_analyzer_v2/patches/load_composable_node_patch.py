from typing import List, Optional

from launch import Action, LaunchContext
from launch.some_substitutions_type import SomeSubstitutionsType_types_tuple
from launch.utilities import (
    is_a_subclass,
    normalize_to_list_of_substitutions,
    perform_substitutions,
)
from launch_ros.actions import ComposableNodeContainer, LoadComposableNodes


def execute(
    self: LoadComposableNodes, context: LaunchContext
) -> Optional[List[Action]]:
    """Execute the action."""
    # resolve target container node name

    if is_a_subclass(
        self._LoadComposableNodes__target_container, ComposableNodeContainer
    ):
        self._LoadComposableNodes__final_target_container_name = (
            self._LoadComposableNodes__target_container.node_name
        )
    elif isinstance(
        self._LoadComposableNodes__target_container, SomeSubstitutionsType_types_tuple
    ):
        subs = normalize_to_list_of_substitutions(
            self._LoadComposableNodes__target_container
        )
        self._LoadComposableNodes__final_target_container_name = perform_substitutions(
            context, subs
        )
    else:
        self._LoadComposableNodes__logger.error(
            "target container is neither a ComposableNodeContainer nor a SubstitutionType"
        )
        return


def apply_load_composable_nodes_patch():
    LoadComposableNodes.execute = execute
