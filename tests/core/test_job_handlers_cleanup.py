"""Tests for markdown cleanup job handler."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

import pytest
from lexiflow_core.config.paths import variant_path
from lexiflow_core.jobs.handlers.cleanup import SOURCE_ROUTE_NATIVE, handle_cleanup
from lexiflow_core.jobs.models import JobRequest, JobStatus, JobType
from lexiflow_core.jobs.service import JobService
from lexiflow_core.library.library_coordinator import LibraryCoordinator
from lexiflow_core.library.models import CreateTextRequest
from lexiflow_core.library.text_repository import TextRepository
from lexiflow_core.llm.fake import FakeLLM


@pytest.fixture
def handler_context(
    tmp_path: Path,
) -> tuple[JobService, TextRepository, UUID, Path]:
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
            body="raw",
        )
    )
    job_service = JobService(data_root)
    return job_service, repo, record.id, data_root


def test_cleanup_writes_native_md_with_document_title(
    handler_context: tuple[JobService, TextRepository, UUID, Path],
) -> None:
    job_service, repo, text_id, data_root = handler_context
    record = repo.get_text(text_id)
    folder = Path(record.folder)
    llm = FakeLLM(response="# Title\n\nbody")
    job_service.enqueue(
        JobRequest(
            job_type=JobType.CLEANUP,
            payload={
                "text_id": str(text_id),
                "raw_paste": "messy paste",
                "source_route": SOURCE_ROUTE_NATIVE,
            },
        )
    )
    job = job_service.claim_next()
    assert job is not None

    handle_cleanup(job, llm=llm, repo=repo, job_service=job_service)

    native = variant_path(folder, "native").read_text(encoding="utf-8")
    assert native.startswith("# Title")
    jobs = job_service.list_jobs()
    assert any(j.job_type == JobType.TRANSLATE for j in jobs)
    cleanup_jobs = [j for j in jobs if j.job_type == JobType.CLEANUP]
    assert cleanup_jobs[0].status == JobStatus.COMPLETED
