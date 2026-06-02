"""Tests for lemma inference jobs."""

from __future__ import annotations

import json
from pathlib import Path

from lexiflow_core.jobs.lemma_queue import enqueue_lemma_job
from lexiflow_core.jobs.models import JobStatus, JobType
from lexiflow_core.jobs.runner import run_worker_loop
from lexiflow_core.jobs.service import JobService
from lexiflow_core.llm.fake import FakeLLM


def test_lemma_job_returns_structured_result(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    job_service = JobService(data_root)
    enqueue_lemma_job(
        job_service,
        language_code="es",
        surface_form="corriendo",
        native_language="en",
        context="Estoy corriendo.",
    )
    llm = FakeLLM(
        responses=[
            json.dumps(
                {
                    "lemma": "correr",
                    "translation": "to run",
                    "explanation": "Movement at speed.",
                }
            )
        ]
    )

    run_worker_loop(job_service, llm, data_root=data_root)

    jobs = job_service.list_jobs()
    assert len(jobs) == 1
    job = jobs[0]
    assert job.job_type == JobType.LEMMA
    assert job.status == JobStatus.COMPLETED
    assert job.result is not None
    assert job.result["lemma"] == "correr"
    assert job.result["translation"] == "to run"
