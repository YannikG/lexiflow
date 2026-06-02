"""Tests for removing a target language."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.config.paths import language_data_root, vocabulary_db_path
from lexiflow_core.config.settings import Settings
from lexiflow_core.config.settings_store import SettingsStore
from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.languages.remove_target import remove_target_language
from lexiflow_core.languages.setup import add_target_with_spacy_download
from lexiflow_core.languages.store import LanguageStore
from lexiflow_core.vocabulary.store import VocabularyStore


def test_remove_target_language_wipes_language_folder(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    add_target_with_spacy_download(data_root, "es", CEFRLevel.A2)
    VocabularyStore(data_root, "es").add_entry(
        lemma="correr",
        translation="to run",
        level_when_learned=CEFRLevel.A2,
    )
    config_dir = tmp_path / "config"
    settings_store = SettingsStore(config_dir)
    settings = Settings(
        data_root=data_root,
        native_language="en",
        active_target_language="es",
        onboarding_complete=True,
    )
    settings_store.save(settings)

    updated = remove_target_language(
        data_root,
        "es",
        settings_store=settings_store,
        settings=settings,
    )

    assert not language_data_root(data_root, "es").exists()
    assert not vocabulary_db_path(data_root, "es").exists()
    assert "es" not in LanguageStore(data_root).list_targets()
    assert updated.active_target_language is None
