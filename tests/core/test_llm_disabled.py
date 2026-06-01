"""Tests for disabled LLM resolution and job failure."""

from __future__ import annotations

from pathlib import Path

import pytest
from lexiflow_core.config.settings import Settings
from lexiflow_core.jobs.models import JobRequest, JobStatus, JobType
from lexiflow_core.jobs.runner import run_worker_loop
from lexiflow_core.jobs.service import JobService
from lexiflow_core.library.library_coordinator import LibraryCoordinator
from lexiflow_core.library.models import CreateTextRequest
from lexiflow_core.library.text_repository import TextRepository
from lexiflow_core.llm.disabled import LLMDisabledError
from lexiflow_core.llm.resolution import resolve_llm


def test_disabled_llm_raises_on_complete() -> None:
    llm = resolve_llm(Settings(llm_enabled=False), Path("/tmp"))

    with pytest.raises(LLMDisabledError, match="disabled"):
        llm.complete("x")


def test_worker_fails_translate_when_llm_disabled(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    coordinator, index = LibraryCoordinator.open(data_root)
    del coordinator
    jobs = JobService(data_root)
    repo = TextRepository(data_root, index)
    record = repo.create_text(
        CreateTextRequest(
            title="Raw",
            group="News",
            target_language="es",
            native_language="en",
            body="raw",
        )
    )
    jobs.enqueue(
        JobRequest(
            job_type=JobType.TRANSLATE,
            payload={"text_id": str(record.id), "phase": "plain"},
        )
    )
    llm = resolve_llm(Settings(llm_enabled=False), data_root)

    run_worker_loop(jobs, llm, data_root=data_root)

    listed = jobs.list_jobs()
    assert listed[0].status == JobStatus.FAILED
    assert listed[0].error_message is not None
    assert "disabled" in listed[0].error_message.lower()
