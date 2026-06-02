"""Tests for scheduling vocabulary embed jobs from the UI."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.embeddings.fake import FakeEmbedder
from lexiflow_core.jobs.handlers.embed import handle_embed
from lexiflow_core.jobs.models import JobStatus, JobType
from lexiflow_core.jobs.service import JobService
from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.library.library_coordinator import LibraryCoordinator
from lexiflow_core.library.text_repository import TextRepository
from lexiflow_core.vectors.store import VectorStore
from lexiflow_core.vocabulary.store import VocabularyStore
from lexiflow_ui.vocabulary_embed_flow import schedule_vocabulary_word_embed


def test_schedule_vocabulary_word_embed_enqueues_job(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    schedule_vocabulary_word_embed(
        data_root,
        language_code="es",
        lemma="correr",
    )

    jobs = JobService(data_root).list_jobs()
    assert len(jobs) == 1
    assert jobs[0].job_type == JobType.EMBED
    assert jobs[0].payload == {"language_code": "es", "lemma": "correr"}


def test_restored_vocabulary_word_is_reembedded(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    coordinator, index = LibraryCoordinator.open(data_root)
    del coordinator
    store = VocabularyStore(data_root, "es")
    store.add_entry(
        lemma="correr",
        translation="to run",
        level_when_learned=CEFRLevel.A2,
    )
    vectors = VectorStore(data_root, "es")
    vectors.upsert_word_vector("correr", FakeEmbedder().embed("correr"))
    snapshot = store.delete_entry("correr")
    assert not vectors.search_similar_words(FakeEmbedder().embed("correr"), limit=1)

    store.restore_entry(snapshot)
    schedule_vocabulary_word_embed(
        data_root,
        language_code="es",
        lemma="correr",
    )
    job_service = JobService(data_root)
    job = job_service.claim_next()
    assert job is not None
    handle_embed(
        job,
        data_root=data_root,
        embedder=FakeEmbedder(),
        repo=TextRepository(data_root, index),
        job_service=job_service,
    )
    completed = job_service.get(job.id)
    assert completed is not None
    assert completed.status == JobStatus.COMPLETED

    hits = vectors.search_similar_words(FakeEmbedder().embed("correr"), limit=1)
    assert hits[0].lemma == "correr"
