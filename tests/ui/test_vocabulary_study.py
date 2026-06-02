"""Vocabulary study mode UI tests."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.languages.store import LanguageStore
from lexiflow_core.vocabulary.models import DifficultyRating
from lexiflow_core.vocabulary.store import VocabularyStore
from lexiflow_ui.main_window import MainWindow
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton

from tests.ui.test_simplify_reader import _open_reader_window_without_worker


def _seed_language(data_root: Path) -> None:
    LanguageStore(data_root).add_target("es", CEFRLevel.A2)


def _open_vocabulary_window(qtbot, data_root: Path) -> MainWindow:
    window = _open_reader_window_without_worker(qtbot, data_root)
    vocabulary_action = window.navigation_action("vocabulary")
    assert vocabulary_action is not None
    vocabulary_action.trigger()
    return window


def _open_study_window(qtbot, data_root: Path) -> MainWindow:
    window = _open_reader_window_without_worker(qtbot, data_root)
    study_action = window.navigation_action("study")
    assert study_action is not None
    study_action.trigger()
    return window


def test_got_it_disabled_before_reveal(qtbot, tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    _seed_language(data_root)
    VocabularyStore(data_root, "es").add_entry(
        lemma="correr",
        translation="to run",
        level_when_learned=CEFRLevel.A2,
    )
    window = _open_study_window(qtbot, data_root)
    got_it = window.findChild(QPushButton, "vocabulary_study_got_it_button")
    flip_button = window.findChild(QPushButton, "vocabulary_study_reveal_button")
    assert got_it is not None
    assert flip_button is not None
    assert flip_button.text() == "Translation"
    assert not got_it.isEnabled()

    qtbot.mouseClick(flip_button, Qt.MouseButton.LeftButton)
    assert flip_button.text() == "Original"
    assert got_it.isEnabled()


def test_got_it_hidden_at_easy(qtbot, tmp_path: Path) -> None:
    from lexiflow_core.vocabulary.models import VocabularyEntry
    from lexiflow_ui.widgets.vocabulary_study_card import VocabularyStudyCard

    card = VocabularyStudyCard()
    qtbot.addWidget(card)
    card.set_entry(
        VocabularyEntry(
            lemma="facil",
            translation="easy",
            explanation="",
            level_when_learned=CEFRLevel.A1,
            difficulty_rating=DifficultyRating.EASY,
        )
    )
    got_it = card.findChild(type(card), "vocabulary_study_got_it_button")
    from PySide6.QtWidgets import QPushButton

    got_it = card.findChild(QPushButton, "vocabulary_study_got_it_button")
    assert got_it is not None
    assert not got_it.isVisible()


def test_study_deck_excludes_mastered_entries(qtbot, tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    _seed_language(data_root)
    store = VocabularyStore(data_root, "es")
    store.add_entry(
        lemma="facil",
        translation="easy",
        level_when_learned=CEFRLevel.A1,
        difficulty_rating=DifficultyRating.EASY,
    )
    store.add_entry(
        lemma="correr",
        translation="to run",
        level_when_learned=CEFRLevel.A2,
    )
    window = _open_study_window(qtbot, data_root)
    from PySide6.QtWidgets import QLabel

    card_text = window.findChild(QLabel, "vocabulary_study_card_text")
    assert card_text is not None
    assert card_text.text() == "correr"


def test_study_reveal_shows_explanation(qtbot, tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    _seed_language(data_root)
    VocabularyStore(data_root, "es").add_entry(
        lemma="correr",
        translation="to run",
        explanation="Movement at speed on foot.",
        level_when_learned=CEFRLevel.A2,
    )
    window = _open_study_window(qtbot, data_root)
    from PySide6.QtWidgets import QLabel, QPushButton

    explanation = window.findChild(QLabel, "vocabulary_study_explanation")
    flip_button = window.findChild(QPushButton, "vocabulary_study_reveal_button")
    card_text = window.findChild(QLabel, "vocabulary_study_card_text")
    assert explanation is not None
    assert flip_button is not None
    assert card_text is not None
    assert not explanation.isVisible()
    assert card_text.text() == "correr"

    qtbot.mouseClick(flip_button, Qt.MouseButton.LeftButton)
    assert explanation.isVisible()
    assert explanation.text() == "Movement at speed on foot."
    assert card_text.text() == "to run"
    assert flip_button.text() == "Original"

    qtbot.mouseClick(flip_button, Qt.MouseButton.LeftButton)
    assert card_text.text() == "correr"
    assert flip_button.text() == "Translation"
    assert not explanation.isVisible()


def test_browse_table_shows_explanation_column(qtbot, tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    _seed_language(data_root)
    VocabularyStore(data_root, "es").add_entry(
        lemma="correr",
        translation="to run",
        explanation="Movement at speed on foot.",
        level_when_learned=CEFRLevel.A2,
    )
    window = _open_vocabulary_window(qtbot, data_root)

    from PySide6.QtWidgets import QTableWidget

    grid = window.findChild(QTableWidget, "vocabulary_browse_grid")
    assert grid is not None
    assert grid.columnCount() == 6
    assert grid.horizontalHeaderItem(3).text() == "Explanation"
    assert grid.item(0, 3) is not None
    assert grid.item(0, 3).text() == "Movement at speed on foot."
