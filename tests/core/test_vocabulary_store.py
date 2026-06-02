"""Tests for minimal vocabulary store."""

from __future__ import annotations

from pathlib import Path

import pytest
from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.vocabulary.models import (
    DifficultyRating,
    NewWordSuggestion,
    VocabularySort,
)
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


def test_add_entry_rejects_duplicate_lemma(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    store = VocabularyStore(data_root, "es")
    store.add_entry(
        lemma="correr",
        translation="to run",
        level_when_learned=CEFRLevel.A2,
    )

    with pytest.raises(VocabularyStoreError, match="duplicate lemma"):
        store.add_entry(
            lemma="correr",
            translation="jog",
            level_when_learned=CEFRLevel.A2,
        )


def test_list_entries_sorts_alphabetically(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    store = VocabularyStore(data_root, "es")
    store.add_entry(lemma="zebra", translation="z", level_when_learned=CEFRLevel.A1)
    store.add_entry(lemma="apple", translation="a", level_when_learned=CEFRLevel.A1)

    entries = store.list_entries(sort=VocabularySort.ALPHABETICAL)
    lemmas = [entry.lemma for entry in entries]

    assert lemmas == ["apple", "zebra"]


def test_list_entries_sorts_by_level(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    store = VocabularyStore(data_root, "es")
    store.add_entry(lemma="advanced", translation="a", level_when_learned=CEFRLevel.C1)
    store.add_entry(lemma="beginner", translation="b", level_when_learned=CEFRLevel.A1)

    entries = store.list_entries(sort=VocabularySort.LEVEL)
    lemmas = [entry.lemma for entry in entries]

    assert lemmas == ["beginner", "advanced"]


def test_list_entries_sorts_by_difficulty(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    store = VocabularyStore(data_root, "es")
    store.add_entry(
        lemma="mastered",
        translation="m",
        level_when_learned=CEFRLevel.A1,
        difficulty_rating=DifficultyRating.EASY,
    )
    store.add_entry(
        lemma="learning",
        translation="l",
        level_when_learned=CEFRLevel.A1,
        difficulty_rating=DifficultyRating.HARD,
    )

    entries = store.list_entries(sort=VocabularySort.DIFFICULTY)
    lemmas = [entry.lemma for entry in entries]

    assert lemmas == ["learning", "mastered"]


def test_list_entries_sorts_by_recent(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    store = VocabularyStore(data_root, "es")
    store.add_entry(lemma="first", translation="f", level_when_learned=CEFRLevel.A1)
    store.add_entry(lemma="second", translation="s", level_when_learned=CEFRLevel.A1)

    entries = store.list_entries(sort=VocabularySort.RECENT)
    lemmas = [entry.lemma for entry in entries]

    assert lemmas == ["second", "first"]


def test_update_entry_can_rename_lemma(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    store = VocabularyStore(data_root, "es")
    store.add_entry(
        lemma="correr",
        translation="to run",
        level_when_learned=CEFRLevel.A2,
    )

    updated = store.update_entry("correr", new_lemma="trotar", translation="to jog")

    assert updated.lemma == "trotar"
    assert store.has_lemma("trotar")
    assert not store.has_lemma("correr")


def test_update_entry_rejects_duplicate_lemma_on_rename(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    store = VocabularyStore(data_root, "es")
    store.add_entry(
        lemma="correr",
        translation="to run",
        level_when_learned=CEFRLevel.A2,
    )
    store.add_entry(
        lemma="nadar",
        translation="to swim",
        level_when_learned=CEFRLevel.A2,
    )

    with pytest.raises(VocabularyStoreError, match="duplicate lemma"):
        store.update_entry("correr", new_lemma="nadar")


def test_update_entry_rename_removes_old_word_embedding(tmp_path: Path) -> None:
    from lexiflow_core.embeddings.fake import FakeEmbedder
    from lexiflow_core.vectors.store import VectorStore

    data_root = tmp_path / "LexiFlow"
    store = VocabularyStore(data_root, "es")
    store.add_entry(
        lemma="correr",
        translation="to run",
        level_when_learned=CEFRLevel.A2,
    )
    vectors = VectorStore(data_root, "es")
    embedder = FakeEmbedder()
    vectors.upsert_word_vector("correr", embedder.embed("correr"))
    assert vectors.search_similar_words(embedder.embed("correr"), limit=1)

    store.update_entry("correr", new_lemma="trotar", translation="to jog")

    assert not vectors.search_similar_words(embedder.embed("correr"), limit=1)


def test_promote_fluency_steps_difficulty(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    store = VocabularyStore(data_root, "es")
    store.add_entry(
        lemma="correr",
        translation="to run",
        level_when_learned=CEFRLevel.A2,
    )

    promoted = store.promote_fluency("correr")

    assert promoted.difficulty_rating == DifficultyRating.WELL


def test_delete_and_restore_entry(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    store = VocabularyStore(data_root, "es")
    store.add_entry(
        lemma="correr",
        translation="to run",
        level_when_learned=CEFRLevel.A2,
    )

    snapshot = store.delete_entry("correr")
    assert store.has_lemma("correr") is False

    restored = store.restore_entry(snapshot)

    assert restored.lemma == "correr"
    assert store.has_lemma("correr")


def test_delete_entry_removes_word_embedding(tmp_path: Path) -> None:
    from lexiflow_core.embeddings.fake import FakeEmbedder
    from lexiflow_core.vectors.store import VectorStore

    data_root = tmp_path / "LexiFlow"
    store = VocabularyStore(data_root, "es")
    store.add_entry(
        lemma="correr",
        translation="to run",
        level_when_learned=CEFRLevel.A2,
    )
    vectors = VectorStore(data_root, "es")
    vectors.upsert_word_vector("correr", FakeEmbedder().embed("correr"))
    assert vectors.search_similar_words(FakeEmbedder().embed("correr"), limit=1)

    store.delete_entry("correr")

    assert not vectors.search_similar_words(FakeEmbedder().embed("correr"), limit=1)
