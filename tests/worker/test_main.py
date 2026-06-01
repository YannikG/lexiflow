"""Tests for lexiflow_worker.main."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.jobs.models import JobRequest, JobStatus, JobType
from lexiflow_core.jobs.service import JobService
from lexiflow_worker.main import main


def test_main_exits_zero_with_empty_queue(tmp_path: Path) -> None:
    assert main(["--data-root", str(tmp_path)]) == 0


def test_main_completes_enqueued_job(tmp_path: Path) -> None:
    job_service = JobService(tmp_path)
    job_service.enqueue(
        JobRequest(job_type=JobType.TRANSLATE, payload={"prompt": "hello"})
    )

    assert main(["--data-root", str(tmp_path)]) == 0

    jobs = JobService(tmp_path).list_jobs()
    assert len(jobs) == 1
    assert jobs[0].status == JobStatus.COMPLETED
    assert jobs[0].result == {"text": "fake completion"}


def test_main_completes_embed_job_with_fake_embedder(tmp_path: Path) -> None:
    from lexiflow_core.library.library_coordinator import LibraryCoordinator
    from lexiflow_core.library.models import CreateTextRequest
    from lexiflow_core.library.text_repository import TextRepository
    from lexiflow_core.vectors.store import VectorStore

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
    repo.apply_translated_variant(record.id, "# Traducción\n\nCuerpo.")
    job_service = JobService(data_root)
    job_service.enqueue(
        JobRequest(job_type=JobType.EMBED, payload={"text_id": str(record.id)})
    )

    assert main(["--data-root", str(data_root)]) == 0

    jobs = job_service.list_jobs()
    assert jobs[0].status == JobStatus.COMPLETED
    assert VectorStore(data_root, "es").get_text_vector(record.id) is not None
