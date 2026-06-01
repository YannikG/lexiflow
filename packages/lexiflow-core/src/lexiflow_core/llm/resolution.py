"""Resolve the production LLM provider from settings and local model state."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.config.settings import Settings
from lexiflow_core.llm.disabled import DisabledLLM
from lexiflow_core.llm.embedded_gemma import EmbeddedGemmaLLM, embedded_gemma_installed
from lexiflow_core.llm.ollama import OllamaLLM
from lexiflow_core.llm.protocol import LLMProvider
from lexiflow_core.llm.unavailable import UnavailableLLM
from lexiflow_core.models.requirements import EMBEDDED_GEMMA_ID


def resolve_llm(settings: Settings, data_root: Path) -> LLMProvider:
    """Select Ollama, embedded Gemma 4 E2B, or disabled provider from settings."""
    if not settings.llm_enabled:
        return DisabledLLM()

    if settings.ollama_url:
        return OllamaLLM(base_url=settings.ollama_url)

    if embedded_gemma_installed(data_root):
        return EmbeddedGemmaLLM.from_data_root(data_root)

    return UnavailableLLM(
        f"{EMBEDDED_GEMMA_ID} is not installed under {data_root}. "
        "Complete onboarding model bootstrap or configure an Ollama endpoint."
    )
