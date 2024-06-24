from launch import LaunchContext
from launch.launch_description_sources import AnyLaunchDescriptionSource


def get_arguments_of_launch_file(launch_file_path: str) -> dict:
    context = LaunchContext()
    launch_description_source = AnyLaunchDescriptionSource(launch_file_path)
    launch_description = launch_description_source.get_launch_description(context)
    launch_arguments = launch_description.get_launch_arguments()
    sub_entities = launch_description.visit(context)
    for entity in sub_entities:
        try:
            entity.visit(context)
        except Exception:
            pass
    arguments = []
    for argument_action in launch_arguments:
        argument = {
            "name": argument_action.name,
            "description": argument_action.description,
            "default_value": (
                "".join(
                    [token.perform(context) for token in argument_action.default_value]
                )
                if argument_action.default_value is not None
                else None
            ),
            "conditionally_included": argument_action._conditionally_included,
        }
        arguments.append(argument)

    return arguments
