"""Copy user-provided model directories into the local cache."""

from __future__ import annotations

import shutil
from pathlib import Path

from lexiflow_core.models.lockfile import ModelArtifact
from lexiflow_core.models.paths import artifact_dir, artifact_revision_path


class ModelImportError(Exception):
    """Raised when a manual model import path is invalid."""


def _looks_like_model_directory(source_dir: Path) -> bool:
    """Return whether *source_dir* contains typical Hugging Face model files."""
    for entry in source_dir.iterdir():
        if not entry.is_file():
            continue
        name = entry.name
        if name in {"config.json", "tokenizer.json", "pytorch_model.bin"}:
            return True
        if name.endswith(".safetensors"):
            return True
    return False


def import_artifact_directory(
    data_root: Path,
    artifact: ModelArtifact,
    source_dir: Path,
) -> Path:
    """Copy a local model folder into the artifact cache and write the pin marker."""
    if not source_dir.is_dir():
        raise ModelImportError(f"import path is not a directory: {source_dir}")
    if not any(source_dir.iterdir()):
        raise ModelImportError(f"import directory is empty: {source_dir}")
    if not _looks_like_model_directory(source_dir):
        raise ModelImportError(
            f"import directory does not look like a model folder: {source_dir}"
        )

    dest = artifact_dir(data_root, artifact.id)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(source_dir, dest)

    marker = artifact_revision_path(data_root, artifact.id)
    marker.write_text(artifact.revision, encoding="utf-8")
    return dest
