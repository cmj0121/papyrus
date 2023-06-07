import string

import pytest
from papyrus.layers import Data
from papyrus.layers import MemLayer
from papyrus.types import Key
from papyrus.types import UniqueID


@pytest.mark.parametrize("layercls", [MemLayer])
class TestLayer:
    TEST_KEYS = [
        (True, False),
        range(10),
        range(1024),
        string.ascii_letters,
        (*range(16), *string.ascii_letters),
    ]

    def test_empty_layer(self, layercls):
        layer = layercls()

        assert len(layer) == 0
        assert layer.cap == 0

    @pytest.mark.parametrize("raws", TEST_KEYS)
    def test_insert_value(self, layercls, raws):
        layer = layercls()
        datas = [Data(Key(key)) for key in raws]

        for index, data in enumerate(datas):
            assert data.primary_key not in layer

            uid = layer.insert(data)

            assert isinstance(uid, UniqueID)
            assert data.primary_key in layer
            assert uid in layer
            assert len(layer) == index + 1
            assert layer.cap == index + 1

    @pytest.mark.parametrize("raws", TEST_KEYS)
    def test_delete_value(self, layercls, raws):
        layer = layercls()
        datas = [Data(Key(key)) for key in raws]

        [layer.insert(data) for data in datas]

        assert len(layer) == len(raws)
        assert layer.cap == len(raws)

        for index, data in enumerate(datas):
            assert data.primary_key in layer

            layer.delete(data.primary_key)

            assert data.primary_key not in layer
            assert len(layer) == len(raws) - index - 1
            assert layer.cap == len(raws) + index + 1

    @pytest.mark.parametrize("raws", TEST_KEYS)
    def test_latest_value(self, layercls, raws):
        layer = layercls()
        datas = [Data(Key(key)) for key in raws]

        for data in datas:
            assert layer.latest(data.primary_key) is None

            layer.insert(data)
            assert layer.latest(data.primary_key) is data

            layer.delete(data.primary_key)
            assert layer.latest(data.primary_key) is None

    @pytest.mark.parametrize("raws", TEST_KEYS)
    def test_revisions(self, layercls, raws):
        layer = layercls()
        datas = [Data(Key(key)) for key in raws]

        for data in datas:
            assert layer.revisions(data.primary_key) == []

            layer.insert(data)
            assert layer.revisions(data.primary_key) == [data]

            layer.delete(data.primary_key)
            assert len(layer.revisions(data.primary_key)) == 2
            assert layer.revisions(data.primary_key)[0].is_deleted is True
            assert layer.revisions(data.primary_key)[1] is data

    @pytest.mark.parametrize("raws", TEST_KEYS)
    def test_purge(self, layercls, raws):
        layer = layercls()
        datas = [Data(Key(key)) for key in raws]

        for data in datas:
            layer.insert(data)
            layer.delete(data.primary_key)

            assert data.primary_key not in layer
            assert len(layer) == 0
            assert layer.cap == 2

            layer.purge()

            assert data.primary_key not in layer
            assert len(layer) == 0
            assert layer.cap == 0
