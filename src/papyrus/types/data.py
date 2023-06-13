from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .key import Key
from .value import Value


@dataclass
class Data:
    """
    The data is the composite of the key, the value and the searchable tags.
    """
    primary_key: Key
    value: Value | None = None

    is_deleted: bool = False

    def __init__(self, key: Any, /, value: Any | None = None, is_deleted: bool = False):
        self.primary_key = key if isinstance(key, Key) else Key(key)
        self.value = Value(value) if value else None
        self.is_deleted = is_deleted

    def __repr__(self):
        return f"{self.sign} {self.primary_key} {self.value or ''}".strip()

    def __str__(self):
        return f"{self.sign} {self.value or ''}".strip()

    @property
    def sign(self) -> str:
        match self.is_deleted:
            case True:
                return "[-]"
            case False:
                return "[+]"
