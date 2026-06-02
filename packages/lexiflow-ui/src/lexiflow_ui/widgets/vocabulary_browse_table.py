"""Browse table for vocabulary entries."""

from __future__ import annotations

from lexiflow_core.vocabulary.models import DifficultyRating, VocabularyEntry
from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QResizeEvent, QShowEvent
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMenu,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from lexiflow_ui.dialogs.word_detail_dialog import open_vocabulary_entry_detail
from lexiflow_ui.word_category_labels import word_category_label

_DEFAULT_PAGE_SIZE = 12

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
        """Request editing the entry at *row* on the current page."""
        entry = self._entry_for_table_row(row)
        if entry is None:
            return
        self.edit_requested.emit(entry.lemma)

    def request_delete(self, row: int) -> None:
        """Request deleting the entry at *row* on the current page."""
        entry = self._entry_for_table_row(row)
        if entry is None:
            return
        self.delete_requested.emit(entry.lemma)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("vocabulary_browse_table")
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self._entries: tuple[VocabularyEntry, ...] = ()
        self._page = 0
        self._page_size = _DEFAULT_PAGE_SIZE

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

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
        self._table.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._show_context_menu)
        self._table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        layout.addWidget(self._table, stretch=1)

        pager = QHBoxLayout()
        pager.setContentsMargins(0, 0, 0, 0)
        self._prev_button = QPushButton("Previous", self)
        self._prev_button.setObjectName("vocabulary_browse_page_prev")
        self._prev_button.clicked.connect(self._go_to_previous_page)
        self._page_label = QLabel(self)
        self._page_label.setObjectName("vocabulary_browse_page_label")
        self._next_button = QPushButton("Next", self)
        self._next_button.setObjectName("vocabulary_browse_page_next")
        self._next_button.clicked.connect(self._go_to_next_page)
        pager.addStretch(1)
        pager.addWidget(self._prev_button)
        pager.addWidget(self._page_label)
        pager.addWidget(self._next_button)
        pager.addStretch(1)
        layout.addLayout(pager)

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self._recalculate_page_size()
        self._render_page()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        previous_size = self._page_size
        self._recalculate_page_size()
        if self._page_size != previous_size:
            self._render_page()

    def set_entries(self, entries: tuple[VocabularyEntry, ...]) -> None:
        self._entries = entries
        self._page = 0
        self._recalculate_page_size()
        self._render_page()

    def _recalculate_page_size(self) -> None:
        viewport_height = self._table.viewport().height()
        if viewport_height <= 0:
            return
        row_height = self._table.verticalHeader().defaultSectionSize()
        if self._table.rowCount() > 0:
            row_height = max(row_height, self._table.rowHeight(0))
        self._page_size = max(1, viewport_height // row_height)

    def _page_count(self) -> int:
        if not self._entries:
            return 1
        return max(1, (len(self._entries) + self._page_size - 1) // self._page_size)

    def _clamp_page(self) -> None:
        self._page = min(self._page, self._page_count() - 1)

    def _page_entries(self) -> tuple[VocabularyEntry, ...]:
        self._clamp_page()
        start = self._page * self._page_size
        return self._entries[start : start + self._page_size]

    def _render_page(self) -> None:
        page_entries = self._page_entries()
        self._table.setRowCount(len(page_entries))
        for row, entry in enumerate(page_entries):
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
        self._update_pager()

    def _update_pager(self) -> None:
        page_count = self._page_count()
        self._page_label.setText(f"Page {self._page + 1} of {page_count}")
        self._prev_button.setEnabled(self._page > 0)
        self._next_button.setEnabled(self._page + 1 < page_count)
        show_pager = len(self._entries) > self._page_size
        self._prev_button.setVisible(show_pager)
        self._page_label.setVisible(show_pager)
        self._next_button.setVisible(show_pager)

    def _go_to_previous_page(self) -> None:
        if self._page <= 0:
            return
        self._page -= 1
        self._render_page()

    def _go_to_next_page(self) -> None:
        if self._page + 1 >= self._page_count():
            return
        self._page += 1
        self._render_page()

    def _global_row(self, table_row: int) -> int:
        return self._page * self._page_size + table_row

    def _entry_for_table_row(self, table_row: int) -> VocabularyEntry | None:
        global_row = self._global_row(table_row)
        if global_row < 0 or global_row >= len(self._entries):
            return None
        return self._entries[global_row]

    def _entry_at_position(self, position: QPoint) -> VocabularyEntry | None:
        index = self._table.indexAt(position)
        if not index.isValid():
            return None
        return self._entry_for_table_row(index.row())

    def _on_cell_double_clicked(self, row: int, _column: int) -> None:
        entry = self._entry_for_table_row(row)
        if entry is None:
            return
        open_vocabulary_entry_detail(entry, parent=self)

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
