"""Modal picker for the user's native language."""

from __future__ import annotations

from lexiflow_core.languages.catalog import get_language
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from lexiflow_ui.widgets.catalog_picker import CatalogPickerWidget


class NativeLanguageDialog(QDialog):
    def __init__(
        self,
        *,
        current_iso: str | None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("native_language_dialog")
        self.setWindowTitle("Native language")
        self._selected_iso = current_iso

        layout = QVBoxLayout(self)
        layout.addWidget(
            QLabel(
                "Choose the language you use for explanations.\n"
                "Does not change language on existing texts.",
                self,
            )
        )
        self._picker = CatalogPickerWidget(self)
        self._picker.setObjectName("native_language_picker")
        if current_iso is not None:
            self._picker.set_selected_iso(current_iso)
        layout.addWidget(self._picker)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def selected_iso(self) -> str | None:
        return self._selected_iso

    def _accept(self) -> None:
        iso = self._picker.selected_iso()
        if iso is None:
            return
        self._selected_iso = iso
        self.accept()


def language_display_name(iso: str | None) -> str:
    if iso is None:
        return "Not set"
    try:
        info = get_language(iso)
    except KeyError:
        return iso
    return f"{info.flag} {info.name} ({info.iso})"
