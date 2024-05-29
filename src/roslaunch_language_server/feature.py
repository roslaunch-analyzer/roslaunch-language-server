from lsprotocol import types
from pygls.server import LanguageServer

from roslaunch_language_server.features import (
    completion_feature_eitities,
    definition_feature_eitities,
)
from roslaunch_language_server.server import logger, server
from typing import List

from .helper import create_tree,remove_group_action_nodes,find_symlinks
import xml.etree.ElementTree as ET

#enable nested async loop
import nest_asyncio
nest_asyncio.apply()

@server.feature("hello_world")
def hello_world(ls: LanguageServer, params: dict):
    ls.show_message("Roslaunch Language Server is running!")
    logger.info("Roslaunch Language Server is running!")
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

    text_before_cursor = (
        "".join(doc.lines[: pos.line - 1]) + doc.lines[pos.line][: pos.character]
    )

    logger.debug(f"Completion triggered at {pos.line}:{pos.character}")

    completions: List[types.CompletionItem] = []

    for feature in completion_feature_eitities:
        match = feature.pattern.search(text_before_cursor)
        if match is None:
            continue
        logger.debug(f"Matched pattern: {match.group(0)}")
        completions.extend(feature.complete(doc, pos, match))

    return completions


@server.feature(types.TEXT_DOCUMENT_DEFINITION)
def on_go_to_definition(ls: LanguageServer, params: types.DefinitionParams):
    uri = params.text_document.uri
    pos = params.position
    doc = ls.workspace.get_document(uri)

    definitions: List[types.Location] = []

    for feature in definition_feature_eitities:
        extracted_string = doc.word_at_position(
            pos, feature.re_start_quote, feature.re_end_quote
        )
        if extracted_string is None:
            continue
        logger.debug(f"Extracted string: {extracted_string}")
        match = feature.pattern.search(extracted_string)
        if match is None:
            continue
        logger.debug(f"Matched pattern: {match.group(0)}")
        definitions.extend(feature.definition(doc, pos, match))

    return definitions
