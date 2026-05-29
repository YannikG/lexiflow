"""Filesystem preparation for SQLite database files."""

from __future__ import annotations

from pathlib import Path


def ensure_database_parent(db_path: Path) -> None:
    """Create the parent directory for a database file when missing."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
