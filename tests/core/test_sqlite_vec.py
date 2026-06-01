"""Tests for sqlite-vec extension loading."""

from __future__ import annotations

import sqlite3

from lexiflow_core.vectors.sqlite_vec import load_sqlite_vec


def test_load_sqlite_vec_allows_vec0_virtual_table() -> None:
    connection = sqlite3.connect(":memory:")
    try:
        load_sqlite_vec(connection)
        connection.execute(
            "CREATE VIRTUAL TABLE test_vectors USING vec0(embedding float[384])"
        )
        (version,) = connection.execute("SELECT vec_version()").fetchone()
        assert isinstance(version, str)
        assert version
    finally:
        connection.close()
