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
