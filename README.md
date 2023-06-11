# Papyrus

> embeddable, persistent, and revisions

Papyrus is an embeddable, persistent, and revisions storage.

Each record in Papyrus has a 128-bit unsigned integer as the data unique identifier (uid),
with the user-defined primary key, arbitrary length value, and optional searchable tags.

User can upload the data multiple times with the same primary key, each upload will create
a new revision of the data with the same primary key but has a different uid.
