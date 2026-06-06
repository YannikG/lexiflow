"""Tests for sqlite-vec extension loading."""

from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

import pytest
import sqlite_vec
from lexiflow_core.vectors.sqlite_vec import load_sqlite_vec


def _resolve_vendored_loadable() -> Path | None:
    base = Path(sqlite_vec.loadable_path())
    for candidate in (
        base,
        Path(f"{base}.dylib"),
        Path(f"{base}.so"),
        Path(f"{base}.dll"),
    ):
        if candidate.exists():
            return candidate
    return None


def test_load_sqlite_vec_honors_lexiflow_sqlite_vec_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    source = _resolve_vendored_loadable()
    if source is None:
        pytest.skip("vendored vec0 loadable not present; run fetch_sqlite_vec.py")

    override = tmp_path / source.name
    shutil.copy2(source, override)
    monkeypatch.setenv("LEXIFLOW_SQLITE_VEC_PATH", str(override))

    connection = sqlite3.connect(":memory:")
    try:
        load_sqlite_vec(connection)
        (version,) = connection.execute("SELECT vec_version()").fetchone()
        assert isinstance(version, str)
        assert version
    finally:
        connection.close()


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


def test_load_sqlite_vec_uses_installed_package_without_env_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("LEXIFLOW_SQLITE_VEC_PATH", raising=False)

    connection = sqlite3.connect(":memory:")
    try:
        load_sqlite_vec(connection)
        (version,) = connection.execute("SELECT vec_version()").fetchone()
        assert isinstance(version, str)
        assert version
    finally:
        connection.close()
