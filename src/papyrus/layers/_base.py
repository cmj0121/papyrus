"""The abstract base class for all layers."""
from __future__ import annotations

import abc
from typing import Any
from typing import Generator
from urllib.parse import ParseResult
from urllib.parse import urlparse

from papyrus.types import Key
from papyrus.types import Value


class ThresholdLimit(ValueError):
    """hit the threshold limit"""


class DuplicateKey(ValueError):
    """the key is already exists"""


class BaseLayer(abc.ABC):
    """
    The abstract base class for all layers.

    Layers are the building blocks of the database. They are the
    """
    # the necessary fields for the layer
    name: str | None = None
    threshold: int | None = None

    # the registered layers and the cached instances
    _register_layers: dict[str, BaseLayer] = {}
    _cached_instance: dict[str, BaseLayer] = {}

    def __init_subclass__(subcls, *args, **kwargs):
        if subcls.name is None:
            raise ValueError(f"{subcls.__class__.__name__} must define the unique name")

        if subcls.name in BaseLayer._register_layers:
            cls = BaseLayer._register_layers[subcls.name]
            raise ValueError(f"{subcls.name} is already registered via {cls.__name__}")

        BaseLayer._register_layers[subcls.name] = subcls
        super().__init_subclass__(*args, **kwargs)

    @classmethod
    def open(cls, url: str, /, threshold: int | None = None, cached: bool = True) -> BaseLayer:
        if url not in cls._cached_instance or not cached:
            uri = urlparse(url)

            layer = BaseLayer._register_layers[uri.scheme]

            if not cached:
                return layer(uri, threshold=threshold)

            cls._cached_instance[url] = layer(uri, threshold=threshold)

        return cls._cached_instance[url]

    # ======== the general methods related on the layer meta ======== #
    @abc.abstractmethod
    def __init__(self, /, uri: ParseResult | None = None, threshold: int | None = None):
        """initialize the layer."""
        self._uri = uri
        self.threshold = self.threshold if threshold is None else threshold

    def __len__(self) -> int:
        return self.count()

    def __repr__(self):
        """the representation of the layer."""
        return f"<{self.__class__.__name__} {self.url}>"

    @abc.abstractmethod
    def __contains__(self, key: Any) -> bool:
        """check the key is exists in the layer."""
        raise NotImplementedError(f"{self.__class__.__name__} must implement __contains__()")

    @property
    def url(self) -> str:
        """the url of the layer."""
        return self._uri.geturl()

    @property
    def is_full(self) -> bool:
        """check the layer is full."""
        if self.threshold is not None and self.capacity >= self.threshold:
            return True

        return False

    # ======== the general methods related to data operations ======== #
    @abc.abstractproperty
    def count(self) -> int:
        """
        The total number of items that the layer already hold.
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement count()")

    @abc.abstractproperty
    def capacity(self) -> int:
        """
        The total number of items that the layer already hold, include the data
        that is marked as deleted.
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement capacity()")

    @abc.abstractmethod
    def insert(self, key: Key, value: Value, /, force: bool = False) -> Value | None:
        """
        the insert operation.

        add new key-value pair into the layer, and return the old value if the key
        already exists with option force=True, otherwise return None.

        It may raise

            - the ThresholdLimit exception if the layer is full.
            - the DuplicateKey exception if the key already exists with option force=False.
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement insert()")

    @abc.abstractmethod
    def delete(self, key: Key) -> bool:
        """
        the delete operation.

        mark the data as deleted, and return the True if the key exists, otherwise
        return False.
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement delete()")

    @abc.abstractmethod
    def query(self, key: Key) -> Value | None:
        """
        the query operation.

        get the value by the key, and return the value if the key exists, otherwise
        return None.
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement search()")

    # ======== the iteration methods related to data operations ======== #
    @abc.abstractmethod
    def iterate(self, /, desc: bool = True, based: Any = None) -> Generator[tuple[Key, Value], None, None]:
        """
        the iterate operation.

        iterate all the key-value pairs in the layer, with the given order.
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement iterate()")

    # ======== the authorized methods related to danger operations ======== #
    @abc.abstractmethod
    def purge(self):
        """
        the purge operation.

        remove all the data that is marked as deleted from the layer.
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement purge()")

    @abc.abstractmethod
    def unlink(self):
        """
        the unlink operation.

        remove all the data from the layer, and remove the persistent storage if exists.
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement unlink()")
