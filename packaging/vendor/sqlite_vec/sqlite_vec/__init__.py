"""Vendored sqlite-vec: platform-specific vec0 loadable paths."""

from __future__ import annotations

import platform
import sqlite3
import struct
import sys
from os import path

__version__ = "0.1.9"
__version_info__ = tuple(__version__.split("."))

_LOADABLE_SUFFIXES = (".dylib", ".so", ".dll")


def _vec0_stem() -> str:
    system = platform.system()
    machine = platform.machine().lower()
    if system == "Windows" and machine in {"arm64", "aarch64"}:
        return "vec0.arm64"
    return "vec0"


def _loadable_file_exists(base_path: str) -> bool:
    for suffix in _LOADABLE_SUFFIXES:
        if path.isfile(base_path + suffix):
            return True
    return path.isfile(base_path)


def _dev_vendor_directory() -> str | None:
    """Return repo vendor vec dir when loadable exists there (non-frozen dev only)."""
    if getattr(sys, "frozen", False):
        return None
    module_dir = path.dirname(path.abspath(__file__))
    stem = _vec0_stem()
    if _loadable_file_exists(path.join(module_dir, stem)):
        return None
    from pathlib import Path

    for parent in Path(module_dir).parents:
        vendor = parent / "packaging" / "vendor" / "sqlite_vec" / "sqlite_vec"
        if vendor.is_dir() and _loadable_file_exists(str(vendor / stem)):
            return str(vendor)
    return None


def _search_directories() -> list[str]:
    directories: list[str] = []
    seen: set[str] = set()

    def add(directory: str) -> None:
        normalized = path.normpath(directory)
        if normalized in seen:
            return
        seen.add(normalized)
        directories.append(normalized)

    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", "")
        if meipass:
            add(path.join(meipass, "sqlite_vec"))
    add(path.dirname(path.abspath(__file__)))
    vendor_dir = _dev_vendor_directory()
    if vendor_dir is not None:
        add(vendor_dir)
    return directories


def loadable_path() -> str:
    """Return the path to the vec0 loadable extension for this platform."""
    stem = _vec0_stem()
    for directory in _search_directories():
        candidate = path.join(directory, stem)
        if _loadable_file_exists(candidate):
            return candidate
    searched = ", ".join(_search_directories())
    raise FileNotFoundError(
        f"sqlite-vec loadable {stem} not found; searched: {searched}"
    )


def load(conn: sqlite3.Connection) -> None:
    """Load the sqlite-vec SQLite extension into the given database connection."""
    conn.load_extension(loadable_path())


def serialize_float32(vector: list[float]) -> bytes:
    """Serialize floats into the raw bytes format sqlite-vec expects."""
    return struct.pack(f"{len(vector)}f", *vector)


def serialize_int8(vector: list[int]) -> bytes:
    """Serialize integers into the raw bytes format sqlite-vec expects."""
    return struct.pack(f"{len(vector)}b", *vector)
