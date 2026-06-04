"""Status bar worker state display."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from lexiflow_core.jobs.service import JobService
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QLabel, QStatusBar, QWidget

from lexiflow_ui.generation_status import format_background_status
from lexiflow_ui.jobs_display import PANEL_JOB_STATUSES
from lexiflow_ui.llama_server_supervisor import LlamaServerSupervisor
from lexiflow_ui.worker_supervisor import WorkerSupervisor


class WorkerStatusBar(QStatusBar):
    def __init__(
        self,
        supervisor: WorkerSupervisor,
        llama_supervisor: LlamaServerSupervisor | None = None,
        embed_supervisor: LlamaServerSupervisor | None = None,
        *,
        data_root: Path | None = None,
        on_open_jobs: Callable[[], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._supervisor = supervisor
        self._llama_supervisor = llama_supervisor
        self._embed_supervisor = embed_supervisor
        self._data_root = data_root if data_root is not None else supervisor.data_root
        self._on_open_jobs = on_open_jobs
        self._message_label = QLabel(self)
        self._message_label.setObjectName("worker_status_message")
        self.addWidget(self._message_label, 1)
        supervisor.state_changed.connect(self.refresh)
        if llama_supervisor is not None:
            llama_supervisor.state_changed.connect(self.refresh)
        if embed_supervisor is not None:
            embed_supervisor.state_changed.connect(self.refresh)
        self.refresh()

    def currentMessage(self) -> str:  # noqa: N802
        """Mirror QStatusBar API for tests and callers."""
        return self._message_label.text()

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self._on_open_jobs is not None
        ):
            self._on_open_jobs()
            return
        super().mousePressEvent(event)

    def refresh(self) -> None:
        base = format_background_status(
            self._supervisor,
            self._llama_supervisor,
            self._embed_supervisor,
        )
        queued = self._queued_count()
        if queued > 0 and self._on_open_jobs is not None:
            suffix = "job" if queued == 1 else "jobs"
            self._set_message(f"{base} — {queued} queued {suffix} (click for panel)")
            return
        self._set_message(base)

    def _queued_count(self) -> int:
        return len(JobService(self._data_root).list_queue_jobs(limit=50))

    def _panel_has_jobs(self) -> bool:
        return any(
            job.status in PANEL_JOB_STATUSES
            for job in JobService(self._data_root).list_jobs()
        )

    def show_job_error(self, message: str, *, timeout_ms: int = 10000) -> None:
        """Show a temporary job failure message, then restore worker state."""
        self._set_message(message)
        QTimer.singleShot(timeout_ms, self.refresh)

    def _set_message(self, text: str) -> None:
        self._message_label.setText(text)
