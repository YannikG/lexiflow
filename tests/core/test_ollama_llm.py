"""Tests for lexiflow_core.llm.ollama."""

from __future__ import annotations

import json
import urllib.error
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
import pytest
from lexiflow_core.llm.ollama import OllamaError, OllamaLLM


class _FakeOpener:
    def __init__(self, handler: type[BaseHTTPRequestHandler]) -> None:
        self._server = HTTPServer(("127.0.0.1", 0), handler)
        self._thread = Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        host, port = self._server.server_address
        self.base_url = f"http://{host}:{port}"

    def close(self) -> None:
        self._server.shutdown()
        self._thread.join(timeout=5)

    def open(self, request, timeout=None):
        import urllib.request

        return urllib.request.urlopen(request, timeout=timeout)


def test_ollama_llm_complete_returns_response_body() -> None:
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length))
            assert body["stream"] is False
            assert body["prompt"] == "translate this"
            payload = json.dumps({"response": "# Title\n\nbody"}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, format: str, *args: object) -> None:
            del format, args

    fake = _FakeOpener(Handler)
    try:
        llm = OllamaLLM(base_url=fake.base_url, opener=fake)
        assert llm.complete("translate this") == "# Title\n\nbody"
    finally:
        fake.close()


def test_ollama_llm_closes_http_error_before_raising() -> None:
    closed: list[bool] = []

    class RecordingHTTPError(urllib.error.HTTPError):
        def close(self) -> None:
            closed.append(True)
            super().close()

    class RaisingOpener:
        def open(self, request, timeout=None):
            del request, timeout
            raise RecordingHTTPError(
                url="http://127.0.0.1:11434/api/generate",
                code=500,
                msg="error",
                hdrs={},
                fp=None,
            )

    llm = OllamaLLM(base_url="http://127.0.0.1:11434", opener=RaisingOpener())
    with pytest.raises(OllamaError, match="HTTP 500"):
        llm.complete("x")
    assert closed == [True]


def test_ollama_llm_complete_raises_on_http_error() -> None:
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            self.send_response(500)
            self.end_headers()

        def log_message(self, format: str, *args: object) -> None:
            del format, args

    fake = _FakeOpener(Handler)
    try:
        llm = OllamaLLM(base_url=fake.base_url, opener=fake)
        with pytest.raises(OllamaError):
            llm.complete("x")
    finally:
        fake.close()
