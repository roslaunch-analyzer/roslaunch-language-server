from collections import defaultdict
from typing import Any, Callable, Dict, List, Tuple, Union, Optional

from launch.substitutions import LaunchConfiguration, TextSubstitution
from launch_ros.parameter_descriptions import ParameterFile, ParameterValue

from .utils import find_linked_path

# Dictionary to store serializers for specific classes
__serializers: Dict[type, Callable[[Any], Any]] = {}


def register_serializer(serialized_cls: type) -> Callable[[Callable], Callable]:
    """
    Decorator to register a serializer function for a specific class.

    Args:
        serialized_cls (type): The class to register the serializer for.

    Returns:
        Callable: The decorator function.
    """

    def actual_decorator(fn: Callable) -> Callable:
        global __serializers
        __serializers[serialized_cls] = fn
        return fn

    return actual_decorator


def __serialize(obj: Any) -> Any:
    """
    Serialize an object using the registered serializer function for its class.

    Args:
        obj (Any): The object to serialize.

    Returns:
        Any: The serialized object.
    """
    if type(obj) in __serializers:
        return __serializers[type(obj)](obj)
    return str(obj)


@register_serializer(serialized_cls=ParameterFile)
def __serialize_parameter_file(parameter_file: ParameterFile) -> Tuple[str, str]:
    """
    Serialize a ParameterFile object.

    Args:
        parameter_file (ParameterFile): The ParameterFile object to serialize.

    Returns:
        Tuple[str, str]: A tuple containing the key "__parameter_files__" and the linked path of the parameter file.
    """
    return (
        "__parameter_files__",
        find_linked_path(__serialize(parameter_file.param_file)),
    )


@register_serializer(serialized_cls=TextSubstitution)
def __serialize_text_substitution(text_substitution: TextSubstitution) -> str:
    """
    Serialize a TextSubstitution object.

    Args:
        text_substitution (TextSubstitution): The TextSubstitution object to serialize.

    Returns:
        str: The text of the TextSubstitution.
    """
    return text_substitution.text


@register_serializer(serialized_cls=LaunchConfiguration)
def __serialize_launch_configuration(launch_configuration: LaunchConfiguration) -> str:
    """
    Serialize a LaunchConfiguration object.

    Args:
        launch_configuration (LaunchConfiguration): The LaunchConfiguration object to serialize.

    Returns:
        str: The concatenated string of all substitutions in the LaunchConfiguration.
    """
    return "".join(
        __serialize(substitution) for substitution in launch_configuration.variable_name
    )


@register_serializer(serialized_cls=ParameterValue)
def __serialize_parameter_value(parameter_value: ParameterValue) -> Any:
    """
    Serialize a ParameterValue object.

    Args:
        parameter_value (ParameterValue): The ParameterValue object to serialize.

    Returns:
        Any: The evaluated parameter value.
    """
    return parameter_value._ParameterValue__evaluated_parameter_value


@register_serializer(serialized_cls=dict)
def __serialize_parameter_dict(parameter_dict: Dict[Any, Any]) -> Tuple[Any, Any]:
    """
    Serialize a dictionary containing a single key-value pair.

    Args:
        parameter_dict (Dict[Any, Any]): The dictionary to serialize.

    Returns:
        Tuple[Any, Any]: A tuple containing the serialized key and value.
    """
    (((key,), value),) = tuple(parameter_dict.items())  # TODO: Check if this is correct
    return (__serialize(key), __serialize(value))


def __group_tuples_by_key(
    tuples: List[Tuple[Any, Any]]
) -> Dict[Any, Union[Any, List[Any]]]:
    """
    Group tuples by their keys and combine values into a list.

    Args:
        tuples (List[Tuple[Any, Any]]): A list of tuples where each tuple contains a key and a value.

    Returns:
        Dict[Any, Union[Any, List[Any]]]: A dictionary where each key maps to a single value or a list of values.
                                          If a key maps to a single value, that value is directly stored.
                                          If a key maps to multiple values, they are stored in a list.

    Example:
        >>> __group_tuples_by_key([("a", 1), ("b", 2), ("c", 3), ("a", 2), ("b", 2)])
        {'a': [1, 2], 'b': [2, 2], 'c': 3}
    """
    grouped_dict = defaultdict(list)
    for k, v in tuples:
        grouped_dict[k].append(v)
    return {k: v[0] if len(v) == 1 else v for k, v in grouped_dict.items()}


def serialize_parameters(
    parameters: Optional[List[Any]],
) -> Dict[Any, Union[Any, List[Any]]]:
    """
    Serialize a list of parameters.

    Args:
        parameters (Optional[List[Any]]): A list of parameters to serialize.

    Returns:
        Dict[Any, Union[Any, List[Any]]]: A dictionary containing the serialized parameters.
    """
    if parameters is None:
        return {}
    serialized_parameters = [__serialize(parameter) for parameter in parameters]
    return __group_tuples_by_key(serialized_parameters)
