"""Tests for vocabulary lemma embedding jobs."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.embeddings.fake import FakeEmbedder
from lexiflow_core.embeddings.llama_server import LlamaServerEmbedError
from lexiflow_core.embeddings.resolution import embed_with_fallback
from lexiflow_core.jobs.handlers.embed import handle_embed
from lexiflow_core.jobs.models import JobRequest, JobStatus, JobType
from lexiflow_core.jobs.service import JobService
from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.library.library_coordinator import LibraryCoordinator
from lexiflow_core.library.text_repository import TextRepository
from lexiflow_core.vectors.store import VectorStore
from lexiflow_core.vocabulary.models import NewWordSuggestion
from lexiflow_core.vocabulary.store import VocabularyStore


def test_embed_job_stores_vocabulary_word_vector(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    coordinator, index = LibraryCoordinator.open(data_root)
    del coordinator
    repo = TextRepository(data_root, index)
    del repo
    vocab = VocabularyStore(data_root, "es")
    vocab.add_from_suggestion(
        NewWordSuggestion(lemma="nadar", gloss="to swim", suggested_level=CEFRLevel.A2)
    )
    job_service = JobService(data_root)
    job_service.enqueue(
        JobRequest(
            job_type=JobType.EMBED,
            payload={"language_code": "es", "lemma": "nadar"},
        )
    )
    job = job_service.claim_next()
    assert job is not None
    handle_embed(
        job,
        data_root=data_root,
        embedder=FakeEmbedder(),
        repo=TextRepository(data_root, index),
        job_service=job_service,
    )

    hits = VectorStore(data_root, "es").search_similar_words(
        FakeEmbedder().embed("nadar"),
        limit=1,
    )
    assert hits[0].lemma == "nadar"
    assert job_service.list_jobs()[0].status == JobStatus.COMPLETED


class _FailingLlamaEmbedder:
    def embed(self, text: str) -> list[float]:
        del text
        raise LlamaServerEmbedError("llama-server request failed: Connection refused")


def test_vocabulary_embed_falls_back_when_llama_server_unavailable(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "LexiFlow"
    coordinator, index = LibraryCoordinator.open(data_root)
    del coordinator
    vocab = VocabularyStore(data_root, "es")
    vocab.add_from_suggestion(
        NewWordSuggestion(lemma="nadar", gloss="to swim", suggested_level=CEFRLevel.A2)
    )
    job_service = JobService(data_root)
    job_service.enqueue(
        JobRequest(
            job_type=JobType.EMBED,
            payload={"language_code": "es", "lemma": "nadar"},
        )
    )
    job = job_service.claim_next()
    assert job is not None
    handle_embed(
        job,
        data_root=data_root,
        embedder=_FailingLlamaEmbedder(),
        repo=TextRepository(data_root, index),
        job_service=job_service,
    )

    assert job_service.list_jobs()[0].status == JobStatus.COMPLETED
    hits = VectorStore(data_root, "es").search_similar_words(
        FakeEmbedder().embed("nadar"),
        limit=1,
    )
    assert hits[0].lemma == "nadar"


def test_embed_with_fallback_uses_fake_embedder_on_llama_error() -> None:
    vector = embed_with_fallback(_FailingLlamaEmbedder(), "hola")
    assert vector == FakeEmbedder().embed("hola")
