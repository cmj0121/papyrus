from dataclasses import dataclass

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
