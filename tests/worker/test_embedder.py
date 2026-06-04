"""Tests for worker embedder resolution."""

from __future__ import annotations

import pytest
from lexiflow_core.config.settings import Settings
from lexiflow_core.embeddings.fake import FakeEmbedder
from lexiflow_core.embeddings.llama_server import LlamaServerEmbedder
from lexiflow_core.embeddings.resolution import resolve_embedder


def test_resolve_embedder_uses_llama_when_health_ok(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "lexiflow_core.embeddings.resolution.llama_server_health",
        lambda _url: True,
    )

    embedder = resolve_embedder(
        Settings(llama_embed_server_url="http://127.0.0.1:8081")
    )

    assert isinstance(embedder, LlamaServerEmbedder)
    assert embedder.base_url == "http://127.0.0.1:8081"


def test_resolve_embedder_fake_when_server_down(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "lexiflow_core.embeddings.resolution.llama_server_health",
        lambda _url: False,
    )

    embedder = resolve_embedder(Settings())

    assert isinstance(embedder, FakeEmbedder)


def test_resolve_embedder_fake_when_ollama_url_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "lexiflow_core.embeddings.resolution.llama_server_health",
        lambda _url: True,
    )

    embedder = resolve_embedder(Settings(ollama_url="http://127.0.0.1:11434"))

    assert isinstance(embedder, FakeEmbedder)


def test_resolve_embedder_fake_when_embedding_pin_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _raise() -> str:
        raise RuntimeError("native-embedding is missing from models.lock")

    monkeypatch.setattr(
        "lexiflow_core.embeddings.resolution.pinned_embedding_hf_model",
        _raise,
    )
    monkeypatch.setattr(
        "lexiflow_core.embeddings.resolution.llama_server_health",
        lambda _url: True,
    )

    embedder = resolve_embedder(Settings())

    assert isinstance(embedder, FakeEmbedder)
