"""Spawn and supervise the native llama-server process."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Protocol

from lexiflow_core.llm.llama_server import (
    llama_server_binary,
    llama_server_health,
    parse_server_host_port,
    pinned_llama_hf_model,
)
from PySide6.QtCore import QObject, QProcess, QTimer, Signal

from lexiflow_ui.llama_server_command import build_llama_server_command
from lexiflow_ui.llama_server_errors import (
    hf_token_required_message,
    llama_server_startup_error,
)

_HEALTH_POLL_MS = 200


class LlamaServerState(Enum):
    OFFLINE = "offline"
    LOADING = "loading"
    READY = "ready"


class ServerProcess(Protocol):
    def setProgram(self, program: str) -> None: ...

    def setArguments(self, arguments: list[str]) -> None: ...

    def start(self) -> None: ...

    def terminate(self) -> None: ...

    def waitForFinished(self, msecs: int = 30000) -> bool: ...

    def kill(self) -> None: ...

    def state(self) -> QProcess.ProcessState: ...


SHUTDOWN_WAIT_MS = 5000


def _model_requires_hf_token(hf_model: str) -> bool:
    return "gemma" in hf_model.lower()


class LlamaServerSupervisor(QObject):
    state_changed = Signal(LlamaServerState)

    def __init__(
        self,
        *,
        data_root: Path,
        base_url: str,
        huggingface_token: str | None = None,
        process_factory: type[ServerProcess] | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._data_root = data_root
        self._base_url = base_url.rstrip("/")
        self._huggingface_token = huggingface_token
        self._process_factory: type[ServerProcess] = (
            process_factory if process_factory is not None else QProcess
        )
        self._process: ServerProcess | None = None
        self._state = LlamaServerState.OFFLINE
        self._startup_error: str | None = None
        self._health_poll_scheduled = False

    @property
    def state(self) -> LlamaServerState:
        return self._state

    @property
    def startup_error(self) -> str | None:
        return self._startup_error

    @property
    def base_url(self) -> str:
        return self._base_url

    def is_ready(self) -> bool:
        return llama_server_health(self._base_url)

    def is_process_running(self) -> bool:
        if self._process is None:
            return False
        return self._process.state() != QProcess.ProcessState.NotRunning

    def ensure_running(self) -> None:
        if self._process is not None and not self.is_process_running():
            self._process = None
            if not llama_server_health(self._base_url):
                self._set_state(LlamaServerState.OFFLINE)

        if llama_server_health(self._base_url):
            self._set_state(LlamaServerState.READY)
            return
        if self.is_process_running():
            self._set_state(LlamaServerState.LOADING)
            self._schedule_health_poll()
            return
        if (
            self._startup_error
            and self._process is None
            and not llama_server_health(self._base_url)
        ):
            self._set_state(LlamaServerState.OFFLINE)
            return

        binary = llama_server_binary()
        hf_model = pinned_llama_hf_model()
        if binary is None:
            self._startup_error = (
                "Install llama.cpp llama-server and ensure it is on PATH, or set "
                "LEXIFLOW_LLAMA_SERVER_BIN."
            )
            self._set_state(LlamaServerState.OFFLINE)
            return
        if _model_requires_hf_token(hf_model) and not self._huggingface_token:
            self._startup_error = hf_token_required_message()
            self._set_state(LlamaServerState.OFFLINE)
            return

        self._startup_error = None
        host, port = parse_server_host_port(self._base_url)
        process = self._process_factory(self)
        if isinstance(process, QProcess):
            process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
            process.finished.connect(self._on_process_finished)
        command = build_llama_server_command(
            binary,
            hf_model=hf_model,
            host=host,
            port=port,
            hf_token=self._huggingface_token,
        )
        process.setProgram(command[0])
        process.setArguments(command[1:])
        self._process = process
        process.start()
        self._set_state(LlamaServerState.LOADING)
        self._schedule_health_poll()

    def shutdown(self, *, wait: bool) -> None:
        self._health_poll_scheduled = False
        if self._process is None:
            self._set_state(LlamaServerState.OFFLINE)
            return
        if wait:
            self._process.terminate()
            if not self._process.waitForFinished(SHUTDOWN_WAIT_MS):
                self._process.kill()
        else:
            self._process.kill()
        self._process = None
        self._set_state(LlamaServerState.OFFLINE)

    def _schedule_health_poll(self) -> None:
        if self._health_poll_scheduled:
            return
        self._health_poll_scheduled = True
        QTimer.singleShot(_HEALTH_POLL_MS, self._poll_health)

    def _poll_health(self) -> None:
        self._health_poll_scheduled = False
        if not self.is_process_running():
            self._process = None
            if llama_server_health(self._base_url):
                self._set_state(LlamaServerState.READY)
                return
            self._set_state(LlamaServerState.OFFLINE)
            return
        if llama_server_health(self._base_url):
            self._set_state(LlamaServerState.READY)
            return
        self._set_state(LlamaServerState.LOADING)
        self._schedule_health_poll()

    def _on_process_finished(self, exit_code: int = 0, exit_status=None) -> None:
        del exit_code, exit_status
        if isinstance(self._process, QProcess):
            output = bytes(self._process.readAllStandardOutput()).decode(
                "utf-8", errors="replace"
            )
            if output.strip():
                self._startup_error = llama_server_startup_error(output)
        self._process = None
        self._health_poll_scheduled = False
        self._set_state(LlamaServerState.OFFLINE)

    def _set_state(self, state: LlamaServerState) -> None:
        if self._state == state:
            return
        self._state = state
        self.state_changed.emit(state)
