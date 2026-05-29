"""Apply pending SQL migration scripts to a database."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from lexiflow_core.db.connection import connect_sqlite
from lexiflow_core.db.database_path import ensure_database_parent
from lexiflow_core.db.migration_loader import MigrationLoader
from lexiflow_core.db.schema_migrations import SchemaMigrationJournal
from lexiflow_core.db.sql_script import split_sql_script


class MigrationError(Exception):
    """Raised when a schema migration cannot be applied."""


class MigrationRunner:
    def migrate(self, db_path: Path, scripts_dir: Path) -> None:
        """Apply pending SQL scripts atomically, one transaction per script."""
        ensure_database_parent(db_path)
        scripts = MigrationLoader(scripts_dir).discover()
        connection = connect_sqlite(db_path)
        try:
            journal = SchemaMigrationJournal(connection)
            journal.ensure_table()
            applied = journal.applied_versions()
            for script in scripts:
                if script.version in applied:
                    continue
                self._apply_script(connection, journal, script.version, script.sql)
        finally:
            connection.close()

    def _apply_script(
        self,
        connection: sqlite3.Connection,
        journal: SchemaMigrationJournal,
        version: str,
        sql: str,
    ) -> None:
        try:
            connection.execute("BEGIN IMMEDIATE")
            for statement in split_sql_script(sql):
                connection.execute(statement)
            journal.record_applied(version)
            connection.commit()
        except sqlite3.Error as exc:
            connection.rollback()
            raise MigrationError(f"failed to apply migration {version}") from exc
