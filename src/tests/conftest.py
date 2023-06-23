import random

import pytest
from papyrus.types.key import Key
from papyrus.types.key import KeyType
from papyrus.types.value import Value
from papyrus.types.value import ValueType


@pytest.fixture
def key(faker):
    ktype = random.choice(list(KeyType))

    match ktype:
        case KeyType.BOOL:
            yield Key(faker.pybool(), ktype)
        case KeyType.WORD | KeyType.INT | KeyType.UID:
            yield Key(faker.pyint(), ktype)
        case KeyType.STR | KeyType.TEXT:
            yield Key(faker.pystr(), ktype)


@pytest.fixture
def value(faker):
    vtype = random.choice(list(ValueType))

    match vtype:
        case ValueType.NIL:
            yield Value(None)
        case ValueType.DEL | ValueType.RAW:
            yield Value(faker.binary())
        case ValueType.CMP:
            yield Value(faker.binary(), vtype)


# ======== aliases ========
key2 = key
value2 = value
