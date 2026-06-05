"""Tests for background progress dialog runner."""

from __future__ import annotations

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
