"""HTTP client for Ollama LLM generation."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Protocol, cast

DEFAULT_OLLAMA_LLM_MODEL = "gemma4:2b"


class OllamaError(Exception):
    """Raised when Ollama generation fails."""


class HTTPResponse(Protocol):
    """Minimal response surface used by OllamaLLM (stdlib or test fake)."""

    def read(self, nbytes: int = -1) -> bytes: ...

    def close(self) -> None: ...


class UrlOpener(Protocol):
    def open(
        self, request: urllib.request.Request, timeout: float | None = ...
    ) -> HTTPResponse: ...


class _DefaultOpener:
    def open(
        self, request: urllib.request.Request, timeout: float | None = None
    ) -> HTTPResponse:
        # urlopen is untyped in stubs; we only need read/close.
        return cast(HTTPResponse, urllib.request.urlopen(request, timeout=timeout))


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
        response: HTTPResponse | None = None
        try:
            response = self._opener.open(request, timeout=self._timeout)
            status = getattr(response, "status", None)
            if status is not None and not (200 <= status < 300):
                raise OllamaError(f"Ollama returned HTTP {status}")
            raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raise OllamaError(f"Ollama request failed: HTTP {exc.code}") from exc
        except urllib.error.URLError as exc:
            raise OllamaError(f"Ollama request failed: {exc.reason}") from exc
        except TimeoutError as exc:
            raise OllamaError("Ollama request timed out") from exc
        except OSError as exc:
            raise OllamaError(f"Ollama request failed: {exc}") from exc
        finally:
            if response is not None:
                response.close()

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise OllamaError("Ollama returned invalid JSON") from exc

        response_text = payload.get("response")
        if not isinstance(response_text, str):
            raise OllamaError("Ollama response missing 'response' field")
        return response_text
