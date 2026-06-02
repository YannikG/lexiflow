"""Dialog to switch or add a target language."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.languages.catalog import get_language
from lexiflow_core.languages.store import LanguageStore
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from lexiflow_ui.widgets.catalog_picker import CatalogPickerWidget


class SwitchLanguageDialog(QDialog):
    def __init__(
        self,
        *,
        data_root: Path,
        active_iso: str | None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("switch_language_dialog")
        self.setWindowTitle("Switch language")
        self._data_root = data_root
        self._selected_iso: str | None = active_iso
        self._add_mode = False

        layout = QVBoxLayout(self)
        self._list = QListWidget(self)
        self._list.setObjectName("switch_language_list")
        self._list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self._list)

        self._picker = CatalogPickerWidget(self)
        self._picker.setObjectName("switch_language_add_picker")
        self._picker.hide()
        layout.addWidget(self._picker)

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        self._add_button = QPushButton("Add language…", self)
        self._add_button.setObjectName("switch_language_add_button")
        self._add_button.clicked.connect(self._show_add_picker)
        self._cancel_button = QPushButton("Cancel", self)
        self._cancel_button.setObjectName("switch_language_cancel_button")
        self._cancel_button.clicked.connect(self.reject)
        self._ok_button = QPushButton("OK", self)
        self._ok_button.setObjectName("switch_language_ok_button")
        self._ok_button.setDefault(True)
        self._ok_button.setAutoDefault(True)
        self._ok_button.clicked.connect(self.accept)
        button_row.addWidget(self._add_button)
        button_row.addWidget(self._cancel_button)
        button_row.addWidget(self._ok_button)
        layout.addLayout(button_row)

        self._populate_list(active_iso)

    @property
    def selected_iso(self) -> str | None:
        if self._add_mode:
            return self._picker.selected_iso()
        return self._selected_iso

    @property
    def is_add_language(self) -> bool:
        return self._add_mode

    def _populate_list(self, active_iso: str | None) -> None:
        self._list.clear()
        store = LanguageStore(self._data_root)
        for iso in store.list_targets():
            try:
                language = get_language(iso)
                label = f"{language.flag} {language.name}"
            except KeyError:
                label = iso
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, iso)
            self._list.addItem(item)
            if iso == active_iso:
                self._list.setCurrentItem(item)

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        iso = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(iso, str):
            self._add_mode = False
            self._picker.hide()
            self._list.show()
            self._add_button.show()
            self._selected_iso = iso

    def _show_add_picker(self) -> None:
        self._add_mode = True
        self._list.hide()
        self._add_button.hide()
        self._picker.show()
