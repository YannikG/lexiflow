"""Load the sqlite-vec extension into a SQLite connection."""

from __future__ import annotations

import os
import sqlite3

import sqlite_vec


def load_sqlite_vec(connection: sqlite3.Connection) -> None:
    """Load sqlite-vec SQL functions into ``connection``."""
    connection.enable_load_extension(True)
    override = os.environ.get("LEXIFLOW_SQLITE_VEC_PATH", "").strip()
    if override:
        connection.load_extension(override)
    else:
        sqlite_vec.load(connection)
    connection.enable_load_extension(False)


def sqlite_vec_version() -> str:
    """Load sqlite-vec on an in-memory connection and return ``vec_version()``."""
    connection = sqlite3.connect(":memory:")
    try:
        load_sqlite_vec(connection)
        (version,) = connection.execute("SELECT vec_version()").fetchone()
        return str(version)
    finally:
        connection.close()
