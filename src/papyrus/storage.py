from __future__ import annotations

from papyrus.layers import Layer
from papyrus.settings import LayerSettings
from papyrus.types import Data
from papyrus.types import Key
from papyrus.types import UniqueID


class Storage:
    def __init__(self, layers: list[str], /, cached: bool = False):
        self._layers = [Layer.open(uri, cached=cached) for uri in layers]

    @classmethod
    def open(cls, settings: LayerSettings) -> Storage:
        uris = [layer.uri for layer in settings]
        return cls(uris)

    @property
    def layer(self) -> Layer:
        """the available layer of storage"""
        return self._layers[0]

    @property
    def layers(self) -> list[Layer]:
        """the available layers of storage"""
        return self._layers

    # ======== the general methods related to data operations ======== #
    def insert(self, data: Data) -> UniqueID:
        """insert a new data into the storage"""
        return self.layer.insert(data)

    def delete(self, key: Key) -> UniqueID:
        """delete a data from the storage"""
        return self.layer.delete(key)

    def latest(self, key: Key) -> Data | None:
        """get the latest data of the key"""
        return self.layer.latest(key)

    def revisions(self, key: Key) -> list[Data]:
        """get all revisions of the key"""
        revisions = [r for layer in self.layers for r in layer.revisions(key)]
        return revisions
