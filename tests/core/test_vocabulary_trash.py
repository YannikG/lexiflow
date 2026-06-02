"""Tests for vocabulary trash storage."""

from __future__ import annotations

from pathlib import Path

import pytest
from lexiflow_core.config.paths import vocabulary_trash_dir
from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.vocabulary.store import VocabularyStore
from lexiflow_core.vocabulary.trash import (
    VocabularyTrashItemNotFoundError,
    empty_vocabulary_trash,
    list_vocabulary_trash,
    load_trash_snapshot,
)


def test_delete_entry_archives_to_vocabulary_trash(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    store = VocabularyStore(data_root, "es")
    store.add_entry(
        lemma="correr",
        translation="to run",
        level_when_learned=CEFRLevel.A2,
    )

    store.delete_entry("correr")

    items = list_vocabulary_trash(data_root, "es")
    assert len(items) == 1
    assert items[0].lemma == "correr"
    assert items[0].translation == "to run"


def test_restore_entry_removes_vocabulary_trash_file(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    store = VocabularyStore(data_root, "es")
    store.add_entry(
        lemma="correr",
        translation="to run",
        level_when_learned=CEFRLevel.A2,
    )
    snapshot = store.delete_entry("correr")

    store.restore_entry(snapshot)

    assert list_vocabulary_trash(data_root, "es") == []


def test_list_vocabulary_trash_scoped_to_language(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
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
    VocabularyStore(data_root, "es").delete_entry("correr")
    VocabularyStore(data_root, "de").delete_entry("laufen")

    assert [item.lemma for item in list_vocabulary_trash(data_root, "es")] == ["correr"]
    assert [item.lemma for item in list_vocabulary_trash(data_root, "de")] == ["laufen"]


def test_empty_vocabulary_trash_only_removes_one_language(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
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
    VocabularyStore(data_root, "es").delete_entry("correr")
    VocabularyStore(data_root, "de").delete_entry("laufen")

    removed = empty_vocabulary_trash(data_root, "es")

    assert removed == 1
    assert list_vocabulary_trash(data_root, "es") == []
    assert [item.lemma for item in list_vocabulary_trash(data_root, "de")] == ["laufen"]


def test_load_trash_snapshot_returns_deleted_entry(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    store = VocabularyStore(data_root, "es")
    store.add_entry(
        lemma="correr",
        translation="to run",
        level_when_learned=CEFRLevel.A2,
    )
    store.delete_entry("correr")

    snapshot = load_trash_snapshot(data_root, "es", "correr")

    assert snapshot.lemma == "correr"
    assert snapshot.translation == "to run"


def test_load_trash_snapshot_missing_raises(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    with pytest.raises(VocabularyTrashItemNotFoundError):
        load_trash_snapshot(data_root, "es", "missing")


def test_vocabulary_trash_dir_under_language(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    expected = data_root / ".trash" / "vocabulary" / "es"
    assert vocabulary_trash_dir(data_root, "es") == expected
