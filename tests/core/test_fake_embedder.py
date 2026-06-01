"""Tests for FakeEmbedder."""

from __future__ import annotations

from lexiflow_core.embeddings.fake import FakeEmbedder
from lexiflow_core.vectors.models import EMBEDDING_DIM


def test_fake_embedder_returns_deterministic_vectors() -> None:
    embedder = FakeEmbedder()

    first = embedder.embed("hola mundo")
    second = embedder.embed("hola mundo")

    assert len(first) == EMBEDDING_DIM
    assert first == second


def test_fake_embedder_differs_for_different_inputs() -> None:
    embedder = FakeEmbedder()

    assert embedder.embed("alpha") != embedder.embed("beta")
