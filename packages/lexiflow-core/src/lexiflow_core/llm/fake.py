"""Deterministic LLM for tests and manual worker runs."""

from __future__ import annotations

import threading

_BLOCK = object()


class FakeLLM:
    def __init__(
        self,
        response: str = "fake completion",
        *,
        error: Exception | None = None,
        block_on_call: int | None = None,
        responses: list[str] | None = None,
    ) -> None:
        self._default_response = response
        self._error = error
        self._block_on_call = block_on_call
        self._responses = list(responses) if responses is not None else None
        self._call_count = 0
        self._unblock = threading.Event()
        self._block_entered = threading.Event()

    @property
    def call_count(self) -> int:
        return self._call_count

    def unblock(self) -> None:
        self._unblock.set()

    def wait_blocked(self, timeout: float | None = 5.0) -> bool:
        return self._block_entered.wait(timeout=timeout)

    def complete(
        self, prompt: str, *, json_schema: dict[str, object] | None = None
    ) -> str:
        del prompt, json_schema
        self._call_count += 1
        call_number = self._call_count

        if self._block_on_call == call_number:
            self._block_entered.set()
            self._unblock.wait()

        if self._error is not None and call_number == 1:
            raise self._error

        if self._responses is not None:
            index = min(call_number - 1, len(self._responses) - 1)
            return self._responses[index]

        return self._default_response
