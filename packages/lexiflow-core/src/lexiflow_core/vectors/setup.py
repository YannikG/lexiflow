"""Per-language vector database setup."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from lexiflow_core.config.paths import text_vectors_db_path, vocabulary_db_path
from lexiflow_core.db.connection import connect_sqlite
from lexiflow_core.db.database_path import ensure_database_parent
from lexiflow_core.db.migration_loader import (
    text_vectors_migrations_dir,
    vocabulary_migrations_dir,
)
from lexiflow_core.db.migrations import MigrationRunner
from lexiflow_core.vectors.sqlite_vec import load_sqlite_vec


def _connect_vector_db(db_path: Path) -> sqlite3.Connection:
    ensure_database_parent(db_path)
    connection = connect_sqlite(db_path)
    load_sqlite_vec(connection)
    return connection


def ensure_vocabulary_db(data_root: Path, language_code: str) -> Path:
    """Migrate the per-language vocabulary database and return its path."""
    db_path = vocabulary_db_path(data_root, language_code)
    connection = _connect_vector_db(db_path)
    try:
        MigrationRunner().migrate_connection(connection, vocabulary_migrations_dir())
    finally:
        connection.close()
    return db_path


def ensure_text_vectors_db(data_root: Path, language_code: str) -> Path:
    """Migrate the per-language text vector database and return its path."""
    db_path = text_vectors_db_path(data_root, language_code)
    connection = _connect_vector_db(db_path)
    try:
        MigrationRunner().migrate_connection(connection, text_vectors_migrations_dir())
    finally:
        connection.close()
    return db_path
