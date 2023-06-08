import os
import random
import time

import pytest
from papyrus.types import Key
from papyrus.types import KeyType
from papyrus.types import UniqueID
from papyrus.types._base import Deserializable
from papyrus.types._base import Serializable
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

    @pytest.mark.parametrize("size", [10, 100, 1000])
    def test_sortable(self, size: int):
        raws = sorted([UniqueID.new() for _ in range(size)])
        data = raws[:]
        random.shuffle(data)

        assert raws == sorted(raws)
        assert raws == sorted(data)

    def test_bench_new_uid(self, benchmark):
        benchmark(UniqueID.new)

    def test_bench_uid_serialize(self, benchmark):
        uid = UniqueID.new()
        benchmark(uid.to_bytes)

    def test_bench_uid_deserialize(self, benchmark):
        uid = UniqueID.new()
        benchmark(UniqueID.from_bytes, uid.to_bytes())


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

    @pytest.mark.parametrize("size", [10, 100, 1000])
    def test_sortable(self, size: int):
        raws = sorted([Key(i) for i in range(size)])
        data = raws[:]
        random.shuffle(data)

        assert raws == sorted(raws)
        assert raws == sorted(data)


class TestSerializable:
    def test_serialize_without_impl(self):
        class Test(Serializable):
            pass

        with pytest.raises(TypeError):
            Test().to_bytes()

    def test_uid(self):
        uid = UniqueID.new()
        data = uid.to_bytes()

        assert len(data) == 16

    def test_uid_nil(self):
        uid = UniqueID(UniqueID.MIN)
        data = uid.to_bytes()

        assert len(data) == 16
        assert data == b"\x00" * 16

    def test_uid_max(self):
        uid = UniqueID(UniqueID.MAX)
        data = uid.to_bytes()

        assert len(data) == 16
        assert data == b"\xff" * 16

    @pytest.mark.parametrize("ktype", KeyType)
    def test_key(self, ktype):
        key = Key(True).cast(ktype)
        data = key.to_bytes()

        assert len(data) == key.ktype.cap()

    @pytest.mark.parametrize(
        "value", [
            True,
            False,
            0,
            1,
            -1,
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
        ],
    )
    def test_bench_key_serialize(self, benchmark, value):
        key = Key(value)
        benchmark(key.to_bytes)


class TestDeserializable:
    def test_deserialize_without_impl(self):
        class Test(Deserializable):
            pass

        with pytest.raises(TypeError):
            Test().to_bytes()

    def test_uid(self):
        uid = UniqueID.new()
        assert uid == UniqueID.from_bytes(uid.to_bytes())

    def test_uid_nil(self):
        uid = UniqueID(UniqueID.MIN)
        assert uid == UniqueID.from_bytes(uid.to_bytes())

    def test_uid_max(self):
        uid = UniqueID(UniqueID.MAX)
        assert uid == UniqueID.from_bytes(uid.to_bytes())

    @pytest.mark.parametrize("ktype", KeyType)
    def test_key(self, ktype):
        key = Key(True).cast(ktype)
        assert key == Key.from_bytes(key.to_bytes())

    @pytest.mark.parametrize(
        "value", [
            True,
            False,
            0,
            1,
            -1,
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
        ],
    )
    def test_bench_key_deserialize(self, benchmark, value):
        key = Key(value)
        benchmark(key.from_bytes, key.to_bytes())
