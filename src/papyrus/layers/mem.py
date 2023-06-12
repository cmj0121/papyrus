"""In-memory layer implementation."""
from urllib.parse import ParseResult

from papyrus.types import Key
from papyrus.types import UniqueID

from ._base import BaseLayer
from ._base import Data


class MemLayer(BaseLayer):
    """
    The in-memory layer implementation.

    All the data is stored in the memory, which the data will be lost after
    the process is terminated.
    """
    name = "mem"

    def __init__(self, /, uri: ParseResult | None = None, threshold: int | None = None):
        self._mem: dict[UniqueID, Data] = {}

        self._keys: set[Key] = set()
        self._revisions: dict[Key, list[Data]] = {}

        super().__init__(uri=uri, threshold=threshold)

    # ======== the general methods related on the layer meta ======== #
    def __len__(self) -> int:
        return len(self._keys)

    def __contains__(self, search: Key | UniqueID) -> bool:
        match search:
            case UniqueID():
                return search in self._mem
            case Key():
                return search in self._keys
            case _:
                raise TypeError(f"search must be either UniqueID or Key: {type(search)=}")

    @property
    def cap(self) -> int:
        return len(self._mem)

    # ======== the general methods related to data operations ======== #
    def insert(self, data: Data) -> UniqueID:
        """insert the data into the layer."""
        uid = UniqueID.new()

        self._mem[uid] = data

        self._keys.add(data.primary_key)
        self._revisions[data.primary_key] = self._revisions.get(data.primary_key, []) + [data]

        return uid

    def delete(self, key: Key) -> UniqueID:
        """mark the data as deleted."""
        data = Data(key, is_deleted=True)
        uid = self.insert(data)

        self._keys.remove(key)

        return uid

    def latest(self, key: Key) -> Data | None:
        """get the latest data by the key."""
        data = self._revisions.get(key, [])
        data = data[-1] if data else None
        return data if (data is None or not data.is_deleted) else None

    def revisions(self, key: Key) -> list[Data]:
        """get all the revisions of data by the key."""
        data = self._revisions.get(key, [])
        return list(data[::-1])

    # ======== the authorized methods related to danger operations ======== #
    def raw(self, uid: UniqueID) -> Data | None:
        """get the data by the unique id."""
        return self._mem.get(uid)

    def purge(self):
        """remove all the data that is marked as deleted."""
        self._revisions = {
            key: [r for r in revisions if not r.is_deleted]
            for key, revisions in self._revisions.items() for key in self._keys
        }

        self._mem = {uid: data for uid, data in self._mem.items() if data.primary_key in self._keys}
