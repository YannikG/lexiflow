"""Ensure the process-wide sqlite3 module can load SQLite extensions."""

from __future__ import annotations

import sys
from types import ModuleType
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    import sqlite3


def connection_supports_loadable_extensions(connection: sqlite3.Connection) -> bool:
    """Return whether ``connection`` can load SQLite extensions."""
    enable = getattr(connection, "enable_load_extension", None)
    if enable is None:
        return False
    try:
        enable(True)
        enable(False)
    except Exception:
        return False
    return True


def replacement_sqlite3_module() -> ModuleType:
    """Return a drop-in sqlite3 module with loadable-extension support."""
    try:
        import sqlean

        return cast(ModuleType, sqlean)
    except ImportError as exc:
        msg = (
            "This Python build's sqlite3 module cannot load extensions. "
            "Install sqlean.py (macOS/Linux) or ensure Windows Python 3.12+."
        )
        raise RuntimeError(msg) from exc


def ensure_loadable_sqlite3() -> None:
    """Use a replacement sqlite3 module when stdlib cannot load extensions."""
    try:
        import sqlite3

        connection = sqlite3.connect(":memory:")
        try:
            if connection_supports_loadable_extensions(connection):
                return
        finally:
            connection.close()
    except Exception:
        pass

    sys.modules["sqlite3"] = replacement_sqlite3_module()
