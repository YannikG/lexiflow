"""Tests for translated-text embedding jobs."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

import pytest
from lexiflow_core.embeddings.fake import FakeEmbedder
from lexiflow_core.jobs.embed_queue import enqueue_translated_text_embed
from lexiflow_core.jobs.handlers.cleanup import TRANSLATE_PHASE_PLAIN
from lexiflow_core.jobs.models import JobRequest, JobStatus, JobType
from lexiflow_core.jobs.runner import run_worker_loop
from lexiflow_core.jobs.service import JobService
from lexiflow_core.library.library_coordinator import LibraryCoordinator
from lexiflow_core.library.models import CreateTextRequest
from lexiflow_core.library.text_repository import TextRepository
from lexiflow_core.llm.fake import FakeLLM
from lexiflow_core.vectors.store import VectorStore


def _setup_text(tmp_path: Path) -> tuple[Path, TextRepository, JobService, UUID]:
    data_root = tmp_path / "LexiFlow"
    coordinator, index = LibraryCoordinator.open(data_root)
    del coordinator
    repo = TextRepository(data_root, index)
    record = repo.create_text(
        CreateTextRequest(
            title="Untitled",
            group="News",
            target_language="es",
            native_language="en",
            body="hola",
        )
    )
    repo.apply_translated_variant(record.id, "# Traducción\n\nCuerpo traducido.")
    return data_root, repo, JobService(data_root), record.id


def test_embed_job_after_translated_edit_stores_vector(tmp_path: Path) -> None:
    data_root, repo, job_service, text_id = _setup_text(tmp_path)

    repo.save_variant_edit(
        text_id,
        "translated",
        "# Nueva traducción\n\nTexto editado.",
    )
    enqueue_translated_text_embed(job_service, text_id)

    run_worker_loop(
        job_service,
        FakeLLM(response="unused"),
        embedder=FakeEmbedder(),
        data_root=data_root,
    )

    jobs = [job for job in job_service.list_jobs() if job.job_type == JobType.EMBED]
    assert len(jobs) == 1
    assert jobs[0].status == JobStatus.COMPLETED

    store = VectorStore(data_root, "es")
    vector = store.get_text_vector(text_id)
    assert vector is not None
    assert len(vector) == 384
    expected = FakeEmbedder().embed("# Nueva traducción\n\nTexto editado.")
    assert vector == pytest.approx(expected, rel=1e-3, abs=1e-3)


def test_translate_completion_enqueues_embed_job(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    coordinator, index = LibraryCoordinator.open(data_root)
    del coordinator
    repo = TextRepository(data_root, index)
    record = repo.create_text(
        CreateTextRequest(
            title="Untitled",
            group="News",
            target_language="es",
            native_language="en",
            body="body",
        )
    )
    repo.write_native_variant(record.id, "# Native\n\ncontent")
    job_service = JobService(data_root)
    job_service.enqueue(
        JobRequest(
            job_type=JobType.TRANSLATE,
            payload={"text_id": str(record.id), "phase": TRANSLATE_PHASE_PLAIN},
        )
    )

    run_worker_loop(
        job_service,
        FakeLLM(response="# Titulo\n\ncuerpo"),
        embedder=FakeEmbedder(),
        data_root=data_root,
    )

    jobs = job_service.list_jobs()
    embed_jobs = [job for job in jobs if job.job_type == JobType.EMBED]
    assert len(embed_jobs) == 1
    assert embed_jobs[0].status == JobStatus.COMPLETED

    store = VectorStore(data_root, "es")
    assert store.get_text_vector(record.id) is not None
