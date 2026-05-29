"""Tests for model hint and Hub URL helpers."""

from __future__ import annotations

from lexiflow_core.models.model_hints import (
    artifact_hub_page_url,
    gemma_hub_page_url,
)
from lexiflow_core.models.requirements import EMBEDDED_GEMMA_ID, EMBEDDING_MINILM_ID


def test_artifact_hub_page_url() -> None:
    assert (
        artifact_hub_page_url(EMBEDDING_MINILM_ID)
        == "https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2"
    )
    assert (
        artifact_hub_page_url(EMBEDDED_GEMMA_ID)
        == "https://huggingface.co/google/gemma-2-2b-it"
    )


def test_gemma_hub_page_url() -> None:
    assert gemma_hub_page_url() == artifact_hub_page_url(EMBEDDED_GEMMA_ID)
