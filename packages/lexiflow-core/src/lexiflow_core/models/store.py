"""Local model install state and bootstrap downloads."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from lexiflow_core.config.app_layout import ensure_app_layout
from lexiflow_core.models.download import (
    ModelAccessError,
    ModelDownloader,
    ModelPinError,
    NetworkError,
)
from lexiflow_core.models.import_paths import (
    ModelImportError,
    import_artifact_directory,
)
from lexiflow_core.models.lockfile import ModelArtifact, ModelsLock, load_models_lock
from lexiflow_core.models.paths import artifact_dir, artifact_revision_path


class ModelStoreError(Exception):
    """Raised when a model store operation is not allowed."""


@dataclass(frozen=True)
class UpdateAvailable:
    artifact_id: str
    installed_revision: str
    pinned_revision: str


class ModelStore:
    def __init__(
        self,
        data_root: Path,
        *,
        lock: ModelsLock | None = None,
        downloader: ModelDownloader,
        huggingface_token: str | None = None,
    ) -> None:
        self._data_root = data_root
        self._lock = lock if lock is not None else load_models_lock()
        self._downloader = downloader
        self._huggingface_token = huggingface_token
        self._artifacts_by_id = {a.id: a for a in self._lock.artifacts}

    def set_huggingface_token(self, token: str | None) -> None:
        """Update the token used for subsequent Hub downloads."""
        self._huggingface_token = token

    def _artifact(self, artifact_id: str) -> ModelArtifact:
        try:
            return self._artifacts_by_id[artifact_id]
        except KeyError as exc:
            raise ModelStoreError(f"unknown artifact: {artifact_id}") from exc

    def is_installed(self, artifact_id: str) -> bool:
        """Return whether the pinned revision is installed for an artifact."""
        artifact = self._artifact(artifact_id)
        marker = artifact_revision_path(self._data_root, artifact_id)
        if not marker.is_file():
            return False
        return marker.read_text(encoding="utf-8").strip() == artifact.revision

    def ensure_installed(
        self,
        artifact_id: str,
        on_progress: Callable[[float], None],
    ) -> Path:
        """Download and install an artifact when the pinned revision is missing."""
        if self.is_installed(artifact_id):
            return artifact_dir(self._data_root, artifact_id)

        ensure_app_layout(self._data_root)
        artifact = self._artifact(artifact_id)
        dest = artifact_dir(self._data_root, artifact_id)
        try:
            self._downloader.download(
                artifact,
                dest,
                token=self._huggingface_token,
                on_progress=on_progress,
            )
        except (NetworkError, ModelAccessError, ModelPinError):
            raise
        except OSError as exc:
            raise ModelStoreError(f"failed to install {artifact_id}") from exc
        except Exception as exc:
            if isinstance(exc, ModelStoreError):
                raise
            raise ModelStoreError(f"failed to install {artifact_id}") from exc

        marker = artifact_revision_path(self._data_root, artifact_id)
        if not marker.is_file():
            marker.write_text(artifact.revision, encoding="utf-8")
        return dest

    def import_from_directory(self, artifact_id: str, source_dir: Path) -> Path:
        """Install an artifact from a user-selected local model folder."""
        ensure_app_layout(self._data_root)
        artifact = self._artifact(artifact_id)
        try:
            return import_artifact_directory(self._data_root, artifact, source_dir)
        except ModelImportError as exc:
            raise ModelStoreError(str(exc)) from exc

    def check_for_updates(self) -> list[UpdateAvailable]:
        """Return artifacts whose installed revision differs from the lock pin."""
        updates: list[UpdateAvailable] = []
        for artifact in self._lock.artifacts:
            marker = artifact_revision_path(self._data_root, artifact.id)
            if not marker.is_file():
                continue
            installed = marker.read_text(encoding="utf-8").strip()
            if installed != artifact.revision:
                updates.append(
                    UpdateAvailable(
                        artifact_id=artifact.id,
                        installed_revision=installed,
                        pinned_revision=artifact.revision,
                    )
                )
        return updates
