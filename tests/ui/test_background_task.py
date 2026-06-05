"""Tests for background progress dialog runner."""

from __future__ import annotations

import threading
import time

from lexiflow_ui.background_task import run_with_progress_dialog
from PySide6.QtWidgets import QWidget


def test_run_with_progress_dialog_keeps_ui_responsive_during_work(
    qtbot,
) -> None:
    parent = QWidget()
    qtbot.addWidget(parent)

    def work(
        on_progress,
        on_status,
    ) -> None:
        on_status("Working…")
        on_progress(0.0)
        time.sleep(0.05)
        on_progress(0.5)
        on_status("Halfway…")
        time.sleep(0.05)
        on_progress(1.0)

    ok, error = run_with_progress_dialog(
        parent,
        title="Test",
        initial_status="Starting…",
        work=work,
    )

    assert ok is True
    assert error is None


def test_run_with_progress_dialog_times_out_when_work_hangs(qtbot) -> None:
    parent = QWidget()
    qtbot.addWidget(parent)

    hang_until_timeout = threading.Event()

    def work(on_progress, on_status) -> None:
        on_status("Starting…")
        on_progress(0.0)
        hang_until_timeout.wait()

    ok, error = run_with_progress_dialog(
        parent,
        title="Test",
        initial_status="Starting…",
        work=work,
        timeout_seconds=0.2,
    )

    assert ok is False
    assert error == "Operation timed out."


def test_run_with_progress_dialog_reports_system_exit(qtbot) -> None:
    parent = QWidget()
    qtbot.addWidget(parent)

    def work(_on_progress, _on_status) -> None:
        raise SystemExit(1)

    ok, error = run_with_progress_dialog(
        parent,
        title="Test",
        initial_status="Starting…",
        work=work,
        timeout_seconds=5.0,
    )

    assert ok is False
    assert error == "Operation exited with code 1."
