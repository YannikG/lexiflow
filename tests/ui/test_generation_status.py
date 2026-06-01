"""Tests for generation infrastructure status copy."""

from __future__ import annotations

import sys
from pathlib import Path

from lexiflow_core.jobs.models import JobRequest, JobType
from lexiflow_core.jobs.service import JobService
from lexiflow_ui.generation_status import (
    format_background_status,
    generation_indicator,
    is_pending_generation_message,
)
from lexiflow_ui.llama_server_supervisor import LlamaServerState, LlamaServerSupervisor
from lexiflow_ui.worker_supervisor import WorkerState, WorkerSupervisor

from tests.ui.fakes import FakeProcess

_PENDING = "This variant is still being generated. Background jobs are running."


def test_is_pending_generation_message() -> None:
    assert is_pending_generation_message(_PENDING) is True
    assert is_pending_generation_message("Generation failed: oops") is False


def test_generation_indicator_loading_model(tmp_path: Path) -> None:
    llama = LlamaServerSupervisor(data_root=tmp_path, base_url="http://127.0.0.1:8080")
    llama._state = LlamaServerState.LOADING

    indicator = generation_indicator(
        llama_supervisor=llama,
        worker_supervisor=None,
        pending_message=_PENDING,
    )

    assert indicator is not None
    assert "language model" in indicator.headline.lower()
    assert indicator.show_progress is True
    assert "hugging face" in indicator.detail.lower()


def test_generation_indicator_starting_worker(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "lexiflow_ui.generation_status.LlamaServerSupervisor.is_ready",
        lambda self: True,
    )
    llama = LlamaServerSupervisor(data_root=tmp_path, base_url="http://127.0.0.1:8080")
    llama._state = LlamaServerState.READY
    worker = WorkerSupervisor(
        data_root=tmp_path,
        executable=sys.executable,
        process_factory=FakeProcess,
    )

    indicator = generation_indicator(
        llama_supervisor=llama,
        worker_supervisor=worker,
        pending_message=_PENDING,
    )

    assert indicator is not None
    assert "background worker" in indicator.headline.lower()
    assert indicator.show_progress is True


def test_generation_indicator_simplify_headline(tmp_path: Path) -> None:
    worker = WorkerSupervisor(
        data_root=tmp_path,
        executable=sys.executable,
        process_factory=FakeProcess,
    )
    worker._state = WorkerState.IDLE

    indicator = generation_indicator(
        llama_supervisor=None,
        worker_supervisor=worker,
        pending_message=_PENDING,
        variant_name="simplified-a2",
    )

    assert indicator is not None
    assert "simplifying to a2" in indicator.headline.lower()
    assert "simplified variant" in indicator.detail.lower()


def test_format_background_status_reports_model_loading(tmp_path: Path) -> None:
    JobService(tmp_path).enqueue(
        JobRequest(job_type=JobType.CLEANUP, payload={"text_id": "x"})
    )
    worker = WorkerSupervisor(data_root=tmp_path)
    llama = LlamaServerSupervisor(data_root=tmp_path, base_url="http://127.0.0.1:8080")
    llama._state = LlamaServerState.LOADING

    message = format_background_status(worker, llama)

    assert "loading language model" in message.lower()
