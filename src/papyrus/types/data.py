from __future__ import annotations

from typing import Any

from .key import Key
from .value import Value


class Data:
    """
    The data is the composite of the key, the value and the searchable tags.
    """
    def __init__(self, key: Any, /, value: Any | None = None, tags: dict[map, Key] = {}, is_deleted: bool = False):
        self.primary_key = key if isinstance(key, Key) else Key(key)
        self.value = Value(value) if value else None
        self.tags = tags
        self.is_deleted = is_deleted

    def __repr__(self):
        tokens = [
            self.sign,
            str(self.primary_key),
            str(self.value or ""),
            self.searchable,
        ]

        return " ".join(n for n in tokens if n)

    def __str__(self):
        tokens = [
            self.sign,
            str(self.value or ""),
        ]

        return " ".join(n for n in tokens if n)

    @property
    def sign(self) -> str:
        match self.is_deleted:
            case True:
                return "[-]"
            case False:
                return "[+]"

    @property
    def searchable(self) -> str:
        if not self.tags:
            return ""

        tags = (f"{key}={self.tags[key]}" for key in sorted(self.tags.keys()))
        return "[{}]".format(", ".join(tags))
