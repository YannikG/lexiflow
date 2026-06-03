"""Regression tests for reader highlight-add selection and context menu."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from lexiflow_ui.reader_selection import (
    normalize_reader_selection,
    surface_form_at_read_position,
)
from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QMenu, QTextBrowser

from tests.ui.reader_test_helpers import reader_with_text
from tests.ui.vocabulary_helpers import select_word_in_reader


def test_normalize_reader_selection_replaces_paragraph_separator() -> None:
    assert normalize_reader_selection("cor\u2029riendo") == "cor riendo"


def test_surface_form_at_read_position_uses_existing_selection(
    qtbot, tmp_path: Path
) -> None:
    data_root = tmp_path / "LexiFlow"
    reader = reader_with_text(qtbot, data_root)
    selected = select_word_in_reader(reader)
    pane = reader.findChild(QTextBrowser, "reader_read_pane")
    assert pane is not None

    surface = surface_form_at_read_position(pane, QPoint(1, 1))

    assert surface == selected


def test_surface_form_at_read_position_uses_word_under_cursor(qtbot) -> None:
    pane = QTextBrowser()
    qtbot.addWidget(pane)
    pane.resize(200, 80)
    pane.setPlainText("Cuerpo")
    position = QPoint(8, 8)

    surface = surface_form_at_read_position(pane, position)

    assert surface == "Cuerpo"


def test_context_menu_add_word_passes_captured_surface_form(
    qtbot, tmp_path: Path
) -> None:
    data_root = tmp_path / "LexiFlow"
    reader = reader_with_text(qtbot, data_root)
    selected = select_word_in_reader(reader)

    with patch(
        "lexiflow_ui.widgets.reader_widget.open_highlight_add_dialog",
        return_value=False,
    ) as open_dialog:
        reader._highlight_add_word(surface_form=selected)

    open_dialog.assert_called_once()
    assert open_dialog.call_args.kwargs["surface_form"] == selected


def test_context_menu_add_word_keeps_surface_after_selection_cleared(
    qtbot, tmp_path: Path
) -> None:
    """Regression: menu action must use surface captured at open, not live cursor."""
    data_root = tmp_path / "LexiFlow"
    reader = reader_with_text(qtbot, data_root)
    selected = select_word_in_reader(reader)
    pane = reader.findChild(QTextBrowser, "reader_read_pane")
    assert pane is not None
    position = pane.cursorRect(pane.textCursor()).center()
    surface_at_open = surface_form_at_read_position(pane, position)

    triggered: list[str | None] = []

    def capture_highlight(*, surface_form: str | None = None) -> bool:
        triggered.append(surface_form)
        return False

    with patch.object(reader, "_highlight_add_word", side_effect=capture_highlight):
        menu = QMenu(reader)
        add_action = menu.addAction("Add word")
        add_action.triggered.connect(
            lambda _checked=False, form=surface_at_open: reader._highlight_add_word(
                surface_form=form
            )
        )
        cursor = pane.textCursor()
        cursor.clearSelection()
        pane.setTextCursor(cursor)
        assert normalize_reader_selection(pane.textCursor().selectedText()) == ""
        add_action.trigger()

    assert triggered == [selected]


def test_context_menu_not_shown_on_native_tab(qtbot, tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    reader = reader_with_text(qtbot, data_root, tab="native")

    with patch(
        "lexiflow_ui.widgets.reader_widget.open_highlight_add_dialog",
    ) as open_dialog:
        reader._show_read_context_menu(QPoint(1, 1))

    open_dialog.assert_not_called()
