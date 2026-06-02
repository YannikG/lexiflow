"""Library backup and index maintenance from the Options menu."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.library.backup import (
    export_library_zip,
    replace_data_root_from_zip,
    restore_library_zip,
)
from lexiflow_core.library.index import LibraryIndex
from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox, QWidget

_REPLACE_CONFIRMATION = "REPLACE LIBRARY"


def export_library_backup(*, parent: QWidget, data_root: Path) -> None:
    path, _filter = QFileDialog.getSaveFileName(
        parent,
        "Export library backup",
        "lexiflow-library.zip",
        "Zip archives (*.zip)",
    )
    if not path:
        return
    export_library_zip(Path(path), data_root=data_root)
    QMessageBox.information(parent, "Backup", "Library backup exported.")


def restore_library_to_new_folder(*, parent: QWidget) -> None:
    archive, _filter = QFileDialog.getOpenFileName(
        parent,
        "Restore library backup",
        "",
        "Zip archives (*.zip)",
    )
    if not archive:
        return
    destination = QFileDialog.getExistingDirectory(
        parent,
        "Choose folder for restored library",
    )
    if not destination:
        return
    restore_library_zip(Path(archive), destination_root=Path(destination))
    QMessageBox.information(
        parent,
        "Backup",
        "Backup extracted. Point LexiFlow data root to the folder in settings "
        "when that is available, or restart with the new folder.",
    )


def replace_current_library(
    *,
    parent: QWidget,
    data_root: Path,
    library_index: LibraryIndex,
) -> bool:
    """Replace the current library from a backup zip. Returns True when replaced."""
    archive, _filter = QFileDialog.getOpenFileName(
        parent,
        "Replace current library",
        "",
        "Zip archives (*.zip)",
    )
    if not archive:
        return False
    confirm = QMessageBox.warning(
        parent,
        "Replace library",
        "This replaces your entire current library with the backup. "
        "This cannot be undone.",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )
    if confirm != QMessageBox.StandardButton.Yes:
        return False
    typed, ok = QInputDialog.getText(
        parent,
        "Confirm replace",
        f'Type "{_REPLACE_CONFIRMATION}" to confirm:',
    )
    if not ok or typed.strip() != _REPLACE_CONFIRMATION:
        return False
    replace_data_root_from_zip(Path(archive), data_root=data_root)
    library_index.rebuild_from_disk(data_root)
    QMessageBox.information(parent, "Backup", "Current library replaced from backup.")
    return True


def rebuild_library_index(
    *,
    parent: QWidget,
    data_root: Path,
    library_index: LibraryIndex,
    language_code: str | None = None,
) -> None:
    from lexiflow_core.library.trash import trashed_text_ids

    indexed_count = library_index.rebuild_from_disk(data_root)
    if language_code is not None:
        active_count = len(library_index.list_by_lang(language_code))
        trashed_count = len(trashed_text_ids(data_root, language_code=language_code))
        if trashed_count:
            message = (
                f"Rebuilt library index with {active_count} active text(s) for "
                f"{language_code.upper()}. "
                f"{trashed_count} trashed text(s) for {language_code.upper()} "
                "were not indexed."
            )
        else:
            message = (
                f"Rebuilt library index with {active_count} text(s) for "
                f"{language_code.upper()}."
            )
    elif trashed_count := len(trashed_text_ids(data_root)):
        message = (
            f"Rebuilt library index with {indexed_count} active text(s). "
            f"{trashed_count} trashed text(s) were not indexed."
        )
    else:
        message = f"Rebuilt library index with {indexed_count} text(s)."
    QMessageBox.information(
        parent,
        "Library index",
        message,
    )
