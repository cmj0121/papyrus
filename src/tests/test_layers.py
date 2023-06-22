import os
import shutil
from pathlib import Path

import pytest
from papyrus.layers import DuplicateKey
from papyrus.layers import Layer
from papyrus.layers import ThresholdLimit


def test_unavailable_layer():
    with pytest.raises(KeyError):
        Layer.open("unknown://")


@pytest.mark.parametrize("scheme", ["mem", "aol"])
class TestLayerBase:
    def setup_method(self):
        self.ws = Path(f"test_ws_{os.getpid()}")
        self.ws.mkdir(exist_ok=True)

    def teardown_method(self):
        shutil.rmtree(self.ws)

    @pytest.fixture
    def uri(self, scheme):
        yield f"{scheme}://{self.ws}/test_register.{scheme}"

    @pytest.fixture
    def layer(self, uri):
        yield Layer.open(uri, cached=False)


class TestLayerRegister(TestLayerBase):
    def test_available_layer(self, uri):
        Layer.open(uri, cached=False)


class TestLayerBasic(TestLayerBase):
    def test_empty_layer(self, uri, layer):
        assert len(layer) == 0
        assert layer.capacity == 0

    def test_layer_insert(self, layer, key, value):
        layer.insert(key, value)

        assert len(layer) == 1
        assert layer.capacity == 1

    def test_layer_insert_exists(self, layer, key, value, value2):
        layer.insert(key, value)

        assert len(layer) == 1
        assert layer.capacity == 1

        with pytest.raises(DuplicateKey):
            layer.insert(key, value2)

        assert len(layer) == 1
        assert layer.capacity == 1

    def test_layer_insert_force(self, layer, key, value, value2):
        layer.insert(key, value)

        assert len(layer) == 1
        assert layer.capacity == 1

        layer.insert(key, value2, force=True)

        assert len(layer) == 1
        assert layer.capacity in (1, 2)

    def test_layer_delete(self, layer, key, value):
        layer.insert(key, value)
        layer.delete(key)

        assert len(layer) == 0
        assert layer.capacity in (1, 2)

    def test_layer_query(self, layer, key, value):
        layer.insert(key, value)
        assert layer.query(key) == value

        layer.delete(key)
        assert layer.query(key).is_deleted

    def test_layer_iterate(self, layer, key, value):
        layer.insert(key, value)
        rows = list(layer.iterate())

        assert rows == [(key, value)]

    def test_layer_purge(self, layer, key, value):
        if layer.name in ("aol"):
            pytest.skip("AOL does not support purge()")

        layer.insert(key, value)

        layer.purge()
        assert len(layer) == 1
        assert layer.capacity == 1

        layer.delete(key)
        layer.purge()
        assert len(layer) == 0
        assert layer.capacity == 0

        layer.purge()

    def test_layer_unlink(self, layer, key, value):
        layer.insert(key, value)

        layer.unlink()
        assert len(layer) == 0
        assert layer.capacity == 0

        layer.unlink()


class TestLayerThreshold(TestLayerBase):
    @pytest.fixture
    def threshold(self) -> int:
        return 1

    @pytest.fixture
    def layer(self, uri, threshold):
        layer = Layer.open(uri, threshold=threshold, cached=False)

        if layer.name in ("aol"):
            pytest.skip("AOL does not support threshold")

        yield layer

    def test_empty_layer(self, uri, layer):
        assert len(layer) == 0
        assert layer.capacity == 0

    def test_layer_insert(self, layer, key, value):
        layer.insert(key, value)

        assert len(layer) == 1
        assert layer.capacity == 1

    def test_layer_insert_hit_threshold(self, layer, key, key2, value):
        layer.insert(key, value)

        assert len(layer) == 1
        assert layer.capacity == 1

        with pytest.raises(ThresholdLimit):
            layer.insert(key2, value)

    def test_layer_delete(self, layer, key, value):
        layer.insert(key, value)
        layer.delete(key)

        assert len(layer) == 0
        assert layer.capacity in (1, 2)
