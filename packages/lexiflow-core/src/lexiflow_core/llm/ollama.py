"""HTTP client for Ollama LLM generation."""

from __future__ import annotations

import json
import urllib.request

from lexiflow_core.llm.llama_server import UrlOpener, _DefaultOpener, _read_http_json

DEFAULT_OLLAMA_LLM_MODEL = "gemma4:2b"


class OllamaError(Exception):
    """Raised when Ollama generation fails."""


class OllamaLLM:
    """Call a local or remote Ollama server for text completion."""

    def __init__(
        self,
        *,
        base_url: str,
        model: str = DEFAULT_OLLAMA_LLM_MODEL,
        opener: UrlOpener | None = None,
        timeout: float = 300.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._opener = opener if opener is not None else _DefaultOpener()
        self._timeout = timeout

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def model(self) -> str:
        return self._model

    def complete(
        self, prompt: str, *, json_schema: dict[str, object] | None = None
    ) -> str:
        del json_schema
        body = json.dumps(
            {
                "model": self._model,
                "prompt": prompt,
                "stream": False,
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            f"{self._base_url}/api/generate",
            data=body,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        payload = _read_http_json(
            self._opener,
            request,
            timeout=self._timeout,
            error_cls=OllamaError,
            service="Ollama",
        )
        response_text = payload.get("response")
        if not isinstance(response_text, str):
            raise OllamaError("Ollama response missing 'response' field")
        return response_text
