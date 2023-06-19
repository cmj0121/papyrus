"""The persistent layer which save data into the local file system."""
from __future__ import annotations

import logging
import struct
import zlib
from pathlib import Path
from typing import BinaryIO
from urllib.parse import ParseResult

from papyrus.settings import PROJ_NAME


logger = logging.getLogger(PROJ_NAME)


class Header:
    """
    the header of the persistent layer.

    The header is used to identify the persistent layer, and store the meta
    information of the persistent layer. It store the magic number, version,
    type, flags, meta offset, meta size and checksum.

    - magic: the magic number of the header, always be \x30\x14\x15\x92.
    - version: the version of the header, the latest version is 1.
    - type: the type of the persistent layer, the value is defined on each implementation.
    - flags: the flags of the persistent layer, the value is used on each implementation.
    - meta offset: the offset of the meta data.
    - meta size: the size of the meta data.
    - checksum: the checksum of the header.

    0          8        16        24        32        40        48        56        64
    +---------+---------+---------+---------+---------+---------+---------+---------+
    |   \x30      \x14      \x15      \x92  |   VER   |   TYPE  |       FLAGS       |
    +-------------------------------------------------------------------------------+
    |            Meta Size                   |              CHECKSUM                 |
    +-------------------------------------------------------------------------------+
    """
    def __init__(self, type: int, /, flags: int = 0):
        self.type = type
        self.flags = flags
        self.meta_size = 0

    def cap(self) -> int:
        """the capacity of the header."""
        return 16

    @property
    def magic(self) -> bytes:
        """the magic number of the header."""
        return b"\x30\x14\x15\x92"

    @property
    def version(self) -> int:
        """the version of the header."""
        return 1

    @property
    def checksum(self) -> int:
        """the checksum of the header."""
        return zlib.crc32(self.bytes_without_checksum)

    @property
    def meta_offset(self) -> int:
        """the offset of the meta data."""
        return self.cap()

    @property
    def bytes_without_checksum(self) -> bytes:
        """the header without checksum."""
        hdr = self.magic + struct.pack("<BBHI", self.version, self.type, self.flags, self.meta_size)
        return hdr

    def to_bytes(self):
        """convert the header to bytes."""
        return self.bytes_without_checksum + struct.pack("<I", self.checksum)

    @classmethod
    def from_bytes(cls, data: bytes) -> Header:
        if len(data) != 16:
            raise ValueError(f"invalid header length: {len(data)=} != 16")

        magic, version, type, flags, meta_size, checksum = struct.unpack("<4sBBHII", data)
        if magic != b"\x30\x14\x15\x92":
            raise ValueError(f"invalid header magic: {magic=}")

        if version != 1:
            raise ValueError(f"invalid header version: {version=}")

        if checksum != zlib.crc32(data[:12]):
            raise ValueError(f"invalid header checksum: {checksum=}")

        header = cls(type, flags)
        header.meta_size = meta_size

        return header


class BaseFileLayer:
    """
    the persistent layer which store the data into the local file system.

    The file-based layer is the persistent layer which store the data into the
    local file system. It contains three parts: header, meta and text.

    - header  the general information of the persistent layer, which contains
              basic meta to decode the following meta and text.
    - meta    the optional meta information of the persistent layer, which is
              used to store the extra meta to decode the text.
    - text    the data of the persistent layer, which contains the key, value
              and other information.

    +-----------------+
    |      Header     |
    +-----------------+
    ~      Meta       ~
    +-----------------+
    ~      Text       ~
    +-----------------+
    """

    type: int | None = None
    flags: int = 0

    def __init_subclass__(subcls, *args, **kwargs):
        if subcls.type is None:
            raise ValueError(f"{subcls.name} must have a type")

        super().__init_subclass__(*args, **kwargs)

    def __init__(self, /, uri: ParseResult | None = None, threshold: int | None = None):
        """initialize the layer."""
        super().__init__(uri=uri, threshold=threshold)

        self._path = Path(f"{uri.netloc}{uri.path}")
        self._fd: BinaryIO | None = None
        self._header = Header(self.type, flags=self.flags)

        self.open()

    def __del__(self):
        """close the file descriptor."""
        self.close()

    def open(self):
        """load the persistent file if possible, or save the basic header."""
        header = self.fd.seek(0)
        header = self.fd.read(self.header.cap())

        if not header:
            # empty file, save the basic header
            self.fd.write(self.header.to_bytes())
            return

        # load the existing header
        self._header = Header.from_bytes(header)

    def close(self):
        """close the file descriptor."""
        if self._fd is not None:
            logger.info(f"close persistent file: {self._path} for {self.__class__.__name__}")
            self._fd.close()
            self._fd = None

    @property
    def is_closed(self) -> bool:
        """whether the file descriptor is closed."""
        return self._fd is None

    def unlink(self):
        """**DANGER** remove the persistent file."""
        self.close()
        self.path.unlink()

    @property
    def path(self) -> Path:
        """the path of the persistent file."""
        return self._path

    @property
    def fd(self) -> BinaryIO:
        if self._fd is None:
            logger.info(f"open persistent file: {self._path} for {self.__class__.__name__}")

            mode = "r+b" if self.path.exists() else "w+b"

            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._fd = self.path.open(mode)

        return self._fd

    @property
    def header(self) -> Header:
        """the header of the persistent file."""
        return self._header

    @property
    def meta(self) -> bytes:
        """the meta of the persistent file."""
        if self.header.meta_size == 0:
            return b""

        self.fd.seek(self.header.meta_offset)
        return self.fd.read(self.header.meta_size)

    @property
    def text_offset(self, block: int = 512) -> int:
        """the offset of the text."""
        offset = self.header.meta_offset + self.header.meta_size
        offset = offset + (block - offset % block) % block
        return offset

    @property
    def text(self) -> bytes:
        """the text of the persistent file."""
        self.fd.seek(self.text_offset)
        return self.fd.read()
