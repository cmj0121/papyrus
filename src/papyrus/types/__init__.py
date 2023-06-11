from dataclasses import dataclass

from .key import Key
from .key import KeyType
from .key import UniqueID


__all__ = [
    "Data",
    "Key",
    "KeyType",
    "UniqueID",
]


@dataclass
class Data:
    """
    The data is the composite of the key, the value and the searchable tags.
    """
    primary_key: Key

    is_deleted: bool = False
