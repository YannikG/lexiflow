"""Read-only modal showing all fields for a vocabulary word."""

from __future__ import annotations

from dataclasses import dataclass

from lexiflow_core.vocabulary.models import (
    DifficultyRating,
    NewWordSuggestion,
    VocabularyEntry,
)
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QWidget,
)

from lexiflow_ui.word_category_labels import word_category_label

_DIFFICULTY_LABELS = {
    DifficultyRating.HARD: "Hard",
    DifficultyRating.WELL: "Well",
    DifficultyRating.FLUENT: "Fluent",
    DifficultyRating.EASY: "Easy",
}


@dataclass(frozen=True)
class _DetailRow:
    label: str
    value: str
    object_name: str


class WordDetailDialog(QDialog):
    def __init__(
        self,
        *,
        title: str,
        rows: tuple[_DetailRow, ...],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("word_detail_dialog")
        self.setWindowTitle(title)
        layout = QFormLayout(self)
        for row in rows:
            value_label = QLabel(row.value or "—")
            value_label.setObjectName(row.object_name)
            value_label.setWordWrap(True)
            value_label.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )
            layout.addRow(row.label, value_label)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close,
            parent=self,
        )
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)


def vocabulary_entry_detail_dialog(
    entry: VocabularyEntry,
    *,
    parent: QWidget | None = None,
) -> WordDetailDialog:
    """Build a read-only modal for a vocabulary entry."""
    rows = (
        _DetailRow("Lemma", entry.lemma, "word_detail_lemma"),
        _DetailRow(
            "Category",
            word_category_label(entry.word_category),
            "word_detail_category",
        ),
        _DetailRow("Translation", entry.translation, "word_detail_translation"),
        _DetailRow("Explanation", entry.explanation, "word_detail_explanation"),
        _DetailRow(
            "Level when learned",
            entry.level_when_learned.value,
            "word_detail_level",
        ),
        _DetailRow(
            "Difficulty",
            _DIFFICULTY_LABELS[entry.difficulty_rating],
            "word_detail_difficulty",
        ),
    )
    return WordDetailDialog(
        title=f"Word details — {entry.lemma}",
        rows=rows,
        parent=parent,
    )


def new_word_suggestion_detail_dialog(
    suggestion: NewWordSuggestion,
    *,
    parent: QWidget | None = None,
) -> WordDetailDialog:
    """Build a read-only modal for a new word suggestion."""
    rows = (
        _DetailRow("Lemma", suggestion.lemma, "word_detail_lemma"),
        _DetailRow(
            "Category",
            word_category_label(suggestion.word_category),
            "word_detail_category",
        ),
        _DetailRow("Gloss", suggestion.gloss, "word_detail_gloss"),
        _DetailRow("Explanation", suggestion.explanation, "word_detail_explanation"),
        _DetailRow(
            "Suggested level",
            suggestion.suggested_level.value,
            "word_detail_level",
        ),
    )
    return WordDetailDialog(
        title=f"Word details — {suggestion.lemma}",
        rows=rows,
        parent=parent,
    )


def open_vocabulary_entry_detail(
    entry: VocabularyEntry,
    *,
    parent: QWidget | None = None,
) -> None:
    """Show a read-only modal with every stored field for a vocabulary entry."""
    vocabulary_entry_detail_dialog(entry, parent=parent).exec()


def open_new_word_suggestion_detail(
    suggestion: NewWordSuggestion,
    *,
    parent: QWidget | None = None,
) -> None:
    """Show a read-only modal with every field for a new word suggestion."""
    new_word_suggestion_detail_dialog(suggestion, parent=parent).exec()
