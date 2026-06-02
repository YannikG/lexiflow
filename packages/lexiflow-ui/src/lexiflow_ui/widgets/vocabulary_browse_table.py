"""Browse table for vocabulary entries."""

from __future__ import annotations

from lexiflow_core.vocabulary.models import DifficultyRating, VocabularyEntry
from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHeaderView,
    QMenu,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from lexiflow_ui.dialogs.word_detail_dialog import open_vocabulary_entry_detail
from lexiflow_ui.word_category_labels import word_category_label

_DIFFICULTY_LABELS = {
    DifficultyRating.HARD: "Hard",
    DifficultyRating.WELL: "Well",
    DifficultyRating.FLUENT: "Fluent",
    DifficultyRating.EASY: "Easy",
}


def _difficulty_from_combo(combo: QComboBox) -> DifficultyRating | None:
    rating = combo.currentData()
    if isinstance(rating, DifficultyRating):
        return rating
    if isinstance(rating, str):
        try:
            return DifficultyRating(rating)
        except ValueError:
            return None
    return None


def _difficulty_combo_index(combo: QComboBox, rating: DifficultyRating) -> int:
    index = combo.findData(rating.value)
    if index >= 0:
        return index
    return combo.findData(rating)


class VocabularyBrowseTable(QWidget):
    edit_requested = Signal(str)
    delete_requested = Signal(str)
    difficulty_changed = Signal(str, DifficultyRating)

    def request_edit(self, row: int) -> None:
        """Request editing the entry at *row* (same as context menu Edit word)."""
        if row < 0 or row >= len(self._entries):
            return
        self.edit_requested.emit(self._entries[row].lemma)

    def request_delete(self, row: int) -> None:
        """Request deleting the entry at *row* (same as context menu Delete)."""
        if row < 0 or row >= len(self._entries):
            return
        self.delete_requested.emit(self._entries[row].lemma)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("vocabulary_browse_table")
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self._entries: tuple[VocabularyEntry, ...] = ()

        layout = QVBoxLayout(self)
        self._table = QTableWidget(self)
        self._table.setObjectName("vocabulary_browse_grid")
        self._table.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels(
            ["Lemma", "Category", "Translation", "Explanation", "Level", "Difficulty"]
        )
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._show_context_menu)
        self._table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        layout.addWidget(self._table, stretch=1)

    def set_entries(self, entries: tuple[VocabularyEntry, ...]) -> None:
        self._entries = entries
        self._table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            self._table.setItem(row, 0, QTableWidgetItem(entry.lemma))
            self._table.setItem(
                row, 1, QTableWidgetItem(word_category_label(entry.word_category))
            )
            self._table.setItem(row, 2, QTableWidgetItem(entry.translation))
            self._table.setItem(row, 3, QTableWidgetItem(entry.explanation))
            self._table.setItem(
                row, 4, QTableWidgetItem(entry.level_when_learned.value)
            )
            combo = QComboBox(self._table)
            combo.setObjectName("vocabulary_browse_difficulty_combo")
            for rating in DifficultyRating:
                combo.addItem(_DIFFICULTY_LABELS[rating], rating.value)
            index = _difficulty_combo_index(combo, entry.difficulty_rating)
            combo.blockSignals(True)
            if index >= 0:
                combo.setCurrentIndex(index)
            combo.blockSignals(False)
            combo.currentIndexChanged.connect(
                lambda _index, lemma=entry.lemma, widget=combo: self._emit_difficulty(
                    lemma, widget
                )
            )
            self._table.setCellWidget(row, 5, combo)

    def _entry_at_position(self, position: QPoint) -> VocabularyEntry | None:
        index = self._table.indexAt(position)
        if not index.isValid():
            return None
        row = index.row()
        if row < 0 or row >= len(self._entries):
            return None
        return self._entries[row]

    def _on_cell_double_clicked(self, row: int, _column: int) -> None:
        if row < 0 or row >= len(self._entries):
            return
        open_vocabulary_entry_detail(self._entries[row], parent=self)

    def _show_context_menu(self, position: QPoint) -> None:
        entry = self._entry_at_position(position)
        if entry is None:
            return
        menu = QMenu(self)
        edit_action = menu.addAction("Edit word")
        delete_action = menu.addAction("Delete")
        chosen = menu.exec(self._table.viewport().mapToGlobal(position))
        if chosen is edit_action:
            self.edit_requested.emit(entry.lemma)
        elif chosen is delete_action:
            self.delete_requested.emit(entry.lemma)

    def _emit_difficulty(self, lemma: str, combo: QComboBox) -> None:
        rating = _difficulty_from_combo(combo)
        if rating is not None:
            self.difficulty_changed.emit(lemma, rating)
