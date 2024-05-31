from typing import List

# enable nested async loop
import nest_asyncio
from lsprotocol import types
from lxml import etree
from pygls.server import LanguageServer
from roslaunch_analyzer import get_launch_file_arguments

from roslaunch_language_server.features import (
    completion_feature_eitities,
    definition_feature_eitities,
)
from roslaunch_language_server.helper import (
    create_tree,
    find_symlinks,
    remove_group_action_nodes,
)
from roslaunch_language_server.server import logger, server

nest_asyncio.apply()


@server.feature("hello_world")
def hello_world(ls: LanguageServer, params: dict):
    ls.show_message("Roslaunch Language Server is running!")
    logger.info("Roslaunch Language Server is running!")
    return {"result": "success"}


@server.feature("parse_launch_file")
def parse_launch_file(ls: LanguageServer, params: dict):
    command = ["ros2 launch", find_symlinks(params.filepath, params.colcon_path)]
    for k, v in params.arguments:
        command.append(f"{k}:={v}")
    command = " ".join(command)
    from roslaunch_analyzer import analyse_launch_structure

    launch_tree = create_tree(analyse_launch_structure(command))
    remove_group_action_nodes(launch_tree)
    tree_info = launch_tree.to_dict()
    return tree_info


@server.feature("get_launch_file_parameters")
def get_launch_file_parameters(ls: LanguageServer, params: dict):
    return get_launch_file_arguments(params.filepath)


@server.feature(
    types.TEXT_DOCUMENT_COMPLETION,
    types.CompletionOptions(
        trigger_characters=["$", "(", " ", "/", '"'],
    ),
)
def on_completion(ls: LanguageServer, params: types.CompletionParams):

    uri = params.text_document.uri
    pos = params.position
    doc = ls.workspace.get_document(uri)

    text_before_cursor = (
        "".join(doc.lines[: pos.line]) + doc.lines[pos.line][: pos.character]
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
        try:
            extracted_string = doc.word_at_position(
                pos, feature.re_start_quote, feature.re_end_quote
            )
        except IndexError:
            continue
        if extracted_string is None:
            continue
        logger.debug(f"Extracted string: {extracted_string}")
        match = feature.pattern.search(extracted_string)
        if match is None:
            continue
        logger.debug(f"Matched pattern: {match.group(0)}")
        definitions.extend(feature.definition(doc, pos, match))

    return definitions


@server.feature(types.TEXT_DOCUMENT_HOVER)
def on_hover(ls: LanguageServer, params: types.HoverParams):
    uri = params.text_document.uri
    pos = params.position
    doc = ls.workspace.get_document(uri)

    hover = None

    # for feature in definition_feature_eitities:
    #     try:
    #         extracted_string = doc.word_at_position(
    #             pos, feature.re_start_quote, feature.re_end_quote
    #         )
    #     except IndexError:
    #         continue
    #     if extracted_string is None:
    #         continue
    #     logger.debug(f"Extracted string: {extracted_string}")
    #     match = feature.pattern.search(extracted_string)
    #     if match is None:
    #         continue
    #     logger.debug(f"Matched pattern: {match.group(0)}")
    #     hover = feature.hover(doc, pos, match)

    return hover
