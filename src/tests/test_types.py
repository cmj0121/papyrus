import os
import time

import pytest
from papyrus.types import Key
from papyrus.types import KeyType
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


class TestKeyType:
    @pytest.mark.parametrize(
        "raw", [
            True,
            False,
            0,
            1,
            -1,
            255,
            -256,
            32767,
            -32768,
            65535,
            -65536,
            2147483647,
            -2147483648,
            4294967295,
            -4294967296,
            9223372036854775807,
            -9223372036854775808,
            18446744073709551615,
            -18446744073709551616,
            "",
            "a",
            "a" * 63,
            "a" * 64,
            "a" * 255,
        ],
    )
    def test_key_cast_detect(self, raw):
        key = Key(raw)

        assert key == raw
        assert key.ktype == KeyType.detect(raw)


class TestKey:
    def test_truth_key(self, faker):
        raw = faker.pybool()
        key = Key(raw)

        assert key == raw
        assert key.ktype == KeyType.BOOL

    def test_small_integer_key(self, faker):
        raw = faker.pyint(min_value=-256, max_value=255)
        key = Key(raw)

        assert key == raw
        assert key.ktype == KeyType.BYTE

    def test_integer_key(self, faker):
        raw = faker.pyint(min_value=32768, max_value=65535)
        key = Key(raw)

        assert key == raw
        assert key.ktype == KeyType.INT

    def test_str_key(self, faker):
        raw = faker.pystr()
        key = Key(raw)

        assert key == raw
        assert key.ktype == KeyType.STR

    def test_text_key(self, faker):
        raw = faker.pystr(min_chars=65, max_chars=256)
        key = Key(raw)

        assert key == raw
        assert key.ktype == KeyType.TEXT

    def test_truth_key_compare(self):
        x = Key(False)
        y = Key(True)

        assert x < y
