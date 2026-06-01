"""User-facing job error messages."""

from __future__ import annotations

_LLAMA_SERVER_INSTALL_HINT = (
    "Install llama.cpp llama-server and ensure it is on PATH, or set "
    "LEXIFLOW_LLAMA_SERVER_BIN."
)
_LLAMA_SERVER_NOT_RUNNING = (
    "llama-server is not running yet. Wait for the model to load, then try again."
)
_INFERENCE_FAILED = "LLM inference failed. Check llama-server or Ollama status."


def _is_llama_server_install_message(message: str) -> bool:
    lower = message.lower()
    return (
        "ensure it is on path" in lower
        or "lexiflow_llama_server_bin" in lower
        or lower.startswith("install llama")
        or "llm not configured" in lower
        or "native llm is not ready" in lower
    )


def _is_llama_server_runtime_failure(message: str) -> bool:
    lower = message.lower()
    return (
        "connection refused" in lower
        or "timed out" in lower
        or "request failed" in lower
        or "not running yet" in lower
    )


def inference_subprocess_error(stderr: str, *, exit_code: int) -> str:
    """Return a short message for a failed inference subprocess."""
    del exit_code
    normalized = stderr.strip()
    if not normalized:
        return _INFERENCE_FAILED
    if _is_llama_server_install_message(normalized):
        return _LLAMA_SERVER_INSTALL_HINT
    lower = normalized.lower()
    if _is_llama_server_runtime_failure(normalized):
        return _LLAMA_SERVER_NOT_RUNNING
    if "connection refused" in lower:
        return _LLAMA_SERVER_NOT_RUNNING
    for line in reversed(normalized.splitlines()):
        stripped = line.strip()
        if not stripped or stripped.startswith("File "):
            continue
        if "traceback" in stripped.lower():
            continue
        if stripped.endswith(":"):
            continue
        return stripped
    return _INFERENCE_FAILED


def user_facing_job_error(message: str) -> str:
    """Return a short, actionable error string for UI and failed job rows."""
    normalized = message.strip()
    if not normalized:
        return "Generation failed. Check background job status and try again."
    if _is_llama_server_install_message(normalized):
        return _LLAMA_SERVER_INSTALL_HINT
    if _is_llama_server_runtime_failure(normalized):
        return _LLAMA_SERVER_NOT_RUNNING
    lower = normalized.lower()
    lines = normalized.splitlines()
    first_line = lines[0].strip()
    if "ollama" in lower and "failed" in lower:
        return (
            "Ollama request failed. Check that Ollama is running "
            "and the model is pulled."
        )
    if "traceback (most recent call last)" in lower:
        if first_line and "traceback" not in first_line.lower():
            return first_line
        return _INFERENCE_FAILED
    if "traceback" in first_line.lower():
        return _INFERENCE_FAILED
    return first_line if first_line else normalized
