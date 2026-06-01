"""Tests for lexiflow_core.llm.llama_server."""

from __future__ import annotations

import json

from lexiflow_core.llm.llama_server import (
    LlamaServerError,
    LlamaServerLLM,
    _parse_chat_completion_payload,
)


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


def test_llama_server_complete_returns_chat_content() -> None:
    opener = FakeOpener(
        FakeResponse(
            {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "clean text",
                        }
                    }
                ]
            }
        )
    )
    llm = LlamaServerLLM(
        base_url="http://127.0.0.1:8080",
        model="org/model:quant",
        opener=opener,
    )

    text = llm.complete("prompt")

    assert text == "clean text"
    assert opener.last_request is not None
    assert opener.last_request.full_url.endswith("/v1/chat/completions")
    body = json.loads(opener.last_request.data.decode("utf-8"))
    assert body["model"] == "org/model:quant"
    assert body["messages"] == [{"role": "user", "content": "prompt"}]


def test_llama_server_complete_raises_on_empty_chat_content() -> None:
    opener = FakeOpener(
        FakeResponse({"choices": [{"message": {"role": "assistant", "content": "  "}}]})
    )
    llm = LlamaServerLLM(model="org/model:quant", opener=opener)

    try:
        llm.complete("prompt")
    except LlamaServerError as exc:
        assert "empty" in str(exc).lower()
    else:
        raise AssertionError("expected LlamaServerError")


def test_parse_chat_completion_payload_rejects_missing_choices() -> None:
    try:
        _parse_chat_completion_payload({})
    except LlamaServerError as exc:
        assert "choices" in str(exc).lower()
    else:
        raise AssertionError("expected LlamaServerError")
