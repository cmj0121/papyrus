import pytest
from papyrus.layers import DuplicateKey
from papyrus.layers import Layer
from papyrus.layers import ThresholdLimit


class TestLayerRegister:
    @pytest.mark.parametrize(
        "uri", [
            "mem://",
            "mem://test",
            "mem://test/foo"
            "mem://test/foo?name=mem",
        ],
    )
    def test_available_layer(self, uri):
        Layer.open(uri)

    def test_unavailable_layer(self):
        with pytest.raises(KeyError):
            Layer.open("unknown://")


@pytest.mark.parametrize(
    "uri", [
        "mem://",
    ],
)
class TestLayerBasic:
    @pytest.fixture
    def layer(self, uri):
        layer = Layer.open(uri, cached=False)
        yield layer

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
        assert layer.capacity == 1

    def test_layer_delete(self, layer, key, value):
        layer.insert(key, value)
        layer.delete(key)

        assert len(layer) == 0
        assert layer.capacity == 1

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


@pytest.mark.parametrize(
    "uri", [
        "mem://",
    ],
)
class TestLayerThreshold:
    @pytest.fixture
    def layer(self, uri):
        layer = Layer.open(uri, threshold=1, cached=False)
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
        assert layer.capacity == 1
