"""Status bar worker state display."""

from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QStatusBar, QWidget

from lexiflow_ui.worker_supervisor import WorkerState, WorkerSupervisor


def format_worker_status(state: WorkerState) -> str:
    return f"Worker: {state.value}"


class WorkerStatusBar(QStatusBar):
    def __init__(
        self,
        supervisor: WorkerSupervisor,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._supervisor = supervisor
        supervisor.state_changed.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        self.showMessage(format_worker_status(self._supervisor.state))

    def show_job_error(self, message: str, *, timeout_ms: int = 10000) -> None:
        """Show a temporary job failure message, then restore worker state."""
        self.showMessage(message, timeout_ms)
        QTimer.singleShot(timeout_ms, self.refresh)
