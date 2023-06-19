from functools import cache
from pathlib import Path

import pytest
from papyrus.layers import DuplicateKey
from papyrus.settings import Settings
from papyrus.storage import Storage


@cache
def load_testing_config() -> list[Settings]:
    """load the testing config"""
    config_path = Path(__file__).parent.parent / "features/files"

    settings = []
    for path in config_path.glob("*.yml"):
        with path.open("r") as fd:
            settings.append(Settings.parse_raw(fd.read()))

    return settings


@pytest.mark.parametrize("config", load_testing_config())
class TestStorage:
    @pytest.fixture
    def storage(self, config) -> Storage:
        """the storage instance"""
        return Storage(config.layers, default_layer=config.default_layer, cached=False)

    def test_empty_storage(self, storage):
        assert len(storage) == 0
        assert storage.capacity == 0
        assert not storage.layer.is_full
        assert storage.layers

    def test_storage_insert(self, storage, key, value):
        storage.insert(key, value)

        assert len(storage) == 1
        assert storage.capacity == 1
        assert storage.query(key) == value

    def test_storage_insert_exists(self, storage, key, value, value2):
        storage.insert(key, value)

        with pytest.raises(DuplicateKey):
            storage.insert(key, value2)

        assert len(storage) == 1
        assert storage.capacity == 1
        assert storage.query(key) == value

    def test_storage_insert_force(self, storage, key, value, value2):
        storage.insert(key, value)
        storage.insert(key, value2, force=True)

        assert len(storage) == 1
        assert storage.capacity == 1
        assert storage.query(key) == value2

    def test_storage_delete(self, storage, key, value):
        storage.insert(key, value)
        storage.delete(key)

        assert len(storage) == 0
        assert storage.capacity == 1
        assert storage.query(key).is_deleted

    def test_storage_purge(self, storage, key, value):
        storage.insert(key, value)
        storage.delete(key)
        storage.purge()

        assert len(storage) == 0
        assert storage.capacity == 0
        assert storage.query(key) is None

    def test_storage_unlink(self, storage, key, value):
        storage.insert(key, value)
        storage.unlink()

        assert len(storage) == 0
        assert storage.capacity == 0
        assert storage.query(key) is None
