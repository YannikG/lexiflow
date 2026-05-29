"""Model download protocol and test doubles."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from lexiflow_core.models.lockfile import ModelArtifact


class NetworkError(Exception):
    """Raised when a model download fails due to connectivity."""


class ModelAccessError(Exception):
    """Raised when a download fails due to auth or a gated Hugging Face repo."""


class ModelPinError(Exception):
    """Raised when models.lock points at a missing repo or revision on the Hub."""


class ModelDownloader(Protocol):
    def download(
        self,
        artifact: ModelArtifact,
        dest: Path,
        *,
        token: str | None,
        on_progress: Callable[[float], None] | None = None,
    ) -> None: ...


class FakeModelDownloader:
    """Writes a revision marker for tests without network access."""

    def __init__(
        self,
        *,
        error: Exception | None = None,
        fail_on_call: int | None = None,
    ) -> None:
        self._error = error
        self._fail_on_call = fail_on_call
        self._call_count = 0
        self.last_token: str | None = None
        self.last_artifact: ModelArtifact | None = None

    @property
    def call_count(self) -> int:
        return self._call_count

    def download(
        self,
        artifact: ModelArtifact,
        dest: Path,
        *,
        token: str | None,
        on_progress: Callable[[float], None] | None = None,
    ) -> None:
        self._call_count += 1
        self.last_token = token
        self.last_artifact = artifact
        if self._fail_on_call == self._call_count and self._error is not None:
            raise self._error
        if self._error is not None and self._call_count == 1:
            raise self._error
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "revision.txt").write_text(artifact.revision, encoding="utf-8")
        if on_progress is not None:
            on_progress(1.0)


def default_model_downloader() -> ModelDownloader:
    """Return the production model downloader."""
    from lexiflow_core.models.huggingface_downloader import HuggingFaceModelDownloader

    return HuggingFaceModelDownloader()
