import re
from typing import List, Optional

from lsprotocol.types import Hover, Position
from pygls.workspace import TextDocument


class HoverFeatureEntity:
    @property
    def re_start_quote(self) -> re.Pattern:
        raise NotImplementedError("The re_start_quote property must be implemented.")

    @property
    def re_end_quote(self) -> re.Pattern:
        raise NotImplementedError("The re_end_quote property must be implemented.")

    @property
    def pattern(self) -> re.Pattern:
        raise NotImplementedError("The pattern property must be implemented.")

    def hover(
        self, doc: TextDocument, pos: Position, match: re.Match
    ) -> Optional[Hover]:
        raise NotImplementedError("The hover method must be implemented.")


class SubstitutionHover(HoverFeatureEntity):
    re_start_quote = re.compile(r"\$\{")
    re_end_quote = re.compile(r"\}")

    @property
    def pattern(self) -> re.Pattern:
        return re.compile(r"\$\{([^}]*)\}")

    def hover(
        self, doc: TextDocument, pos: Position, match: re.Match
    ) -> Optional[Hover]:
        return Hover(
            contents={"kind": "markdown", "value": f"Substitution: `{match.group(1)}`"}
        )


hover_feature_entities: List[HoverFeatureEntity] = [SubstitutionHover()]
