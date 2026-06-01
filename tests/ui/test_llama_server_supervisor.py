"""Tests for llama-server process supervision."""

from __future__ import annotations

from pathlib import Path

from lexiflow_ui.llama_server_supervisor import LlamaServerState, LlamaServerSupervisor

from tests.ui.fakes import FakeProcess


def test_ensure_running_spawns_only_one_process(tmp_path: Path, monkeypatch) -> None:
    FakeProcess.instances.clear()
    monkeypatch.setattr(
        "lexiflow_ui.llama_server_supervisor.llama_server_binary",
        lambda: "/usr/bin/llama-server",
    )
    monkeypatch.setattr(
        "lexiflow_ui.llama_server_supervisor.pinned_llama_hf_model",
        lambda: "org/model:quant",
    )
    monkeypatch.setattr(
        "lexiflow_ui.llama_server_supervisor.llama_server_health",
        lambda _url: False,
    )
    supervisor = LlamaServerSupervisor(
        data_root=tmp_path,
        base_url="http://127.0.0.1:8080",
        huggingface_token="hf_test",
        process_factory=FakeProcess,
    )

    supervisor.ensure_running()
    supervisor.ensure_running()

    assert len(FakeProcess.instances) == 1


def test_ensure_running_reentrant_state_change_does_not_double_spawn(
    tmp_path: Path, monkeypatch
) -> None:
    FakeProcess.instances.clear()
    monkeypatch.setattr(
        "lexiflow_ui.llama_server_supervisor.llama_server_binary",
        lambda: "/usr/bin/llama-server",
    )
    monkeypatch.setattr(
        "lexiflow_ui.llama_server_supervisor.pinned_llama_hf_model",
        lambda: "org/model:quant",
    )
    monkeypatch.setattr(
        "lexiflow_ui.llama_server_supervisor.llama_server_health",
        lambda _url: False,
    )
    supervisor = LlamaServerSupervisor(
        data_root=tmp_path,
        base_url="http://127.0.0.1:8080",
        huggingface_token="hf_test",
        process_factory=FakeProcess,
    )
    supervisor.state_changed.connect(lambda _state: supervisor.ensure_running())

    supervisor.ensure_running()

    assert len(FakeProcess.instances) == 1


def test_ensure_running_reuses_existing_healthy_server(
    tmp_path: Path, monkeypatch
) -> None:
    FakeProcess.instances.clear()
    monkeypatch.setattr(
        "lexiflow_ui.llama_server_supervisor.llama_server_health",
        lambda _url: True,
    )
    supervisor = LlamaServerSupervisor(
        data_root=tmp_path,
        base_url="http://127.0.0.1:8080",
        process_factory=FakeProcess,
    )

    supervisor.ensure_running()

    assert len(FakeProcess.instances) == 0
    assert supervisor.state is LlamaServerState.READY


def test_ensure_running_requires_hf_token_for_gemma(
    tmp_path: Path, monkeypatch
) -> None:
    FakeProcess.instances.clear()
    monkeypatch.setattr(
        "lexiflow_ui.llama_server_supervisor.llama_server_binary",
        lambda: "/usr/bin/llama-server",
    )
    monkeypatch.setattr(
        "lexiflow_ui.llama_server_supervisor.pinned_llama_hf_model",
        lambda: "ggml-org/gemma-4-E2B-it-GGUF:Q8_0",
    )
    monkeypatch.setattr(
        "lexiflow_ui.llama_server_supervisor.llama_server_health",
        lambda _url: False,
    )
    supervisor = LlamaServerSupervisor(
        data_root=tmp_path,
        base_url="http://127.0.0.1:8080",
        process_factory=FakeProcess,
    )

    supervisor.ensure_running()

    assert len(FakeProcess.instances) == 0
    assert supervisor.startup_error is not None
    assert "hugging face access token" in supervisor.startup_error.lower()


def test_pinned_native_model_is_gemma_4_from_ggml_org() -> None:
    from lexiflow_core.llm.llama_server import pinned_llama_hf_model

    spec = pinned_llama_hf_model()

    assert "ggml-org" in spec.lower()
    assert "gemma-4" in spec.lower()
    assert "gemma-2" not in spec.lower()
