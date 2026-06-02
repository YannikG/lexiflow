"""Vocabulary browse mode UI tests."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.vocabulary.models import (
    DifficultyRating,
    VocabularyEntry,
    VocabularySort,
)
from lexiflow_core.vocabulary.store import VocabularyStore
from lexiflow_ui.dialogs.add_word_dialog import EditWordForm
from lexiflow_ui.widgets.vocabulary_browse_table import VocabularyBrowseTable
from PySide6.QtWidgets import QComboBox, QTableWidget

from tests.ui.test_vocabulary_study import _open_vocabulary_window, _seed_language
from tests.ui.vocabulary_helpers import trigger_browse_context_menu


def test_vocabulary_opens_browse_table(qtbot, tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    _seed_language(data_root)
    VocabularyStore(data_root, "es").add_entry(
        lemma="correr",
        translation="to run",
        level_when_learned=CEFRLevel.A2,
    )
    window = _open_vocabulary_window(qtbot, data_root)

    grid = window.findChild(QTableWidget, "vocabulary_browse_grid")
    assert grid is not None
    assert grid.isVisible()
    assert grid.rowCount() == 1


def test_browse_table_difficulty_combo_emits_change(qtbot) -> None:
    table = VocabularyBrowseTable()
    qtbot.addWidget(table)
    table.set_entries(
        (
            VocabularyEntry(
                lemma="correr",
                translation="to run",
                explanation="",
                level_when_learned=CEFRLevel.A2,
                difficulty_rating=DifficultyRating.HARD,
            ),
        )
    )
    combo = table.findChild(QComboBox, "vocabulary_browse_difficulty_combo")
    assert combo is not None
    well_index = combo.findData(DifficultyRating.WELL.value)
    assert well_index >= 0

    with qtbot.waitSignal(table.difficulty_changed, timeout=1000) as blocker:
        combo.setCurrentIndex(well_index)

    assert blocker.args == ["correr", DifficultyRating.WELL]


def test_browse_difficulty_combo_updates_store(qtbot, tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    _seed_language(data_root)
    store = VocabularyStore(data_root, "es")
    store.add_entry(
        lemma="correr",
        translation="to run",
        level_when_learned=CEFRLevel.A2,
    )

    window = _open_vocabulary_window(qtbot, data_root)

    grid = window.findChild(QTableWidget, "vocabulary_browse_grid")
    assert grid is not None
    combo = grid.cellWidget(0, 4)
    assert isinstance(combo, QComboBox)
    well_index = combo.findData(DifficultyRating.WELL.value)
    assert well_index >= 0
    combo.setCurrentIndex(well_index)

    entry = store.get("correr")
    assert entry is not None
    assert entry.difficulty_rating == DifficultyRating.WELL


def test_browse_difficulty_survives_table_refresh(qtbot, tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    _seed_language(data_root)
    store = VocabularyStore(data_root, "es")
    store.add_entry(
        lemma="correr",
        translation="to run",
        level_when_learned=CEFRLevel.A2,
    )

    window = _open_vocabulary_window(qtbot, data_root)

    grid = window.findChild(QTableWidget, "vocabulary_browse_grid")
    assert grid is not None
    combo = grid.cellWidget(0, 4)
    assert isinstance(combo, QComboBox)
    well_index = combo.findData(DifficultyRating.WELL.value)
    assert well_index >= 0
    combo.setCurrentIndex(well_index)

    window._vocabulary.refresh()
    grid = window.findChild(QTableWidget, "vocabulary_browse_grid")
    assert grid is not None
    combo = grid.cellWidget(0, 4)
    assert isinstance(combo, QComboBox)
    assert combo.currentIndex() == well_index

    entry = store.get("correr")
    assert entry is not None
    assert entry.difficulty_rating == DifficultyRating.WELL


def test_edit_via_context_menu_updates_store(
    qtbot, tmp_path: Path, monkeypatch
) -> None:
    data_root = tmp_path / "LexiFlow"
    _seed_language(data_root)
    store = VocabularyStore(data_root, "es")
    store.add_entry(
        lemma="correr",
        translation="to run",
        explanation="movement",
        level_when_learned=CEFRLevel.A2,
    )

    window = _open_vocabulary_window(qtbot, data_root)

    updated_form = EditWordForm(
        lemma="correr",
        translation="to jog",
        explanation="fast movement",
        level_when_learned=CEFRLevel.B1,
        surface_form="corriendo",
        difficulty_rating=DifficultyRating.WELL,
    )
    with patch(
        "lexiflow_ui.widgets.vocabulary_widget.prompt_edit_word",
        return_value=updated_form,
    ):
        trigger_browse_context_menu(
            window,
            row=0,
            monkeypatch=monkeypatch,
            action_text="Edit word",
        )

    entry = store.get("correr")
    assert entry is not None
    assert entry.translation == "to jog"
    assert entry.explanation == "fast movement"
    assert entry.level_when_learned == CEFRLevel.B1
    assert entry.surface_form == "corriendo"
    assert entry.difficulty_rating == DifficultyRating.WELL


def test_sort_combo_reorders_browse_table(qtbot, tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    _seed_language(data_root)
    store = VocabularyStore(data_root, "es")
    store.add_entry(lemma="zebra", translation="z", level_when_learned=CEFRLevel.A1)
    store.add_entry(lemma="apple", translation="a", level_when_learned=CEFRLevel.A1)

    window = _open_vocabulary_window(qtbot, data_root)

    sort_combo = window.findChild(QComboBox, "vocabulary_sort")
    assert sort_combo is not None
    alpha_index = sort_combo.findData(VocabularySort.ALPHABETICAL.value)
    assert alpha_index >= 0
    sort_combo.setCurrentIndex(alpha_index)

    grid = window.findChild(QTableWidget, "vocabulary_browse_grid")
    assert grid is not None
    assert grid.item(0, 0) is not None
    assert grid.item(1, 0) is not None
    assert grid.item(0, 0).text() == "apple"
    assert grid.item(1, 0).text() == "zebra"
