from launch.launch_description_sources import (
    get_launch_description_from_any_launch_file,
)

from launch.frontend import Parser
from launch.substitutions import TextSubstitution


def _parse_substitution_patch(self, text):
    return [TextSubstitution(text=text)]


Parser.parse_substitution = _parse_substitution_patch


def get_arguments_of_launch_file(launch_file_path: str) -> dict:

    # monkey patching

    launch_description = get_launch_description_from_any_launch_file(launch_file_path)
    launch_arguments = launch_description.get_launch_arguments()

    arguments = []
    for argument_action in launch_arguments:
        argument = {
            "name": argument_action.name,
            "description": argument_action.description,
            "default_value": (
                "".join([token.describe() for token in argument_action.default_value])
                if argument_action.default_value is not None
                else None
            ),
            "conditionally_included": argument_action._conditionally_included,
        }
        arguments.append(argument)

    return arguments
