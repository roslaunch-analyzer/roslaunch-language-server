from typing import Any, Callable, Dict, Iterable, List, Optional, Union

from launch.substitutions import LaunchConfiguration, TextSubstitution
from launch_ros.parameter_descriptions import ParameterFile, ParameterValue

from .utils import resolve_symlink

# Dictionary to store serializers for specific classes
_serializers: Dict[type, Callable[[Any], Any]] = {}


def register_serializer(target_class: type) -> Callable[[Callable], Callable]:
    """
    Decorator to register a serializer function for a specific class.

    Args:
        target_class (type): The class to register the serializer for.

    Returns:
        Callable: The decorator function.
    """

    def decorator(func: Callable) -> Callable:
        _serializers[target_class] = func
        return func

    return decorator


def serialize_object(obj: Any) -> Any:
    """
    Serialize an object using the registered serializer function for its class.

    Args:
        obj (Any): The object to serialize.

    Returns:
        Any: The serialized object.
    """
    serializer = _serializers.get(type(obj), str)
    return serializer(obj)


@register_serializer(ParameterFile)
def serialize_parameter_file(parameter_file: ParameterFile) -> Dict[str, str]:
    """
    Serialize a ParameterFile object.

    Args:
        parameter_file (ParameterFile): The ParameterFile object to serialize.

    Returns:
        Dict[str, str]: A dictionary containing the key "__parameter_file__" and the linked path of the parameter file.
    """
    return {
        "__parameter_file__": resolve_symlink(
            serialize_object(parameter_file.param_file)
        ),
    }


@register_serializer(TextSubstitution)
def serialize_text_substitution(text_substitution: TextSubstitution) -> str:
    """
    Serialize a TextSubstitution object.

    Args:
        text_substitution (TextSubstitution): The TextSubstitution object to serialize.

    Returns:
        str: The text of the TextSubstitution.
    """
    return text_substitution.text


@register_serializer(LaunchConfiguration)
def serialize_launch_configuration(launch_configuration: LaunchConfiguration) -> str:
    """
    Serialize a LaunchConfiguration object.

    Args:
        launch_configuration (LaunchConfiguration): The LaunchConfiguration object to serialize.

    Returns:
        str: The concatenated string of all substitutions in the LaunchConfiguration.
    """
    return "".join(
        serialize_object(substitution)
        for substitution in launch_configuration.variable_name
    )


@register_serializer(ParameterValue)
def serialize_parameter_value(parameter_value: ParameterValue) -> Any:
    """
    Serialize a ParameterValue object.

    Args:
        parameter_value (ParameterValue): The ParameterValue object to serialize.

    Returns:
        Any: The evaluated parameter value.
    """
    return parameter_value._ParameterValue__evaluated_parameter_value


@register_serializer(tuple)
def serialize_parameter_tuple(parameter_tuple: tuple) -> str:
    """
    Serialize a tuple containing parameters.

    Args:
        parameter_tuple (tuple): The tuple to serialize.

    Returns:
        str: The concatenated string of all parameters in the tuple.
    """
    return "".join(map(serialize_object, parameter_tuple))


@register_serializer(list)
def serialize_parameter_list(parameter_list: List[Any]) -> str:
    """
    Serialize a list containing parameters.

    Args:
        parameter_list (List[Any]): The list to serialize.

    Returns:
        str: The concatenated string of all parameters in the list.
    """
    return "".join(map(serialize_object, parameter_list))


@register_serializer(dict)
def serialize_parameter_dict(parameter_dict: Dict[Any, Any]) -> Dict[Any, Any]:
    """
    Serialize a dictionary containing key-value pairs.

    Args:
        parameter_dict (Dict[Any, Any]): The dictionary to serialize.

    Returns:
        Dict[Any, Any]: A dictionary containing the serialized key and value pairs.
    """
    return {
        "".join(map(serialize_object, k)): serialize_object(v)
        for k, v in parameter_dict.items()
    }


def serialize_parameters(
    parameters: Optional[Iterable[Any]],
) -> Dict[Any, Union[Any, List[Any]]]:
    """
    Serialize a list of parameters.

    Args:
        parameters (Optional[Iterable[Any]]): A list of parameters to serialize.

    Returns:
        Dict[Any, Union[Any, List[Any]]]: A dictionary containing the serialized parameters.
    """
    if parameters is None:
        return {}
    serialized = [serialize_object(parameter) for parameter in parameters]
    return serialized
