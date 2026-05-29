"""Schema migration runner."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

from lexiflow_core.db.connection import connect_sqlite

_MIGRATION_PATTERN = re.compile(r"^(\d{3})_.+\.sql$")


class MigrationError(Exception):
    """Raised when a schema migration cannot be applied."""


class MigrationRunner:
    def migrate(self, db_path: Path, scripts_dir: Path) -> None:
        """Apply pending SQL scripts atomically, one transaction per script."""
        scripts = _discover_scripts(scripts_dir)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = connect_sqlite(db_path)
        try:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS schema_migrations ("
                "version TEXT PRIMARY KEY"
                ")"
            )
            connection.commit()
            applied = {
                row[0]
                for row in connection.execute("SELECT version FROM schema_migrations")
            }
            for version, script_path in scripts:
                if version in applied:
                    continue
                sql = script_path.read_text(encoding="utf-8")
                try:
                    connection.execute("BEGIN IMMEDIATE")
                    for statement in _split_sql_script(sql):
                        connection.execute(statement)
                    connection.execute(
                        "INSERT INTO schema_migrations(version) VALUES (?)",
                        (version,),
                    )
                    connection.commit()
                except sqlite3.Error as exc:
                    connection.rollback()
                    raise MigrationError(
                        f"failed to apply migration {version}"
                    ) from exc
        finally:
            connection.close()


def bundled_migrations_dir() -> Path:
    """Return the packaged SQL migrations directory shipped with lexiflow-core."""
    return Path(__file__).resolve().parent.parent / "migrations"


def _discover_scripts(scripts_dir: Path) -> list[tuple[str, Path]]:
    scripts: list[tuple[str, Path]] = []
    for path in sorted(scripts_dir.glob("*.sql")):
        match = _MIGRATION_PATTERN.match(path.name)
        if match is None:
            continue
        version = path.stem
        scripts.append((version, path))
    return scripts


def _split_sql_script(sql: str) -> list[str]:
    """Split SQL into statements without breaking on semicolons inside literals."""
    statements: list[str] = []
    current: list[str] = []
    index = 0
    length = len(sql)
    in_single_quote = False
    in_double_quote = False
    in_line_comment = False
    in_block_comment = False

    while index < length:
        char = sql[index]
        next_char = sql[index + 1] if index + 1 < length else ""

        if in_line_comment:
            current.append(char)
            if char == "\n":
                in_line_comment = False
            index += 1
            continue

        if in_block_comment:
            current.append(char)
            if char == "*" and next_char == "/":
                current.append(next_char)
                in_block_comment = False
                index += 2
                continue
            index += 1
            continue

        if in_single_quote:
            current.append(char)
            if char == "'" and next_char == "'":
                current.append(next_char)
                index += 2
                continue
            if char == "'":
                in_single_quote = False
            index += 1
            continue

        if in_double_quote:
            current.append(char)
            if char == '"' and next_char == '"':
                current.append(next_char)
                index += 2
                continue
            if char == '"':
                in_double_quote = False
            index += 1
            continue

        if char == "-" and next_char == "-":
            current.extend((char, next_char))
            in_line_comment = True
            index += 2
            continue

        if char == "/" and next_char == "*":
            current.extend((char, next_char))
            in_block_comment = True
            index += 2
            continue

        if char == "'":
            current.append(char)
            in_single_quote = True
            index += 1
            continue

        if char == '"':
            current.append(char)
            in_double_quote = True
            index += 1
            continue

        if char == ";":
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
            index += 1
            continue

        current.append(char)
        index += 1

    statement = "".join(current).strip()
    if statement:
        statements.append(statement)
    return statements
