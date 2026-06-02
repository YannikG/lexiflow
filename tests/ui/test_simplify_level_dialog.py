"""Tests for the simplify level picker dialog."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.languages.models import CEFRLevel
from lexiflow_ui.dialogs.simplify_level_dialog import SimplifyLevelDialog
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialogButtonBox, QListWidget


def test_simplify_level_dialog_defaults_to_a2(qtbot, tmp_path: Path) -> None:
    dialog = SimplifyLevelDialog(
        data_root=tmp_path / "LexiFlow",
        target_language="es",
    )
    qtbot.addWidget(dialog)
    dialog.show()

    item = dialog._list.currentItem()
    assert item is not None
    assert item.text() == "A2"


def test_simplify_level_dialog_returns_selected_level(qtbot, tmp_path: Path) -> None:
    dialog = SimplifyLevelDialog(
        data_root=tmp_path / "LexiFlow",
        target_language="es",
    )
    qtbot.addWidget(dialog)
    dialog.show()

    list_widget = dialog.findChild(QListWidget, "simplify_level_list")
    assert list_widget is not None
    for row in range(list_widget.count()):
        item = list_widget.item(row)
        if item is not None and item.text() == "B1":
            list_widget.setCurrentItem(item)
            break

    box = dialog.findChild(QDialogButtonBox)
    assert box is not None
    ok = box.button(QDialogButtonBox.StandardButton.Ok)
    qtbot.mouseClick(ok, Qt.MouseButton.LeftButton)

    assert dialog.selected_level() == CEFRLevel.B1
