"""Ensure the process-wide sqlite3 module can load SQLite extensions."""

from __future__ import annotations

import sqlite3
import sys
from types import ModuleType
from typing import cast


def connection_supports_loadable_extensions(connection: sqlite3.Connection) -> bool:
    """Return whether ``connection`` can load SQLite extensions."""
    enable = getattr(connection, "enable_load_extension", None)
    if enable is None:
        return False
    try:
        enable(True)
        enable(False)
    except sqlite3.OperationalError:
        return False
    return True


def reload_stdlib_sqlite3_module() -> ModuleType:
    """Reload the stdlib ``sqlite3`` module, bypassing ``sys.modules`` cache."""
    saved = sys.modules.pop("sqlite3", None)
    try:
        import sqlite3 as stdlib

        return stdlib
    finally:
        if saved is not None:
            sys.modules["sqlite3"] = saved


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
    current = sys.modules.get("sqlite3")
    if current is not None:
        connection = current.connect(":memory:")
        try:
            if connection_supports_loadable_extensions(connection):
                return
        finally:
            connection.close()

    stdlib = reload_stdlib_sqlite3_module()
    connection = stdlib.connect(":memory:")
    try:
        if connection_supports_loadable_extensions(connection):
            sys.modules["sqlite3"] = stdlib
            return
    finally:
        connection.close()

    sys.modules["sqlite3"] = replacement_sqlite3_module()
