"""Vocabulary browse delete tests."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.vocabulary.store import VocabularyStore
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox, QPushButton, QWidget

from tests.ui.test_vocabulary_study import _open_vocabulary_window, _seed_language
from tests.ui.vocabulary_helpers import trigger_browse_context_menu


def test_delete_via_context_menu_removes_entry(
    qtbot, tmp_path: Path, monkeypatch
) -> None:
    data_root = tmp_path / "LexiFlow"
    _seed_language(data_root)
    VocabularyStore(data_root, "es").add_entry(
        lemma="correr",
        translation="to run",
        level_when_learned=CEFRLevel.A2,
    )
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
    window = _open_vocabulary_window(qtbot, data_root)

    trigger_browse_context_menu(
        window,
        row=0,
        action_text="Delete",
    )
    store = VocabularyStore(data_root, "es")
    assert not store.has_lemma("correr")

    undo_banner = window._vocabulary.findChild(QWidget, "vocabulary_delete_undo_banner")
    assert undo_banner is not None
    assert undo_banner.isVisible()


def test_delete_undo_restores_entry(qtbot, tmp_path: Path, monkeypatch) -> None:
    data_root = tmp_path / "LexiFlow"
    _seed_language(data_root)
    VocabularyStore(data_root, "es").add_entry(
        lemma="correr",
        translation="to run",
        level_when_learned=CEFRLevel.A2,
    )
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
    window = _open_vocabulary_window(qtbot, data_root)
    trigger_browse_context_menu(window, row=0, action_text="Delete")

    store = VocabularyStore(data_root, "es")
    assert not store.has_lemma("correr")

    undo_button = window._vocabulary.findChild(
        QPushButton, "vocabulary_delete_undo_button"
    )
    assert undo_button is not None
    qtbot.mouseClick(undo_button, Qt.MouseButton.LeftButton)

    assert store.has_lemma("correr")
    entry = store.get("correr")
    assert entry is not None
    assert entry.translation == "to run"

    undo_banner = window._vocabulary.findChild(QWidget, "vocabulary_delete_undo_banner")
    assert undo_banner is not None
    assert not undo_banner.isVisible()
    assert store.get("correr") is not None
