"""Tests for application quit confirmation with active jobs."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from lexiflow_core.jobs.models import JobRequest, JobType
from lexiflow_core.jobs.service import JobService
from lexiflow_ui.shutdown_flow import confirm_application_quit
from PySide6.QtWidgets import QMessageBox


def test_confirm_quit_wait_keeps_app_open(
    qtbot, tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    JobService(tmp_path).enqueue(
        JobRequest(job_type=JobType.CLEANUP, payload={"text_id": "x"})
    )
    parent = MagicMock()
    worker = MagicMock()
    llama = MagicMock()

    box = MagicMock()
    box.exec.return_value = int(QMessageBox.StandardButton.Yes)

    class _MessageBoxFactory:
        StandardButton = QMessageBox.StandardButton

        def __call__(self, _parent: object) -> MagicMock:
            return box

    monkeypatch.setattr(
        "lexiflow_ui.shutdown_flow.QMessageBox",
        _MessageBoxFactory(),
    )

    allowed = confirm_application_quit(
        parent,
        job_service=JobService(tmp_path),
        worker_supervisor=worker,
        llama_supervisor=llama,
    )

    assert allowed is False
    worker.shutdown.assert_not_called()
    llama.shutdown.assert_not_called()
