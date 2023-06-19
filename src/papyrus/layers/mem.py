"""In-memory layer implementation."""
import logging
from typing import Any
from typing import Generator
from urllib.parse import ParseResult

from papyrus.settings import PROJ_NAME
from papyrus.types import Key
from papyrus.types import Value

from ._base import BaseLayer
from ._base import DuplicateKey
from ._base import ThresholdLimit


logger = logging.getLogger(PROJ_NAME)


class MemLayer(BaseLayer):
    """
    The in-memory layer implementation.

    All the data is stored in the memory, which the data will be lost after
    the process is terminated.
    """
    name = "mem"
    threshold = 8196

    # ======== the general methods related on the layer meta ======== #
    def __init__(self, /, uri: ParseResult | None = None, threshold: int | None = None):
        super().__init__(uri=uri, threshold=threshold)

        self._keys: set[Key] = set()
        self._mem: dict[Key, Value] = {}
        self._del: dict[Key, Value] = {}

    def __contains__(self, key: Any) -> bool:
        key = key if isinstance(key, Key) else Key(key)
        return key in self._keys

    # ======== the general methods related to data operations ======== #
    def count(self) -> int:
        """number of key-value pairs in the layer."""
        return len(self._mem)

    @property
    def capacity(self) -> int:
        """number of key-value pairs in the layer, include the deleted data."""
        return len(self._keys)

    def insert(self, key: Key, value: Value, /, force: bool = False) -> Value | None:
        """insert the key-value pair into the layer."""
        logger.debug(f"insert {key=}, {value=}, {force=}")

        if key in self._mem and not force:
            raise DuplicateKey(key)

        old_value = self._mem.get(key, None) or self._del.get(key, None)
        if self.threshold is not None and old_value is None and self.capacity >= self.threshold:
            raise ThresholdLimit(self.threshold)

        self._keys.add(key)
        self._mem[key] = value
        self._del.pop(key, None)

        return old_value

    def delete(self, key: Key) -> bool:
        """mark the data as deleted."""
        logger.debug(f"delete {key=}")

        if key in self._mem:
            self._del[key] = self._mem.pop(key)
            self._del[key].delete()
            return True

        return False

    def query(self, key: Key) -> Value | None:
        """get the value from layer with the key."""
        logger.debug(f"query {key=}")

        return self._mem.get(key, None) or self._del.get(key, None)

    # ======== the iteration methods related to data operations ======== #
    def iterate(self, /, desc: bool = True, based: Any = None) -> Generator[tuple[Key, Value], None, None]:
        """iterate all the key-value pairs in the layer."""
        keys = sorted(self._keys, reverse=desc)

        if based is not None:
            based = based if isinstance(based, Key) else Key(based)
            keys = keys[keys.index(based):]

        for key in keys:
            yield key, self.query(key)

    # ======== the authorized methods related to danger operations ======== #
    def purge(self):
        """purge all the marked-as-deleted data in the layer."""
        self._keys -= self._del.keys()
        self._del.clear()

    def unlink(self):
        """purge all the data in the layer."""
        self._keys.clear()
        self._mem.clear()
        self._del.clear()
