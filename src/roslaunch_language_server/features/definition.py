import re

# import os
from typing import List

# from ament_index_python.packages import get_package_share_directory
from lsprotocol.types import (
    Position,
    TextDocumentItem,
    Location,
)


class DefinitionFeature:

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
