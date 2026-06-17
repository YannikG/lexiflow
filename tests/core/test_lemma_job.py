"""Tests for lemma inference jobs."""

from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest
from lexiflow_core.config.settings import Settings
from lexiflow_core.config.settings_store import SettingsStore
from lexiflow_core.jobs.lemma_queue import cancel_lemma_job, enqueue_lemma_job
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
                    "category": "verb",
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
    assert job.result["category"] == "verb"


def test_cancel_pending_lemma_job_never_runs(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    job_service = JobService(data_root)
    enqueue_lemma_job(
        job_service,
        language_code="es",
        surface_form="corriendo",
        native_language="en",
    )

    cancel_lemma_job(data_root, surface_form="corriendo")
    run_worker_loop(job_service, FakeLLM(response="unused"), data_root=data_root)

    jobs = job_service.list_jobs()
    assert len(jobs) == 1
    assert jobs[0].status == JobStatus.CANCELLED


def test_cancel_running_lemma_job_skips_completion(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    job_service = JobService(data_root)
    job_id = enqueue_lemma_job(
        job_service,
        language_code="es",
        surface_form="corriendo",
        native_language="en",
    )
    llm = FakeLLM(
        responses=[
            json.dumps(
                {
                    "lemma": "correr",
                    "translation": "to run",
                    "explanation": "Movement at speed.",
                    "category": "verb",
                }
            )
        ],
        block_on_call=1,
    )

    worker = threading.Thread(
        target=run_worker_loop,
        args=(job_service, llm),
        kwargs={"data_root": data_root},
    )
    worker.start()
    assert llm.wait_blocked()

    cancel_lemma_job(data_root, surface_form="corriendo")
    llm.unblock()
    worker.join(timeout=5)

    job = job_service.get(job_id)
    assert job is not None
    assert job.status == JobStatus.CANCELLED
    assert job.result is None


def test_lemma_job_uses_settings_native_language_for_prompt(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "LexiFlow"
    config_dir = tmp_path / "config"
    SettingsStore(config_dir=config_dir).save(Settings(native_language="de"))
    monkeypatch.setattr(
        "lexiflow_core.config.settings_resolution.SettingsStore",
        lambda: SettingsStore(config_dir=config_dir),
    )

    class RecordingLLM(FakeLLM):
        def __init__(self) -> None:
            super().__init__(
                responses=[
                    json.dumps(
                        {
                            "lemma": "correr",
                            "translation": "rennen",
                            "explanation": "Schnelle Bewegung.",
                            "category": "verb",
                        }
                    )
                ]
            )
            self.last_prompt = ""

        def complete(
            self, prompt: str, *, json_schema: dict[str, object] | None = None
        ) -> str:
            self.last_prompt = prompt
            return super().complete(prompt, json_schema=json_schema)

    job_service = JobService(data_root)
    enqueue_lemma_job(
        job_service,
        language_code="es",
        surface_form="corriendo",
        native_language="en",
    )
    llm = RecordingLLM()
    run_worker_loop(job_service, llm, data_root=data_root)

    assert "Native language: German (de) (de)" in llm.last_prompt
    assert "Write translation and explanation in German (de) only." in llm.last_prompt
