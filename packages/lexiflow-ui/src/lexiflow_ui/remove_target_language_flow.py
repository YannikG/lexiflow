"""UI flow to export vocabulary before removing a target language."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.config.settings import Settings
from lexiflow_core.config.settings_store import SettingsStore
from lexiflow_core.languages.remove_target import (
    RemoveTargetLanguageError,
    remove_target_language,
)
from lexiflow_core.vocabulary.export import export_vocabulary_zip
from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox, QWidget


def offer_remove_target_language(
    parent: QWidget,
    *,
    data_root: Path,
    language_code: str,
    settings: Settings,
    settings_store: SettingsStore,
) -> Settings | None:
    """Offer export, confirm removal, and wipe the target language folder."""
    export_first = QMessageBox.question(
        parent,
        "Remove target language",
        (
            f"Export vocabulary for {language_code} before removing the language? "
            "All texts and data for this language will be deleted."
        ),
        QMessageBox.StandardButton.Yes
        | QMessageBox.StandardButton.No
        | QMessageBox.StandardButton.Cancel,
        QMessageBox.StandardButton.Yes,
    )
    if export_first == QMessageBox.StandardButton.Cancel:
        return None
    if export_first == QMessageBox.StandardButton.Yes:
        path, _filter = QFileDialog.getSaveFileName(
            parent,
            "Export vocabulary",
            f"vocabulary-{language_code}.zip",
            "Zip archives (*.zip)",
        )
        if not path:
            return None
        export_vocabulary_zip(
            Path(path),
            data_root=data_root,
            language_code=language_code,
        )
    confirm = QMessageBox.warning(
        parent,
        "Remove target language",
        (
            f"This permanently deletes all texts, vocabulary, and metadata for "
            f"{language_code}. This cannot be undone."
        ),
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )
    if confirm != QMessageBox.StandardButton.Yes:
        return None
    typed, ok = QInputDialog.getText(
        parent,
        "Confirm removal",
        f'Type "{language_code}" to confirm removal:',
    )
    if not ok or typed.strip() != language_code:
        return None
    try:
        return remove_target_language(
            data_root,
            language_code,
            settings_store=settings_store,
            settings=settings,
        )
    except (RemoveTargetLanguageError, OSError) as exc:
        QMessageBox.warning(
            parent,
            "Remove target language",
            f"Failed to remove target language: {exc}",
        )
        return None
