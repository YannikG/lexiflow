"""Persistence for applied schema migration versions."""

from __future__ import annotations

import sqlite3


class SchemaMigrationJournal:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def ensure_table(self) -> None:
        self._connection.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY)"
        )
        self._connection.commit()

    def applied_versions(self) -> set[str]:
        return {
            row[0]
            for row in self._connection.execute("SELECT version FROM schema_migrations")
        }

    def record_applied(self, version: str) -> None:
        self._connection.execute(
            "INSERT INTO schema_migrations(version) VALUES (?)",
            (version,),
        )
