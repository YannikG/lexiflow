"""Tests for combined worker and llama-server status text."""

from __future__ import annotations

from lexiflow_core.jobs.models import JobRequest, JobType
from lexiflow_core.jobs.service import JobService
from lexiflow_ui.generation_status import format_background_status
from lexiflow_ui.llama_server_supervisor import LlamaServerState, LlamaServerSupervisor
from lexiflow_ui.worker_supervisor import WorkerSupervisor


def test_format_background_status_shows_loading_model(tmp_path) -> None:
    supervisor = WorkerSupervisor(data_root=tmp_path)
    llama = LlamaServerSupervisor(data_root=tmp_path, base_url="http://127.0.0.1:8080")
    llama._state = LlamaServerState.LOADING
    JobService(tmp_path).enqueue(
        JobRequest(job_type=JobType.CLEANUP, payload={"text_id": "x"})
    )

    message = format_background_status(supervisor, llama)

    assert "loading gemma 4" in message.lower()


def test_format_background_status_shows_startup_error(tmp_path) -> None:
    supervisor = WorkerSupervisor(data_root=tmp_path)
    llama = LlamaServerSupervisor(data_root=tmp_path, base_url="http://127.0.0.1:8080")
    llama._startup_error = "Hugging Face access token required"
    llama._state = LlamaServerState.OFFLINE
    JobService(tmp_path).enqueue(
        JobRequest(job_type=JobType.CLEANUP, payload={"text_id": "x"})
    )

    message = format_background_status(supervisor, llama)

    assert "hugging face access token" in message.lower()
