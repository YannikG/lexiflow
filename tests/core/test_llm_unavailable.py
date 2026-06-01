"""Tests for unavailable LLM resolution and job failure."""

from __future__ import annotations

from pathlib import Path

import pytest
from lexiflow_core.config.settings import Settings
from lexiflow_core.jobs.models import JobRequest, JobStatus, JobType
from lexiflow_core.jobs.runner import run_worker_loop
from lexiflow_core.jobs.service import JobService
from lexiflow_core.llm.resolution import resolve_llm
from lexiflow_core.llm.unavailable import LLMUnavailableError


def test_unavailable_llm_raises_on_complete(tmp_path: Path) -> None:
    llm = resolve_llm(Settings(), tmp_path)

    with pytest.raises(LLMUnavailableError, match="not installed"):
        llm.complete("x")


def test_worker_fails_legacy_job_when_llm_unavailable(tmp_path: Path) -> None:
    data_root = tmp_path / "library"
    job_service = JobService(data_root)
    job_service.enqueue(
        JobRequest(job_type=JobType.TRANSLATE, payload={"prompt": "hello"})
    )
    llm = resolve_llm(Settings(), data_root)

    run_worker_loop(job_service, llm, data_root=data_root)

    jobs = job_service.list_jobs()
    assert jobs[0].status == JobStatus.FAILED
    assert jobs[0].error_message is not None
    assert "not installed" in jobs[0].error_message.lower()
