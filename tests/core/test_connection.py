"""Tests for lexiflow_core.db.connection."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.db.connection import connect_sqlite


def test_connect_sqlite_enables_wal(tmp_path: Path) -> None:
    db_path = tmp_path / "test.sqlite"
    connection = connect_sqlite(db_path)
    try:
        journal_mode = connection.execute("PRAGMA journal_mode").fetchone()
        foreign_keys = connection.execute("PRAGMA foreign_keys").fetchone()
    finally:
        connection.close()

    assert journal_mode is not None
    assert journal_mode[0].lower() == "wal"
    assert foreign_keys == (1,)
