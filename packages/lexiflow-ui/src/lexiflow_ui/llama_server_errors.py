"""User-facing llama-server startup errors."""

from __future__ import annotations

_HF_TOKEN_HINT = (
    "Hugging Face access token required to download the pinned language model. "
    "Add or verify your token in Settings (LLM) and restart LexiFlow."
)
_PINNED_MODEL_NOT_FOUND = (
    "The pinned language model was not found on Hugging Face. "
    "Update LexiFlow to the latest version."
)
_INVALID_MODEL_SPEC = (
    "The pinned language model spec is invalid for llama-server. "
    "Update LexiFlow to the latest version."
)
_HF_DOWNLOAD_FAILED = (
    "Failed to download the pinned language model from Hugging Face. "
    "Check your connection and Hugging Face access token in Settings (LLM)."
)
_LLAMA_START_FAILED = "llama-server failed to start. Check LexiFlow logs and try again."


def hf_token_required_message() -> str:
    return _HF_TOKEN_HINT


def llama_server_startup_error(output: str) -> str:
    """Return a short message for llama-server process output."""
    normalized = output.strip()
    if not normalized:
        return _LLAMA_START_FAILED
    lower = normalized.lower()
    if "401" in normalized or "invalid username or password" in lower:
        return _HF_TOKEN_HINT
    if (
        "404" in normalized
        or "repository not found" in lower
        or "repo not found" in lower
    ):
        return _PINNED_MODEL_NOT_FOUND
    if "no gguf files found" in lower:
        return _INVALID_MODEL_SPEC
    if "failed to download model from hugging face" in lower:
        return _HF_DOWNLOAD_FAILED
    for line in reversed(normalized.splitlines()):
        stripped = line.strip()
        if stripped and not stripped.startswith("File "):
            return stripped
    return _LLAMA_START_FAILED
