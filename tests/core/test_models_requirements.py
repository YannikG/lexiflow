"""Tests for lexiflow_core.models.requirements."""

from __future__ import annotations

from lexiflow_core.config.settings import Settings
from lexiflow_core.models.requirements import (
    EMBEDDED_GEMMA_ID,
    EMBEDDING_MINILM_ID,
    required_artifact_ids,
)


def test_required_artifact_ids_skip_gemma_when_ollama_configured() -> None:
    settings = Settings(ollama_url="http://127.0.0.1:11434")

    required = required_artifact_ids(settings)

    assert required == (EMBEDDING_MINILM_ID,)
    assert EMBEDDED_GEMMA_ID not in required


def test_required_artifact_ids_include_gemma_for_embedded_path() -> None:
    settings = Settings(ollama_url=None)

    required = required_artifact_ids(settings)

    assert EMBEDDING_MINILM_ID in required
    assert EMBEDDED_GEMMA_ID in required
