"""LLM provider used when settings require a model that is not installed."""

from __future__ import annotations


class LLMUnavailableError(Exception):
    """Raised when completion is requested without a configured LLM."""


class UnavailableLLM:
    def __init__(self, message: str) -> None:
        self._message = message

    def complete(
        self, prompt: str, *, json_schema: dict[str, object] | None = None
    ) -> str:
        del prompt, json_schema
        raise LLMUnavailableError(self._message)
