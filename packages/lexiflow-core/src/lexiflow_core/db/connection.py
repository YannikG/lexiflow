"""SQLite connection helpers."""

from __future__ import annotations

import sqlite3
from pathlib import Path


def connect_sqlite(path: Path) -> sqlite3.Connection:
    """Open a SQLite database with WAL journaling and foreign keys enabled."""
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA busy_timeout=5000")
    return connection
