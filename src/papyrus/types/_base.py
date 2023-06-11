from __future__ import annotations

import abc


class Serializable(abc.ABC):
    @abc.abstractmethod
    def to_bytes(self) -> bytes:
        raise NotImplementedError(f"{self.__class__.__name__} must implement to_bytes()")


class Deserializable(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def from_bytes(cls, data: bytes) -> Deserializable:
        raise NotImplementedError(f"{cls.__class__.__name__} must implement from_bytes()")
