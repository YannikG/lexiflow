"""Tests for the add text dialog."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from lexiflow_ui.dialogs.add_text_dialog import AddTextDialog
from PySide6.QtCore import Qt
from PySide6.QtGui import QClipboard
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialogButtonBox,
    QLineEdit,
    QPlainTextEdit,
)


def test_add_text_dialog_opens_with_empty_paste(qtbot, tmp_path: Path) -> None:
    dialog = AddTextDialog(
        data_root=tmp_path / "LexiFlow",
        target_language="es",
        groups=["News"],
    )
    qtbot.addWidget(dialog)
    dialog.show()
    paste = dialog.findChild(QPlainTextEdit, "add_text_paste")
    title = dialog.findChild(QLineEdit, "add_text_title")
    assert paste is not None
    assert title is not None
    assert paste.toPlainText() == ""
    assert title.text() == ""


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


def test_add_text_dialog_rejects_empty_title(
    qtbot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "lexiflow_ui.dialogs.add_text_dialog.QMessageBox.warning",
        lambda *_args, **_kwargs: None,
    )
    dialog = AddTextDialog(
        data_root=tmp_path / "LexiFlow",
        target_language="es",
        groups=["News"],
    )
    qtbot.addWidget(dialog)
    dialog.show()
    group = dialog.findChild(QComboBox, "add_text_group")
    assert group is not None
    group.setCurrentText("News")
    dialog.paste_edit().setPlainText("Hola")

    box = dialog.findChild(QDialogButtonBox)
    assert box is not None
    qtbot.mouseClick(box.button(QDialogButtonBox.StandardButton.Save), Qt.LeftButton)
    assert dialog.isVisible()
    assert dialog.form_data() is None


def test_add_text_dialog_rejects_empty_group(
    qtbot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "lexiflow_ui.dialogs.add_text_dialog.QMessageBox.warning",
        lambda *_args, **_kwargs: None,
    )
    dialog = AddTextDialog(
        data_root=tmp_path / "LexiFlow",
        target_language="es",
        groups=["News"],
    )
    qtbot.addWidget(dialog)
    dialog.show()
    title = dialog.findChild(QLineEdit, "add_text_title")
    assert title is not None
    title.setText("My title")
    dialog.paste_edit().setPlainText("Hola")
    group = dialog.findChild(QComboBox, "add_text_group")
    assert group is not None
    group.setCurrentText("   ")

    box = dialog.findChild(QDialogButtonBox)
    assert box is not None
    qtbot.mouseClick(box.button(QDialogButtonBox.StandardButton.Save), Qt.LeftButton)
    assert dialog.isVisible()
    assert dialog.form_data() is None


def test_add_text_dialog_rejects_empty_paste(
    qtbot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "lexiflow_ui.dialogs.add_text_dialog.QMessageBox.warning",
        lambda *_args, **_kwargs: None,
    )
    dialog = AddTextDialog(
        data_root=tmp_path / "LexiFlow",
        target_language="es",
        groups=["News"],
    )
    qtbot.addWidget(dialog)
    dialog.show()
    title = dialog.findChild(QLineEdit, "add_text_title")
    assert title is not None
    title.setText("My title")
    group = dialog.findChild(QComboBox, "add_text_group")
    assert group is not None
    group.setCurrentText("News")

    box = dialog.findChild(QDialogButtonBox)
    assert box is not None
    qtbot.mouseClick(box.button(QDialogButtonBox.StandardButton.Save), Qt.LeftButton)
    assert dialog.isVisible()
    assert dialog.form_data() is None


def test_add_text_dialog_returns_title_in_form_data(qtbot, tmp_path: Path) -> None:
    dialog = AddTextDialog(
        data_root=tmp_path / "LexiFlow",
        target_language="es",
        groups=["News"],
    )
    qtbot.addWidget(dialog)
    dialog.show()
    title = dialog.findChild(QLineEdit, "add_text_title")
    group = dialog.findChild(QComboBox, "add_text_group")
    assert title is not None and group is not None
    title.setText("  Article title  ")
    group.setCurrentText("News")
    dialog.paste_edit().setPlainText("Body text")

    data = dialog.form_data()

    assert data is not None
    assert data.title == "Article title"


def test_add_text_dialog_rejects_title_with_hash(
    qtbot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "lexiflow_ui.dialogs.add_text_dialog.QMessageBox.warning",
        lambda *_args, **_kwargs: None,
    )
    dialog = AddTextDialog(
        data_root=tmp_path / "LexiFlow",
        target_language="es",
        groups=["News"],
    )
    qtbot.addWidget(dialog)
    dialog.show()
    title = dialog.findChild(QLineEdit, "add_text_title")
    group = dialog.findChild(QComboBox, "add_text_group")
    assert title is not None and group is not None
    title.setText("Bad # title")
    group.setCurrentText("News")
    dialog.paste_edit().setPlainText("Body text")

    box = dialog.findChild(QDialogButtonBox)
    assert box is not None
    qtbot.mouseClick(box.button(QDialogButtonBox.StandardButton.Save), Qt.LeftButton)

    assert dialog.isVisible()
    assert dialog.form_data() is None


def test_add_text_dialog_treats_blank_source_url_as_missing(
    qtbot, tmp_path: Path
) -> None:
    dialog = AddTextDialog(
        data_root=tmp_path / "LexiFlow",
        target_language="es",
        groups=["News"],
    )
    qtbot.addWidget(dialog)
    dialog.show()
    title = dialog.findChild(QLineEdit, "add_text_title")
    group = dialog.findChild(QComboBox, "add_text_group")
    source_url = dialog.findChild(QLineEdit, "add_text_source_url")
    assert title is not None and group is not None and source_url is not None
    title.setText("Article title")
    group.setCurrentText("News")
    source_url.setText("   ")
    dialog.paste_edit().setPlainText("Body text")

    data = dialog.form_data()

    assert data is not None
    assert data.source_url is None
