"""Schema migration runner."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from lexiflow_core.db.connection import connect_sqlite
from lexiflow_core.db.migration_loader import MigrationLoader
from lexiflow_core.db.sql_script import split_sql_script


class MigrationError(Exception):
    """Raised when a schema migration cannot be applied."""


class MigrationRunner:
    def migrate(self, db_path: Path, scripts_dir: Path) -> None:
        """Apply pending SQL scripts atomically, one transaction per script."""
        loader = MigrationLoader(scripts_dir)
        scripts = loader.discover()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = connect_sqlite(db_path)
        try:
            self._ensure_schema_table(connection)
            applied = self._load_applied_versions(connection)
            for script in scripts:
                if script.version in applied:
                    continue
                self._apply_script(connection, script.version, script.sql)
        finally:
            connection.close()

    def _ensure_schema_table(self, connection: sqlite3.Connection) -> None:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY)"
        )
        connection.commit()

    def _load_applied_versions(self, connection: sqlite3.Connection) -> set[str]:
        return {
            row[0]
            for row in connection.execute("SELECT version FROM schema_migrations")
        }

    def _apply_script(
        self,
        connection: sqlite3.Connection,
        version: str,
        sql: str,
    ) -> None:
        try:
            connection.execute("BEGIN IMMEDIATE")
            for statement in split_sql_script(sql):
                connection.execute(statement)
            connection.execute(
                "INSERT INTO schema_migrations(version) VALUES (?)",
                (version,),
            )
            connection.commit()
        except sqlite3.Error as exc:
            connection.rollback()
            raise MigrationError(f"failed to apply migration {version}") from exc


def bundled_migrations_dir() -> Path:
    """Return the packaged SQL migrations directory shipped with lexiflow-core."""
    return Path(__file__).resolve().parent.parent / "migrations"
