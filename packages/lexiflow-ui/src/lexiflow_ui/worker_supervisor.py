"""Spawn and supervise the background worker process."""

from __future__ import annotations

import sys
from enum import Enum
from pathlib import Path
from typing import Protocol

from PySide6.QtCore import QObject, QProcess, Signal

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


SHUTDOWN_WAIT_MS = 5000


class WorkerSupervisor(QObject):
    state_changed = Signal(WorkerState)

    def __init__(
        self,
        *,
        data_root: Path,
        executable: str | None = None,
        process_factory: type[WorkerProcess] | None = None,
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

    @property
    def state(self) -> WorkerState:
        return self._state

    def ensure_running(self) -> None:
        if self._process is not None:
            return
        process = self._process_factory(self)
        command = build_worker_command(self._executable, self._data_root)
        process.setProgram(command[0])
        process.setArguments(command[1:])
        process.start()
        self._process = process
        self._set_state(WorkerState.IDLE)

    def shutdown(self, *, wait: bool) -> None:
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

    def _set_state(self, state: WorkerState) -> None:
        if self._state == state:
            return
        self._state = state
        self.state_changed.emit(state)
