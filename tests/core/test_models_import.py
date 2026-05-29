"""Tests for manual model import."""

from __future__ import annotations

from pathlib import Path

import pytest
from lexiflow_core.models.download import FakeModelDownloader
from lexiflow_core.models.import_paths import (
    ModelImportError,
    import_artifact_directory,
)
from lexiflow_core.models.lockfile import ModelArtifact
from lexiflow_core.models.paths import artifact_revision_path
from lexiflow_core.models.store import ModelStore


def test_import_artifact_directory_copies_files_and_writes_marker(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "library"
    source = tmp_path / "source-minilm"
    source.mkdir()
    (source / "config.json").write_text("{}", encoding="utf-8")
    artifact = ModelArtifact(
        id="embedding-minilm",
        repo="sentence-transformers/all-MiniLM-L6-v2",
        revision="abc123",
    )

    dest = import_artifact_directory(data_root, artifact, source)

    assert (dest / "config.json").is_file()
    assert artifact_revision_path(data_root, "embedding-minilm").read_text() == "abc123"


def test_import_artifact_directory_rejects_non_model_directory(tmp_path: Path) -> None:
    data_root = tmp_path / "library"
    source = tmp_path / "downloads"
    source.mkdir()
    (source / "readme.txt").write_text("not a model", encoding="utf-8")
    artifact = ModelArtifact(
        id="embedding-minilm",
        repo="sentence-transformers/all-MiniLM-L6-v2",
        revision="abc123",
    )

    with pytest.raises(ModelImportError, match="does not look like a model"):
        import_artifact_directory(data_root, artifact, source)


def test_import_artifact_directory_rejects_empty_directory(tmp_path: Path) -> None:
    data_root = tmp_path / "library"
    source = tmp_path / "empty"
    source.mkdir()
    artifact = ModelArtifact(
        id="embedding-minilm",
        repo="sentence-transformers/all-MiniLM-L6-v2",
        revision="abc123",
    )

    with pytest.raises(ModelImportError, match="empty"):
        import_artifact_directory(data_root, artifact, source)


def test_model_store_import_from_directory(tmp_path: Path) -> None:
    data_root = tmp_path / "library"
    source = tmp_path / "gemma-src"
    source.mkdir()
    (source / "model.safetensors").write_text("x", encoding="utf-8")
    store = ModelStore(data_root, downloader=FakeModelDownloader())

    dest = store.import_from_directory("embedded-gemma", source)

    assert (dest / "model.safetensors").is_file()
    assert store.is_installed("embedded-gemma")
