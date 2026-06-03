"""Vocabulary browse is scoped to the active target language."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.config.settings import Settings
from lexiflow_core.languages.setup import add_target_with_spacy_download
from lexiflow_core.vocabulary.models import CEFRLevel
from lexiflow_core.vocabulary.store import VocabularyStore
from lexiflow_ui.widgets.vocabulary_widget import VocabularyWidget
from PySide6.QtWidgets import QApplication


def test_apply_settings_shows_only_active_language_vocabulary(
    qtbot, tmp_path: Path
) -> None:
    QApplication.instance() or QApplication([])
    data_root = tmp_path / "LexiFlow"
    add_target_with_spacy_download(data_root, "es")
    add_target_with_spacy_download(data_root, "de")
    VocabularyStore(data_root, "es").add_entry(
        lemma="correr",
        translation="to run",
        level_when_learned=CEFRLevel.A2,
    )
    VocabularyStore(data_root, "de").add_entry(
        lemma="laufen",
        translation="to run",
        level_when_learned=CEFRLevel.A2,
    )

    widget = VocabularyWidget(
        data_root=data_root,
        settings=Settings(active_target_language="es", onboarding_complete=True),
    )
    qtbot.addWidget(widget)
    widget.refresh()
    lemmas = {entry.lemma for entry in widget._browse_table._entries}
    assert lemmas == {"correr"}

    widget.apply_settings(
        Settings(active_target_language="de", onboarding_complete=True)
    )
    lemmas = {entry.lemma for entry in widget._browse_table._entries}
    assert lemmas == {"laufen"}
