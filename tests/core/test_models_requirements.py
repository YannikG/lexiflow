"""Tests for lexiflow_core.models.requirements."""

from __future__ import annotations

from lexiflow_core.config.settings import Settings
from lexiflow_core.models.requirements import (
    NATIVE_EMBEDDING_ID,
    NATIVE_LLM_ID,
    required_artifact_ids,
)


def test_required_artifact_ids_empty_for_ollama() -> None:
    settings = Settings(ollama_url="http://127.0.0.1:11434")

    required = required_artifact_ids(settings)

    assert required == ()
    assert NATIVE_EMBEDDING_ID not in required
    assert NATIVE_LLM_ID not in required


def test_required_artifact_ids_empty_for_native_path() -> None:
    settings = Settings(ollama_url=None)

    required = required_artifact_ids(settings)

    assert required == ()
