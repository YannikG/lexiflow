"""Shared helpers for vocabulary UI tests."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QPoint
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QTableWidget, QTextBrowser


def select_word_in_reader(window, text: str = "Cuerpo") -> str:
    reader = window.reader
    pane = reader.findChild(QTextBrowser, "reader_read_pane")
    assert pane is not None
    haystack = pane.toPlainText()
    start = haystack.index(text)
    cursor = pane.textCursor()
    cursor.setPosition(start)
    cursor.setPosition(start + len(text), cursor.MoveMode.KeepAnchor)
    pane.setTextCursor(cursor)
    return text


def browse_row_position(window, row: int) -> QPoint:
    grid = window.findChild(QTableWidget, "vocabulary_browse_grid")
    assert grid is not None
    index = grid.model().index(row, 0)
    center = grid.visualRect(index).center()
    return QPoint(center)


def install_browse_context_menu_choice(
    monkeypatch: pytest.MonkeyPatch,
    action_text: str,
) -> None:
    class _Menu:
        def __init__(self, *args, **kwargs) -> None:
            self._actions: dict[str, QAction] = {}

        def addAction(self, text: str) -> QAction:
            action = QAction(text)
            self._actions[text] = action
            return action

        def exec(self, *args, **kwargs) -> QAction | None:
            return self._actions.get(action_text)

    monkeypatch.setattr(
        "lexiflow_ui.widgets.vocabulary_browse_table.QMenu",
        _Menu,
    )


def trigger_browse_context_menu(
    window,
    *,
    row: int,
    monkeypatch: pytest.MonkeyPatch,
    action_text: str,
) -> None:
    install_browse_context_menu_choice(monkeypatch, action_text)
    browse_table = window._vocabulary._browse_table
    browse_table._show_context_menu(browse_row_position(window, row))
