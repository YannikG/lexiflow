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
        repo="google/gemma-2-2b-it",
        revision="299a8560bedf22ed1c72a8a11e7dce4a7f9f51f8",
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
