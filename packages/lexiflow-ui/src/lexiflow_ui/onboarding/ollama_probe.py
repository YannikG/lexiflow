"""Ollama availability probes for onboarding."""

from __future__ import annotations

import urllib.error
import urllib.request
from typing import Protocol


class OllamaProbe(Protocol):
    def is_available(self, url: str) -> bool: ...


class PlatformOllamaProbe:
    """Probe a local Ollama HTTP endpoint."""

    def is_available(self, url: str) -> bool:
        base = url.rstrip("/")
        request = urllib.request.Request(
            f"{base}/api/tags",
            method="GET",
            headers={"Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=2) as response:
                return 200 <= response.status < 300
        except (urllib.error.URLError, TimeoutError, OSError):
            return False


class FakeOllamaProbe:
    """Deterministic probe for tests."""

    def __init__(self, *, available: bool = False) -> None:
        self._available = available
        self.last_url: str | None = None

    def is_available(self, url: str) -> bool:
        self.last_url = url
        return self._available
