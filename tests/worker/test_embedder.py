"""Tests for worker embedder resolution."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.embeddings.fake import FakeEmbedder
from lexiflow_core.models.paths import artifact_revision_path
from lexiflow_core.models.requirements import EMBEDDING_MINILM_ID
from lexiflow_worker.embedder import resolve_embedder


def test_resolve_embedder_uses_fake_when_minilm_not_installed(tmp_path: Path) -> None:
    embedder = resolve_embedder(tmp_path)
    assert isinstance(embedder, FakeEmbedder)


def test_resolve_embedder_falls_back_when_sentence_transformers_missing(
    tmp_path: Path,
) -> None:
    marker = artifact_revision_path(tmp_path, EMBEDDING_MINILM_ID)
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("abc123", encoding="utf-8")

    embedder = resolve_embedder(tmp_path)

    assert isinstance(embedder, FakeEmbedder)
