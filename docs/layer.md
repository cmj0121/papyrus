# Layer

> The fundantion of Papyrus

The **layer** is the fundantion of Papyrus, which provides the basic data
operations. The data in layer is the key-value pair which key is the predefined
and fixed length data type, and the value is the arbitrarily length compressed
data.

## Type

The layer provides two data types to user: key and value. The key is the
predefined and fixed length data type, and the value is the arbitrarily length.

### Key

The key, also called primary key, is the predefined and fixed length data type.
It can be used to identify the data on the user-space, which means the primary
key is the unique key in the current layer.

If user upload the data with the same primary key multiple times, layer will
overwrite the old data with the new data with `force=true` option, or raise the
error as the default behavior.

| type | size | description                      |
| ---- | ---- | -------------------------------- |
| BOOL | 1    | the truth value                  |
| WORD | 2    | the 16-bit signed integer        |
| INT  | 8    | the 64-bit signed integer        |
| UID  | 16   | the 128-bit unsigned integer     |
| STR  | 64   | 64 bytes null-terminated string  |
| TEXT | 256  | 256 bytes null-terminated string |

### Value

The value is the arbitrarily length data which can be used to store the
binary data and user can define the data type by themselves.

    0        8       16     24      32
    +-------+-------+-------+-------+
    | type  |     size              |
    +-------+-------+-------+-------+
    ~             data              ~
    +-------+-------+-------+-------+
    ~             padding           ~
    +-------+-------+-------+-------+
    |             checksum          |
    +-------+-------+-------+-------+

In general, the value has following fields:

- type: the category of the value.
- size: the total size in bytes of the data.
- data: the stored data.
- padding: the padding bytes to align and make the total size is multiple of 32.
- checksum: the checksum of the data.

## Operation

The layer provides the following operations:

| operations | description                                                            |
| ---------- | ---------------------------------------------------------------------- |
| count      | the total count of the records in the layer.                           |
| capacity   | the total count of the records, include marked as delete in the layer. |
| insert     | insert a new record with the given primary key.                        |
| delete     | the special insert operation which mark the record as deleted.         |
| query      | query the record with the given primary key.                           |
| purge      | purge all the marked as deleted records.                               |
| unlink     | remove all the records in the layer.                                   |
| iterate    | iterate all the records in the layer with the given order.             |
