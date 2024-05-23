from lsprotocol import types
from pygls.server import LanguageServer

from roslaunch_analyzer.serialization import find_linked_path
from roslaunch_language_server.features.completion import completion_features
from roslaunch_language_server.logger import logger
from .helper import create_tree,remove_group_action_nodes,find_symlinks

import nest_asyncio
import re
import xml.etree.ElementTree as ET

nest_asyncio.apply()

logger.info("Starting roslaunch-language-server")
server = LanguageServer("roslaunch-language-server", version="0.1.0")


@server.feature("hello_world")
def hello_world(ls: LanguageServer, params: dict):
    ls.show_message("Roslaunch Language Server is running!")
    logger.info("Hello World")
    ls.show_message_log("Roslaunch Language Server is running!")
    return {"result": "success"}

@server.feature("parse_launch_file")
def parse_launch_file(ls: LanguageServer, params:dict):
    command = ["ros2 launch",find_symlinks(params.filepath,params.colcon_path)]
    for k,v in params.arguments:
        command.append(f"{k}:={v}")
    command = " ".join(command)
    print(command)
    from roslaunch_analyzer import analyse_launch_structure
    launch_tree = create_tree(analyse_launch_structure(command))
    remove_group_action_nodes(launch_tree)
    tree_info = launch_tree.to_dict()
    return tree_info

@server.feature("get_launch_file_parameters")
def parse_launch_file(ls: LanguageServer, params: dict):
    tree = ET.parse(params.filepath)
    root = tree.getroot()
    params = {}
    for arg in root.findall('arg'):
        name = arg.get('name')
        default = arg.get('default', '')  # If no default value, set as 'N/A'
        description = arg.get('description', 'No Description Available')  # If no description, set as 'N/A'
        params[name] ={
                'default': default,
                'description': description
            }

    return params

@server.feature(
    types.TEXT_DOCUMENT_COMPLETION,
    types.CompletionOptions(
        trigger_characters=["$", "(", " ", "/"],
    ),
)
def on_completion(ls: LanguageServer, params: types.CompletionParams):

    uri = params.text_document.uri
    pos = params.position
    doc = ls.workspace.get_document(uri)

    try:
        line = doc.lines[pos.line]
    except IndexError:
        line = ""

    line_before_cursor = line[: pos.character]

    ls.show_message_log(f"[Completion] : Text before cursor: {line_before_cursor}")

    completions = []

    for feature in completion_features:
        match = feature.pattern.search(line_before_cursor)
        if match is None:
            continue
        ls.show_message_log(f"[Completion] : Triggered by {feature.__class__.__name__}")
        completions.extend(feature.complete(doc, pos, match))

    return completions


@server.feature(types.TEXT_DOCUMENT_DEFINITION)
def on_go_to_definition(ls: LanguageServer, params: types.DefinitionParams):

    types.TextDocumentDefinitionResponse

    document = ls.workspace.get_document(params.text_document.uri)

    # Regular expressions to find the string within quotes
    re_start_quote = re.compile(r'"([^"]*)$')
    re_end_quote = re.compile(r'^[^"]*')

    # Extract the string at the cursor position
    string = document.word_at_position(params.position, re_start_quote, re_end_quote)

    if string is None:
        return None

    # Resolve the package share path
    resolved_path = resolve_pkg_share_path(string)

    if resolved_path is None:
        return None

    return types.Location(
        uri=f"file://{resolved_path}",
        range=types.Range(start=types.Position(0, 0), end=types.Position(0, 0)),
    )


def resolve_pkg_share_path(path: str) -> str:
    """
    Resolves a ROS2 package share path to an absolute file path.
    """
    match = re.match(r"\$\((find\-pkg\-share ([^\)]+))\)(.*)", path)
    if not match:
        return None

    pkg_name = match.group(2)
    relative_path = match.group(3)

    # Assume that 'ament_index_python.packages.get_package_share_directory' is available
    try:
        from ament_index_python.packages import get_package_share_directory

        pkg_share_path = get_package_share_directory(pkg_name)
        return find_linked_path(os.path.join(pkg_share_path, relative_path.lstrip("/")))
    except (ImportError, LookupError):
        return None

# if __name__=="__main__":
#     from roslaunch_analyzer import analyse_launch_structure
#     command="ros2 launch /home/samratthapa/workspace/training/autoware.logiee-st-c/install/autoware_launch/share/autoware_launch/launch/autoware.launch.xml map_path:=$HOME/workspace/training/2f_map vehicle_model:=logiee_st_c sensor_model:=logiee_st_c_sensor"
#     print(analyse_launch_structure(command))