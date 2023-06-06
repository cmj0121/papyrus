"""The Key is the known and fixed length type."""
from __future__ import annotations

import os
import random
import time
from typing import Generator


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


class UniqueID:
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
