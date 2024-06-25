from launch.actions import IncludeLaunchDescription
from launch.launch_description import (
    DeclareLaunchArgument,
    LaunchDescription,
    List,
    Tuple,
)


def get_launch_arguments_with_include_launch_description_actions(
    self: LaunchDescription, conditional_inclusion=False, **kwargs
) -> List[Tuple[DeclareLaunchArgument, List["IncludeLaunchDescription"]]]:

    from launch.actions import IncludeLaunchDescription  # noqa: F811

    declared_launch_arguments: List[
        Tuple[DeclareLaunchArgument, List[IncludeLaunchDescription]]
    ] = []
    from launch.actions import ResetLaunchConfigurations

    def process_entities(entities, *, _conditional_inclusion, nested_ild_actions=None):
        for entity in entities:
            if isinstance(entity, DeclareLaunchArgument):
                # Avoid duplicate entries with the same name.
                if entity.name in (e.name for e, _ in declared_launch_arguments):
                    continue
                # Stuff this contextual information into the class for
                # potential use in command-line descriptions or errors.
                entity._conditionally_included = _conditional_inclusion
                entity._conditionally_included |= entity.condition is not None
                declared_launch_arguments.append((entity, nested_ild_actions))

            if isinstance(
                entity, IncludeLaunchDescription
            ):  # modification from original code is here
                continue

            if isinstance(entity, ResetLaunchConfigurations):
                # Launch arguments after this cannot be set directly by top level arguments
                return
            else:
                next_nested_ild_actions = nested_ild_actions
                if isinstance(entity, IncludeLaunchDescription):
                    if next_nested_ild_actions is None:
                        next_nested_ild_actions = []
                    next_nested_ild_actions.append(entity)
                process_entities(
                    entity.describe_sub_entities(),
                    _conditional_inclusion=False,
                    nested_ild_actions=next_nested_ild_actions,
                )
                for (
                    conditional_sub_entity
                ) in entity.describe_conditional_sub_entities():
                    process_entities(
                        conditional_sub_entity[1],
                        _conditional_inclusion=True,
                        nested_ild_actions=next_nested_ild_actions,
                    )

    process_entities(self.entities, _conditional_inclusion=conditional_inclusion)

    return declared_launch_arguments


def apply_launch_description_patch():
    LaunchDescription.get_launch_arguments_with_include_launch_description_actions = (
        get_launch_arguments_with_include_launch_description_actions
    )
