"""Dialog to confirm adding a word to vocabulary."""

from __future__ import annotations

from dataclasses import dataclass

from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.vocabulary.models import (
    DifficultyRating,
    VocabularyEntry,
    WordCategory,
)
from PySide6.QtCore import QElapsedTimer, QTimer
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QTextEdit,
    QWidget,
)

from lexiflow_ui.lemma_suggestions import (
    LEMMA_FILL_POLL_MS,
    LEMMA_FILL_TIMEOUT_MS,
    AsyncLemmaFill,
    LemmaSuggestions,
)
from lexiflow_ui.word_category_labels import WORD_CATEGORY_LABELS


@dataclass(frozen=True)
class AddWordForm:
    lemma: str
    translation: str
    explanation: str
    level_when_learned: CEFRLevel
    word_category: WordCategory


@dataclass(frozen=True)
class EditWordForm:
    lemma: str
    translation: str
    explanation: str
    level_when_learned: CEFRLevel
    word_category: WordCategory
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


def _combo_category(combo: QComboBox) -> WordCategory | None:
    category = combo.currentData()
    if isinstance(category, str):
        try:
            category = WordCategory(category)
        except ValueError:
            return None
    if isinstance(category, WordCategory):
        return category
    return None


def _populate_category_combo(combo: QComboBox, *, selected: WordCategory) -> None:
    for category in WordCategory:
        combo.addItem(WORD_CATEGORY_LABELS[category], category.value)
    index = combo.findData(selected.value)
    if index >= 0:
        combo.setCurrentIndex(index)


class AddWordDialog(QDialog):
    def __init__(
        self,
        *,
        default_level: CEFRLevel,
        default_category: WordCategory = WordCategory.OTHER,
        lemma: str = "",
        translation: str = "",
        explanation: str = "",
        async_lemma_fill: AsyncLemmaFill | None = None,
        auto_fill_on_open: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("add_word_dialog")
        self.setWindowTitle("Add word")
        self._async_lemma_fill = async_lemma_fill
        self._auto_fill_on_open = auto_fill_on_open
        self._auto_fill_done = False
        self._fill_in_progress = False
        self._pending_surface = ""
        self._fill_timer: QTimer | None = None
        self._fill_elapsed = QElapsedTimer()
        layout = QFormLayout(self)

        self._lemma = QLineEdit(self)
        self._lemma.setObjectName("add_word_lemma")
        self._lemma.setText(lemma)
        layout.addRow("Lemma", self._lemma)

        self._loading_label = QLabel("Filling with LLM…", self)
        self._loading_label.setObjectName("add_word_fill_loading_label")
        self._loading_label.hide()
        layout.addRow("", self._loading_label)

        self._loading_bar = QProgressBar(self)
        self._loading_bar.setObjectName("add_word_fill_loading_bar")
        self._loading_bar.setRange(0, 0)
        self._loading_bar.hide()
        layout.addRow("", self._loading_bar)

        self._category = QComboBox(self)
        self._category.setObjectName("add_word_category")
        _populate_category_combo(self._category, selected=default_category)
        layout.addRow("Category", self._category)

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
        buttons.accepted.connect(self._try_accept)
        buttons.rejected.connect(self.reject)
        self._button_box = buttons
        layout.addRow(buttons)
        self._interactive_fields = (
            self._lemma,
            self._category,
            self._translation,
            self._explanation,
            self._level,
        )
        self._update_ok_enabled()

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        if (
            self._auto_fill_on_open
            and not self._auto_fill_done
            and self._async_lemma_fill is not None
            and self._lemma.text().strip()
        ):
            self._auto_fill_done = True
            QTimer.singleShot(0, self._start_lemma_fill)

    def _start_lemma_fill(self) -> None:
        if self._async_lemma_fill is None or self._fill_in_progress:
            return
        surface_form = self._lemma.text().strip()
        if not surface_form:
            return
        self._pending_surface = surface_form
        self._set_loading(True)
        self._async_lemma_fill.begin(surface_form)
        self._fill_elapsed.start()
        self._fill_timer = QTimer(self)
        self._fill_timer.timeout.connect(self._poll_lemma_fill)
        self._fill_timer.start(LEMMA_FILL_POLL_MS)

    def _poll_lemma_fill(self) -> None:
        if self._async_lemma_fill is None:
            return
        suggestions = self._async_lemma_fill.poll(self._pending_surface)
        if suggestions is None:
            if self._fill_elapsed.elapsed() >= LEMMA_FILL_TIMEOUT_MS:
                self._finish_fill(
                    failed=True,
                    message="Timed out waiting for LLM inference.",
                )
            return
        if not suggestions.lemma and not suggestions.translation:
            self._finish_fill(
                failed=True,
                message="Could not infer word details. Fill the fields manually.",
            )
            return
        self._apply_suggestions(suggestions)
        self._finish_fill(failed=False)

    def _try_accept(self) -> None:
        if self._fill_in_progress:
            return
        lemma = self._lemma.text().strip()
        translation = self._translation.text().strip()
        if not lemma or not translation:
            QMessageBox.information(
                self,
                "Add word",
                "Lemma and translation are required.",
            )
            return
        self.accept()

    def _finish_fill(self, *, failed: bool, message: str = "") -> None:
        if self._fill_timer is not None:
            self._fill_timer.stop()
            self._fill_timer = None
        self._set_loading(False)
        self._update_ok_enabled()
        if failed and message:
            QMessageBox.warning(self, "Add word", message)

    def _update_ok_enabled(self) -> None:
        ok_button = self._button_box.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button is None:
            return
        if self._fill_in_progress:
            ok_button.setEnabled(False)
            return
        lemma = self._lemma.text().strip()
        translation = self._translation.text().strip()
        ok_button.setEnabled(bool(lemma and translation))

    def _set_loading(self, loading: bool) -> None:
        self._fill_in_progress = loading
        self._loading_label.setVisible(loading)
        self._loading_bar.setVisible(loading)
        for field in self._interactive_fields:
            field.setEnabled(not loading)
        self._update_ok_enabled()

    def _apply_suggestions(self, suggestions: LemmaSuggestions) -> None:
        if suggestions.lemma:
            self._lemma.setText(suggestions.lemma)
        if suggestions.translation:
            self._translation.setText(suggestions.translation)
        if suggestions.explanation:
            self._explanation.setPlainText(suggestions.explanation)
        index = self._category.findData(suggestions.word_category.value)
        if index >= 0:
            self._category.setCurrentIndex(index)

    def form(self) -> AddWordForm | None:
        if self.exec() != int(QDialog.DialogCode.Accepted):
            return None
        lemma = self._lemma.text().strip()
        translation = self._translation.text().strip()
        if not lemma or not translation:
            return None
        level_value = _combo_level(self._level)
        category = _combo_category(self._category)
        if level_value is None or category is None:
            return None
        return AddWordForm(
            lemma=lemma,
            translation=translation,
            explanation=self._explanation.toPlainText().strip(),
            level_when_learned=level_value,
            word_category=category,
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
        layout.addRow("Lemma", self._lemma)

        self._category = QComboBox(self)
        self._category.setObjectName("edit_word_category")
        _populate_category_combo(self._category, selected=entry.word_category)
        layout.addRow("Category", self._category)

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
        lemma = self._lemma.text().strip()
        translation = self._translation.text().strip()
        if not lemma or not translation:
            QMessageBox.information(
                self,
                "Edit word",
                "Lemma and translation are required.",
            )
            return None
        level_value = _combo_level(self._level)
        difficulty = _combo_difficulty(self._difficulty)
        category = _combo_category(self._category)
        if level_value is None or difficulty is None or category is None:
            return None
        return EditWordForm(
            lemma=lemma,
            translation=translation,
            explanation=self._explanation.toPlainText().strip(),
            level_when_learned=level_value,
            word_category=category,
            difficulty_rating=difficulty,
        )
