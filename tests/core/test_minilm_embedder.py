"""Tests for pinned MiniLM embedder helpers."""

from __future__ import annotations

from lexiflow_core.embeddings.minilm import pinned_embedding_artifact
from lexiflow_core.models.requirements import EMBEDDING_MINILM_ID


def test_pinned_embedding_artifact_reads_bundled_lock() -> None:
    artifact = pinned_embedding_artifact()

    assert artifact.id == EMBEDDING_MINILM_ID
    assert artifact.repo
    assert artifact.revision
