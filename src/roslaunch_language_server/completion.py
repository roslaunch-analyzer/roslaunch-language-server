import re


class CompleionFeature:
    def __init__(self) -> None:
        pass

    @property
    def pattern(self): ...


class FindPkgCompletion(CompleionFeature): ...
