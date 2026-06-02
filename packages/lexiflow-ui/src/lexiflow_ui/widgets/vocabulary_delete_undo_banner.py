"""Timed undo banner after a vocabulary entry is deleted."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from lexiflow_core.vocabulary.store import (
    DeletedVocabularyEntry,
    VocabularyStore,
    VocabularyStoreError,
)
from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import QHBoxLayout, QMessageBox, QPushButton, QWidget

DELETE_UNDO_WINDOW_MS = 8_000


class VocabularyDeleteUndoBanner(QWidget):
    """Show a brief undo window after delete_entry returns a snapshot."""

    restored = Signal()

    def __init__(
        self,
        *,
        data_root: Path | None,
        language_code: Callable[[], str | None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("vocabulary_delete_undo_banner")
        self._data_root = data_root
        self._language_code = language_code
        self._snapshot: DeletedVocabularyEntry | None = None
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.clear)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        label = QPushButton("Word deleted.", self)
        label.setObjectName("vocabulary_delete_undo_label")
        label.setFlat(True)
        label.setEnabled(False)
        layout.addWidget(label)
        undo_button = QPushButton("Undo", self)
        undo_button.setObjectName("vocabulary_delete_undo_button")
        undo_button.clicked.connect(self._undo)
        layout.addWidget(undo_button)
        layout.addStretch(1)
        self.hide()

    def offer(self, snapshot: DeletedVocabularyEntry) -> None:
        self._snapshot = snapshot
        self.show()
        self._timer.start(DELETE_UNDO_WINDOW_MS)

    def clear(self) -> None:
        self._timer.stop()
        self._snapshot = None
        self.hide()

    def _undo(self) -> None:
        language = self._language_code()
        snapshot = self._snapshot
        if self._data_root is None or language is None or snapshot is None:
            return
        store = VocabularyStore(self._data_root, language)
        try:
            store.restore_entry(snapshot)
        except VocabularyStoreError as error:
            QMessageBox.warning(self, "Vocabulary", str(error))
            return
        self.clear()
        self.restored.emit()
