"""Tests for the add-word dialog."""

from __future__ import annotations

from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.vocabulary.models import WordCategory
from lexiflow_ui.dialogs.add_word_dialog import AddWordDialog
from lexiflow_ui.lemma_suggestions import (
    LEMMA_FILL_POLL_MS,
    AsyncLemmaFill,
    LemmaSuggestions,
)
from PySide6.QtWidgets import QDialogButtonBox, QLineEdit, QProgressBar, QTextEdit


def _immediate_async_fill(
    suggestions: LemmaSuggestions,
) -> AsyncLemmaFill:
    pending = {"ready": False}

    def begin(_surface: str) -> None:
        pending["ready"] = True

    def poll(_surface: str) -> LemmaSuggestions | None:
        if not pending["ready"]:
            return None
        return suggestions

    return AsyncLemmaFill(begin=begin, poll=poll)


def test_add_word_dialog_auto_fill_on_open(qtbot) -> None:
    dialog = AddWordDialog(
        default_level=CEFRLevel.A2,
        lemma="corriendo",
        async_lemma_fill=_immediate_async_fill(
            LemmaSuggestions(
                lemma="correr",
                translation="to run",
                explanation="Movement at speed.",
                word_category=WordCategory.VERB,
            )
        ),
        auto_fill_on_open=True,
    )
    qtbot.addWidget(dialog)
    dialog.show()
    qtbot.wait(LEMMA_FILL_POLL_MS + 50)

    translation = dialog.findChild(QLineEdit, "add_word_translation")
    assert translation is not None
    assert translation.text() == "to run"


def test_add_word_dialog_ok_disabled_until_translation_present(qtbot) -> None:
    dialog = AddWordDialog(
        default_level=CEFRLevel.A2,
        lemma="corriendo",
        async_lemma_fill=_immediate_async_fill(
            LemmaSuggestions(
                lemma="correr",
                translation="to run",
                explanation="",
                word_category=WordCategory.VERB,
            )
        ),
        auto_fill_on_open=True,
    )
    qtbot.addWidget(dialog)
    ok_button = dialog._button_box.button(QDialogButtonBox.StandardButton.Ok)
    assert ok_button is not None
    assert not ok_button.isEnabled()

    dialog.show()
    qtbot.wait(LEMMA_FILL_POLL_MS + 50)

    assert ok_button.isEnabled()


def test_add_word_dialog_shows_loading_indicator_while_filling(qtbot) -> None:
    def begin(_surface: str) -> None:
        return

    def poll(_surface: str) -> LemmaSuggestions | None:
        return None

    dialog = AddWordDialog(
        default_level=CEFRLevel.A2,
        lemma="corriendo",
        async_lemma_fill=AsyncLemmaFill(begin=begin, poll=poll),
        auto_fill_on_open=True,
    )
    qtbot.addWidget(dialog)
    dialog.show()
    qtbot.wait(10)

    loading_bar = dialog.findChild(QProgressBar, "add_word_fill_loading_bar")
    assert loading_bar is not None
    assert loading_bar.isVisible()


def test_edit_word_dialog_allows_editing_translation_and_explanation(qtbot) -> None:
    from lexiflow_core.vocabulary.models import DifficultyRating, VocabularyEntry
    from lexiflow_ui.dialogs.add_word_dialog import EditWordDialog

    entry = VocabularyEntry(
        lemma="correr",
        translation="to run",
        explanation="Movement on foot.",
        level_when_learned=CEFRLevel.A2,
        difficulty_rating=DifficultyRating.HARD,
        word_category=WordCategory.VERB,
    )
    dialog = EditWordDialog(entry=entry)
    qtbot.addWidget(dialog)
    dialog.show()

    lemma = dialog.findChild(QLineEdit, "edit_word_lemma")
    translation = dialog.findChild(QLineEdit, "edit_word_translation")
    explanation = dialog.findChild(QTextEdit, "edit_word_explanation")
    assert lemma is not None and translation is not None and explanation is not None
    assert not lemma.isReadOnly()
    assert translation.isEnabled()
    assert not translation.isReadOnly()
    assert explanation.isEnabled()
    assert not explanation.isReadOnly()

    translation.clear()
    qtbot.keyClicks(translation, "to jog")
    lemma.clear()
    qtbot.keyClicks(lemma, "trotar")
    explanation.clear()
    qtbot.keyClicks(explanation, "Faster movement.")

    assert lemma.text() == "trotar"
    assert translation.text() == "to jog"
    assert explanation.toPlainText() == "Faster movement."
