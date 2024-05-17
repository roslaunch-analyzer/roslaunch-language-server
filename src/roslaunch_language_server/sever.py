import os
import re

from lsprotocol import types
from pygls.server import LanguageServer

from roslaunch_language_server.logger import logger

logger.info("Starting roslaunch-language-server")
server = LanguageServer("roslaunch-language-server", version="0.1.0")


@server.feature("hello_world")
def hello_world(ls: LanguageServer, params: dict):
    ls.show_message("Hello World")
    logger.info("Hello World")
    return {"result": "success"}


@server.feature("parse_launch_file")
def parse_launch_file(ls: LanguageServer, params: dict):
    from roslaunch_analyzer import analyse_launch_structure

    launch_command = params["command"]
    ls.show_message_log(f"Analyzing launch file: {launch_command}")
    return analyse_launch_structure(launch_command)


@server.feature(
    types.TEXT_DOCUMENT_COMPLETION,
    types.CompletionOptions(trigger_characters=["$", " "]),
)
def on_completion(ls: LanguageServer, params: types.CompletionParams):

    uri = params.text_document.uri
    pos = params.position
    doc = ls.workspace.get_document(uri)

    try:
        line = doc.lines[pos.line]
    except IndexError:
        line = ""

    ls.show_message(f"Completion request at {uri}:{pos.line}:{pos.character}")

    return []

    # items = []

    # for feature in completion_features:
    #     for pattern in feature.trigger_characters:
    #         for match in pattern.finditer(line):
    #             items.extend(feature.completion(ls, params, match))

    # ls

    # document = ls.workspace.get_document(params.text_document.uri)
    # position = params.position
    # line = document.lines[position.line]

    # # Extract the text before the cursor
    # text_before_cursor = line[: position.character]
    # ls.show_message(f"Text before cursor: {text_before_cursor}")

    # if text_before_cursor.endswith("$"):
    #     return [
    #         types.CompletionItem(
    #             label="$(var )",
    #             kind=types.CompletionItemKind.Variable,
    #             insert_text="(var )",
    #             insert_text_format=types.InsertTextFormat.PlainText,
    #         ),
    #         types.CompletionItem(
    #             label="$(find-pkg-share )",
    #             kind=types.CompletionItemKind.Function,
    #             insert_text="(find-pkg-share )",
    #             insert_text_format=types.InsertTextFormat.PlainText,
    #         ),
    #     ]
    # elif text_before_cursor.endswith("$(find-pkg-share "):
    #     return get_package_names_completions()
    # elif "$(find-pkg-share " in text_before_cursor:
    #     pkg_name_match = re.search(
    #         r"\$\((find-pkg-share ([^\)]+))\)", text_before_cursor
    #     )
    #     if pkg_name_match:
    #         pkg_name = pkg_name_match.group(2)
    #         return get_package_files_completions(pkg_name)

    # return []


def get_package_names_completions():
    """
    Retrieves package names for completion.
    """
    try:
        from ament_index_python.packages import get_packages_with_prefixes

        packages = get_packages_with_prefixes()
        return [
            types.CompletionItem(label=pkg, kind=types.CompletionItemKind.Module)
            for pkg in packages.keys()
        ]
    except ImportError:
        return []


def get_package_files_completions(pkg_name: str):
    """
    Retrieves file paths within a package for completion.
    """
    try:
        from ament_index_python.packages import get_package_share_directory

        pkg_share_path = get_package_share_directory(pkg_name)
        file_paths = []
        for root, dirs, files in os.walk(pkg_share_path):
            for file in files:
                file_path = os.path.relpath(os.path.join(root, file), pkg_share_path)
                file_paths.append(
                    types.CompletionItem(
                        label=file_path, kind=types.CompletionItemKind.File
                    )
                )
        return file_paths
    except (ImportError, LookupError):
        return []


@server.feature(types.TEXT_DOCUMENT_DEFINITION)
def text_document_definition(ls: LanguageServer, params: types.DefinitionParams):
    if not params.text_document.uri.endswith(".launch.xml"):
        return None

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
    match = re.match(r"\$\((find-pkg-share ([^\)]+))\)(.*)", path)
    if not match:
        return None

    pkg_name = match.group(2)
    relative_path = match.group(3)

    # Assume that 'ament_index_python.packages.get_package_share_directory' is available
    try:
        from ament_index_python.packages import get_package_share_directory

        pkg_share_path = get_package_share_directory(pkg_name)
        return os.path.join(pkg_share_path, relative_path.lstrip("/"))
    except (ImportError, LookupError):
        return None
