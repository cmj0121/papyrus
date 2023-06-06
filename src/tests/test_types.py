import os
import time

import pytest
from papyrus.types import UniqueID
from papyrus.types.key import CrockfordBase32


class TestUniqueID:
    def test_new_key(self):
        key = UniqueID.new()

        assert key.process_id == os.getpid() % 256
        assert abs(int(time.time() * 1000) - key.timestamp) < 10

    def test_new_zero_key(self):
        key = UniqueID.new(
            timestamp=0,
            cluster_id=0,
            process_id=0,
            randomness=0,
        )

        assert key == UniqueID.MIN, key
        assert str(key) == "00000000000000000000000000"
        assert key.timestamp == 0
        assert key.process_id == 0
        assert key.cluster_id == 0

    def test_rand_key(self, faker):
        raw = faker.pyint(min_value=UniqueID.MIN, max_value=UniqueID.MAX)
        key = UniqueID(raw)

        assert key == raw
        assert str(key) == CrockfordBase32.encode(raw)

    def test_min_key(self):
        key = UniqueID(UniqueID.MIN)

        assert key == 0
        assert str(key) == "00000000000000000000000000"

    def test_max_key(self):
        key = UniqueID(UniqueID.MAX)

        assert key == UniqueID.MAX
        assert str(key) == "7ZZZZZZZZZZZZZZZZZZZZZZZZZ"

    def test_invalid_key_type(self):
        with pytest.raises(TypeError):
            UniqueID("invalid")

    def test_signed_key_type(self):
        with pytest.raises(ValueError):
            UniqueID(-1)

    def test_too_large_key_type(self):
        with pytest.raises(ValueError):
            UniqueID(UniqueID.MAX + 1)
