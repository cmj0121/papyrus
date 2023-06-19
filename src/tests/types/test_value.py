import pytest
from papyrus.types import Value
from papyrus.types.value import ValueType


class TestValueType:
    @pytest.mark.parametrize("vtype", ValueType)
    def test_value_type_convert(self, vtype):
        assert vtype.to_bytes()[0] == int(vtype)
        assert ValueType.from_bytes(vtype.to_bytes()) == vtype


class TestValue:
    def test_nil_value(self):
        value = Value(None)

        assert value.raw is None
        assert value.vtype == ValueType.NIL
        assert len(value) == 0
        assert value == Value.from_bytes(value.to_bytes())

    @pytest.mark.parametrize(
        "raw", [
            b"",
            b"test",
            b"test" * 1024,
        ],
    )
    def test_raw_value(self, raw):
        value = Value(raw)

        assert value == raw
        assert value.raw == raw
        assert value.vtype == ValueType.RAW
        assert len(value) == len(raw)
        assert value == Value.from_bytes(value.to_bytes())

    @pytest.mark.parametrize(
        "raw", [
            b"",
            b"test",
            b"test" * 1024,
        ],
    )
    def test_compressed_value(self, raw):
        value = Value(raw, vtype=ValueType.CMP)

        assert value == raw
        assert value.raw == raw
        assert value.vtype == ValueType.CMP
        assert len(value) == len(raw)
        assert value == Value.from_bytes(value.to_bytes())

    def test_random_value(self, value):
        assert value == Value.from_bytes(value.to_bytes())
        assert value == Value(value)
