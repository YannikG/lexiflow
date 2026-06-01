"""Resolve the production LLM provider from settings and local model state."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.config.settings import Settings
from lexiflow_core.llm.disabled import DisabledLLM
from lexiflow_core.llm.llama_server import (
    LlamaServerLLM,
    native_llm_operational,
)
from lexiflow_core.llm.ollama import OllamaLLM
from lexiflow_core.llm.protocol import LLMProvider
from lexiflow_core.llm.unavailable import UnavailableLLM


def resolve_llm(settings: Settings, data_root: Path) -> LLMProvider:
    """Select Ollama or native llama-server from settings."""
    if not settings.llm_enabled:
        return DisabledLLM()

    if settings.ollama_url:
        return OllamaLLM(base_url=settings.ollama_url)

    operational, message = native_llm_operational(settings)
    if not operational:
        return UnavailableLLM(message or "Native LLM is not ready.")
    return LlamaServerLLM(base_url=settings.llama_server_url)
