"""Toolbar display for the active target language."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.config.settings import Settings
from lexiflow_core.languages.catalog import get_language
from lexiflow_core.languages.store import LanguageStore, LanguageStoreError
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget


class ActiveTargetLanguageWidget(QWidget):
    def __init__(
        self,
        *,
        settings: Settings,
        data_root: Path,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("active_target_language")
        self._label = QLabel(self)
        self._label.setObjectName("active_target_language_label")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._label)
        self.refresh(settings=settings, data_root=data_root)

    def refresh(self, *, settings: Settings, data_root: Path) -> None:
        iso = settings.active_target_language
        if iso is None:
            self._label.setText("No language")
            return
        try:
            language = get_language(iso)
            level = LanguageStore(data_root).get_user_level(iso)
            self._label.setText(f"{language.flag} {language.name} ({level.value})")
        except (KeyError, LanguageStoreError):
            self._label.setText(f"Language: {iso}")

    def label(self) -> QLabel:
        return self._label
