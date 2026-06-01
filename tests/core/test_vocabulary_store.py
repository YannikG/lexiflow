"""Tests for minimal vocabulary store."""

from __future__ import annotations

from pathlib import Path

import pytest
from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.vocabulary.models import NewWordSuggestion
from lexiflow_core.vocabulary.store import VocabularyStore, VocabularyStoreError


def test_vocabulary_store_add_and_has_lemma(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    store = VocabularyStore(data_root, "es")

    store.add_from_suggestion(
        NewWordSuggestion(lemma="correr", gloss="to run", suggested_level=CEFRLevel.A2)
    )

    assert store.has_lemma("correr")
    entries = store.list_for_simplify()
    assert len(entries) == 1
    assert entries[0].lemma == "correr"


def test_vocabulary_store_rejects_duplicate_lemma(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    store = VocabularyStore(data_root, "es")
    suggestion = NewWordSuggestion(
        lemma="correr", gloss="to run", suggested_level=CEFRLevel.A2
    )
    store.add_from_suggestion(suggestion)

    with pytest.raises(VocabularyStoreError, match="duplicate lemma"):
        store.add_from_suggestion(suggestion)


def test_vocabulary_store_reads_do_not_create_database(tmp_path: Path) -> None:
    from lexiflow_core.config.paths import vocabulary_db_path

    data_root = tmp_path / "LexiFlow"
    store = VocabularyStore(data_root, "es")
    db_path = vocabulary_db_path(data_root, "es")

    assert store.has_lemma("correr") is False
    assert store.list_for_simplify() == ()
    assert not db_path.exists()


def test_add_from_suggestion_honors_level_when_learned_override(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    store = VocabularyStore(data_root, "es")
    entry = store.add_from_suggestion(
        NewWordSuggestion(lemma="nadar", gloss="to swim", suggested_level=CEFRLevel.A1),
        level_when_learned=CEFRLevel.B1,
    )

    assert entry.level_when_learned == CEFRLevel.B1
