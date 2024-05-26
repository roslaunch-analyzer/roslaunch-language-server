import re

from typing import List

from lsprotocol.types import Location, Position, TextDocumentItem, Range

from roslaunch_language_server.server import logger
from roslaunch_analyzer_v2.utils import find_linked_path
from ament_index_python.packages import (
    get_package_share_directory,
    PackageNotFoundError,
)
import os


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
        self, doc: TextDocumentItem, pos: Position, match: re.Match
    ) -> List[Location]:
        raise NotImplementedError("The get_definition method must be implemented.")


class FindPkgSharePathDefinition(DefinitionFeatureEntity):

    logger = logger.getChild("FindPkgSharePathDefinition")

    @property
    def re_start_quote(self) -> re.Pattern:
        return re.compile(r'"([^"]*)$')

    @property
    def re_end_quote(self) -> re.Pattern:
        return re.compile(r'^[^"]*')

    @property
    def pattern(self) -> re.Pattern:
        return re.compile(
            r"\$\(find\-pkg\-share\s+(?P<pkg_name>[a-zA-Z0-9_-]*)\)\/(?P<relative_path>.*)"
        )

    def definition(
        self, doc: TextDocumentItem, pos: Position, match: re.Match
    ) -> List[Location]:
        pkg_name = match.group("pkg_name")
        relative_path = match.group("relative_path")

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
        return [
            Location(
                uri=f"file://{resolved_path}",
                range=Range(start=Position(0, 0), end=Position(0, 0)),
            )
        ]


definition_feature_eitities = [FindPkgSharePathDefinition()]
