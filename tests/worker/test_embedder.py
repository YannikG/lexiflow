"""Tests for worker embedder resolution."""

from __future__ import annotations

import importlib

import pytest
from lexiflow_core.config.settings import Settings
from lexiflow_core.embeddings.fake import FakeEmbedder
from lexiflow_core.embeddings.minilm import MiniLMEmbedder
from lexiflow_worker.embedder import resolve_embedder


def test_resolve_embedder_uses_fake_when_sentence_transformers_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _raise_import_error(name: str) -> object:
        if name == "sentence_transformers":
            raise ImportError("not installed")
        return importlib.import_module(name)

    monkeypatch.setattr(importlib, "import_module", _raise_import_error)

    embedder = resolve_embedder(Settings())

    assert isinstance(embedder, FakeEmbedder)


def test_resolve_embedder_uses_minilm_when_runtime_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _FakeSentenceTransformersModule:
        pass

    def _import_module(name: str) -> object:
        if name == "sentence_transformers":
            return _FakeSentenceTransformersModule()
        return importlib.import_module(name)

    monkeypatch.setattr(importlib, "import_module", _import_module)

    embedder = resolve_embedder(Settings(huggingface_token="hf_test"))

    assert isinstance(embedder, MiniLMEmbedder)


def test_resolve_embedder_falls_back_on_runtime_import_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _raise_os_error(name: str) -> object:
        if name == "sentence_transformers":
            raise OSError("incompatible torch build")
        return importlib.import_module(name)

    monkeypatch.setattr(importlib, "import_module", _raise_os_error)

    embedder = resolve_embedder(Settings())

    assert isinstance(embedder, FakeEmbedder)
