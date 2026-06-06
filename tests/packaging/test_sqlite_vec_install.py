"""Tests that the installed sqlite-vec package ships the platform vec0 loadable."""

from __future__ import annotations

from pathlib import Path

import pytest
import sqlite_vec

_SETUP_HINT = (
    "sqlite-vec loadable missing from installed package; "
    "run fetch_sqlite_vec.py then uv sync --reinstall-package sqlite-vec"
)


def _resolve_installed_loadable() -> Path | None:
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


def test_installed_sqlite_vec_package_includes_platform_loadable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("LEXIFLOW_SQLITE_VEC_PATH", raising=False)

    loadable = _resolve_installed_loadable()
    assert loadable is not None, _SETUP_HINT
