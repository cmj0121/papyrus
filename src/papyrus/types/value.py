"""The Value is the arbitrary length of the variable."""
from __future__ import annotations

import enum
import struct
import zlib
from typing import Any

from ._base import Deserializable
from ._base import Serializable


@enum.unique
class ValueType(enum.Enum):
    """the type of the value."""
    NIL = 0
    RAW = 1
    CMP = 2
    DEL = 3

    def __int__(self) -> int:
        return self.value

    def to_bytes(self) -> bytes:
        return int(self).to_bytes(1, "big")

    @classmethod
    def from_bytes(cls, data: bytes) -> ValueType:
        return cls(int.from_bytes(data, "big"))


class Value(Serializable, Deserializable):
    """
    the arbitrary length of the variable.

    The `Value` instance is the arbitrary length of the variable, which can store
    any length of the data. It has the following fields:

        - type: the category of the value.
        - size: the total size in bytes of the data.
        - data: the stored data.
        - padding: the padding bytes to align and make the total size is multiple of 32.
        - checksum: the checksum of the data.

    0        8       16     24      32
    +-------+-------+-------+-------+
    | type  |     size              |
    +-------+-------+-------+-------+
    ~             data              ~
    +-------+-------+-------+-------+
    ~             padding           ~
    +-------+-------+-------+-------+
    |             checksum          |
    +-------+-------+-------+-------+
    """

    def __init__(self, raw: bytes | None, vtype: ValueType | None = None):
        self._raw = raw
        self._vtype = (ValueType.NIL if raw is None else ValueType.RAW) if vtype is None else vtype

        if self.raw and len(self.raw) > 0x1000000:
            self._vtype = ValueType.CMP

    def __repr__(self):
        return f"<Value: {self.vtype}> {self.raw}"

    def __str__(self):
        return f"{self.raw}"

    def __len__(self) -> int:
        match self.vtype:
            case ValueType.NIL | ValueType.DEL:
                return 0
            case ValueType.RAW | ValueType.CMP:
                return self._raw.__len__()
            case _:
                raise NotImplementedError(f"unknown value type: {self.vtype}")

    def __eq__(self, other):
        match other:
            case Value():
                return self.vtype == other.vtype and self.raw == other.raw
            case _:
                return self.raw == other

    @property
    def vtype(self) -> ValueType:
        """the category of the value."""
        return self._vtype

    @property
    def raw(self) -> Any:
        """the stored data."""
        return self._raw

    @property
    def compressed_data(self) -> bytes:
        """get the compressed raw data."""
        return zlib.compress(self.raw)

    @classmethod
    def checksum(cls, data: bytes) -> int:
        """calculate the checksum of the data."""
        return zlib.adler32(data)

    # ======== Serializable ========
    def to_bytes(self) -> bytes:
        """serialize the value to bytes."""
        match self.vtype:
            case ValueType.NIL | ValueType.DEL:
                head = (int(self.vtype) << 24)
                data = b""
            case ValueType.RAW:
                data = self.raw
                head = (int(self.vtype) << 24) + len(data)
            case ValueType.CMP:
                data = self.compressed_data
                head = (int(self.vtype) << 24) + len(data)
            case _:
                raise NotImplementedError(f"unknown value type: {self.vtype}")

        payload = struct.pack(">I", head) + data
        padding = b"\x00" * (32 - len(payload) % 32)

        return payload + padding + struct.pack(">I", self.checksum(payload + padding))

    # ======== Deserializable ========
    @classmethod
    def from_bytes(self, data: bytes) -> Value:
        if len(data) < 32:
            raise ValueError(f"invalid value length: {len(data)=} < 32")

        head, = struct.unpack(">I", data[:4])
        vtype, size = ValueType(head >> 24), head & 0xFFFFFF

        if len(data) < size + 4:
            raise ValueError(f"invalid value length: {len(data)=} < {size + 4=}")

        payload = data[4:4 + size]
        padding = 32 - (4 + size) % 32
        checksum = data[4 + size + padding:]

        if checksum != struct.pack(">I", self.checksum(data[:4 + size + padding])):
            raise ValueError("invalid value checksum: {checksum=} != {self.checksum(data[:4 + size + padding])=}")

        match vtype:
            case ValueType.NIL:
                value = Value(None)
            case ValueType.DEL:
                value = Value(None, vtype=ValueType.DEL)
            case ValueType.RAW:
                value = Value(payload)
            case ValueType.CMP:
                value = Value(zlib.decompress(payload), vtype=ValueType.CMP)
            case _:
                raise NotImplementedError(f"unknown value type: {vtype}")

        return value
