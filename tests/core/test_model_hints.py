"""Tests for model hint and Hub URL helpers."""

from __future__ import annotations

from lexiflow_core.models.model_hints import (
    artifact_hub_page_url,
    native_llm_hub_page_url,
)
from lexiflow_core.models.requirements import NATIVE_EMBEDDING_ID, NATIVE_LLM_ID


def test_artifact_hub_page_url() -> None:
    assert (
        artifact_hub_page_url(NATIVE_EMBEDDING_ID)
        == "https://huggingface.co/LLukas22/all-MiniLM-L6-v2-GGUF"
    )
    assert (
        artifact_hub_page_url(NATIVE_LLM_ID)
        == "https://huggingface.co/ggml-org/gemma-4-E2B-it-GGUF"
    )


def test_native_llm_hub_page_url_matches_lock_artifact() -> None:
    assert native_llm_hub_page_url() == artifact_hub_page_url(NATIVE_LLM_ID)
