"""Flashcard surface for vocabulary study mode."""

from __future__ import annotations

from lexiflow_core.vocabulary.models import DifficultyRating, VocabularyEntry
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

_CARD_FACE_MAX_WIDTH = 560
_ACTION_BUTTON_MIN_WIDTH = 104


class VocabularyStudyCard(QWidget):
    promote_requested = Signal(str)
    next_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("vocabulary_study_card")
        self._entry: VocabularyEntry | None = None
        self._revealed = False

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.addStretch(1)

        self._card_face = QWidget(self)
        self._card_face.setObjectName("vocabulary_study_card_face")
        self._card_face.setMaximumWidth(_CARD_FACE_MAX_WIDTH)
        self._card_face.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Expanding,
        )
        face_layout = QVBoxLayout(self._card_face)
        face_layout.setContentsMargins(32, 48, 32, 48)
        face_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._card_text = QLabel(self._card_face)
        self._card_text.setObjectName("vocabulary_study_card_text")
        self._card_text.setWordWrap(True)
        self._card_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._card_text.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        self._card_text.setAutoFillBackground(False)
        face_layout.addWidget(self._card_text)

        self._explanation_label = QLabel(self._card_face)
        self._explanation_label.setObjectName("vocabulary_study_explanation")
        self._explanation_label.setWordWrap(True)
        self._explanation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._explanation_label.setAutoFillBackground(False)
        self._explanation_label.hide()
        face_layout.addWidget(self._explanation_label)

        root.addWidget(
            self._card_face,
            stretch=1,
            alignment=Qt.AlignmentFlag.AlignHCenter,
        )
        root.addStretch(1)

        buttons = QHBoxLayout()
        buttons.addStretch(1)

        self._flip_button = QPushButton("Translation", self)
        self._flip_button.setObjectName("vocabulary_study_reveal_button")
        self._flip_button.setMinimumWidth(_ACTION_BUTTON_MIN_WIDTH)
        self._flip_button.clicked.connect(self._toggle_card_face)
        buttons.addWidget(self._flip_button)

        self._got_it_slot = QWidget(self)
        self._got_it_slot.setMinimumWidth(_ACTION_BUTTON_MIN_WIDTH)
        got_it_layout = QHBoxLayout(self._got_it_slot)
        got_it_layout.setContentsMargins(0, 0, 0, 0)
        self._got_it_button = QPushButton("Got it", self._got_it_slot)
        self._got_it_button.setObjectName("vocabulary_study_got_it_button")
        self._got_it_button.setMinimumWidth(_ACTION_BUTTON_MIN_WIDTH)
        self._got_it_button.clicked.connect(self._on_got_it)
        self._got_it_button.setEnabled(False)
        got_it_layout.addWidget(self._got_it_button)
        buttons.addWidget(self._got_it_slot)

        self._next_button = QPushButton("Next", self)
        self._next_button.setObjectName("vocabulary_study_next_button")
        self._next_button.setMinimumWidth(_ACTION_BUTTON_MIN_WIDTH)
        self._next_button.clicked.connect(self.next_requested.emit)
        buttons.addWidget(self._next_button)

        buttons.addStretch(1)
        root.addLayout(buttons)

    def set_entry(self, entry: VocabularyEntry | None) -> None:
        self._entry = entry
        self._revealed = False
        if entry is None:
            self._card_text.setText("No words to study")
            self._explanation_label.hide()
            self._flip_button.setEnabled(False)
            self._flip_button.setText("Translation")
            self._got_it_button.hide()
            self._next_button.setEnabled(False)
            return
        self._show_lemma()
        explanation = entry.explanation.strip()
        if explanation:
            self._explanation_label.setText(explanation)
        else:
            self._explanation_label.clear()
        self._flip_button.setEnabled(True)
        self._flip_button.setText("Translation")
        mastered = entry.difficulty_rating == DifficultyRating.EASY
        self._got_it_button.setVisible(not mastered)
        self._next_button.setEnabled(True)

    def _show_lemma(self) -> None:
        if self._entry is None:
            return
        self._revealed = False
        self._card_text.setText(self._entry.lemma)
        self._explanation_label.hide()
        self._flip_button.setText("Translation")
        self._got_it_button.setEnabled(False)

    def _show_translation(self) -> None:
        if self._entry is None:
            return
        self._revealed = True
        self._card_text.setText(self._entry.translation)
        if self._explanation_label.text().strip():
            self._explanation_label.show()
        else:
            self._explanation_label.hide()
        self._flip_button.setText("Original")
        if self._entry.difficulty_rating != DifficultyRating.EASY:
            self._got_it_button.setEnabled(True)

    def _toggle_card_face(self) -> None:
        if self._entry is None:
            return
        if self._revealed:
            self._show_lemma()
        else:
            explanation = self._entry.explanation.strip()
            if explanation:
                self._explanation_label.setText(explanation)
            else:
                self._explanation_label.clear()
            self._show_translation()

    def _on_got_it(self) -> None:
        if self._entry is None or not self._revealed:
            return
        self.promote_requested.emit(self._entry.lemma)
