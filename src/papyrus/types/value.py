"""The Value is the arbitrary length of the variable."""
from __future__ import annotations

import enum
import zlib
from typing import Any

from ._base import Deserializable
from ._base import Serializable


@enum.unique
class ValueType(enum.Enum):
    """the type of the value."""
    STR = 1
    BIN = 2

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
    any length of the data. It has four parts:


    0         8        16       24       32
    +--------+--------+--------+--------+
    | vtype  |         length           |
    +-----------------------------------+
    ~           compressed data         ~
    +-----------------------------------+
    |              checksum             |
    +-----------------------------------+
    """

    def __init__(self, raw: Any):
        self._vtype = Value.classify(raw)
        self._raw = raw

    def __len__(self) -> int:
        match self.vtype:
            case ValueType.STR | ValueType.BIN:
                return len(self.raw)
            case _:
                raise NotImplementedError(f"cannot get length of {self.vtype}")

    def __eq__(self, other):
        match other:
            case Value():
                return self.vtype == other.vtype and self.raw == other.raw
            case _:
                return self.raw == other

    def __str__(self):
        return self.raw

    @staticmethod
    def classify(raw: Any) -> ValueType:
        match raw:
            case str():
                return ValueType.STR
            case bytes():
                return ValueType.BIN
            case _:
                raise NotImplementedError(f"cannot classify {raw} ({type(raw)}=)")

    @property
    def vtype(self) -> ValueType:
        return self._vtype

    @property
    def raw(self) -> Any:
        return self._raw

    @property
    def compressed_data(self) -> bytes:
        match self.vtype:
            case ValueType.STR:
                return zlib.compress(self.raw.encode())
            case ValueType.BIN:
                return zlib.compress(self.raw)
            case _:
                raise NotImplementedError(f"cannot compress {self.vtype}")

    def to_bytes(self) -> bytes:
        data = ((int(self.vtype) << 24) | len(self)).to_bytes(4, "big")
        data = data + self.compressed_data
        data = data + zlib.adler32(data).to_bytes(4, "big")

        return data

    @classmethod
    def from_bytes(cls, data: bytes) -> Value:
        if len(data) < 4:
            raise ValueError(f"the length of the data is too short: {len(data)=}")

        checksum = int.from_bytes(data[-4:], "big")
        if checksum != zlib.adler32(data[:-4]):
            raise ValueError(f"the checksum is not matched: {checksum=} <> {zlib.adler32(data[:-4])=}")

        hdr = int.from_bytes(data[:4], "big")
        vtype, length = ValueType(hdr >> 24), hdr & 0x00FFFFFF

        raw = zlib.decompress(data[4:-4])
        match vtype:
            case ValueType.STR:
                raw = raw.decode()
            case ValueType.BIN:
                pass
            case _:
                raise NotImplementedError(f"cannot decompress {vtype}")

        if len(raw) != length:
            raise ValueError(f"the length is not matched: {length=} <> {len(raw)=}")

        return cls(raw)
