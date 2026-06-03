"""Resolve reader text selections for highlight-add."""

from __future__ import annotations

from PySide6.QtCore import QPoint
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QTextBrowser


def normalize_reader_selection(text: str) -> str:
    """Normalize QTextEdit selection text (paragraph separators) for vocabulary."""
    return text.replace("\u2029", " ").strip()


def surface_form_at_read_position(pane: QTextBrowser, position: QPoint) -> str:
    """Return the highlighted word or the word under *position* in the read pane."""
    selected = normalize_reader_selection(pane.textCursor().selectedText())
    if selected:
        return selected
    cursor = pane.cursorForPosition(position)
    cursor.select(QTextCursor.SelectionType.WordUnderCursor)
    return normalize_reader_selection(cursor.selectedText())
