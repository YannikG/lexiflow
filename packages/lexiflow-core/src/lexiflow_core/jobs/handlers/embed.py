"""Embed translated text into the per-language vector store."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from lexiflow_core.embeddings.protocol import Embedder
from lexiflow_core.jobs.models import JobRecord
from lexiflow_core.jobs.service import JobService
from lexiflow_core.library.text_repository import TextRepository
from lexiflow_core.vectors.store import VectorStore


def _text_id_from_payload(job: JobRecord) -> UUID:
    raw = job.payload.get("text_id")
    if not isinstance(raw, str):
        raise ValueError(f"job {job.id} is missing text_id")
    return UUID(raw)


def handle_embed(
    job: JobRecord,
    *,
    data_root: Path,
    embedder: Embedder,
    repo: TextRepository,
    job_service: JobService,
    vector_store: VectorStore | None = None,
) -> None:
    """Embed the translated variant for a text and persist its vector."""
    try:
        text_id = _text_id_from_payload(job)
    except ValueError as exc:
        job_service.fail(job.id, str(exc))
        return

    try:
        record = repo.get_text(text_id)
        translated = repo.read_variant(text_id, "translated")
        vector = embedder.embed(translated)
        store = (
            vector_store
            if vector_store is not None
            else VectorStore(data_root, record.target_language)
        )
        store.upsert_text_vector(text_id, vector)
    except Exception as exc:
        job_service.fail(job.id, str(exc))
        return

    job_service.complete(job.id, {})
