"""Shared helpers for sqlite-vec packaging tests."""

from __future__ import annotations

from pathlib import Path

_LOADABLE_SUFFIXES = (".dylib", ".so", ".dll")


def resolve_installed_sqlite_vec_loadable() -> Path | None:
    """Return the installed vec0 file, or None when fetch/sync has not run."""
    try:
        import sqlite_vec
    except ImportError:
        return None
    try:
        stem = Path(sqlite_vec.loadable_path())
    except FileNotFoundError:
        return None
    for suffix in _LOADABLE_SUFFIXES:
        candidate = Path(f"{stem}{suffix}")
        if candidate.is_file():
            return candidate
    if stem.is_file():
        return stem
    return None
