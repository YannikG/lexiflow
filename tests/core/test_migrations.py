"""Tests for lexiflow_core.db.migrations."""

from __future__ import annotations

from pathlib import Path

import pytest

from lexiflow_core.db.connection import connect_sqlite
from lexiflow_core.db.migrations import MigrationError, MigrationRunner


def test_migration_applies_once(tmp_path: Path) -> None:
    db_path = tmp_path / "app.sqlite"
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "001_create.sql").write_text(
        "CREATE TABLE widgets (id INTEGER PRIMARY KEY);",
        encoding="utf-8",
    )
    runner = MigrationRunner()

    runner.migrate(db_path, scripts_dir)
    runner.migrate(db_path, scripts_dir)

    connection = connect_sqlite(db_path)
    try:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        versions = connection.execute(
            "SELECT version FROM schema_migrations ORDER BY version"
        ).fetchall()
    finally:
        connection.close()

    assert "widgets" in tables
    assert versions == [("001_create",)]


def test_migrations_apply_in_order(tmp_path: Path) -> None:
    db_path = tmp_path / "app.sqlite"
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "001_create.sql").write_text(
        "CREATE TABLE first (id INTEGER PRIMARY KEY);",
        encoding="utf-8",
    )
    (scripts_dir / "002_add_second.sql").write_text(
        "CREATE TABLE second (id INTEGER PRIMARY KEY);",
        encoding="utf-8",
    )
    runner = MigrationRunner()

    runner.migrate(db_path, scripts_dir)

    connection = connect_sqlite(db_path)
    try:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        versions = connection.execute(
            "SELECT version FROM schema_migrations ORDER BY version"
        ).fetchall()
    finally:
        connection.close()

    assert {"first", "second"}.issubset(tables)
    assert versions == [("001_create",), ("002_add_second",)]


def test_failed_migration_rolls_back(tmp_path: Path) -> None:
    db_path = tmp_path / "app.sqlite"
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "001_create.sql").write_text(
        "CREATE TABLE widgets (id INTEGER PRIMARY KEY);",
        encoding="utf-8",
    )
    (scripts_dir / "002_broken.sql").write_text(
        "CREATE TABLE widgets (id INTEGER PRIMARY KEY);",
        encoding="utf-8",
    )
    runner = MigrationRunner()

    with pytest.raises(MigrationError):
        runner.migrate(db_path, scripts_dir)

    connection = connect_sqlite(db_path)
    try:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        versions = connection.execute(
            "SELECT version FROM schema_migrations ORDER BY version"
        ).fetchall()
    finally:
        connection.close()

    assert "widgets" in tables
    assert versions == [("001_create",)]
