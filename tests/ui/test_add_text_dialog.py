"""Tests for the add text dialog."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from lexiflow_ui.dialogs.add_text_dialog import AddTextDialog
from PySide6.QtGui import QClipboard
from PySide6.QtWidgets import QApplication, QPlainTextEdit


def test_add_text_dialog_opens_with_empty_paste(qtbot, tmp_path: Path) -> None:
    dialog = AddTextDialog(
        data_root=tmp_path / "LexiFlow",
        target_language="es",
        groups=["News"],
    )
    qtbot.addWidget(dialog)
    dialog.show()
    paste = dialog.findChild(QPlainTextEdit, "add_text_paste")
    assert paste is not None
    assert paste.toPlainText() == ""


def test_add_text_dialog_does_not_read_clipboard(
    qtbot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    clipboard = MagicMock(spec=QClipboard)
    clipboard.text.side_effect = AssertionError("clipboard must not be read on open")
    app = QApplication.instance()
    assert app is not None
    monkeypatch.setattr(app, "clipboard", lambda: clipboard)

    dialog = AddTextDialog(
        data_root=tmp_path / "LexiFlow",
        target_language="es",
        groups=["News"],
    )
    qtbot.addWidget(dialog)
    dialog.show()
    clipboard.text.assert_not_called()
