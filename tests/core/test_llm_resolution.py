"""Tests for lexiflow_core.llm.resolution."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.config.settings import Settings
from lexiflow_core.llm.llama_server import LlamaServerLLM
from lexiflow_core.llm.ollama import OllamaLLM
from lexiflow_core.llm.resolution import resolve_llm
from lexiflow_core.llm.unavailable import UnavailableLLM


def test_resolve_llm_returns_ollama_when_url_set(tmp_path: Path) -> None:
    settings = Settings(ollama_url="http://127.0.0.1:11434/")

    provider = resolve_llm(settings)

    assert isinstance(provider, OllamaLLM)
    assert provider.base_url == "http://127.0.0.1:11434"


def test_resolve_llm_returns_llama_server_when_native_ready(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(
        "lexiflow_core.llm.resolution.native_llm_operational",
        lambda settings: (True, None),
    )

    provider = resolve_llm(Settings())

    assert isinstance(provider, LlamaServerLLM)


def test_resolve_llm_returns_unavailable_when_runtime_missing(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(
        "lexiflow_core.llm.resolution.native_llm_operational",
        lambda settings: (False, "Install llama-server"),
    )

    provider = resolve_llm(Settings())

    assert isinstance(provider, UnavailableLLM)
    assert "llama-server" in provider.reason.lower()


def test_resolve_llm_returns_unavailable_when_no_ollama_and_native_missing(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(
        "lexiflow_core.llm.resolution.native_llm_operational",
        lambda settings: (False, "Install llama-server"),
    )

    provider = resolve_llm(Settings())

    assert isinstance(provider, UnavailableLLM)
