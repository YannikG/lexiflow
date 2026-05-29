"""Worker supervisor tests."""

from __future__ import annotations

import sys
from pathlib import Path

from lexiflow_ui.main_window import MainWindow
from lexiflow_ui.worker_supervisor import WorkerState, WorkerSupervisor

from tests.ui.fakes import FakeProcess


def test_ensure_running_spawns_worker_once(tmp_path: Path) -> None:
    FakeProcess.instances.clear()
    supervisor = WorkerSupervisor(
        data_root=tmp_path,
        executable=sys.executable,
        process_factory=FakeProcess,
    )

    assert supervisor.state is WorkerState.OFFLINE

    supervisor.ensure_running()
    supervisor.ensure_running()

    assert supervisor.state is WorkerState.IDLE
    assert len(FakeProcess.instances) == 1
    process = FakeProcess.instances[0]
    assert process.program == sys.executable
    assert "-m" in process.arguments
    assert "lexiflow_worker" in process.arguments
    assert "--data-root" in process.arguments
    assert str(tmp_path) in process.arguments


def test_shutdown_waits_for_worker(tmp_path: Path) -> None:
    FakeProcess.instances.clear()
    FakeProcess.shutdown_calls.clear()
    supervisor = WorkerSupervisor(
        data_root=tmp_path,
        executable=sys.executable,
        process_factory=FakeProcess,
    )
    supervisor.ensure_running()
    supervisor.shutdown(wait=True)

    assert FakeProcess.shutdown_calls == [True]
    assert supervisor.state is WorkerState.OFFLINE


def test_main_window_close_shuts_down_supervisor(qtbot, tmp_path: Path) -> None:
    FakeProcess.instances.clear()
    FakeProcess.shutdown_calls.clear()
    supervisor = WorkerSupervisor(
        data_root=tmp_path,
        executable=sys.executable,
        process_factory=FakeProcess,
    )
    supervisor.ensure_running()
    window = MainWindow(supervisor=supervisor)
    qtbot.addWidget(window)

    window.close()
    qtbot.waitUntil(lambda: len(FakeProcess.shutdown_calls) == 1, timeout=2000)


def test_main_window_close_without_worker_is_clean(qtbot, tmp_path: Path) -> None:
    class RecordingSupervisor(WorkerSupervisor):
        shutdown_calls: list[bool] = []

        def shutdown(self, *, wait: bool) -> None:
            self.shutdown_calls.append(wait)
            super().shutdown(wait=wait)

    RecordingSupervisor.shutdown_calls.clear()
    supervisor = RecordingSupervisor(data_root=tmp_path)
    window = MainWindow(supervisor=supervisor)
    qtbot.addWidget(window)

    window.close()

    assert supervisor.shutdown_calls == [True]
    assert supervisor.state is WorkerState.OFFLINE
