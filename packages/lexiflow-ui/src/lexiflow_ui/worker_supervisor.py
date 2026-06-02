"""Spawn and supervise the background worker process."""

from __future__ import annotations

import sys
from enum import Enum
from pathlib import Path
from typing import Protocol

from lexiflow_core.jobs.service import JobService
from PySide6.QtCore import QObject, QProcess, QTimer, Signal

from lexiflow_ui.worker_command import build_worker_command


class WorkerState(Enum):
    OFFLINE = "offline"
    IDLE = "idle"


class WorkerProcess(Protocol):
    def setProgram(self, program: str) -> None: ...

    def setArguments(self, arguments: list[str]) -> None: ...

    def start(self) -> None: ...

    def terminate(self) -> None: ...

    def waitForFinished(self, msecs: int = 30000) -> bool: ...

    def kill(self) -> None: ...

    def state(self) -> QProcess.ProcessState: ...

    def exitCode(self) -> int: ...


SHUTDOWN_WAIT_MS = 5000
DEFAULT_IDLE_TIMEOUT_MS = 5 * 60 * 1000


class WorkerSupervisor(QObject):
    state_changed = Signal(WorkerState)
    crashed = Signal(int)

    def __init__(
        self,
        *,
        data_root: Path,
        executable: str | None = None,
        process_factory: type[WorkerProcess] | None = None,
        idle_timeout_ms: int = DEFAULT_IDLE_TIMEOUT_MS,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._data_root = data_root
        self._executable = executable if executable is not None else sys.executable
        self._process_factory: type[WorkerProcess] = (
            process_factory if process_factory is not None else QProcess
        )
        self._process: WorkerProcess | None = None
        self._state = WorkerState.OFFLINE
        self._idle_timeout_ms = idle_timeout_ms
        self._idle_timer = QTimer(self)
        self._idle_timer.setSingleShot(True)
        self._idle_timer.timeout.connect(self._on_idle_timeout)

    @property
    def state(self) -> WorkerState:
        return self._state

    @property
    def data_root(self) -> Path:
        return self._data_root

    def is_process_running(self) -> bool:
        if self._process is None:
            return False
        return self._process.state() != QProcess.ProcessState.NotRunning

    def note_queue_activity(self) -> None:
        """Reset the idle shutdown timer after queue or worker activity."""
        if not self.is_process_running():
            return
        self._idle_timer.start(self._idle_timeout_ms)

    def ensure_running(self) -> None:
        if self._process is not None and not self.is_process_running():
            self._process = None
            self._set_state(WorkerState.OFFLINE)
        if self.is_process_running():
            self.note_queue_activity()
            return
        process = self._process_factory(self)
        if isinstance(process, QProcess):
            process.finished.connect(self._on_process_finished)
        command = build_worker_command(self._executable, self._data_root)
        process.setProgram(command[0])
        process.setArguments(command[1:])
        self._process = process
        process.start()
        self._set_state(WorkerState.IDLE)
        self.note_queue_activity()

    def shutdown(self, *, wait: bool) -> None:
        self._idle_timer.stop()
        if self._process is None:
            self._set_state(WorkerState.OFFLINE)
            return
        if wait:
            self._process.terminate()
            if not self._process.waitForFinished(SHUTDOWN_WAIT_MS):
                self._process.kill()
        else:
            self._process.kill()
        self._process = None
        self._set_state(WorkerState.OFFLINE)

    def _queue_has_active_work(self) -> bool:
        return bool(JobService(self._data_root).list_queue_jobs(limit=1))

    def _on_idle_timeout(self) -> None:
        if not self.is_process_running():
            return
        if self._queue_has_active_work():
            self.note_queue_activity()
            return
        self.shutdown(wait=False)

    def _on_process_finished(self, exit_code: int = 0, exit_status=None) -> None:
        self._idle_timer.stop()
        process = self._process
        self._process = None
        self._set_state(WorkerState.OFFLINE)
        if process is not None and isinstance(process, QProcess):
            code = process.exitCode()
            if code != 0:
                self.crashed.emit(code)
                return
        if exit_code != 0:
            self.crashed.emit(exit_code)

    def _set_state(self, state: WorkerState) -> None:
        if self._state == state:
            return
        self._state = state
        self.state_changed.emit(state)
