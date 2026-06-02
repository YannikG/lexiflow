"""Trash restore and empty controls."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.library.text_repository import TextRepository
from lexiflow_core.library.trash import (
    TrashItem,
    TrashItemNotFoundError,
    TrashRestoreError,
)
from lexiflow_core.vocabulary.store import VocabularyStore, VocabularyStoreError
from lexiflow_core.vocabulary.trash import (
    VocabularyTrashItem,
    empty_vocabulary_trash,
    list_vocabulary_trash,
    load_trash_snapshot,
)
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from lexiflow_ui.vocabulary_embed_flow import schedule_vocabulary_word_embed
from lexiflow_ui.worker_supervisor import WorkerSupervisor


class TrashDialog(QDialog):
    def __init__(
        self,
        *,
        data_root: Path,
        language_code: str,
        text_repository: TextRepository,
        supervisor: WorkerSupervisor | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Trash")
        self.setObjectName("trash_dialog")
        self._data_root = data_root
        self._language_code = language_code
        self._text_repo = text_repository
        self._supervisor = supervisor
        self._vocabulary_store = VocabularyStore(data_root, language_code)

        layout = QVBoxLayout(self)
        layout.addWidget(
            QLabel(f"Showing deleted items for {language_code.upper()}", self)
        )

        self._tabs = QTabWidget(self)
        self._tabs.setObjectName("trash_tabs")

        self._texts_list = QListWidget(self)
        self._texts_list.setObjectName("library_trash_list")
        self._tabs.addTab(self._texts_list, "Texts")

        self._vocabulary_list = QListWidget(self)
        self._vocabulary_list.setObjectName("vocabulary_trash_list")
        self._tabs.addTab(self._vocabulary_list, "Vocabulary")

        layout.addWidget(self._tabs)

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        self._empty_trash_button = QPushButton("Empty trash", self)
        self._empty_trash_button.setObjectName("trash_empty_button")
        self._empty_trash_button.clicked.connect(self._empty_trash)
        button_row.addWidget(self._empty_trash_button)
        self._close_button = QPushButton("Close", self)
        self._close_button.setObjectName("trash_close_button")
        self._close_button.clicked.connect(self.reject)
        button_row.addWidget(self._close_button)
        self._restore_button = QPushButton("Restore selected", self)
        self._restore_button.setObjectName("trash_restore_button")
        self._restore_button.setDefault(True)
        self._restore_button.setAutoDefault(True)
        self._restore_button.clicked.connect(self._restore_selected)
        button_row.addWidget(self._restore_button)
        layout.addLayout(button_row)

        self._reload_all()

    def _reload_all(self) -> None:
        self._reload_text_trash()
        self._reload_vocabulary_trash()

    def _reload_text_trash(self) -> None:
        self._texts_list.clear()
        for item in self._text_repo.list_trash(language_code=self._language_code):
            label = f"{item.title} · {item.group}"
            list_item = QListWidgetItem(label)
            list_item.setData(Qt.ItemDataRole.UserRole, item)
            self._texts_list.addItem(list_item)

    def _reload_vocabulary_trash(self) -> None:
        self._vocabulary_list.clear()
        for item in list_vocabulary_trash(self._data_root, self._language_code):
            label = f"{item.lemma} — {item.translation}"
            list_item = QListWidgetItem(label)
            list_item.setData(Qt.ItemDataRole.UserRole, item)
            self._vocabulary_list.addItem(list_item)

    def _active_list(self) -> tuple[QListWidget, str]:
        if self._tabs.currentIndex() == 0:
            return self._texts_list, "text"
        return self._vocabulary_list, "vocabulary"

    def _selected_text_item(self) -> TrashItem | None:
        row = self._texts_list.currentRow()
        if row < 0:
            return None
        item = self._texts_list.item(row)
        if item is None:
            return None
        stored = item.data(Qt.ItemDataRole.UserRole)
        return stored if isinstance(stored, TrashItem) else None

    def _selected_vocabulary_item(self) -> VocabularyTrashItem | None:
        row = self._vocabulary_list.currentRow()
        if row < 0:
            return None
        item = self._vocabulary_list.item(row)
        if item is None:
            return None
        stored = item.data(Qt.ItemDataRole.UserRole)
        return stored if isinstance(stored, VocabularyTrashItem) else None

    def _restore_selected(self) -> None:
        kind = self._active_list()[1]
        if kind == "text":
            self._restore_selected_text()
        else:
            self._restore_selected_vocabulary()

    def _restore_selected_text(self) -> None:
        trash_item = self._selected_text_item()
        if trash_item is None:
            QMessageBox.information(self, "Trash", "Select a trashed text to restore.")
            return
        try:
            self._text_repo.restore_from_trash(trash_item.text_id)
        except (TrashItemNotFoundError, TrashRestoreError) as error:
            QMessageBox.warning(self, "Trash", str(error))
            return
        self._reload_text_trash()
        QMessageBox.information(self, "Trash", f'Restored "{trash_item.title}".')

    def _restore_selected_vocabulary(self) -> None:
        trash_item = self._selected_vocabulary_item()
        if trash_item is None:
            QMessageBox.information(
                self, "Trash", "Select a trashed vocabulary entry to restore."
            )
            return
        snapshot = load_trash_snapshot(
            self._data_root,
            self._language_code,
            trash_item.lemma,
        )
        try:
            self._vocabulary_store.restore_entry(snapshot)
        except VocabularyStoreError as error:
            QMessageBox.warning(self, "Trash", str(error))
            return
        schedule_vocabulary_word_embed(
            self._data_root,
            language_code=self._language_code,
            lemma=trash_item.lemma,
            supervisor=self._supervisor,
        )
        self._reload_vocabulary_trash()
        QMessageBox.information(self, "Trash", f'Restored "{trash_item.lemma}".')

    def _empty_trash(self) -> None:
        kind = self._active_list()[1]
        if kind == "text":
            self._empty_text_trash()
        else:
            self._empty_vocabulary_trash()

    def _empty_text_trash(self) -> None:
        if not self._text_repo.list_trash(language_code=self._language_code):
            QMessageBox.information(self, "Trash", "Text trash is already empty.")
            return
        confirm = QMessageBox.warning(
            self,
            "Empty trash",
            f"Permanently delete all trashed texts for {self._language_code.upper()}? "
            "This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        removed = self._text_repo.empty_trash(language_code=self._language_code)
        self._reload_text_trash()
        QMessageBox.information(self, "Trash", f"Removed {removed} trashed text(s).")

    def _empty_vocabulary_trash(self) -> None:
        if not list_vocabulary_trash(self._data_root, self._language_code):
            QMessageBox.information(self, "Trash", "Vocabulary trash is already empty.")
            return
        confirm = QMessageBox.warning(
            self,
            "Empty trash",
            f"Permanently delete all trashed vocabulary for "
            f"{self._language_code.upper()}? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        removed = empty_vocabulary_trash(self._data_root, self._language_code)
        self._reload_vocabulary_trash()
        label = "entry" if removed == 1 else "entries"
        QMessageBox.information(
            self,
            "Trash",
            f"Removed {removed} trashed vocabulary {label}.",
        )


def open_trash_dialog(
    parent: QWidget,
    *,
    data_root: Path,
    language_code: str | None,
    text_repository: TextRepository,
    supervisor: WorkerSupervisor | None = None,
) -> None:
    """Show trash restore and empty controls for the active target language."""
    if language_code is None:
        QMessageBox.information(
            parent,
            "Trash",
            "Choose an active target language before opening trash.",
        )
        return
    dialog = TrashDialog(
        data_root=data_root,
        language_code=language_code,
        text_repository=text_repository,
        supervisor=supervisor,
        parent=parent,
    )
    dialog.exec()
