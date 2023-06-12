# Papyrus

> embeddable, persistent, and revisions

[![Testing][0]][1]

Papyrus is an embeddable, persistent, and revisions storage.

Each record in Papyrus has a 128-bit unsigned integer as the data unique identifier (uid),
with the user-defined primary key, arbitrary length value, and optional searchable tags.

User can upload the data multiple times with the same primary key, each upload will create
a new revision of the data with the same primary key but has a different uid.

[0]: https://github.com/cmj0121/papyrus/actions/workflows/testing.yml/badge.svg
[1]: https://github.com/cmj0121/papyrus/actions/workflows/testing.yml
