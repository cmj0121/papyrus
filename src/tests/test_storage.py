import pytest
from papyrus.storage import Storage
from papyrus.types import Data
from papyrus.types import Key


@pytest.mark.parametrize(
    "layers", [
        ["mem://test"],
    ],
)
class TestStorage:
    def test_storage_init(self, layers):
        storage = Storage(layers, cached=False)

        assert len(storage.layers) == len(layers)
        assert storage.layer.url == layers[0]

    @pytest.fixture
    def storage(self, layers):
        storage = Storage(layers, cached=False)
        yield storage

    @pytest.mark.parametrize("size", [10, 64, 1024])
    def test_storage_insert_multi(self, storage, size):
        keys = [Key(n) for n in range(size)]

        for key in keys:
            assert storage.latest(key) is None

            data = Data(key)
            storage.insert(data)
            assert storage.latest(key) == data
            assert storage.revision(key) == [data]

            storage.insert(data)
            assert len(storage.revision(key)) == 2

    def test_storage_insert_and_latest(self, storage):
        key = Key(True)
        data = Data(key)

        assert storage.latest(key) is None

        storage.insert(data)
        assert storage.latest(key) == data

    def test_storage_delete_and_latest(self, storage):
        key = Key(True)
        data = Data(key)

        storage.insert(data)
        assert storage.latest(key) == data

        storage.delete(key)
        assert storage.latest(key) is None

    def test_storage_revision(self, storage):
        keys = [Key(True), Key(True), Key(True)]
        data = [Data(key) for key in keys]

        for index, key in enumerate(keys):
            cur_data = data[index]
            storage.insert(cur_data)

            assert storage.latest(key) == cur_data
            assert len(storage.revision(key)) == index + 1

    def test_storage_search(self, storage, data):
        storage.insert(data)

        assert storage.latest(data.primary_key) == data

        for tkey, tvalue in data.tags.items():
            assert data.primary_key in storage.search(tkey, tvalue)
