"""Copy user-provided model directories into the local cache."""

from __future__ import annotations

import shutil
from pathlib import Path

from lexiflow_core.models.lockfile import ModelArtifact
from lexiflow_core.models.paths import artifact_dir, artifact_revision_path


class ModelImportError(Exception):
    """Raised when a manual model import path is invalid."""


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

    dest = artifact_dir(data_root, artifact.id)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(source_dir, dest)

    marker = artifact_revision_path(data_root, artifact.id)
    marker.write_text(artifact.revision, encoding="utf-8")
    return dest
