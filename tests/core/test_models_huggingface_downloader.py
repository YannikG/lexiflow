"""Tests for Hugging Face model download error mapping."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from huggingface_hub.errors import GatedRepoError, RepositoryNotFoundError
from lexiflow_core.models.download import ModelAccessError, ModelPinError
from lexiflow_core.models.huggingface_downloader import HuggingFaceModelDownloader
from lexiflow_core.models.lockfile import ModelArtifact


class _GatedLike(GatedRepoError):
    """Minimal stand-in; real GatedRepoError needs an HTTP response object."""

    def __init__(self) -> None:
        Exception.__init__(self, "gated")


def test_gated_repo_error_maps_to_model_access_not_pin(tmp_path: Path) -> None:
    """GatedRepoError must map to ModelAccessError, not ModelPinError."""
    artifact = ModelArtifact(
        id="embedded-gemma",
        repo="google/gemma-4-E2B-it",
        revision="905e84b50c4d2a365ebde34e685027578e6728db",
    )
    downloader = HuggingFaceModelDownloader()
    dest = tmp_path / "gemma"

    with patch(
        "lexiflow_core.models.huggingface_downloader.snapshot_download",
        side_effect=_GatedLike(),
    ):
        with pytest.raises(ModelAccessError):
            downloader.download(artifact, dest, token=None)

    class _MissingRepo(RepositoryNotFoundError):
        def __init__(self) -> None:
            Exception.__init__(self, "missing")

    with patch(
        "lexiflow_core.models.huggingface_downloader.snapshot_download",
        side_effect=_MissingRepo(),
    ):
        with pytest.raises(ModelPinError):
            downloader.download(artifact, dest, token=None)


def test_gated_repo_error_is_subclass_of_repository_not_found() -> None:
    assert issubclass(GatedRepoError, RepositoryNotFoundError)


def test_download_passes_reporting_tqdm_class_when_callbacks_set(
    tmp_path: Path,
) -> None:
    artifact = ModelArtifact(
        id="embedding-minilm",
        repo="sentence-transformers/all-MiniLM-L6-v2",
        revision="abc",
    )
    downloader = HuggingFaceModelDownloader()
    dest = tmp_path / "minilm"
    lines: list[str] = []

    with patch(
        "lexiflow_core.models.huggingface_downloader.snapshot_download",
    ) as snapshot:
        downloader.download(
            artifact,
            dest,
            token=None,
            on_progress=lambda _v: None,
            on_log_line=lines.append,
        )

    assert snapshot.call_count == 1
    assert snapshot.call_args.kwargs.get("tqdm_class") is not None
