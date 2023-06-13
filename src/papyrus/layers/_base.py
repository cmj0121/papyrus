"""The abstract base class for all layers."""
from __future__ import annotations

import abc
from urllib.parse import ParseResult
from urllib.parse import urlparse

from papyrus.types import Data
from papyrus.types import Key
from papyrus.types import UniqueID


class BaseLayer(abc.ABC):
    """
    The abstract base class for all layers.

    Layers are the building blocks of the database. They are the
    """
    # the necessary fields for the layer
    name: str | None = None
    threshold: int | None = None

    # the registered layers
    _layers: dict[str, BaseLayer] = {}
    _instances: dict[str, BaseLayer] = {}

    def __init_subclass__(subcls, *args, **kwargs):
        if subcls.name is None:
            raise ValueError(f"{subcls.name} must have a name")

        if subcls.name in BaseLayer._layers:
            raise ValueError(f"{subcls.name} is already registered")

        BaseLayer._layers[subcls.name] = subcls
        super().__init_subclass__(*args, **kwargs)

    @classmethod
    def open(cls, url: str, threshold: int | None = None, /, cached: bool = True) -> BaseLayer:
        if url not in cls._instances or not cached:
            uri = urlparse(url)

            layer = BaseLayer._layers[uri.scheme]

            if not cached:
                return layer(uri, threshold=threshold)

            cls._instances[url] = layer(uri, threshold=threshold)

        return cls._instances[url]

    @classmethod
    def cache_clear(cls, name: str | None = None):
        """cache the layer instances."""
        if name is None:
            cls._instances.clear()
            return

        if name in cls._instances:
            del cls._instances[name]

    # ======== the general methods related on the layer meta ======== #
    @abc.abstractmethod
    def __init__(self, /, uri: ParseResult | None = None, threshold: int | None = None):
        """initialize the layer."""
        self._uri = uri
        self._threshold = threshold or self.threshold

    @property
    def url(self) -> str:
        """the url of the layer."""
        return self._uri.geturl()

    @abc.abstractmethod
    def __len__(self) -> int:
        """the number of available keys in the layer."""
        raise NotImplementedError(f"{self.__class__.__name__} must implement __len__()")

    @abc.abstractmethod
    def __contains__(self, search: Key | UniqueID) -> bool:
        """check the key is in the layer or not."""
        raise NotImplementedError(f"{self.__class__.__name__} must implement __contains__()")

    @abc.abstractproperty
    def cap(self) -> int:
        """
        The maximum number of items that the layer already hold, include the data
        that is marked as deleted.
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement cap()")

    # ======== the general methods related to data operations ======== #
    @abc.abstractmethod
    def insert(self, data: Data) -> UniqueID:
        """
        the insert operation.

        add new data into the layer, and return the unique id of the data. The key may
        be duplicated, but the unique id will be different and Papyrus will use the
        unique id to identify the data.
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement insert()")

    @abc.abstractmethod
    def delete(self, key: Key) -> UniqueID:
        """
        the delete operation.

        mark the data as deleted, and the data will not be returned by the layer. The
        data will be removed from the layer when the layer is purged.
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement delete()")

    @abc.abstractmethod
    def latest(self, key: Key) -> Data | None:
        """
        the query operation

        get the latest revision of data by the key. If the key is not in the layer, return None.
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement latest()")

    @abc.abstractmethod
    def revision(self, key: Key) -> list[Data]:
        """
        the query operation

        get all the revision of data by the key. If the key is not in the layer, return an empty list.
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement revision()")

    # ======== the authorized methods related to danger operations ======== #
    @abc.abstractmethod
    def raw(self, uid: UniqueID) -> Data | None:
        """get the data by the unique id."""
        raise NotImplementedError(f"{self.__class__.__name__} must implement raw()")

    @abc.abstractmethod
    def purge(self):
        """
        the purge operation.

        remove all the data that is marked as deleted from the layer.
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement purge()")
