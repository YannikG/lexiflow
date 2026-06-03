"""Tests for translate job enqueue helpers."""

from __future__ import annotations

from uuid import uuid4

from lexiflow_core.jobs.handlers.cleanup import TRANSLATE_PHASE_PLAIN
from lexiflow_core.jobs.models import JobStatus, JobType
from lexiflow_core.jobs.service import JobService
from lexiflow_core.jobs.translate_queue import enqueue_retranslate


def test_enqueue_retranslate_creates_pending_plain_job(tmp_path) -> None:
    data_root = tmp_path / "library"
    job_service = JobService(data_root)
    text_id = uuid4()

    enqueue_retranslate(job_service, text_id)

    jobs = job_service.list_jobs()
    assert len(jobs) == 1
    assert jobs[0].status == JobStatus.PENDING
    assert jobs[0].job_type == JobType.TRANSLATE
    assert jobs[0].payload["text_id"] == str(text_id)
    assert jobs[0].payload["phase"] == TRANSLATE_PHASE_PLAIN
