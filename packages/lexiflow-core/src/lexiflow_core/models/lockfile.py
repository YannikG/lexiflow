"""Parse the shipped models.lock manifest."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


class ModelsLockError(Exception):
    """Raised when models.lock cannot be read or parsed."""


@dataclass(frozen=True)
class ModelArtifact:
    id: str
    repo: str
    revision: str


@dataclass(frozen=True)
class ModelsLock:
    artifacts: tuple[ModelArtifact, ...]


def bundled_models_lock_path() -> Path:
    """Return the packaged models.lock shipped with lexiflow-core."""
    return Path(__file__).resolve().parent / "models.lock"


def load_models_lock(path: Path | None = None) -> ModelsLock:
    """Load and parse a models.lock file."""
    lock_path = path if path is not None else bundled_models_lock_path()
    try:
        with lock_path.open("rb") as handle:
            raw = tomllib.load(handle)
    except tomllib.TOMLDecodeError as exc:
        raise ModelsLockError(f"invalid models.lock: {lock_path}") from exc
    except OSError as exc:
        raise ModelsLockError(f"failed to read models.lock: {lock_path}") from exc

    entries = raw.get("artifacts")
    if not isinstance(entries, list) or not entries:
        raise ModelsLockError(f"models.lock has no artifacts: {lock_path}")

    artifacts: list[ModelArtifact] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise ModelsLockError(f"invalid artifact entry in {lock_path}")
        artifact_id = entry.get("id")
        repo = entry.get("repo")
        revision = entry.get("revision")
        if not isinstance(artifact_id, str) or not artifact_id:
            raise ModelsLockError(f"artifact missing id in {lock_path}")
        if not isinstance(repo, str) or not repo:
            raise ModelsLockError(f"artifact {artifact_id} missing repo in {lock_path}")
        if not isinstance(revision, str) or not revision:
            raise ModelsLockError(
                f"artifact {artifact_id} missing revision in {lock_path}"
            )
        artifacts.append(ModelArtifact(id=artifact_id, repo=repo, revision=revision))

    return ModelsLock(artifacts=tuple(artifacts))
