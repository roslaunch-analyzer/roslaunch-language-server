import os
from launch import LaunchService
from launch.launch_description_sources import AnyLaunchDescriptionSource
from launch.actions import DeclareLaunchArgument
from  launch.substitutions.text_substitution import TextSubstitution
from launch.utilities import perform_substitutions

def package_share_sub(description):
    pkg_name = description.split("'")[1]
    return f"$(find-package-share {pkg_name})"

def var_sub(description):
    pkg_name = description.split("'")[1]
    return f"$(var {pkg_name})"

def join_substitution_descriptions(descriptions):
    formatted_parts = []
    for description in descriptions:
        if "FindPackageShare" in description :
            formatted_parts.append(package_share_sub(description))
        if "LaunchConfig" in description:
            formatted_parts.append(var_sub(description))
        else:
            # Remove surrounding quotes if present
            formatted_parts.append(description.strip("'").strip('"'))
    return ''.join(formatted_parts)
    
def get_launch_file_arguments(launch_file_path):
    # Check if the launch file exists
    if not os.path.exists(launch_file_path):
        raise FileNotFoundError(f"Launch file '{launch_file_path}' does not exist")

    # Create a launch service
    launch_service = LaunchService()

    # Create a launch description source from the launch file
    launch_description_source = AnyLaunchDescriptionSource(launch_file_path)

    # Parse the launch file to get the launch description
    launch_description = launch_description_source.get_launch_description(launch_service.context)
    
    # Extract launch arguments
    launch_arguments = {}
    for action in launch_description.entities:
        if isinstance(action, DeclareLaunchArgument):
            default_value = ""
            if action.default_value is not None:
                try:
                    default_value = perform_substitutions(launch_service.context, action.default_value)
                except Exception:
                    # If substitution fails, use the describe method and format the result
                    descriptions = [sub.describe() for sub in action.default_value]
                    default_value = join_substitution_descriptions(descriptions)
            
            launch_arguments[action.name] = {
                'default': default_value,
                'description': action.description,
            }

    return launch_arguments
