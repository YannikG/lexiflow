"""Pure path calculations for the local model cache."""

from __future__ import annotations

from pathlib import Path


def models_cache_dir(data_root: Path) -> Path:
    """Return the directory that stores downloaded model artifacts."""
    return data_root / ".app" / "models"


def artifact_dir(data_root: Path, artifact_id: str) -> Path:
    """Return the install directory for a single artifact."""
    return models_cache_dir(data_root) / artifact_id


def artifact_revision_path(data_root: Path, artifact_id: str) -> Path:
    """Return the path to the installed revision marker file."""
    return artifact_dir(data_root, artifact_id) / "revision.txt"
