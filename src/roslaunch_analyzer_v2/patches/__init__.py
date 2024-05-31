from .action_patch import apply_action_patch
from .execute_local_patch import apply_execute_local_patch
from .launch_description_patch import apply_launch_description_patch
from .load_composable_node_patch import apply_load_composable_nodes_patch


def apply_patches():
    apply_load_composable_nodes_patch()
    apply_action_patch()
    apply_launch_description_patch()
    apply_execute_local_patch()
