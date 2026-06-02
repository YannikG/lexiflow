"""Tests for read-only word detail dialog."""

from __future__ import annotations

from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.vocabulary.models import (
    DifficultyRating,
    NewWordSuggestion,
    VocabularyEntry,
    WordCategory,
)
from lexiflow_ui.dialogs.word_detail_dialog import (
    new_word_suggestion_detail_dialog,
    vocabulary_entry_detail_dialog,
)
from lexiflow_ui.widgets.vocabulary_browse_table import VocabularyBrowseTable
from lexiflow_ui.widgets.word_panel import WordPanel
from PySide6.QtWidgets import QLabel, QTableWidget


def _label_text(parent, object_name: str) -> str:
    label = parent.findChild(QLabel, object_name)
    assert label is not None
    return label.text()


def test_vocabulary_entry_detail_shows_all_fields(qtbot) -> None:
    entry = VocabularyEntry(
        lemma="correr",
        translation="to run",
        explanation="Movement at speed on foot.",
        level_when_learned=CEFRLevel.A2,
        difficulty_rating=DifficultyRating.WELL,
        word_category=WordCategory.VERB,
    )
    dialog = vocabulary_entry_detail_dialog(entry)
    qtbot.addWidget(dialog)
    dialog.show()
    qtbot.waitExposed(dialog)

    assert _label_text(dialog, "word_detail_lemma") == "correr"
    assert _label_text(dialog, "word_detail_category") == "Verb"
    assert _label_text(dialog, "word_detail_translation") == "to run"
    assert _label_text(dialog, "word_detail_explanation") == (
        "Movement at speed on foot."
    )
    assert _label_text(dialog, "word_detail_level") == "A2"
    assert _label_text(dialog, "word_detail_difficulty") == "Well"


def test_new_word_suggestion_detail_shows_all_fields(qtbot) -> None:
    suggestion = NewWordSuggestion(
        lemma="nadar",
        gloss="to swim",
        suggested_level=CEFRLevel.B2,
        explanation="Move through water.",
        word_category=WordCategory.VERB,
    )
    dialog = new_word_suggestion_detail_dialog(suggestion)
    qtbot.addWidget(dialog)
    dialog.show()
    qtbot.waitExposed(dialog)

    assert _label_text(dialog, "word_detail_lemma") == "nadar"
    assert _label_text(dialog, "word_detail_category") == "Verb"
    assert _label_text(dialog, "word_detail_gloss") == "to swim"
    assert _label_text(dialog, "word_detail_explanation") == "Move through water."
    assert _label_text(dialog, "word_detail_level") == "B2"


def test_browse_table_double_click_opens_detail(qtbot, monkeypatch) -> None:
    opened: list[VocabularyEntry] = []

    monkeypatch.setattr(
        "lexiflow_ui.widgets.vocabulary_browse_table.open_vocabulary_entry_detail",
        lambda entry, *, parent=None: opened.append(entry),
    )
    table = VocabularyBrowseTable()
    qtbot.addWidget(table)
    table.set_entries(
        (
            VocabularyEntry(
                lemma="correr",
                translation="to run",
                explanation="Fast movement.",
                level_when_learned=CEFRLevel.A2,
                difficulty_rating=DifficultyRating.HARD,
                word_category=WordCategory.VERB,
            ),
        )
    )
    grid = table.findChild(QTableWidget, "vocabulary_browse_grid")
    assert grid is not None
    grid.cellDoubleClicked.emit(0, 0)

    assert len(opened) == 1
    assert opened[0].lemma == "correr"


def test_word_panel_double_click_opens_detail_for_new_and_learned(
    qtbot, monkeypatch
) -> None:
    opened_suggestions: list[NewWordSuggestion] = []
    opened_entries: list[VocabularyEntry] = []

    monkeypatch.setattr(
        "lexiflow_ui.widgets.word_panel.open_new_word_suggestion_detail",
        lambda suggestion, *, parent=None: opened_suggestions.append(suggestion),
    )
    monkeypatch.setattr(
        "lexiflow_ui.widgets.word_panel.open_vocabulary_entry_detail",
        lambda entry, *, parent=None: opened_entries.append(entry),
    )

    panel = WordPanel()
    qtbot.addWidget(panel)
    suggestion = NewWordSuggestion(
        lemma="nadar",
        gloss="to swim",
        suggested_level=CEFRLevel.A2,
        explanation="In water.",
        word_category=WordCategory.VERB,
    )
    entry = VocabularyEntry(
        lemma="correr",
        translation="to run",
        explanation="On foot.",
        level_when_learned=CEFRLevel.A1,
        difficulty_rating=DifficultyRating.EASY,
        word_category=WordCategory.VERB,
    )
    panel.set_content(new_words=(suggestion,), learned_words=(entry,))

    new_table = panel.findChild(QTableWidget, "word_panel_new_table")
    learned_table = panel.findChild(QTableWidget, "word_panel_learned_table")
    assert new_table is not None and learned_table is not None

    new_table.cellDoubleClicked.emit(0, 0)
    assert opened_suggestions == [suggestion]

    learned_table.cellDoubleClicked.emit(0, 0)
    assert opened_entries == [entry]
