"""Flashcard study mode for vocabulary."""

from __future__ import annotations

import random
from pathlib import Path

from lexiflow_core.config.settings import Settings
from lexiflow_core.vocabulary.models import DifficultyRating, VocabularyEntry
from lexiflow_core.vocabulary.store import VocabularyStore, VocabularyStoreError
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QMessageBox, QStackedWidget, QVBoxLayout, QWidget

from lexiflow_ui.widgets.empty_state import EmptyStateWidget
from lexiflow_ui.widgets.vocabulary_study_card import VocabularyStudyCard


class StudyWidget(QWidget):
    vocabulary_changed = Signal()

    def __init__(
        self,
        *,
        data_root: Path,
        settings: Settings,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("study_widget")
        self._data_root = data_root
        self._settings = settings
        self._study_deck: list[VocabularyEntry] = []
        self._study_index = 0

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)

        self._stack = QStackedWidget(self)
        self._empty_state = EmptyStateWidget(
            title="No words to study yet",
            message="Words you save while reading will appear here.",
            parent=self._stack,
        )
        self._study_card = VocabularyStudyCard(self._stack)
        self._stack.addWidget(self._empty_state)
        self._stack.addWidget(self._study_card)
        root.addWidget(self._stack, stretch=1)

        self._study_card.promote_requested.connect(self._promote_entry)
        self._study_card.next_requested.connect(self._study_next)

        self.refresh()

    def apply_settings(self, settings: Settings) -> None:
        """Update active target language and reload the study deck."""
        self._settings = settings
        self.refresh()

    def refresh(self) -> None:
        language = self._settings.active_target_language
        if language is None:
            self._stack.setCurrentWidget(self._empty_state)
            return
        store = VocabularyStore(self._data_root, language)
        entries = store.list_entries()
        if not entries:
            self._stack.setCurrentWidget(self._empty_state)
            return
        self._stack.setCurrentWidget(self._study_card)
        self._reload_study_deck(entries)
        self._show_study_card()

    def _reload_study_deck(self, entries: tuple[VocabularyEntry, ...]) -> None:
        self._study_deck = [
            entry
            for entry in entries
            if entry.difficulty_rating != DifficultyRating.EASY
        ]
        random.shuffle(self._study_deck)
        self._study_index = 0

    def _show_study_card(self) -> None:
        if not self._study_deck:
            self._study_card.set_entry(None)
            return
        if self._study_index >= len(self._study_deck):
            self._study_index = 0
        self._study_card.set_entry(self._study_deck[self._study_index])

    def _study_next(self) -> None:
        if not self._study_deck:
            return
        self._study_index = (self._study_index + 1) % len(self._study_deck)
        self._show_study_card()

    def _promote_entry(self, lemma: str) -> None:
        language = self._settings.active_target_language
        if language is None:
            return
        store = VocabularyStore(self._data_root, language)
        try:
            store.promote_fluency(lemma)
        except VocabularyStoreError as error:
            QMessageBox.warning(self, "Study", str(error))
            return
        self.vocabulary_changed.emit()
        self.refresh()
        self._study_next()
