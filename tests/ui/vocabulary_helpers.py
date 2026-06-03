"""Shared helpers for vocabulary UI tests."""

from __future__ import annotations

from lexiflow_ui.widgets.vocabulary_browse_table import VocabularyBrowseTable
from PySide6.QtWidgets import QTableWidget, QTextBrowser


def select_word_in_reader(window_or_reader, text: str = "Cuerpo") -> str:
    reader = getattr(window_or_reader, "reader", window_or_reader)
    pane = reader.findChild(QTextBrowser, "reader_read_pane")
    assert pane is not None
    haystack = pane.toPlainText()
    start = haystack.index(text)
    cursor = pane.textCursor()
    cursor.setPosition(start)
    cursor.setPosition(start + len(text), cursor.MoveMode.KeepAnchor)
    pane.setTextCursor(cursor)
    return text


def browse_table(window) -> VocabularyBrowseTable:
    table = window.findChild(VocabularyBrowseTable, "vocabulary_browse_table")
    assert table is not None
    return table


def browse_grid(window) -> QTableWidget:
    grid = window.findChild(QTableWidget, "vocabulary_browse_grid")
    assert grid is not None
    return grid


def trigger_browse_context_menu(
    window,
    *,
    row: int,
    action_text: str,
) -> None:
    table = browse_table(window)
    if action_text == "Edit word":
        table.request_edit(row)
    elif action_text == "Delete":
        table.request_delete(row)
    else:
        raise ValueError(f"unsupported browse context action: {action_text}")
