from typing import Any
from typing import Generator

from papyrus.layers import Layer
from papyrus.layers import ThresholdLimit
from papyrus.settings import LayerSettings
from papyrus.types import Key
from papyrus.types import Value


class Storage:
    """
    the pseudo layer storage of Papyrus.

    the storage is a pseudo layer, which contains multiple layers, serve the incoming request
    as the normal layer.
    """
    def __init__(self, settings: LayerSettings, /, default_layer: LayerSettings | None = None, cached: bool = False):
        self._layers = [
            Layer.open(
                setting.uri,
                threshold=setting.threshold,
                cached=cached,
            ) for setting in settings
        ]

        self._default_layer = None
        if default_layer is not None:
            self._default_layer = Layer.open(
                url=default_layer.uri,
                threshold=default_layer.threshold,
                cached=cached,
            )

    def __len__(self) -> int:
        return self.count()

    @property
    def layers(self) -> list[Layer]:
        """list all the exists layers."""
        return self._layers

    @property
    def layer(self) -> Layer:
        """the first available layer."""
        for layer in self.layers:
            if not layer.is_full:
                return layer

        if self.default_layer is not None:
            layer = self.default_layer.dup()
            self._layers.append(layer)
            return layer

        raise ThresholdLimit("all layers are full")

    @property
    def default_layer(self) -> Layer | None:
        """the default layer."""
        return self._default_layer

    # ======== the general methods related on the layer meta ======== #
    def __contains__(self, key: Any) -> bool:
        """check the key is exists in the layer."""
        return any(key in layer for layer in self.layers)

    # ======== the general methods related to data operations ======== #
    def count(self) -> int:
        """
        The total number of items that the layer already hold.
        """
        return sum(layer.count() for layer in self.layers)

    @property
    def capacity(self) -> int:
        """
        The total number of items that the layer already hold, include the data
        that is marked as deleted.
        """
        return sum(layer.capacity for layer in self.layers)

    def insert(self, key: Any, value: Any, /, force: bool = False) -> Value | None:
        """call the insert method of the layer."""
        return self.layer.insert(Key(key), Value(value), force=force)

    def delete(self, key: Any) -> bool:
        """call the delete method of the layer."""
        return self.layer.delete(Key(key))

    def query(self, key: Any) -> Value | None:
        key = Key(key)
        for layer in self.layers:
            value = layer.query(key)
            if value is not None:
                return value

        return None

    # ======== the iteration methods related to data operations ======== #
    def iterate(self, /, desc: bool = True, based: Any = None) -> Generator[tuple[Key, Value], None, None]:
        """call the iterate method of the layer."""
        for layer in self.layers:
            yield from layer.iterate(desc=desc, based=based)

    # ======== the authorized methods related to danger operations ======== #
    def purge(self):
        """call the purge method of the layer."""
        for layer in self.layers:
            layer.purge()

    def unlink(self):
        """call the unlink method of the layer."""
        for layer in self.layers:
            layer.unlink()
