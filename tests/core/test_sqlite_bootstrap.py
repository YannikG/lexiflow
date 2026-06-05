"""Tests for sqlite3 bootstrap when stdlib lacks loadable extensions."""

from __future__ import annotations

import sqlite3 as stdlib_sqlite3
import sys
import types
from collections.abc import Generator

import pytest
from lexiflow_core.db.sqlite_bootstrap import (
    connection_supports_loadable_extensions,
    ensure_loadable_sqlite3,
)
from lexiflow_core.vectors.sqlite_vec import load_sqlite_vec, sqlite_vec_version


@pytest.fixture(autouse=True)
def _restore_stdlib_sqlite3() -> Generator[None, None, None]:
    yield
    sys.modules["sqlite3"] = stdlib_sqlite3


def test_connection_supports_loadable_extensions_false_without_method() -> None:
    class BrokenConnection:
        def close(self) -> None:
            return None

    assert connection_supports_loadable_extensions(BrokenConnection()) is False  # type: ignore[arg-type]


def test_ensure_loadable_sqlite3_replaces_stdlib_without_extensions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    broken = types.ModuleType("sqlite3")

    class BrokenConnection:
        def close(self) -> None:
            return None

    broken.connect = lambda *args, **kwargs: BrokenConnection()  # noqa: ARG005
    broken.Connection = BrokenConnection
    monkeypatch.setitem(sys.modules, "sqlite3", broken)
    monkeypatch.setattr(
        "lexiflow_core.db.sqlite_bootstrap.reload_stdlib_sqlite3_module",
        lambda: broken,
    )

    ensure_loadable_sqlite3()

    import sqlite3

    assert sqlite3 is not stdlib_sqlite3
    connection = sqlite3.connect(":memory:")
    try:
        connection.enable_load_extension(True)
        connection.enable_load_extension(False)
        load_sqlite_vec(connection)
        (version,) = connection.execute("SELECT vec_version()").fetchone()
        assert isinstance(version, str)
        assert version
    except Exception as exc:
        if "vec0" in str(exc).lower() or "no such file" in str(exc).lower():
            pytest.skip("vendored vec0 loadable not present; run fetch_sqlite_vec.py")
        raise
    finally:
        connection.close()


def test_sqlite_vec_version_returns_non_empty_string() -> None:
    try:
        version = sqlite_vec_version()
    except Exception as exc:
        if "vec0" in str(exc).lower() or "no such file" in str(exc).lower():
            pytest.skip("vendored vec0 loadable not present; run fetch_sqlite_vec.py")
        raise
    assert version


def test_ensure_loadable_sqlite3_noop_when_stdlib_supports_extensions() -> None:
    connection = stdlib_sqlite3.connect(":memory:")
    try:
        if not hasattr(connection, "enable_load_extension"):
            pytest.skip("stdlib sqlite3 lacks enable_load_extension on this host")

        ensure_loadable_sqlite3()

        import sqlite3 as sqlite3_after

        assert sqlite3_after is stdlib_sqlite3
        connection_after = sqlite3_after.connect(":memory:")
        try:
            connection_after.enable_load_extension(True)
            connection_after.enable_load_extension(False)
        finally:
            connection_after.close()
    finally:
        connection.close()
