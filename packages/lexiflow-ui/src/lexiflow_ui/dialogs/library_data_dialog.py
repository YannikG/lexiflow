"""Library trash, backup, and index rebuild settings."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.library.backup import (
    export_library_zip,
    replace_data_root_from_zip,
    restore_library_zip,
)
from lexiflow_core.library.index import LibraryIndex
from lexiflow_core.library.text_repository import TextRepository
from lexiflow_core.library.trash import TrashItem
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

_REPLACE_CONFIRMATION = "REPLACE LIBRARY"


class LibraryDataDialog(QDialog):
    def __init__(
        self,
        *,
        data_root: Path,
        text_repository: TextRepository,
        library_index: LibraryIndex,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Library and data")
        self.setObjectName("library_data_dialog")
        self._data_root = data_root
        self._repo = text_repository
        self._index = library_index

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Trash", self))
        self._trash_list = QListWidget(self)
        self._trash_list.setObjectName("library_trash_list")
        layout.addWidget(self._trash_list)

        trash_actions = QHBoxLayout()
        self._restore_button = QPushButton("Restore selected", self)
        self._restore_button.clicked.connect(self._restore_selected)
        trash_actions.addWidget(self._restore_button)
        self._empty_trash_button = QPushButton("Empty trash", self)
        self._empty_trash_button.clicked.connect(self._empty_trash)
        trash_actions.addWidget(self._empty_trash_button)
        trash_actions.addStretch(1)
        layout.addLayout(trash_actions)

        layout.addWidget(QLabel("Backup", self))
        backup_actions = QHBoxLayout()
        export_button = QPushButton("Export library…", self)
        export_button.clicked.connect(self._export_backup)
        backup_actions.addWidget(export_button)
        restore_button = QPushButton("Restore to new folder…", self)
        restore_button.clicked.connect(self._restore_to_new_folder)
        backup_actions.addWidget(restore_button)
        replace_button = QPushButton("Replace current library…", self)
        replace_button.clicked.connect(self._replace_current_library)
        backup_actions.addWidget(replace_button)
        backup_actions.addStretch(1)
        layout.addLayout(backup_actions)

        layout.addWidget(QLabel("Index", self))
        rebuild_button = QPushButton("Rebuild library index", self)
        rebuild_button.clicked.connect(self._rebuild_index)
        layout.addWidget(rebuild_button)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, parent=self)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._reload_trash()

    def _reload_trash(self) -> None:
        self._trash_list.clear()
        for item in self._repo.list_trash():
            label = f"{item.title} ({item.target_language}) · {item.group}"
            list_item = QListWidgetItem(label)
            list_item.setData(Qt.ItemDataRole.UserRole, item)
            self._trash_list.addItem(list_item)

    def _selected_trash_item(self) -> TrashItem | None:
        row = self._trash_list.currentRow()
        if row < 0:
            return None
        item = self._trash_list.item(row)
        if item is None:
            return None
        stored = item.data(Qt.ItemDataRole.UserRole)
        return stored if isinstance(stored, TrashItem) else None

    def _restore_selected(self) -> None:
        trash_item = self._selected_trash_item()
        if trash_item is None:
            QMessageBox.information(self, "Trash", "Select a trashed text to restore.")
            return
        self._repo.restore_from_trash(trash_item.text_id)
        self._reload_trash()
        QMessageBox.information(self, "Trash", f'Restored "{trash_item.title}".')

    def _empty_trash(self) -> None:
        if not self._repo.list_trash():
            QMessageBox.information(self, "Trash", "Trash is already empty.")
            return
        confirm = QMessageBox.warning(
            self,
            "Empty trash",
            "Permanently delete all trashed texts? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        removed = self._repo.empty_trash()
        self._reload_trash()
        QMessageBox.information(self, "Trash", f"Removed {removed} trashed text(s).")

    def _export_backup(self) -> None:
        path, _filter = QFileDialog.getSaveFileName(
            self,
            "Export library backup",
            "lexiflow-library.zip",
            "Zip archives (*.zip)",
        )
        if not path:
            return
        export_library_zip(Path(path), data_root=self._data_root)
        QMessageBox.information(self, "Backup", "Library backup exported.")

    def _restore_to_new_folder(self) -> None:
        archive, _filter = QFileDialog.getOpenFileName(
            self,
            "Restore library backup",
            "",
            "Zip archives (*.zip)",
        )
        if not archive:
            return
        destination = QFileDialog.getExistingDirectory(
            self,
            "Choose folder for restored library",
        )
        if not destination:
            return
        restore_library_zip(Path(archive), destination_root=Path(destination))
        QMessageBox.information(
            self,
            "Backup",
            "Backup extracted. Point LexiFlow data root to the folder in settings "
            "when that is available, or restart with the new folder.",
        )

    def _replace_current_library(self) -> None:
        archive, _filter = QFileDialog.getOpenFileName(
            self,
            "Replace current library",
            "",
            "Zip archives (*.zip)",
        )
        if not archive:
            return
        confirm = QMessageBox.warning(
            self,
            "Replace library",
            "This replaces your entire current library with the backup. "
            "This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        typed, ok = QInputDialog.getText(
            self,
            "Confirm replace",
            f'Type "{_REPLACE_CONFIRMATION}" to confirm:',
        )
        if not ok or typed.strip() != _REPLACE_CONFIRMATION:
            return
        replace_data_root_from_zip(Path(archive), data_root=self._data_root)
        self._index.rebuild_from_disk(self._data_root)
        self._reload_trash()
        QMessageBox.information(self, "Backup", "Current library replaced from backup.")

    def _rebuild_index(self) -> None:
        count = self._index.rebuild_from_disk(self._data_root)
        QMessageBox.information(
            self,
            "Library index",
            f"Rebuilt library index with {count} text(s).",
        )


def open_library_data_dialog(
    parent: QWidget,
    *,
    data_root: Path,
    text_repository: TextRepository,
    library_index: LibraryIndex,
) -> None:
    """Show trash, backup, and rebuild controls."""
    dialog = LibraryDataDialog(
        data_root=data_root,
        text_repository=text_repository,
        library_index=library_index,
        parent=parent,
    )
    dialog.exec()
