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


def test_failed_mid_script_migration_rolls_back_entire_script(tmp_path: Path) -> None:
    db_path = tmp_path / "app.sqlite"
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "001_create.sql").write_text(
        "CREATE TABLE widgets (id INTEGER PRIMARY KEY);",
        encoding="utf-8",
    )
    (scripts_dir / "002_partial.sql").write_text(
        "CREATE TABLE partial (id INTEGER PRIMARY KEY);"
        "CREATE TABLE partial (id INTEGER PRIMARY KEY);",
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

    assert "partial" not in tables
    assert versions == [("001_create",)]


def test_bundled_migrations_dir_contains_initial_script() -> None:
    from lexiflow_core.db.migration_loader import bundled_migrations_dir

    migrations_dir = bundled_migrations_dir()

    assert migrations_dir.is_dir()
    assert (migrations_dir / "001_initial.sql").is_file()


def test_migration_splits_semicolon_inside_string_literal(tmp_path: Path) -> None:
    db_path = tmp_path / "nested" / "app.sqlite"
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "001_quotes.sql").write_text(
        "CREATE TABLE quotes (id INTEGER PRIMARY KEY, note TEXT);\n"
        "INSERT INTO quotes (id, note) VALUES (1, 'a;b');\n"
        "-- trailing comment with ; should not split\n",
        encoding="utf-8",
    )
    runner = MigrationRunner()

    runner.migrate(db_path, scripts_dir)

    connection = connect_sqlite(db_path)
    try:
        note = connection.execute("SELECT note FROM quotes WHERE id = 1").fetchone()
    finally:
        connection.close()

    assert note == ("a;b",)
