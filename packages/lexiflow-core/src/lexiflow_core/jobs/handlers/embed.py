"""Route embed jobs to text or vocabulary handlers."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.embeddings.protocol import Embedder
from lexiflow_core.jobs.handlers.embed_text import handle_text_embed
from lexiflow_core.jobs.handlers.embed_vocabulary import (
    handle_vocabulary_embed,
    vocabulary_payload,
)
from lexiflow_core.jobs.models import JobRecord
from lexiflow_core.jobs.service import JobService
from lexiflow_core.library.text_repository import TextRepository
from lexiflow_core.vectors.store import VectorStore
from lexiflow_core.vocabulary.store import VocabularyStore


def handle_embed(
    job: JobRecord,
    *,
    data_root: Path,
    embedder: Embedder,
    repo: TextRepository,
    job_service: JobService,
    vector_store: VectorStore | None = None,
    vocabulary_store: VocabularyStore | None = None,
) -> None:
    """Dispatch an embed job by payload shape."""
    try:
        payload = vocabulary_payload(job)
    except ValueError as exc:
        job_service.fail(job.id, str(exc))
        return

    if payload is not None:
        handle_vocabulary_embed(
            job,
            data_root=data_root,
            embedder=embedder,
            job_service=job_service,
            vector_store=vector_store,
            vocabulary_store=vocabulary_store,
        )
        return

    handle_text_embed(
        job,
        data_root=data_root,
        embedder=embedder,
        repo=repo,
        job_service=job_service,
        vector_store=vector_store,
    )
