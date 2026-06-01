"""Background model bootstrap downloads for onboarding."""

from __future__ import annotations

from lexiflow_core.models.download import (
    ModelAccessError,
    ModelPinError,
    NetworkError,
)
from lexiflow_core.models.store import ModelStore, ModelStoreError
from PySide6.QtCore import QObject, QThread, Signal, Slot


class ModelBootstrapWorker(QObject):
    """Runs ModelStore.ensure_installed on a worker thread."""

    progress_changed = Signal(int, str)
    log_line_changed = Signal(str)
    succeeded = Signal()
    failed = Signal(object)

    def __init__(
        self,
        store: ModelStore,
        artifact_ids: tuple[str, ...],
        *,
        force_redownload: bool = False,
    ) -> None:
        super().__init__()
        self._store = store
        self._artifact_ids = artifact_ids
        self._force_redownload = force_redownload

    @Slot()
    def run(self) -> None:
        total = len(self._artifact_ids)
        if total == 0:
            self.progress_changed.emit(100, "All required models are ready.")
            self.succeeded.emit()
            return

        try:
            for index, artifact_id in enumerate(self._artifact_ids, start=1):
                if QThread.currentThread().isInterruptionRequested():
                    return
                status = f"Downloading {artifact_id}…"

                def on_progress(
                    value: float,
                    *,
                    _index: int = index,
                    _status: str = status,
                ) -> None:
                    percent = int((_index - 1 + value) / total * 100)
                    self.progress_changed.emit(percent, _status)

                def on_log_line(line: str) -> None:
                    self.log_line_changed.emit(line)

                self.progress_changed.emit(
                    int((index - 1) / total * 100),
                    status,
                )
                if self._force_redownload:
                    self._store.remove_installed(artifact_id)
                self._store.ensure_installed(
                    artifact_id,
                    on_progress=on_progress,
                    on_log_line=on_log_line,
                )
            self.progress_changed.emit(100, "All required models are ready.")
            self.succeeded.emit()
        except (ModelPinError, ModelAccessError, NetworkError, ModelStoreError) as exc:
            self.failed.emit(exc)
        except Exception as exc:
            self.failed.emit(exc)
