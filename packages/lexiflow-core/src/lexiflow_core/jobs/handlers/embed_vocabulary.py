"""Embed vocabulary lemmas into vector storage."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.embeddings.protocol import Embedder
from lexiflow_core.embeddings.resolution import embed_with_fallback
from lexiflow_core.jobs.models import JobRecord
from lexiflow_core.jobs.service import JobService
from lexiflow_core.vectors.store import VectorStore
from lexiflow_core.vocabulary.store import VocabularyStore


def vocabulary_payload(job: JobRecord) -> tuple[str, str] | None:
    language_code = job.payload.get("language_code")
    lemma = job.payload.get("lemma")
    if language_code is None and lemma is None:
        return None
    if not isinstance(language_code, str) or not isinstance(lemma, str):
        raise ValueError(f"job {job.id} has invalid vocabulary embed payload")
    normalized = lemma.strip().lower()
    if not normalized:
        raise ValueError(f"job {job.id} has empty lemma")
    return language_code, normalized


def handle_vocabulary_embed(
    job: JobRecord,
    *,
    data_root: Path,
    embedder: Embedder,
    job_service: JobService,
    vector_store: VectorStore | None = None,
    vocabulary_store: VocabularyStore | None = None,
) -> None:
    """Embed one vocabulary lemma."""
    try:
        payload = vocabulary_payload(job)
    except ValueError as exc:
        job_service.fail(job.id, str(exc))
        return
    if payload is None:
        job_service.fail(
            job.id,
            "vocabulary embed job is missing language_code and lemma",
        )
        return

    language_code, lemma = payload
    try:
        vocab = (
            vocabulary_store
            if vocabulary_store is not None
            else VocabularyStore(data_root, language_code)
        )
        if not vocab.has_lemma(lemma):
            raise ValueError(f"vocabulary lemma not found: {lemma}")
        vector = embed_with_fallback(embedder, lemma)
        store = (
            vector_store
            if vector_store is not None
            else VectorStore(data_root, language_code)
        )
        store.upsert_word_vector(lemma, vector)
    except Exception as exc:
        job_service.fail(job.id, str(exc))
        return

    job_service.complete(job.id, {})
