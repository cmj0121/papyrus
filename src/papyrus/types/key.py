"""The Key is the known and fixed length type."""
from __future__ import annotations

import enum
import os
import random
import time
from typing import Any
from typing import Generator

from ._base import Deserializable
from ._base import Serializable


class CrockfordBase32:
    """the Crockford's Base32 algo"""
    ENCODING_TABLE = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

    @staticmethod
    def encode(key: int, size: int | None = None) -> str:
        """encode the key as Crockford's Base32 string."""

        chars = list(CrockfordBase32._encode(key))
        chars = chars[::-1]

        if size and len(chars) < size:
            padding = CrockfordBase32.ENCODING_TABLE[0] * (size - len(chars))
            chars.append(padding)

        return "".join(chars)

    @staticmethod
    def _encode(key: int) -> Generator[str, None, None]:
        while key > 0:
            yield CrockfordBase32.ENCODING_TABLE[key & 0x1F]
            key >>= 5

        return


class UniqueID(Serializable, Deserializable):
    """
    The UniqueID is the 128-bit unsigned integer.

    It is similar to the ULID but contains the process id and cluster id.

    The first 48 bits are the timestamp in milliseconds since the Unix epoch,
    then the following 8 bits are the process id, the next 8 bits are the
    cluster id, and the last 64 bits are random bits.

    +---------------------------------------------------------------+
    |                      32_bit_uint_time_high                    |
    +---------------------------------------------------------------+
    |     16_bit_uint_time_low      |   8 bit pid   |   8 bit cid   |
    +---------------------------------------------------------------+
    |                       32_bit_uint_random                      |
    +---------------------------------------------------------------+
    |                       32_bit_uint_random                      |
    +---------------------------------------------------------------+

    In this implementation, the primary key can generate 2^64 unique keys
    per millisecond per cluster per process.
    """
    MIN = 0x00000000000000000000000000000000
    MAX = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF

    LENGTH = 26

    def __init__(self, key: int):
        self._validate(key)
        self._key = key

    def __hash__(self):
        return hash(self._key)

    def __eq__(self, other):
        match other:
            case UniqueID():
                return self._key == other.key
            case _:
                return self._key == other

    def __lt__(self, other):
        match other:
            case UniqueID():
                return self.key < other.key
            case _:
                return self.key < other

    def __repr__(self):
        """show the key with verbose."""
        return f"#{str(self)} {self.timestamp=} {self.cluster_id=} {self.process_id=}"

    def __str__(self):
        """show the key as Crockford's Base32."""
        return CrockfordBase32.encode(self._key, size=self.LENGTH)

    @staticmethod
    def _validate(key: int):
        """validate the key is a 128-bit unsigned integer."""
        if not isinstance(key, int):
            raise TypeError(f"The key must be an integer: {key}")

        if key & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF == key:
            return

        raise ValueError(f"The key must be a 128-bit unsigned integer: {key}")

    @property
    def key(self) -> int:
        return self._key

    @staticmethod
    def new(
            timestamp: int | None = None,
            cluster_id: int | None = None,
            process_id: int | None = None,
            randomness: int | None = None,
    ) -> UniqueID:
        """
        create a new UniqueID by timestamp and cluster_id
        """
        timestamp = timestamp if timestamp is not None else int(time.time() * 1000)
        cluster_id = cluster_id if cluster_id is not None else random.randint(0, 255)
        process_id = process_id if process_id is not None else os.getpid() % 256
        randomness = randomness if randomness is not None else random.randint(0, 0xFFFFFFFFFFFFFFFF)

        if not isinstance(timestamp, int) or not 0 <= timestamp < (1 << 64):
            raise ValueError(f"timestamp must be an integer between 0 ~ 1<<64: {timestamp}")

        if not isinstance(cluster_id, int) or not 0 <= cluster_id < (1 << 8):
            raise ValueError(f"cluster_id must be an integer between 0 ~ 1<<8: {cluster_id}")

        if not isinstance(process_id, int) or not 0 <= process_id < (1 << 8):
            raise ValueError(f"process_id must be an integer between 0 ~ 1<<8: {process_id}")

        if not isinstance(randomness, int) or not 0 <= randomness < (1 << 64):
            raise ValueError(f"randomness must be an integer between 0 ~ 1<<64: {randomness}")

        key = (timestamp << 80) | (process_id << 72) | (cluster_id << 64) | randomness
        return UniqueID(key)

    @property
    def timestamp(self) -> int:
        """get the timestamp in milliseconds since the Unix epoch."""
        return self._key >> 80

    @property
    def cluster_id(self) -> int:
        """get the cluster id."""
        return (self._key >> 64) & 0xFF

    @property
    def process_id(self) -> int:
        """get the process id."""
        return (self._key >> 72) & 0xFF

    def to_bytes(self) -> bytes:
        """convert the key to bytes."""
        byteorder = "big"
        return self._key.to_bytes(16, byteorder=byteorder)

    @classmethod
    def from_bytes(cls, data: bytes) -> UniqueID:
        """convert the bytes to the key."""
        byteorder = "big"
        raw = int.from_bytes(data, byteorder=byteorder)
        return cls(raw)


class KeyType(enum.Enum):
    BOOL = 0    # the truth value, 1 byte
    WORD = 1    # the signed integer, 2 byte
    INT = 2     # the signed integer, 16 byte
    STR = 3     # the 63-bytes null-end string
    TEXT = 4    # the 255-bytes arbitrary string

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
            case int():
                return KeyType.INT
            case str() if len(raw) < 64:
                return KeyType.STR
            case str() if len(raw) < 256:
                return KeyType.TEXT
            case _:
                raise NotImplementedError(f"unknown key type: {raw} ({type(raw)}=)")


class Key(Serializable, Deserializable):
    """
    The known data length and pre-defined type key.

    It can be used as the primary key and the searchable index of data in the storage.
    At the same time, it can convert the key into the binary format with the fixed length,
    and convert from the binary format to the key.
    """
    def __init__(self, raw: Any, ktype: KeyType | None = None):
        self._raw = raw
        self._ktype = KeyType.detect(raw) if ktype is None else ktype
        self._value = None

    def __repr__(self):
        return f"<Key #{self.ktype} {self.value}>"

    def __str__(self):
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
    def raw(self) -> Any:
        return self._raw

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
            case KeyType.WORD | KeyType.INT:
                return Key(int(self.value), ktype)
            case KeyType.STR | KeyType.TEXT if self.ktype == KeyType.BOOL:
                return Key(str(int(self.value)), ktype)
            case KeyType.STR | KeyType.TEXT:
                return Key(str(self.value), ktype)
            case _:
                raise NotImplementedError(f"unknown key type: {ktype}")

    def to_bytes(self) -> bytes:
        match self.ktype:
            case KeyType.BOOL:
                return int(self.value).to_bytes(self.ktype.cap(), byteorder="big", signed=True)
            case KeyType.WORD | KeyType.INT:
                return self.value.to_bytes(self.ktype.cap(), byteorder="big", signed=True)
            case KeyType.STR | KeyType.TEXT:
                data = self.value.encode("utf-8")
                data = data + b"\x00" * (self.ktype.cap() - len(data))
                return data
            case _:
                raise NotImplementedError(f"unknown key type: {self.ktype}")

    @classmethod
    def from_bytes(cls, data: bytes) -> Key:
        match len(data):
            case 1:
                raw = bool(int.from_bytes(data, byteorder="big", signed=True))
                ktype = KeyType.BOOL
            case 2:
                raw = int.from_bytes(data, byteorder="big", signed=True)
                ktype = KeyType.WORD
            case 16:
                raw = int.from_bytes(data, byteorder="big", signed=True)
                ktype = KeyType.INT
            case 64:
                raw = data.decode("utf-8").rstrip("\x00")
                ktype = KeyType.STR
            case 256:
                raw = data.decode("utf-8").rstrip("\x00")
                ktype = KeyType.TEXT
            case _:
                raise NotImplementedError(f"unknown key type: {len(data)=}")

        return cls(raw, ktype)
