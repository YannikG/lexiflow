"""Tests for lexiflow_core.embeddings.llama_server."""

from __future__ import annotations

import json

from lexiflow_core.embeddings.llama_server import (
    LlamaServerEmbedder,
    LlamaServerEmbedError,
    _parse_embeddings_payload,
)
from lexiflow_core.vectors.models import EMBEDDING_DIM


class FakeResponse:
    def __init__(self, payload: dict[str, object], *, status: int = 200) -> None:
        self._payload = payload
        self.status = status

    def read(self, nbytes: int = -1) -> bytes:
        del nbytes
        return json.dumps(self._payload).encode("utf-8")

    def close(self) -> None:
        return None


class FakeOpener:
    def __init__(self, response: FakeResponse) -> None:
        self._response = response
        self.last_request = None

    def open(self, request, timeout=None):  # noqa: ANN001
        del timeout
        self.last_request = request
        return self._response


def test_llama_server_embed_returns_384_floats() -> None:
    embedding = [float(i) / EMBEDDING_DIM for i in range(EMBEDDING_DIM)]
    opener = FakeOpener(FakeResponse({"data": [{"embedding": embedding, "index": 0}]}))
    embedder = LlamaServerEmbedder(
        base_url="http://127.0.0.1:8081",
        model="org/embed:Q8_0",
        opener=opener,
    )

    vector = embedder.embed("hello")

    assert len(vector) == EMBEDDING_DIM
    assert vector == embedding
    assert opener.last_request is not None
    assert opener.last_request.full_url.endswith("/v1/embeddings")
    body = json.loads(opener.last_request.data.decode("utf-8"))
    assert body["model"] == "org/embed:Q8_0"
    assert body["input"] == "hello"


def test_llama_server_embed_raises_on_empty_embedding() -> None:
    opener = FakeOpener(FakeResponse({"data": [{"embedding": [], "index": 0}]}))
    embedder = LlamaServerEmbedder(model="org/embed:Q8_0", opener=opener)

    try:
        embedder.embed("hello")
    except LlamaServerEmbedError as exc:
        assert "empty" in str(exc).lower() or "dimension" in str(exc).lower()
    else:
        raise AssertionError("expected LlamaServerEmbedError")


def test_parse_embeddings_payload_rejects_missing_data() -> None:
    try:
        _parse_embeddings_payload({})
    except LlamaServerEmbedError as exc:
        assert "data" in str(exc).lower()
    else:
        raise AssertionError("expected LlamaServerEmbedError")
