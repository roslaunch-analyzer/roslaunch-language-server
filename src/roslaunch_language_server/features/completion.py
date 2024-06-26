import os
import re
from typing import List

import lxml.etree as etree
from ament_index_python.packages import get_package_share_directory
from lsprotocol.types import (
    CompletionItem,
    CompletionItemKind,
    InsertTextFormat,
    Position,
)
from pygls.workspace import TextDocument

from roslaunch_language_server.utils import all_env_vars, all_ros_packages


class CompletionFeatureEntity:
    """
    Base class for completion features in ROS XML launch files.
    Each subclass must define a pattern property and implement the complete method.
    """

    @property
    def pattern(self) -> re.Pattern:
        """
        Regular expression pattern that triggers this completion.
        Must be implemented by subclasses.
        """
        raise NotImplementedError("The pattern property must be implemented.")

    def complete(
        self, doc: TextDocument, pos: Position, match: re.Match
    ) -> List[CompletionItem]:
        """
        Generates completion items based on the match.
        Must be implemented by subclasses.

        :param doc: The text document in which completion is triggered.
        :param pos: The position in the document where completion is triggered.
        :param match: The regex match object.
        :return: A list of completion items.
        """
        raise NotImplementedError("The complete method must be implemented.")


class SubstitutionCompletion(CompletionFeatureEntity):
    """
    Provides completion items for <substitution> in $(<substitution>).
    """

    pattern = re.compile(r"\".*?\$\((?P<semantics_name_prefix>[a-z-]*)$")

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

    def complete(
        self, doc: TextDocument, pos: Position, match: re.Match
    ) -> List[CompletionItem]:
        """
        Generates completion items for <substitution> in $(<substitution>).

        :param doc: The text document in which completion is triggered.
        :param pos: The position in the document where completion is triggered.
        :param match: The regex match object.

        :return: A list of completion items.
        """
        semantics_name_prefix: str = match.group("semantics_name_prefix")
        pattern = re.compile(r"^" + semantics_name_prefix + r"[a-z-]*")
        # TODO: check whether the end-bracket is present and if not, add it
        return [
            CompletionItem(
                label=match.string,
                kind=CompletionItemKind.Function,
                insert_text_format=InsertTextFormat.PlainText,
            )
            for match in filter(None, map(pattern.match, self.available_semantics))
        ]


class FindPkgSharePkgNameCompletion(CompletionFeatureEntity):
    """
    Provides completion items for <package_name> in $(find-pkg-share <package_name>).
    """

    pattern = re.compile(
        r"\".*?\$\(find\-pkg\-share\s+(?P<pkg_name_prefix>[a-zA-Z0-9_-]*)$"
    )

    def complete(
        self, doc: TextDocument, pos: Position, match: re.Match
    ) -> List[CompletionItem]:
        """
        Generates completion items for <package_name> in $(find-pkg-share <package_name>).

        :param doc: The text document in which completion is triggered.
        :param pos: The position in the document where completion is triggered.
        :param match: The regex match object.
        :return: A list of completion items.
        """
        pkg_name_prefix: str = match.group("pkg_name_prefix")
        pattern = re.compile(r"^" + pkg_name_prefix + r"[a-zA-Z0-9_-]*")
        return [
            CompletionItem(
                label=match.string,
                kind=CompletionItemKind.Module,
                insert_text_format=InsertTextFormat.PlainText,
            )
            for match in filter(None, map(pattern.match, all_ros_packages))
        ]


class EnvCompletion(CompletionFeatureEntity):
    """
    Provides completion items for <env_variable> in $(env <env_variable>).
    """

    pattern = re.compile(r"\".*?\$\(env\s+(?P<env_var_prefix>[a-zA-Z0-9_-]*)$")

    def complete(
        self, doc: TextDocument, pos: Position, match: re.Match
    ) -> List[CompletionItem]:
        """
        Generates completion items for <env_variable> in $(env <env_variable>).

        :param doc: The text document in which completion is triggered.
        :param pos: The position in the document where completion is triggered.
        :param match: The regex match object.
        :return: A list of completion items.
        """
        env_var_prefix: str = match.group("env_var_prefix")
        pattern = re.compile(r"^" + env_var_prefix + r"[a-zA-Z0-9_-]*")
        return [
            CompletionItem(
                label=match.string,
                kind=CompletionItemKind.Variable,
                insert_text_format=InsertTextFormat.PlainText,
            )
            for match in filter(None, map(pattern.match, all_env_vars))
        ]


class FindPkgShareSuffixPathCompletion(CompletionFeatureEntity):
    """
    Provides completion items for <path> in $(find-pkg-share <package_name>)/<path>.
    """

    pattern = re.compile(
        r"\".*?\$\(find\-pkg\-share\s+(?P<package_name>[a-zA-Z0-9_-]+)\)(?P<path_suffix>.*)$"
    )

    def complete(
        self, doc: TextDocument, pos: Position, match: re.Match
    ) -> List[CompletionItem]:
        """
        Generates completion items for <path> in $(find-pkg-share package_name)/<path>.

        :param doc: The text document in which completion is triggered.
        :param pos: The position in the document where completion is triggered.
        :param match: The regex match object.

        :return: A list of completion items.
        """
        package_name: str = match.group("package_name")
        path_suffix: str = match.group("path_suffix")

        try:
            share_dir = get_package_share_directory(package_name)
        except Exception:
            return []

        path = os.path.join(share_dir, path_suffix.lstrip("/"))

        dir_path, incomplete_part = os.path.split(path)

        if not os.path.isdir(dir_path):
            return []

        return [
            CompletionItem(
                label=os.path.basename(path),
                kind=(
                    CompletionItemKind.Folder
                    if os.path.isdir(path)
                    else CompletionItemKind.File
                ),
            )
            for path in map(
                lambda item: os.path.join(dir_path, item),
                filter(lambda x: x.startswith(incomplete_part), os.listdir(dir_path)),
            )
        ]


class EnvHomeSuffixPathCompletion(CompletionFeatureEntity):
    """
    Provides completion items for <path> of $(env HOME)/<path>.
    """

    pattern = re.compile(r"\".*?\$\(env\s+HOME\)(?P<path_suffix>.*)$")

    def complete(
        self, doc: TextDocument, pos: Position, match: re.Match
    ) -> List[CompletionItem]:
        """
        Generates completion items for <path> within a package's share directory.

        :param doc: The text document in which completion is triggered.
        :param pos: The position in the document where completion is triggered.
        :param match: The regex match object.
        :return: A list of completion items.
        """
        path_suffix: str = match.group("path_suffix")

        home_dir = os.path.expanduser("~")

        path = os.path.join(home_dir, path_suffix.lstrip("/"))

        dir_path, incomplete_part = os.path.split(path)

        if not os.path.isdir(dir_path):
            return []

        return [
            CompletionItem(
                label=os.path.basename(path),
                kind=(
                    CompletionItemKind.Folder
                    if os.path.isdir(path)
                    else CompletionItemKind.File
                ),
            )
            for path in map(
                lambda item: os.path.join(dir_path, item),
                filter(lambda x: x.startswith(incomplete_part), os.listdir(dir_path)),
            )
        ]


class VarCompletion(CompletionFeatureEntity):
    """
    Provides completion items for <variable_name> in $(var <variable_name>).
    """

    pattern = re.compile(r"\".*?\$\(var\s+(?P<var_name_prefix>[a-zA-Z0-9_-]*)$")

    def complete(
        self, doc: TextDocument, pos: Position, match: re.Match
    ) -> List[CompletionItem]:
        """
        Generates completion items for <variable_name> in $(var <variable_name>).

        :param doc: The text document in which completion is triggered.
        :param pos: The position in the document where completion is triggered.
        :param match: The regex match object.
        :return: A list of completion items.
        """
        var_name_prefix: str = match.group("var_name_prefix")
        parser = etree.XMLPullParser(events=("start", "end"))

        try:
            text_before_element_at_cursor = (
                doc.source[: doc.offset_at_position(pos)]
                + re.search(
                    r"^([^>^<]*>)", doc.source[doc.offset_at_position(pos) :]
                ).group()
            )
        except AttributeError:
            return []

        parser.feed(text_before_element_at_cursor)

        event, elem_at_cursor = list(parser.read_events())[-1]

        def search_usable_variable(elem: etree.Element, tag: str = "arg"):
            parent = elem.getparent()
            if parent is not None:
                return [
                    e.get("name")
                    for e in parent.findall(tag)
                    if e.get("name", "").startswith(var_name_prefix)
                ] + search_usable_variable(parent, tag)
            else:
                return []

        usable_vars = search_usable_variable(
            elem_at_cursor, "arg"
        ) + search_usable_variable(elem_at_cursor, "let")

        # Remove duplicates
        usable_vars = list(set(usable_vars))

        return [
            CompletionItem(
                label=var,
                kind=CompletionItemKind.Variable,
                insert_text_format=InsertTextFormat.PlainText,
            )
            for var in usable_vars
        ]


class NodePkgCompletion(CompletionFeatureEntity):
    """
    Provides completion items for <package_name> in <node pkg="<package_name>".
    """

    pattern = re.compile(r"\<node[^<]*pkg\s*=\s*\"(?P<pkg_name_prefix>[a-zA-Z0-9_-]*)$")

    def complete(
        self, doc: TextDocument, pos: Position, match: re.Match
    ) -> List[CompletionItem]:
        """
        Generates completion items for <package_name> in <node pkg="<package_name>" />.

        :param doc: The text document in which completion is triggered.
        :param pos: The position in the document where completion is triggered.
        :param match: The regex match object.
        :return: A list of completion items.
        """
        pkg_name_prefix: str = match.group("pkg_name_prefix")
        pattern = re.compile(r"^" + pkg_name_prefix + r"[a-zA-Z0-9_-]*")
        return [
            CompletionItem(
                label=match.string,
                kind=CompletionItemKind.Module,
                insert_text_format=InsertTextFormat.PlainText,
            )
            for match in filter(None, map(pattern.match, all_ros_packages))
        ]


completion_feature_eitities: List[CompletionFeatureEntity] = [
    SubstitutionCompletion(),
    FindPkgSharePkgNameCompletion(),
    EnvCompletion(),
    FindPkgShareSuffixPathCompletion(),
    EnvHomeSuffixPathCompletion(),
    VarCompletion(),
    NodePkgCompletion(),
]
