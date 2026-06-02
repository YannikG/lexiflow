"""Vocabulary entries persist when a text is deleted."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.library.library_coordinator import LibraryCoordinator
from lexiflow_core.library.models import CreateTextRequest
from lexiflow_core.library.text_repository import TextRepository
from lexiflow_core.vocabulary.store import VocabularyStore


def test_vocabulary_survives_text_delete(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    coordinator, index = LibraryCoordinator.open(data_root)
    del coordinator
    repo = TextRepository(data_root, index)
    record = repo.create_text(
        CreateTextRequest(
            title="Sample",
            group="News",
            target_language="es",
            native_language="en",
            body="hola",
        )
    )
    text_id: UUID = record.id
    VocabularyStore(data_root, "es").add_entry(
        lemma="correr",
        translation="to run",
        level_when_learned=CEFRLevel.A2,
    )

    repo.delete_to_trash(text_id)

    assert VocabularyStore(data_root, "es").has_lemma("correr")
