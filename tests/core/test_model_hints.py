"""Tests for model hint and Hub URL helpers."""

from __future__ import annotations

from lexiflow_core.models.model_hints import (
    artifact_hub_page_url,
    native_llm_hub_page_url,
)
from lexiflow_core.models.requirements import EMBEDDING_MINILM_ID, NATIVE_LLM_ID


def test_artifact_hub_page_url() -> None:
    assert (
        artifact_hub_page_url(EMBEDDING_MINILM_ID)
        == "https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2"
    )
    assert (
        artifact_hub_page_url(NATIVE_LLM_ID)
        == "https://huggingface.co/ggml-org/gemma-4-E2B-it-GGUF"
    )


def test_native_llm_hub_page_url_matches_lock_artifact() -> None:
    assert native_llm_hub_page_url() == artifact_hub_page_url(NATIVE_LLM_ID)
