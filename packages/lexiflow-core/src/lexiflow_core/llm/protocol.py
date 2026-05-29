"""LLM provider protocol."""

from __future__ import annotations

from typing import Protocol


class LLMProvider(Protocol):
    def complete(
        self, prompt: str, *, json_schema: dict[str, object] | None = None
    ) -> str: ...
