"""Word panel below the simplified reader with new and learned tabs."""

from __future__ import annotations

from lexiflow_core.vocabulary.models import (
    DifficultyRating,
    NewWordSuggestion,
    VocabularyEntry,
)
from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtWidgets import (
    QHeaderView,
    QMenu,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from lexiflow_ui.dialogs.word_detail_dialog import (
    open_new_word_suggestion_detail,
    open_vocabulary_entry_detail,
)
from lexiflow_ui.word_category_labels import word_category_label

WORD_PANEL_MAX_HEIGHT = 200

_DIFFICULTY_LABELS = {
    DifficultyRating.HARD: "Hard",
    DifficultyRating.WELL: "Well",
    DifficultyRating.FLUENT: "Fluent",
    DifficultyRating.EASY: "Easy",
}


class WordPanel(QWidget):
    """Tabbed tables for new word suggestions and already learned vocabulary."""

    add_requested = Signal(NewWordSuggestion)
    edit_requested = Signal(VocabularyEntry)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("word_panel")
        self.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Maximum,
        )
        self.setMaximumHeight(WORD_PANEL_MAX_HEIGHT)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(4)

        self._tabs = QTabWidget(self)
        self._tabs.setObjectName("word_panel_tabs")

        self._new_table = self._make_table(
            object_name="word_panel_new_table",
            headers=["Lemma", "Gloss", "Category", "Level", ""],
        )
        self._learned_table = self._make_table(
            object_name="word_panel_learned_table",
            headers=["Lemma", "Category", "Translation", "Level", "Difficulty"],
        )

        self._tabs.addTab(self._new_table, "New words")
        self._tabs.addTab(self._learned_table, "Learned")
        layout.addWidget(self._tabs)
        self._new_suggestions: tuple[NewWordSuggestion, ...] = ()
        self._learned_entries: tuple[VocabularyEntry, ...] = ()
        self._new_table.cellDoubleClicked.connect(self._on_new_word_double_clicked)
        self._learned_table.cellDoubleClicked.connect(
            self._on_learned_word_double_clicked
        )
        self._learned_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._learned_table.customContextMenuRequested.connect(
            self._show_learned_context_menu
        )
        self.hide()

    def clear(self) -> None:
        """Hide the panel and remove all rows."""
        self._populate_new_table(())
        self._populate_learned_table(())
        self.hide()

    def set_content(
        self,
        *,
        new_words: tuple[NewWordSuggestion, ...],
        learned_words: tuple[VocabularyEntry, ...],
    ) -> None:
        """Replace tab contents and show the panel when either tab has rows."""
        self._populate_new_table(new_words)
        self._populate_learned_table(learned_words)
        if not new_words and not learned_words:
            self.hide()
            return
        if new_words:
            self._tabs.setCurrentWidget(self._new_table)
        else:
            self._tabs.setCurrentWidget(self._learned_table)
        self.show()

    def _make_table(self, *, object_name: str, headers: list[str]) -> QTableWidget:
        table = QTableWidget(self)
        table.setObjectName(object_name)
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        if len(headers) > 2:
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        if len(headers) > 4:
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        return table

    def _populate_new_table(self, suggestions: tuple[NewWordSuggestion, ...]) -> None:
        self._new_suggestions = suggestions
        self._new_table.setRowCount(len(suggestions))
        for row, suggestion in enumerate(suggestions):
            self._new_table.setItem(row, 0, QTableWidgetItem(suggestion.lemma))
            self._new_table.setItem(row, 1, QTableWidgetItem(suggestion.gloss))
            self._new_table.setItem(
                row, 2, QTableWidgetItem(word_category_label(suggestion.word_category))
            )
            self._new_table.setItem(
                row, 3, QTableWidgetItem(suggestion.suggested_level.value)
            )
            add_button = QPushButton("Add", self._new_table)
            add_button.setObjectName("word_panel_add_button")
            add_button.clicked.connect(
                lambda _checked=False, item=suggestion: self.add_requested.emit(item)
            )
            self._new_table.setCellWidget(row, 4, add_button)

    def _populate_learned_table(self, entries: tuple[VocabularyEntry, ...]) -> None:
        self._learned_entries = entries
        self._learned_table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            self._learned_table.setItem(row, 0, QTableWidgetItem(entry.lemma))
            self._learned_table.setItem(
                row, 1, QTableWidgetItem(word_category_label(entry.word_category))
            )
            self._learned_table.setItem(row, 2, QTableWidgetItem(entry.translation))
            self._learned_table.setItem(
                row, 3, QTableWidgetItem(entry.level_when_learned.value)
            )
            self._learned_table.setItem(
                row,
                4,
                QTableWidgetItem(_DIFFICULTY_LABELS[entry.difficulty_rating]),
            )

    def _on_new_word_double_clicked(self, row: int, _column: int) -> None:
        if row < 0 or row >= len(self._new_suggestions):
            return
        open_new_word_suggestion_detail(self._new_suggestions[row], parent=self)

    def _on_learned_word_double_clicked(self, row: int, _column: int) -> None:
        if row < 0 or row >= len(self._learned_entries):
            return
        open_vocabulary_entry_detail(self._learned_entries[row], parent=self)

    def _learned_entry_at_position(self, position: QPoint) -> VocabularyEntry | None:
        index = self._learned_table.indexAt(position)
        if not index.isValid():
            return None
        row = index.row()
        if row < 0 or row >= len(self._learned_entries):
            return None
        return self._learned_entries[row]

    def _show_learned_context_menu(self, position: QPoint) -> None:
        entry = self._learned_entry_at_position(position)
        if entry is None:
            return
        menu = QMenu(self)
        edit_action = menu.addAction("Edit word")
        chosen = menu.exec(self._learned_table.viewport().mapToGlobal(position))
        if chosen is edit_action:
            self.edit_requested.emit(entry)
