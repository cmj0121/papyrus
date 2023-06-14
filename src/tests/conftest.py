import pytest
from papyrus.layers import Data
from papyrus.types import Key


@pytest.fixture
def key(faker):
    yield Key(faker.pyint())


@pytest.fixture
def value(faker):
    yield faker.pystr()


@pytest.fixture
def data(faker, key, value):
    tags = {
        faker.name(): Key(faker.pyint()),
        faker.name(): Key(faker.pyint()),
        faker.name(): Key(faker.pyint()),
    }
    yield Data(key, value=value, tags=tags)
