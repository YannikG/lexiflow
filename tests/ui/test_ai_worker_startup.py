"""Tests for coordinated llama-server and worker startup."""

from __future__ import annotations

import sys
from pathlib import Path

from lexiflow_ui.ai_worker_startup import ensure_ai_workers_running
from lexiflow_ui.llama_server_supervisor import LlamaServerState, LlamaServerSupervisor
from lexiflow_ui.worker_supervisor import WorkerState, WorkerSupervisor

from tests.ui.fakes import FakeProcess


def test_ensure_ai_workers_running_waits_for_llama_server(
    tmp_path: Path, monkeypatch
) -> None:
    FakeProcess.instances.clear()
    worker = WorkerSupervisor(
        data_root=tmp_path,
        executable=sys.executable,
        process_factory=FakeProcess,
    )
    llama = LlamaServerSupervisor(
        data_root=tmp_path,
        base_url="http://127.0.0.1:8080",
        huggingface_token="hf_test",
        process_factory=FakeProcess,
    )
    monkeypatch.setattr(
        "lexiflow_ui.llama_server_supervisor.llama_server_health",
        lambda _url: False,
    )
    monkeypatch.setattr(
        "lexiflow_ui.llama_server_supervisor.llama_server_binary",
        lambda: "/usr/bin/llama-server",
    )

    ensure_ai_workers_running(worker, llama)

    assert len(FakeProcess.instances) == 1
    assert worker.state is WorkerState.OFFLINE


def test_ensure_ai_workers_running_starts_worker_when_llama_ready(
    tmp_path: Path, monkeypatch
) -> None:
    FakeProcess.instances.clear()
    worker = WorkerSupervisor(
        data_root=tmp_path,
        executable=sys.executable,
        process_factory=FakeProcess,
    )
    llama = LlamaServerSupervisor(
        data_root=tmp_path,
        base_url="http://127.0.0.1:8080",
        process_factory=FakeProcess,
    )
    monkeypatch.setattr(
        "lexiflow_ui.ai_worker_startup.LlamaServerSupervisor.is_ready",
        lambda self: True,
    )
    llama._state = LlamaServerState.READY

    ensure_ai_workers_running(worker, llama)

    assert len(FakeProcess.instances) == 1
