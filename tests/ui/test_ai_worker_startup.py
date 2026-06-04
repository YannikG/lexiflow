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


def test_ensure_ai_workers_running_waits_for_embed_server(
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
    embed = LlamaServerSupervisor(
        data_root=tmp_path,
        base_url="http://127.0.0.1:8081",
        hf_model=lambda: "LLukas22/all-MiniLM-L6-v2-GGUF:Q8_0",
        embeddings=True,
        process_factory=FakeProcess,
    )
    ready_urls: set[str] = set()

    def _health(url: str) -> bool:
        return url in ready_urls

    monkeypatch.setattr(
        "lexiflow_ui.llama_server_supervisor.llama_server_health",
        _health,
    )
    monkeypatch.setattr(
        "lexiflow_ui.llama_server_supervisor.llama_server_binary",
        lambda: "/usr/bin/llama-server",
    )
    ready_urls.add("http://127.0.0.1:8080")

    ensure_ai_workers_running(worker, llama, embed)

    assert len(FakeProcess.instances) == 1
    assert worker.state is WorkerState.OFFLINE


def test_ensure_ai_workers_running_starts_worker_when_both_servers_ready(
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
    embed = LlamaServerSupervisor(
        data_root=tmp_path,
        base_url="http://127.0.0.1:8081",
        process_factory=FakeProcess,
    )
    monkeypatch.setattr(
        "lexiflow_ui.llama_server_supervisor.llama_server_health",
        lambda _url: True,
    )
    llama._state = LlamaServerState.READY
    embed._state = LlamaServerState.READY

    ensure_ai_workers_running(worker, llama, embed)

    assert len(FakeProcess.instances) == 1
    assert worker.state is WorkerState.IDLE


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
