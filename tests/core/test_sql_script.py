"""Tests for lexiflow_core.db.sql_script."""

from __future__ import annotations

from lexiflow_core.db.sql_script import split_sql_script


def test_split_sql_script_ignores_semicolon_inside_string() -> None:
    sql = (
        "INSERT INTO quotes (id, note) VALUES (1, 'a;b');\n"
        "CREATE TABLE second (id INTEGER PRIMARY KEY);"
    )

    statements = split_sql_script(sql)

    assert len(statements) == 2
    assert "VALUES (1, 'a;b')" in statements[0]
    assert statements[1].startswith("CREATE TABLE second")


def test_split_sql_script_ignores_semicolon_in_line_comment() -> None:
    sql = "CREATE TABLE demo (id INTEGER PRIMARY KEY); -- ends with ;\n"

    statements = split_sql_script(sql)

    assert statements == ["CREATE TABLE demo (id INTEGER PRIMARY KEY)"]
