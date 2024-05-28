import os
import re
from typing import List

from ament_index_python.packages import (
    PackageNotFoundError,
    get_package_share_directory,
)
from lsprotocol.types import Location, Position, Range
from lxml import etree
from pygls.workspace import TextDocument

from roslaunch_analyzer_v2.utils import find_linked_path
from roslaunch_language_server.server import logger


def position_at_offset(text: TextDocument, offset: int) -> Position:
    """Return the position pointed at by the given character offset using the provided object."""
    lines = text.lines
    accumulated_offset = 0

    for i, line in enumerate(lines):
        line_length = text._position_codec.client_num_units(line)
        if accumulated_offset + line_length >= offset:
            col = offset - accumulated_offset
            server_position = text._position_codec.position_to_client_units(
                lines, Position(line=i, character=col)
            )
            return server_position

        accumulated_offset += line_length

    raise ValueError("Offset out of range")


class DefinitionFeatureEntity:

    @property
    def re_start_quote(self) -> re.Pattern:
        raise NotImplementedError("The re_start_quote property must be implemented.")

    @property
    def re_end_quote(self) -> re.Pattern:
        raise NotImplementedError("The re_end_quote property must be implemented.")

    @property
    def pattern(self) -> re.Pattern:
        raise NotImplementedError("The pattern property must be implemented.")

    def definition(
        self, doc: TextDocument, pos: Position, match: re.Match
    ) -> List[Location]:
        raise NotImplementedError("The get_definition method must be implemented.")


class FindPkgSharePathDefinition(DefinitionFeatureEntity):

    logger = logger.getChild("FindPkgSharePathDefinition")

    re_start_quote = re.compile(r'"([^"]*)$')

    re_end_quote = re.compile(r'^[^"]*')

    pattern = re.compile(
        r"\$\(find\-pkg\-share\s+(?P<pkg_name>[a-zA-Z0-9_-]*)\)\/(?P<relative_path>.*)"
    )

    def definition(
        self, doc: TextDocument, pos: Position, match: re.Match
    ) -> List[Location]:
        pkg_name: str = match.group("pkg_name")
        relative_path: str = match.group("relative_path")

        try:
            pkg_share_path = get_package_share_directory(pkg_name)
        except PackageNotFoundError:
            self.logger.error(
                f"Failed to find share directory for package '{pkg_name}'"
            )
            return []
        resolved_path = find_linked_path(
            os.path.join(pkg_share_path, relative_path.lstrip("/"))
        )
        self.logger.debug(f"Resolved path: {resolved_path}")

        # check if the resolved path exists
        if not os.path.exists(resolved_path):
            self.logger.error(f"Resolved path '{resolved_path}' does not exist")
            return []

        return [
            Location(
                uri=f"file://{resolved_path}",
                range=Range(start=Position(0, 0), end=Position(0, 0)),
            )
        ]


def _are_in_same_scope(higer_elem: etree.Element, lower_elem: etree.Element):
    if lower_elem.getparent() is None:
        return False

    if higer_elem in lower_elem.getparent().getchildren():
        return True

    return _are_in_same_scope(higer_elem, lower_elem.getparent())


def are_in_same_scope(
    text_before_element_at_cursor: str, text_before_matched_element: str
):
    parser = etree.XMLPullParser(events=("start", "end"))

    parser.feed(text_before_matched_element)

    event, matched_elem = list(parser.read_events())[-1]

    parser.feed(text_before_element_at_cursor.replace(text_before_matched_element, ""))

    event, elem_at_cursor = list(parser.read_events())[-1]

    return _are_in_same_scope(matched_elem, elem_at_cursor)


class FindVarDefinition(DefinitionFeatureEntity):

    re_start_quote = re.compile(r"\$\(var\s+(.*)$")

    re_end_quote = re.compile(r"^[^\)]*")

    pattern = re.compile(r"(?P<var_name>[a-zA-Z0-9_-]+)$")

    def definition(
        self, doc: TextDocument, pos: Position, match: re.Match
    ) -> List[Location]:

        var_name = match.group("var_name")

        arg_definition_pattern = re.compile(
            rf'(?P<higher_contents>.*)<arg\b[^>]*\bname=["\'](?P<name>{var_name})["\'][^>]*(?:>(?P<content>.*?)<\/arg>|\/>)',
            re.DOTALL,
        )
        let_definition_pattern = re.compile(
            rf'(?P<higher_contents>.*)<let\b[^>]*\bname=["\'](?P<name>{var_name})["\'][^>]*\bvalue=["\'](?P<value>[^"\']+)["\'][^>]*(?:>(?P<content>.*?)<\/let>|\/>)',
            re.DOTALL,
        )

        text_before_cursor = doc.source[: doc.offset_at_position(pos)]

        text_before_element_at_cursor = (
            doc.source[: doc.offset_at_position(pos)]
            + doc.source[doc.offset_at_position(pos) :].split("<")[0]
        )

        matches = re.finditer(arg_definition_pattern, text_before_cursor)

        definitions = []

        for match in matches:
            text_before_matched_element = match.group()
            if not are_in_same_scope(
                text_before_element_at_cursor, text_before_matched_element
            ):
                continue
            start = position_at_offset(doc, match.start("name"))
            end = position_at_offset(doc, match.end("name"))
            definitions.append(
                Location(
                    uri=doc.uri,
                    range=Range(start=start, end=end),
                )
            )

        matches = re.finditer(let_definition_pattern, text_before_cursor)

        for match in matches:
            text_before_matched_element = match.group()
            if not are_in_same_scope(
                text_before_element_at_cursor, text_before_matched_element
            ):
                continue
            start = position_at_offset(doc, match.start("name"))
            end = position_at_offset(doc, match.end("name"))
            definitions.append(
                Location(
                    uri=doc.uri,
                    range=Range(start=start, end=end),
                )
            )

        return definitions


definition_feature_eitities: List[DefinitionFeatureEntity] = [
    FindPkgSharePathDefinition(),
    FindVarDefinition(),
]
