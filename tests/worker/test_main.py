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
