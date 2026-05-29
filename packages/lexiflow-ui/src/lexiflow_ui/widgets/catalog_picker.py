"""Searchable language picker for onboarding and settings."""

from __future__ import annotations

from lexiflow_core.languages.catalog import list_languages
from lexiflow_core.languages.models import LanguageInfo
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)


class CatalogPickerWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._languages = list_languages()
        self._search = QLineEdit(self)
        self._search.setPlaceholderText("Search languages")
        self._search.setObjectName("catalog_search")
        self._list = QListWidget(self)
        self._list.setObjectName("catalog_list")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._search)
        layout.addWidget(self._list)
        self._search.textChanged.connect(self._apply_filter)
        self._populate(self._languages)

    def selected_iso(self) -> str | None:
        item = self._list.currentItem()
        if item is None:
            return None
        return item.data(Qt.ItemDataRole.UserRole)

    def set_selected_iso(self, iso: str) -> None:
        for row in range(self._list.count()):
            item = self._list.item(row)
            if item is not None and item.data(Qt.ItemDataRole.UserRole) == iso:
                self._list.setCurrentItem(item)
                return

    def set_filter_text(self, text: str) -> None:
        self._search.setText(text)

    def visible_isos(self) -> list[str]:
        isos: list[str] = []
        for row in range(self._list.count()):
            item = self._list.item(row)
            if item is None:
                continue
            iso = item.data(Qt.ItemDataRole.UserRole)
            if isinstance(iso, str):
                isos.append(iso)
        return isos

    def _populate(self, languages: list[LanguageInfo]) -> None:
        self._list.clear()
        for language in languages:
            item = QListWidgetItem(f"{language.flag}  {language.name}")
            item.setData(Qt.ItemDataRole.UserRole, language.iso)
            self._list.addItem(item)
        if self._list.count() > 0:
            self._list.setCurrentRow(0)

    def _apply_filter(self, text: str) -> None:
        needle = text.strip().casefold()
        if not needle:
            self._populate(self._languages)
            return
        filtered = [
            language
            for language in self._languages
            if needle in language.name.casefold() or needle in language.iso.casefold()
        ]
        self._populate(filtered)
