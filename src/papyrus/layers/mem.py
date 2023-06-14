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
        self._revision: dict[Key, list[Data]] = {}
        self._search: dict[str, dict[Key, set[Key]]] = {}

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
        self._revision[data.primary_key] = self._revision.get(data.primary_key, []) + [data]

        for tkey, tvalue in data.tags.items():
            self._search[tkey] = self._search.get(tkey, {})
            self._search[tkey][tvalue] = self._search[tkey].get(tvalue, set())
            self._search[tkey][tvalue].add(data.primary_key)

        return uid

    def delete(self, key: Key) -> UniqueID:
        """mark the data as deleted."""
        data = Data(key, is_deleted=True)
        uid = self.insert(data)

        self._keys.remove(key)
        for tag in self._search.values():
            for key_set in tag.values():
                key_set.discard(key)

        return uid

    def latest(self, key: Key) -> Data | None:
        """get the latest data by the key."""
        data = self._revision.get(key, [])
        data = data[-1] if data else None
        return data if (data is None or not data.is_deleted) else None

    def revision(self, key: Key) -> list[Data]:
        """get all the revision of data by the key."""
        data = self._revision.get(key, [])
        return data[::-1]

    def search(self, name: str, key: Key) -> set[Key]:
        """list all the keys by the search tag (named key)."""
        search_pool = self._search.get(name, {})
        return search_pool.get(key, set())

    # ======== the authorized methods related to danger operations ======== #
    def raw(self, uid: UniqueID) -> Data | None:
        """get the data by the unique id."""
        return self._mem.get(uid)

    def purge(self):
        """remove all the data that is marked as deleted."""
        self._revision = {
            key: [r for r in revision if not r.is_deleted]
            for key, revision in self._revision.items() for key in self._keys
        }

        self._mem = {uid: data for uid, data in self._mem.items() if data.primary_key in self._keys}
