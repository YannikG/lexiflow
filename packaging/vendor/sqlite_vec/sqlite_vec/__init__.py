"""Vendored sqlite-vec: platform-specific vec0 loadable paths."""

from __future__ import annotations

import platform
import sqlite3
import struct
from os import path

__version__ = "0.1.9"
__version_info__ = tuple(__version__.split("."))


def loadable_path() -> str:
    """Return the path to the vec0 loadable extension for this platform."""
    package_dir = path.dirname(__file__)
    system = platform.system()
    machine = platform.machine().lower()
    if system == "Windows" and machine in {"arm64", "aarch64"}:
        stem = "vec0.arm64"
    else:
        stem = "vec0"
    return path.normpath(path.join(package_dir, stem))


def load(conn: sqlite3.Connection) -> None:
    """Load the sqlite-vec SQLite extension into the given database connection."""
    conn.load_extension(loadable_path())


def serialize_float32(vector: list[float]) -> bytes:
    """Serialize floats into the raw bytes format sqlite-vec expects."""
    return struct.pack(f"{len(vector)}f", *vector)


def serialize_int8(vector: list[int]) -> bytes:
    """Serialize integers into the raw bytes format sqlite-vec expects."""
    return struct.pack(f"{len(vector)}b", *vector)
