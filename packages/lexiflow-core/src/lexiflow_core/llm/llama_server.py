"""Built-in llama-server LLM provider and model readiness queries."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Protocol, cast
from urllib.parse import urlparse

from lexiflow_core.config.settings import Settings
from lexiflow_core.models.lockfile import load_models_lock
from lexiflow_core.models.requirements import NATIVE_LLM_ID

_DEFAULT_SERVER_URL = "http://127.0.0.1:8080"
_LLAMA_SERVER_BIN_ENV = "LEXIFLOW_LLAMA_SERVER_BIN"
_BINARY_HINT = (
    "Install llama.cpp llama-server and ensure it is on PATH, or set "
    f"{_LLAMA_SERVER_BIN_ENV}."
)


class LlamaServerError(Exception):
    """Raised when llama-server generation fails."""


class HTTPResponse(Protocol):
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
        return cast(HTTPResponse, urllib.request.urlopen(request, timeout=timeout))


def _read_http_json(
    opener: UrlOpener,
    request: urllib.request.Request,
    *,
    timeout: float,
    error_cls: type[Exception],
    service: str,
) -> dict[str, object]:
    response: HTTPResponse | None = None
    try:
        response = opener.open(request, timeout=timeout)
        status = getattr(response, "status", None)
        if status is not None and not (200 <= status < 300):
            raise error_cls(f"{service} returned HTTP {status}")
        raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        exc.close()
        raise error_cls(f"{service} request failed: HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise error_cls(f"{service} request failed: {exc.reason}") from exc
    except TimeoutError as exc:
        raise error_cls(f"{service} request timed out") from exc
    except OSError as exc:
        raise error_cls(f"{service} request failed: {exc}") from exc
    finally:
        if response is not None:
            response.close()

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise error_cls(f"{service} returned invalid JSON") from exc
    if not isinstance(payload, dict):
        raise error_cls(f"{service} returned invalid JSON")
    return payload


def _llama_server_executable_name() -> str:
    return "llama-server.exe" if os.name == "nt" else "llama-server"


# GUI apps on macOS often inherit a minimal PATH without Homebrew.
_SUPPLEMENTARY_PATH_DIRS = ("/opt/homebrew/bin", "/usr/local/bin")


def _path_directories() -> tuple[str, ...]:
    """Return PATH segments plus common install dirs not always present in PATH."""
    seen: set[str] = set()
    directories: list[str] = []
    for segment in os.environ.get("PATH", "").split(os.pathsep):
        if not segment or segment in seen:
            continue
        seen.add(segment)
        directories.append(segment)
    for segment in _SUPPLEMENTARY_PATH_DIRS:
        if segment not in seen:
            seen.add(segment)
            directories.append(segment)
    return tuple(directories)


def _executable_path(path: Path) -> str | None:
    if path.is_file() and os.access(path, os.X_OK):
        return str(path)
    return None


def llama_server_runtime_env() -> dict[str, str]:
    """Return env vars so child processes resolve llama-server like the UI process."""
    env: dict[str, str] = {}
    binary = llama_server_binary()
    if binary:
        env[_LLAMA_SERVER_BIN_ENV] = binary
    path_dirs = _path_directories()
    if path_dirs:
        env["PATH"] = os.pathsep.join(path_dirs)
    return env


def _bundled_llama_server_binary() -> str | None:
    """Return llama-server shipped inside a PyInstaller bundle."""
    if not getattr(sys, "frozen", False):
        return None
    meipass = getattr(sys, "_MEIPASS", "")
    if not meipass:
        return None
    return _executable_path(Path(meipass) / "bin" / _llama_server_executable_name())


def llama_server_binary() -> str | None:
    """Return the llama-server executable path when available."""
    override = os.environ.get(_LLAMA_SERVER_BIN_ENV, "").strip()
    if override:
        return _executable_path(Path(override))
    bundled = _bundled_llama_server_binary()
    if bundled is not None:
        return bundled
    for directory in _path_directories():
        resolved = _executable_path(Path(directory) / _llama_server_executable_name())
        if resolved is not None:
            return resolved
    return None


def pinned_llama_hf_model() -> str:
    """Return the Hugging Face model spec passed to llama-server ``-hf``."""
    lock = load_models_lock()
    by_id = {artifact.id: artifact for artifact in lock.artifacts}
    artifact = by_id[NATIVE_LLM_ID]
    if artifact.llama_hf_model:
        return artifact.llama_hf_model
    raise RuntimeError(f"{NATIVE_LLM_ID} is missing llama_hf_model in models.lock")


def native_llm_operational(settings: Settings) -> tuple[bool, str | None]:
    """Return whether native llama-server inference can run."""
    if settings.ollama_url:
        return True, None
    if llama_server_binary() is None:
        return False, _BINARY_HINT
    try:
        pinned_llama_hf_model()
    except RuntimeError as exc:
        return False, str(exc)
    return True, None


def llama_server_health(base_url: str, *, timeout: float = 2.0) -> bool:
    """Return whether llama-server responds at *base_url*."""
    base = base_url.rstrip("/")
    request = urllib.request.Request(f"{base}/health", method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = getattr(response, "status", 200)
            return bool(200 <= status < 300)
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def parse_server_host_port(base_url: str) -> tuple[str, int]:
    parsed = urlparse(base_url)
    host = parsed.hostname or "127.0.0.1"
    if parsed.port is not None:
        return host, parsed.port
    if parsed.scheme == "https":
        return host, 443
    return host, 8080


def _chat_completion_request_body(
    prompt: str,
    *,
    model: str,
    json_schema: dict[str, object] | None,
) -> dict[str, object]:
    body: dict[str, object] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4096,
        "temperature": 0.2,
        "stream": False,
    }
    if json_schema is not None:
        body["response_format"] = {"type": "json_object", "schema": json_schema}
    return body


def _parse_chat_completion_payload(payload: dict[str, object]) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise LlamaServerError("llama-server response missing 'choices'")
    first = choices[0]
    if not isinstance(first, dict):
        raise LlamaServerError("llama-server response has invalid 'choices' entry")
    message = first.get("message")
    if not isinstance(message, dict):
        raise LlamaServerError("llama-server response missing 'message'")
    content = message.get("content")
    if isinstance(content, str) and content.strip():
        return content
    raise LlamaServerError("llama-server returned empty completion")


class LlamaServerLLM:
    """Call a managed llama-server instance for text completion."""

    def __init__(
        self,
        *,
        base_url: str = _DEFAULT_SERVER_URL,
        model: str | None = None,
        opener: UrlOpener | None = None,
        timeout: float = 300.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model if model is not None else pinned_llama_hf_model()
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
        body = json.dumps(
            _chat_completion_request_body(
                prompt,
                model=self._model,
                json_schema=json_schema,
            )
        ).encode("utf-8")
        request = urllib.request.Request(
            f"{self._base_url}/v1/chat/completions",
            data=body,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        payload = _read_http_json(
            self._opener,
            request,
            timeout=self._timeout,
            error_cls=LlamaServerError,
            service="llama-server",
        )
        return _parse_chat_completion_payload(payload)
