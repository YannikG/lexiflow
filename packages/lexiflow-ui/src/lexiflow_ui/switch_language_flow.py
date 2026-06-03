"""Switch or add target languages from the Library menu."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from lexiflow_core.config.settings import Settings
from lexiflow_core.config.settings_store import SettingsStore
from lexiflow_core.languages.setup import (
    LanguageSetupError,
    add_target_with_spacy_download,
)
from lexiflow_core.languages.switch_target import switch_active_target
from PySide6.QtWidgets import QMessageBox, QWidget

from lexiflow_ui.dialogs.switch_language_dialog import SwitchLanguageDialog


def open_switch_language_dialog(
    parent: QWidget,
    *,
    data_root: Path,
    settings: Settings,
    settings_store: SettingsStore,
    on_switched: Callable[[Settings], None],
) -> None:
    """Show language picker; invoke on_switched when active target changes."""
    dialog = SwitchLanguageDialog(
        data_root=data_root,
        active_iso=settings.active_target_language,
        parent=parent,
    )
    if dialog.exec() != int(dialog.DialogCode.Accepted):
        return

    if dialog.is_add_language:
        iso = dialog.selected_iso
        if iso is None:
            return
        native = settings.native_language
        if native is not None and native == iso:
            QMessageBox.warning(
                parent,
                "Add language",
                "Target language must differ from your native language.",
            )
            return
        try:
            add_target_with_spacy_download(data_root, iso)
            updated = switch_active_target(
                data_root=data_root,
                settings_store=settings_store,
                settings=settings,
                target_language=iso,
            )
        except (LanguageSetupError, OSError) as exc:
            QMessageBox.warning(parent, "Add language", str(exc))
            return
        on_switched(updated)
        return

    iso = dialog.selected_iso
    if iso is None or iso == settings.active_target_language:
        return
    try:
        updated = switch_active_target(
            data_root=data_root,
            settings_store=settings_store,
            settings=settings,
            target_language=iso,
        )
    except OSError as exc:
        QMessageBox.warning(parent, "Switch language", str(exc))
        return
    on_switched(updated)
