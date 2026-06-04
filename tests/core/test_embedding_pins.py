"""Tests for pinned native embedding helpers."""

from __future__ import annotations

from lexiflow_core.embeddings.pins import (
    pinned_embedding_artifact,
    pinned_embedding_hf_model,
)
from lexiflow_core.models.requirements import NATIVE_EMBEDDING_ID


def test_pinned_embedding_artifact_reads_bundled_lock() -> None:
    artifact = pinned_embedding_artifact()

    assert artifact.id == NATIVE_EMBEDDING_ID
    assert artifact.repo
    assert artifact.revision
    assert artifact.llama_hf_model


def test_pinned_embedding_hf_model_reads_bundled_lock() -> None:
    model = pinned_embedding_hf_model()

    assert model.startswith("LLukas22/")
    assert ":Q8_0" in model
