"""Tests for sqlite-vec extension loading."""

from __future__ import annotations

import sqlite3

import pytest
from lexiflow_core.vectors.sqlite_vec import load_sqlite_vec
from tests.packaging.sqlite_vec_test_support import (
    resolve_installed_sqlite_vec_loadable,
)


def test_load_sqlite_vec_allows_vec0_virtual_table() -> None:
    if resolve_installed_sqlite_vec_loadable() is None:
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
    if resolve_installed_sqlite_vec_loadable() is None:
        pytest.skip("installed sqlite-vec loadable not present")

    connection = sqlite3.connect(":memory:")
    try:
        load_sqlite_vec(connection)
        (version,) = connection.execute("SELECT vec_version()").fetchone()
        assert isinstance(version, str)
        assert version
    finally:
        connection.close()
