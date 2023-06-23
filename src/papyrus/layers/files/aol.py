"""The Append-only Log persistent layer implementation"""
from __future__ import annotations

import logging
import os
import struct
from dataclasses import dataclass
from typing import Any
from typing import Generator

from papyrus.layers import DuplicateKey
from papyrus.settings import PROJ_NAME
from papyrus.types import Key
from papyrus.types import KeyType
from papyrus.types import Value

from .._base import BaseLayer
from ._base import BaseFileLayer


logger = logging.getLogger(PROJ_NAME)


@dataclass
class Pair:
    """
    the key-value pair.
    """
    key: Key
    value: Value

    @property
    def padding(self) -> bytes:
        return b"\x00\x00"

    def __len__(self) -> int:
        return len(self.to_bytes())

    def __lt__(self, other: Any) -> bool:
        match other:
            case Pair():
                return self.key < other.key
            case Key():
                return self.key < other
            case _:
                return NotImplemented

    def to_bytes(self) -> bytes:
        keytype = struct.pack(">B", self.key.ktype.value)
        payload = keytype + self.key.to_bytes() + self.value.to_bytes()
        payload = struct.pack("<I", len(payload)) + payload + self.padding
        logger.info(f"to_bytes: {payload=}")
        return payload

    @classmethod
    def from_bytes(cls, payload: bytes) -> Pair:

        if len(payload) < 4:
            raise ValueError(f"invalid pair length: {len(payload)=} < 4")

        size, keytype = struct.unpack("<IB", payload[:5])
        if len(payload) < 6 + size:
            raise ValueError(f"invalid pair length: {len(payload)=} < {6 + size=}")

        keytype = KeyType(keytype)
        key = Key.from_bytes(payload[5:5 + keytype.capacity])
        value = Value.from_bytes(payload[5 + keytype.capacity:4 + size])

        pair = cls(key=key, value=value)
        if pair.padding != payload[4 + size:4 + size + 2]:
            raise ValueError(f"invalid pair padding: {payload[5 + size:5 + size + 2]=} != {pair.padding=}")

        return pair


class AOLFileLayer(BaseFileLayer, BaseLayer):
    name = "aol"
    type = ord("A")

    def __iter__(self) -> Generator[Pair, None, None]:
        text = self.text

        while text:
            pair = Pair.from_bytes(text)
            yield pair

            text = text[len(pair):]

    def seek_to_tell(self):
        pos = self.fd.seek(0, os.SEEK_END)
        if pos < self.text_offset:
            self.fd.seek(self.text_offset)

    # ======== the general methods related on the layer meta ======== #
    def __contains__(self, key: Any) -> bool:
        return self.query(key) is not None

    # ======== the general methods related to data operations ======== #
    def count(self) -> int:
        pool = set()
        for pair in iter(self):
            if pair.value.is_deleted:
                pool -= {pair.key}
            else:
                pool |= {pair.key}

        return len(pool)

    @property
    def capacity(self) -> int:
        return len(list(self.iterate()))

    def insert(self, key: Key, value: Value, /, force: bool = False) -> Value | None:
        """insert the key-value pair into the layer."""
        if not force and key in self:
            raise DuplicateKey(key)

        pair = Pair(key=key, value=value)

        self.seek_to_tell()

        self.fd.write(pair.to_bytes())
        self.fd.flush()

    def delete(self, key: Key) -> bool:
        """insert the key-value pair into the layer which value mark as deleted."""
        value = Value(None)
        value.delete()

        pair = Pair(key=key, value=value)

        self.seek_to_tell()

        self.fd.write(pair.to_bytes())
        self.fd.flush()

    def query(self, key: Key) -> Value | None:
        value = None

        for pair in iter(self):
            if pair.key == key:
                value = pair.value

        return value

    # ======== the iteration methods related to data operations ======== #
    def iterate(self, /, desc: bool = True, based: Any = None) -> Generator[tuple[Key, Value], None, None]:
        if based is not None:
            raise ValueError(f"AOL does not support iterate with based: {based=}")

        pairs = sorted(iter(self), reverse=desc)
        yield from ((pair.key, pair.value) for pair in pairs)

    # ======== the authorized methods related to danger operations ======== #
    def purge(self):
        raise NotImplementedError("AOL does not support purge")
