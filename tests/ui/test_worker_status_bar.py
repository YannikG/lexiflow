"""Tests for the worker status bar job counter."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.jobs.models import JobRequest, JobType
from lexiflow_core.jobs.service import JobService
from lexiflow_ui.widgets.worker_status import WorkerStatusBar


def test_queued_count_excludes_completed_and_failed(tmp_path: Path) -> None:
    jobs = JobService(tmp_path)
    completed_id = jobs.enqueue(
        JobRequest(job_type=JobType.CLEANUP, payload={"text_id": "a"})
    )
    claimed = jobs.claim_next()
    assert claimed is not None
    jobs.complete(completed_id, {"ok": True})
    jobs.enqueue(JobRequest(job_type=JobType.CLEANUP, payload={"text_id": "b"}))
    jobs.enqueue(JobRequest(job_type=JobType.CLEANUP, payload={"text_id": "c"}))

    bar = WorkerStatusBar.__new__(WorkerStatusBar)
    bar._data_root = tmp_path

    assert bar._queued_count() == 2
