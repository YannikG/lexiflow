"""Tests for sqlite-vec extension loading."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
import sqlite_vec
from lexiflow_core.vectors.sqlite_vec import load_sqlite_vec


def _resolve_installed_loadable() -> Path | None:
    package_dir = Path(sqlite_vec.loadable_path()).parent
    for name in ("vec0.dylib", "vec0.so", "vec0.dll", "vec0.arm64.dll"):
        candidate = package_dir / name
        if candidate.exists():
            return candidate
    return None


def test_load_sqlite_vec_allows_vec0_virtual_table() -> None:
    if _resolve_installed_loadable() is None:
        pytest.skip("installed sqlite-vec loadable not present")

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


def test_load_sqlite_vec_uses_installed_package_loadable() -> None:
    if _resolve_installed_loadable() is None:
        pytest.skip("installed sqlite-vec loadable not present")

    connection = sqlite3.connect(":memory:")
    try:
        load_sqlite_vec(connection)
        (version,) = connection.execute("SELECT vec_version()").fetchone()
        assert isinstance(version, str)
        assert version
    finally:
        connection.close()
