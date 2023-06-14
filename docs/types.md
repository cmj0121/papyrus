# Types

Papyrus provides three category types: primary key, value and the tag.

- Primary key: identify the data on the user-space.
- Value: the arbitrarily data what user want to store.
- Tag: the search key for the data.

## Primary Key

The primary key is the fixed length and searchable key.

It can be used to identify the data on the user-space, which means
the primary key is the unique key in the user-space. User can upload
the data with the same primary key multiple times and all the data
will be stored in the Papyrus. The `latest` operation will return the
latest data with the given primary key.

The primary key can be converted to another key type, and upgrade the
key type will not affect the data stored in the Papyrus.

| Type | Size | Description                      |
| ---- | ---- | -------------------------------- |
| BOOL | 1    | the truth value                  |
| WORD | 2    | the 16-bit signed integer        |
| INT  | 16   | the 128-bit signed integer       |
| STR  | 64   | 64 bytes null-terminated string  |
| TEXT | 256  | 256 bytes null-terminated string |

### Unique ID

The unique ID (UID) is the internal 128-bit key structure. The UID
combination of the timestamp, random number and other information.

## Value

The value is the arbitrarily data what user want to store. It is the optional
field and can store data with arbitrarily type or size. The size of value is
limited by the Papyrus implementations and the maximum size is 16MB.

The end of value is the checksum of the value. The checksum is the 32-bit data
depends on the implementation. It may be the CRC32 or the Adler32.

    0         8        16       24       32
    +--------+--------+--------+--------+
    | vtype  |         length           |
    +-----------------------------------+
    ~           compressed data         ~
    +-----------------------------------+
    |              checksum             |
    +-----------------------------------+

## Lifecycle

The data in Papyrus has the following lifecycle:

| State  | Description                                                    |
| ------ | -------------------------------------------------------------- |
| Insert | insert a new record with the given primary key.                |
| Delete | the special insert operation which mark the record as deleted. |
| Move   | move the record from one layer to another layer.               |
| Purge  | purge all the records in layer which marked as deleted.        |
