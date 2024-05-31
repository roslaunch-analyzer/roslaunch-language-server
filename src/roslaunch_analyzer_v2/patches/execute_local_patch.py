from typing import List, Optional

from launch.actions import ExecuteLocal
from launch.launch_context import LaunchContext
from launch.launch_description import LaunchDescriptionEntity


def execute(
    self: ExecuteLocal, context: LaunchContext
) -> Optional[List[LaunchDescriptionEntity]]:
    """
    Execute the action.

    This does the following:
    - register an event handler for the shutdown process event
    - register an event handler for the signal process event
    - register an event handler for the stdin event
    - configures logging for the IO process event
    - create a task for the coroutine that monitors the process
    """
    self.prepare(context)
    name = self.process_description.final_name

    if self._ExecuteLocal__executed:
        raise RuntimeError(
            f"ExecuteLocal action '{name}': executed more than once: {self.describe()}"
        )

    return None


def apply_execute_local_patch():
    ExecuteLocal.execute = execute
