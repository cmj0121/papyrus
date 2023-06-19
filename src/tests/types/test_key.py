import random

import pytest
from papyrus.types import Key
from papyrus.types import KeyType


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
        assert key.ktype == KeyType.WORD

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

    @pytest.mark.parametrize("size", [10, 100, 1000])
    def test_sortable(self, size: int):
        raws = sorted([Key(i) for i in range(size)])
        data = raws[:]
        random.shuffle(data)

        assert raws == sorted(raws)
        assert raws == sorted(data)

    def test_random_key(self, key):
        assert key == Key.from_bytes(key.to_bytes())
        assert key == Key(key)
