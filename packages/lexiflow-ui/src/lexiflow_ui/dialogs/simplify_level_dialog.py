"""Dialog to choose a CEFR level before running simplify."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.languages.models import CEFRLevel
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from lexiflow_ui.simplify_flow import default_simplify_level


def open_simplify_level_dialog(
    parent: QWidget | None,
    *,
    data_root: Path,
    target_language: str,
) -> CEFRLevel | None:
    """Show level picker; return chosen level or None if cancelled."""
    dialog = SimplifyLevelDialog(
        data_root=data_root,
        target_language=target_language,
        parent=parent,
    )
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return None
    return dialog.selected_level()


class SimplifyLevelDialog(QDialog):
    def __init__(
        self,
        *,
        data_root: Path,
        target_language: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("simplify_level_dialog")
        self.setWindowTitle("Simplify")
        self._selected: CEFRLevel | None = None

        layout = QVBoxLayout(self)
        layout.addWidget(
            QLabel("Choose the CEFR level for the simplified reading text.", self)
        )

        self._list = QListWidget(self)
        self._list.setObjectName("simplify_level_list")
        default_level = default_simplify_level(data_root, target_language)
        for level in CEFRLevel:
            item = QListWidgetItem(level.value)
            item.setData(Qt.ItemDataRole.UserRole, level.value)
            self._list.addItem(item)
            if level == default_level:
                self._list.setCurrentItem(item)
        self._list.itemDoubleClicked.connect(self._accept_current)
        layout.addWidget(self._list)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self._accept_current)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def selected_level(self) -> CEFRLevel | None:
        return self._selected

    def _accept_current(self) -> None:
        item = self._list.currentItem()
        if item is None:
            return
        level_value = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(level_value, str):
            return
        try:
            self._selected = CEFRLevel(level_value.strip().upper())
        except ValueError:
            return
        self.accept()
