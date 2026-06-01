"""Status bar worker state display."""

from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QStatusBar, QWidget

from lexiflow_ui.generation_status import format_background_status
from lexiflow_ui.llama_server_supervisor import LlamaServerSupervisor
from lexiflow_ui.worker_supervisor import WorkerSupervisor


class WorkerStatusBar(QStatusBar):
    def __init__(
        self,
        supervisor: WorkerSupervisor,
        llama_supervisor: LlamaServerSupervisor | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._supervisor = supervisor
        self._llama_supervisor = llama_supervisor
        supervisor.state_changed.connect(self.refresh)
        if llama_supervisor is not None:
            llama_supervisor.state_changed.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        self.showMessage(
            format_background_status(self._supervisor, self._llama_supervisor)
        )

    def show_job_error(self, message: str, *, timeout_ms: int = 10000) -> None:
        """Show a temporary job failure message, then restore worker state."""
        self.showMessage(message, timeout_ms)
        QTimer.singleShot(timeout_ms, self.refresh)
