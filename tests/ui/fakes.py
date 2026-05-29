"""Test doubles for lexiflow-ui."""

from __future__ import annotations

from PySide6.QtCore import QProcess


class FakeProcess:
    instances: list[FakeProcess] = []
    shutdown_calls: list[str] = []

    def __init__(self, parent: object | None = None) -> None:
        self.parent = parent
        self.program = ""
        self.arguments: list[str] = []
        self.started = False
        FakeProcess.instances.append(self)

    def setProgram(self, program: str) -> None:
        self.program = program

    def setArguments(self, arguments: list[str]) -> None:
        self.arguments = arguments

    def start(self) -> None:
        self.started = True

    def terminate(self) -> None:
        self.started = False
        FakeProcess.shutdown_calls.append("terminate")

    def waitForFinished(self, msecs: int = 30000) -> bool:
        FakeProcess.shutdown_calls.append("wait")
        return True

    def kill(self) -> None:
        FakeProcess.shutdown_calls.append("kill")

    def state(self) -> QProcess.ProcessState:
        if self.started:
            return QProcess.ProcessState.Running
        return QProcess.ProcessState.NotRunning
