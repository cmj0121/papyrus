"""The Key is the known and fixed length type."""
from __future__ import annotations

import enum
from typing import Any

from ._base import Deserializable
from ._base import Serializable


class KeyType(enum.Enum):
    BOOL = 0    # the truth value, 1 byte
    WORD = 1    # the signed integer, 2 byte
    INT = 2     # the signed integer, 8 byte
    UID = 3     # the unsigned integer, 16 byte
    STR = 4     # the 63-bytes null-end string
    TEXT = 5    # the 255-bytes arbitrary string

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    def __gt__(self, other):
        match other:
            case KeyType():
                return self.value > other.value
            case _:
                raise NotImplementedError(f"unknown key type: {other}")

    def cap(self):
        match self:
            case KeyType.BOOL:
                return 1
            case KeyType.WORD:
                return 2
            case KeyType.INT:
                return 8
            case KeyType.UID:
                return 16
            case KeyType.STR:
                return 64
            case KeyType.TEXT:
                return 256
            case _:
                raise NotImplementedError(f"unknown key type: {self}")

    @staticmethod
    def detect(raw: Any) -> KeyType:
        match raw:
            case bool():
                return KeyType.BOOL
            case int() if -32768 <= raw <= 32767:
                return KeyType.WORD
            case int() if -9223372036854775808 <= raw <= 9223372036854775807:
                return KeyType.INT
            case int() if 0 <= raw <= 340282366920938463463374607431768211455:
                return KeyType.UID
            case str() if len(raw) < 64:
                return KeyType.STR
            case str() if len(raw) < 256:
                return KeyType.TEXT
            case _:
                raise NotImplementedError(f"unknown key type: {raw} ({type(raw)}=)")

    def cast(self, raw: Any) -> Any:
        match self:
            case KeyType.BOOL:
                value = bool(raw)
            case KeyType.WORD | KeyType.INT | KeyType.UID:
                value = int(raw)
            case KeyType.STR | KeyType.TEXT:
                value = str(raw)
            case _:
                raise NotImplementedError(f"unknown key type: {self}")
        return value


class Key(Serializable, Deserializable):
    """
    The known data length and pre-defined type key.

    It can be used as the primary key and the searchable index of data in the storage.
    At the same time, it can convert the key into the binary format with the fixed length,
    and convert from the binary format to the key.
    """
    def __init__(self, raw: Any, ktype: KeyType | None = None):
        match isinstance(raw, Key):
            case True:
                self._ktype = raw.ktype
                self._value = raw.value
            case False:
                self._ktype = KeyType.detect(raw) if ktype is None else ktype
                self._value = self._ktype.cast(raw)

    def __repr__(self):
        """show the human-readable representation of the key."""
        return f"<Key #{self.ktype} {self.value}>"

    def __str__(self):
        """show the raw value as string."""
        return str(self.value)

    def __eq__(self, other):
        match other:
            case Key():
                ktype = max(self.ktype, other.ktype)
                return self.cast(ktype).value == other.cast(ktype).value
            case _:
                return self.value == other

    def __lt__(self, other):
        match other:
            case Key():
                ktype = max(self.ktype, other.ktype)
                return self.cast(ktype).value < other.cast(ktype).value
            case _:
                return self.value < other

    def __hash__(self):
        return hash(self.value)

    @property
    def ktype(self) -> KeyType:
        return self._ktype

    @property
    def value(self) -> Any:
        if self._value is None:
            match self.ktype:
                case KeyType.BOOL:
                    self._value = bool(self.raw)
                case KeyType.WORD | KeyType.INT:
                    self._value = int(self.raw)
                case KeyType.STR | KeyType.TEXT:
                    self._value = str(self.raw)
                case _:
                    raise NotImplementedError(f"unknown key type: {self.ktype}")

        return self._value

    def cast(self, ktype: KeyType) -> Key:
        match ktype:
            case KeyType.BOOL:
                return Key(bool(self.value), ktype)
            case KeyType.WORD | KeyType.INT | KeyType.UID:
                return Key(int(self.value), ktype)
            case KeyType.STR | KeyType.TEXT if self.ktype == KeyType.BOOL:
                return Key(str(int(self.value)), ktype)
            case KeyType.STR | KeyType.TEXT:
                return Key(str(self.value), ktype)
            case _:
                raise NotImplementedError(f"unknown key type: {ktype}")

    # ======== Serializable ========
    def to_bytes(self) -> bytes:
        match self.ktype:
            case KeyType.BOOL:
                return int(self.value).to_bytes(self.ktype.cap(), byteorder="big", signed=True)
            case KeyType.WORD | KeyType.INT | KeyType.UID:
                return self.value.to_bytes(self.ktype.cap(), byteorder="big", signed=True)
            case KeyType.STR | KeyType.TEXT:
                data = self.value.encode("utf-8")
                data = data + b"\x00" * (self.ktype.cap() - len(data))
                return data
            case _:
                raise NotImplementedError(f"unknown key type: {self.ktype}")

    # ======== Deserializable ========
    @classmethod
    def from_bytes(cls, data: bytes) -> Key:
        match len(data):
            case 1:
                raw = bool(int.from_bytes(data, byteorder="big", signed=True))
                ktype = KeyType.BOOL
            case 2:
                raw = int.from_bytes(data, byteorder="big", signed=True)
                ktype = KeyType.WORD
            case 8:
                raw = int.from_bytes(data, byteorder="big", signed=True)
                ktype = KeyType.INT
            case 16:
                raw = int.from_bytes(data, byteorder="big", signed=True)
                ktype = KeyType.UID
            case 64:
                raw = data.decode("utf-8").rstrip("\x00")
                ktype = KeyType.STR
            case 256:
                raw = data.decode("utf-8").rstrip("\x00")
                ktype = KeyType.TEXT
            case _:
                raise NotImplementedError(f"unknown key type: {len(data)=}")

        return cls(raw, ktype)
