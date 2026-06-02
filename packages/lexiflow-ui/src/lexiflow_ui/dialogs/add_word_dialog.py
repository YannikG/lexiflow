"""Dialog to confirm adding a word to vocabulary."""

from __future__ import annotations

from dataclasses import dataclass

from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.vocabulary.models import DifficultyRating, VocabularyEntry
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QWidget,
)


@dataclass(frozen=True)
class AddWordForm:
    lemma: str
    translation: str
    explanation: str
    level_when_learned: CEFRLevel
    surface_form: str | None


@dataclass(frozen=True)
class EditWordForm:
    lemma: str
    translation: str
    explanation: str
    level_when_learned: CEFRLevel
    surface_form: str | None
    difficulty_rating: DifficultyRating


def _combo_level(combo: QComboBox) -> CEFRLevel | None:
    level_value = combo.currentData()
    if isinstance(level_value, str):
        try:
            level_value = CEFRLevel(level_value)
        except ValueError:
            return None
    if isinstance(level_value, CEFRLevel):
        return level_value
    return None


def _combo_difficulty(combo: QComboBox) -> DifficultyRating | None:
    rating = combo.currentData()
    if isinstance(rating, str):
        try:
            rating = DifficultyRating(rating)
        except ValueError:
            return None
    if isinstance(rating, DifficultyRating):
        return rating
    return None


class AddWordDialog(QDialog):
    def __init__(
        self,
        *,
        default_level: CEFRLevel,
        surface_form: str | None = None,
        lemma: str = "",
        translation: str = "",
        explanation: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("add_word_dialog")
        self.setWindowTitle("Add word")
        layout = QFormLayout(self)

        self._surface_form = QLineEdit(self)
        self._surface_form.setObjectName("add_word_surface_form")
        if surface_form:
            self._surface_form.setText(surface_form)
        layout.addRow("Surface form", self._surface_form)

        self._lemma = QLineEdit(self)
        self._lemma.setObjectName("add_word_lemma")
        self._lemma.setText(lemma)
        layout.addRow("Lemma", self._lemma)

        self._translation = QLineEdit(self)
        self._translation.setObjectName("add_word_translation")
        self._translation.setText(translation)
        layout.addRow("Translation", self._translation)

        self._explanation = QTextEdit(self)
        self._explanation.setObjectName("add_word_explanation")
        self._explanation.setPlainText(explanation)
        self._explanation.setMaximumHeight(80)
        layout.addRow("Explanation", self._explanation)

        self._level = QComboBox(self)
        self._level.setObjectName("add_word_level")
        for level in CEFRLevel:
            self._level.addItem(level.value, level)
        index = self._level.findData(default_level)
        if index >= 0:
            self._level.setCurrentIndex(index)
        layout.addRow("Level when learned", self._level)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def form(self) -> AddWordForm | None:
        if self.exec() != int(QDialog.DialogCode.Accepted):
            return None
        lemma = self._lemma.text().strip().lower()
        translation = self._translation.text().strip()
        if not lemma or not translation:
            return None
        level_value = self._level.currentData()
        if not isinstance(level_value, CEFRLevel):
            level_value = _combo_level(self._level)
        if level_value is None:
            return None
        surface = self._surface_form.text().strip() or None
        return AddWordForm(
            lemma=lemma,
            translation=translation,
            explanation=self._explanation.toPlainText().strip(),
            level_when_learned=level_value,
            surface_form=surface,
        )


_DIFFICULTY_LABELS = {
    DifficultyRating.HARD: "Hard",
    DifficultyRating.WELL: "Well",
    DifficultyRating.FLUENT: "Fluent",
    DifficultyRating.EASY: "Easy",
}


class EditWordDialog(QDialog):
    def __init__(
        self,
        *,
        entry: VocabularyEntry,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("edit_word_dialog")
        self.setWindowTitle("Edit word")
        layout = QFormLayout(self)

        self._lemma = QLineEdit(self)
        self._lemma.setObjectName("edit_word_lemma")
        self._lemma.setText(entry.lemma)
        self._lemma.setReadOnly(True)
        layout.addRow("Lemma", self._lemma)

        self._surface_form = QLineEdit(self)
        self._surface_form.setObjectName("edit_word_surface_form")
        if entry.surface_form:
            self._surface_form.setText(entry.surface_form)
        layout.addRow("Surface form", self._surface_form)

        self._translation = QLineEdit(self)
        self._translation.setObjectName("edit_word_translation")
        self._translation.setText(entry.translation)
        layout.addRow("Translation", self._translation)

        self._explanation = QTextEdit(self)
        self._explanation.setObjectName("edit_word_explanation")
        self._explanation.setPlainText(entry.explanation)
        self._explanation.setMaximumHeight(80)
        layout.addRow("Explanation", self._explanation)

        self._level = QComboBox(self)
        self._level.setObjectName("edit_word_level")
        for level in CEFRLevel:
            self._level.addItem(level.value, level)
        level_index = self._level.findData(entry.level_when_learned)
        if level_index >= 0:
            self._level.setCurrentIndex(level_index)
        layout.addRow("Level when learned", self._level)

        self._difficulty = QComboBox(self)
        self._difficulty.setObjectName("edit_word_difficulty")
        for rating in DifficultyRating:
            self._difficulty.addItem(_DIFFICULTY_LABELS[rating], rating)
        difficulty_index = self._difficulty.findData(entry.difficulty_rating)
        if difficulty_index >= 0:
            self._difficulty.setCurrentIndex(difficulty_index)
        layout.addRow("Difficulty", self._difficulty)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def form(self) -> EditWordForm | None:
        if self.exec() != int(QDialog.DialogCode.Accepted):
            return None
        translation = self._translation.text().strip()
        if not translation:
            return None
        level_value = _combo_level(self._level)
        difficulty = _combo_difficulty(self._difficulty)
        if level_value is None or difficulty is None:
            return None
        surface = self._surface_form.text().strip() or None
        return EditWordForm(
            lemma=self._lemma.text().strip().lower(),
            translation=translation,
            explanation=self._explanation.toPlainText().strip(),
            level_when_learned=level_value,
            surface_form=surface,
            difficulty_rating=difficulty,
        )
