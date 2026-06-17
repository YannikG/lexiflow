"""Tests that the installed sqlite-vec package ships the platform vec0 loadable."""

from __future__ import annotations

from tests.packaging.sqlite_vec_test_support import (
    resolve_installed_sqlite_vec_loadable,
)

_SETUP_HINT = (
    "sqlite-vec loadable missing from installed package; "
    "run fetch_sqlite_vec.py then uv sync --reinstall-package sqlite-vec"
)


def test_installed_sqlite_vec_package_includes_platform_loadable() -> None:
    loadable = resolve_installed_sqlite_vec_loadable()
    assert loadable is not None, _SETUP_HINT
