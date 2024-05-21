import os
import re
from typing import List

from ament_index_python.packages import get_package_share_directory
from lsprotocol.types import (
    CompletionItem,
    CompletionItemKind,
    InsertTextFormat,
    Position,
    TextDocumentItem,
)

from roslaunch_language_server.utils import all_env_vars, all_ros_packages


class CompleionFeature:
    @property
    def pattern(self) -> re.Pattern:
        raise NotImplementedError("The pattern property must be implemented.")

    def complete(
        self, doc: TextDocumentItem, pos: Position, match: re.Match
    ) -> List[CompletionItem]:
        raise NotImplementedError("The complete method must be implemented.")


class SubstitutionCompletion(CompleionFeature):

    pattern = re.compile(r"\".*?\$\((?P<semantics_name_head>[a-z-]*)$")

    available_semantics = [
        "find-pkg-prefix",
        "find-pkg-share",
        "find-exec",
        "env-in-package",
        "var",
        "env",
        "eval",
        "dirname",
        "let",
    ]

    def __init__(self) -> None:
        super().__init__()

    def complete(
        self, doc: TextDocumentItem, pos: Position, match: re.Match
    ) -> List[CompletionItem]:
        semantics_name_head: str = match.group("semantics_name_head")
        pattern = re.compile(r"^" + semantics_name_head + r"[a-z-]*")
        return list(
            map(
                lambda match: CompletionItem(
                    label=match.string,
                    kind=CompletionItemKind.Function,
                    insert_text_format=InsertTextFormat.PlainText,
                ),
                filter(
                    lambda x: x,
                    map(lambda x: pattern.match(x), self.available_semantics),
                ),
            )
        )


class FindPkgSharePkgNameCompletion(CompleionFeature):

    pattern = re.compile(
        r"\".*?\$\(find\-pkg\-share\s+(?P<pkg_name_head>[a-zA-Z0-9_-]*)$"
    )

    def __init__(self) -> None:
        super().__init__()

    def complete(
        self, doc: TextDocumentItem, pos: Position, match: re.Match
    ) -> List[CompletionItem]:  # noqa
        pkg_name_head: str = match.group("pkg_name_head")
        pattern = re.compile(r"^" + pkg_name_head + r"[a-zA-Z0-9_-]*")
        return list(
            map(
                lambda match: CompletionItem(
                    label=match.string,
                    kind=CompletionItemKind.Module,
                    insert_text_format=InsertTextFormat.PlainText,
                ),
                filter(lambda x: x, map(lambda x: pattern.match(x), all_ros_packages)),
            )
        )


class EnvCompletion(CompleionFeature):

    pattern = re.compile(r"\".*?\$\(env\s+(?P<env_var_head>[a-zA-Z0-9_-]*)$")

    def __init__(self) -> None:
        super().__init__()

    def complete(
        self, doc: TextDocumentItem, pos: Position, match: re.Match
    ) -> List[CompletionItem]:  # noqa
        env_var_head: str = match.group("env_var_head")
        pattern = re.compile(r"^" + env_var_head + r"[a-zA-Z0-9_-]*")

        return list(
            map(
                lambda match: CompletionItem(
                    label=match.string,
                    kind=CompletionItemKind.Variable,
                    insert_text_format=InsertTextFormat.PlainText,
                ),
                filter(lambda x: x, map(lambda x: pattern.match(x), all_env_vars)),
            )
        )


class FindPkgSharePathCompletion(CompleionFeature):

    pattern = re.compile(
        r"\".*?\$\(find\-pkg\-share\s+(?P<package_name>[a-zA-Z0-9_-]+)\)(?P<path_tail>.*)$"
    )

    def __init__(self) -> None:
        super().__init__()

    def complete(
        self, doc: TextDocumentItem, pos: Position, match: re.Match
    ) -> List[CompletionItem]:  # noqa
        package_name: str = match.group("package_name")
        path_tail: str = match.group("path_tail")

        try:
            share_dir = get_package_share_directory(package_name)
        except Exception:
            return []

        path = os.path.join(share_dir, path_tail.lstrip("/"))

        dir_path, incomplete_part = os.path.split(path)

        if not os.path.isdir(dir_path):
            return []

        return list(
            map(
                lambda path: CompletionItem(
                    label=os.path.basename(path),
                    kind=(
                        CompletionItemKind.Folder
                        if os.path.isdir(path)
                        else CompletionItemKind.File
                    ),
                ),
                map(
                    lambda item: os.path.join(dir_path, item),
                    filter(
                        lambda x: x.startswith(incomplete_part), os.listdir(dir_path)
                    ),
                ),
            )
        )


completion_features: List[CompleionFeature] = [
    SubstitutionCompletion(),
    FindPkgSharePkgNameCompletion(),
    EnvCompletion(),
    FindPkgSharePathCompletion(),
]
