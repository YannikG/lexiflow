"""Tests for the background jobs panel dialog."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from lexiflow_core.jobs.models import JobRequest, JobStatus, JobType
from lexiflow_core.jobs.service import JobService
from lexiflow_ui.dialogs.job_detail_dialog import JobDetailDialog
from lexiflow_ui.dialogs.jobs_panel_dialog import (
    _TAB_FAILED,
    _TAB_SUCCESS,
    JobsPanelDialog,
)
from lexiflow_ui.jobs_display import JOB_TABLE_HEADERS
from PySide6.QtWidgets import QWidget


def test_jobs_panel_shows_jobs_in_queue_tab(qtbot, tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    JobService(data_root).enqueue(
        JobRequest(job_type=JobType.DOWNLOAD_SPACY, payload={"iso": "es"})
    )

    parent = QWidget()
    qtbot.addWidget(parent)
    dialog = JobsPanelDialog(data_root=data_root, parent=parent)
    qtbot.addWidget(dialog)
    dialog.show()
    qtbot.waitExposed(dialog)

    assert dialog._tabs.currentIndex() == 0
    assert dialog._table.columnCount() == len(JOB_TABLE_HEADERS)
    assert dialog._table.rowCount() == 1
    assert dialog._table.item(0, 0).text() == "download_spacy"
    assert dialog._table.item(0, 1).text() == JobStatus.PENDING.value

    dialog._table.selectRow(0)
    qtbot.wait(10)

    assert dialog._cancel_button.isEnabled()
    assert not dialog._retry_button.isEnabled()


def test_jobs_panel_tabs_show_separate_job_lists(qtbot, tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    jobs = JobService(data_root)
    failed_id = jobs.enqueue(
        JobRequest(job_type=JobType.DOWNLOAD_SPACY, payload={"iso": "de"})
    )
    claimed = jobs.claim_next()
    assert claimed is not None
    jobs.fail(failed_id, "download failed")
    completed_id = jobs.enqueue(
        JobRequest(job_type=JobType.CLEANUP, payload={"text_id": "done"})
    )
    claimed = jobs.claim_next()
    assert claimed is not None
    jobs.complete(completed_id, {"ok": True})
    pending_id = jobs.enqueue(
        JobRequest(job_type=JobType.CLEANUP, payload={"text_id": "wait"})
    )

    parent = QWidget()
    qtbot.addWidget(parent)
    dialog = JobsPanelDialog(data_root=data_root, parent=parent)
    qtbot.addWidget(dialog)
    dialog.show()
    qtbot.waitExposed(dialog)

    assert dialog._table.rowCount() == 1
    assert dialog._table.item(0, 1).text() == JobStatus.PENDING.value

    dialog._tabs.setCurrentIndex(_TAB_SUCCESS)
    qtbot.wait(10)
    assert dialog._table.rowCount() == 1
    assert dialog._table.item(0, 1).text() == JobStatus.COMPLETED.value
    assert not dialog._retry_button.isEnabled()
    assert not dialog._cancel_button.isEnabled()

    dialog._tabs.setCurrentIndex(_TAB_FAILED)
    qtbot.wait(10)
    assert dialog._table.rowCount() == 1
    assert dialog._table.item(0, 1).text() == JobStatus.FAILED.value
    dialog._table.selectRow(0)
    qtbot.wait(10)
    assert dialog._retry_button.isEnabled()
    assert not dialog._cancel_button.isEnabled()

    dialog._tabs.setCurrentIndex(0)
    qtbot.wait(10)
    job = dialog._job_for_row(0)
    assert job is not None
    assert job.id == pending_id


def test_jobs_panel_queue_tab_ignores_completed_and_failed(
    qtbot, tmp_path: Path
) -> None:
    data_root = tmp_path / "LexiFlow"
    jobs = JobService(data_root)
    for index in range(25):
        failed_id = jobs.enqueue(
            JobRequest(job_type=JobType.EMBED, payload={"prompt": f"fail-{index}"})
        )
        claimed = jobs.claim_next()
        assert claimed is not None
        jobs.fail(failed_id, f"error-{index}")
    jobs.enqueue(JobRequest(job_type=JobType.CLEANUP, payload={"text_id": "active"}))

    parent = QWidget()
    qtbot.addWidget(parent)
    dialog = JobsPanelDialog(data_root=data_root, parent=parent)
    qtbot.addWidget(dialog)
    dialog.show()
    qtbot.waitExposed(dialog)

    assert dialog._table.rowCount() == 1
    assert dialog._table.item(0, 1).text() == JobStatus.PENDING.value


def test_jobs_panel_poll_updates_running_status(qtbot, tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    jobs = JobService(data_root)
    jobs.enqueue(JobRequest(job_type=JobType.CLEANUP, payload={"text_id": "x"}))

    parent = QWidget()
    qtbot.addWidget(parent)
    dialog = JobsPanelDialog(data_root=data_root, parent=parent)
    qtbot.addWidget(dialog)
    dialog.show()
    qtbot.waitExposed(dialog)

    assert dialog._poll_timer.isActive()
    assert dialog._table.item(0, 1).text() == JobStatus.PENDING.value

    claimed = jobs.claim_next()
    assert claimed is not None
    dialog._poll_jobs()

    assert dialog._table.item(0, 1).text() == JobStatus.RUNNING.value


def test_jobs_panel_double_click_opens_detail_dialog(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    JobService(data_root).enqueue(
        JobRequest(job_type=JobType.DOWNLOAD_SPACY, payload={"iso": "es"})
    )

    dialog = JobsPanelDialog(data_root=data_root)

    job = dialog._job_for_row(0)
    assert job is not None
    with patch("lexiflow_ui.dialogs.jobs_panel_dialog.open_job_detail") as open_detail:
        dialog._on_cell_double_clicked(0, 0)
        open_detail.assert_called_once_with(dialog, job)


def test_job_detail_dialog_shows_full_text(qtbot, tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    jobs = JobService(data_root)
    job_id = jobs.enqueue(
        JobRequest(job_type=JobType.DOWNLOAD_SPACY, payload={"iso": "fr"})
    )
    claimed = jobs.claim_next()
    assert claimed is not None
    job = jobs.complete(job_id, {"path": "/tmp"})
    assert job.completed_at is not None

    detail = JobDetailDialog(job=job)
    qtbot.addWidget(detail)
    detail.show()
    qtbot.waitExposed(detail)

    from PySide6.QtWidgets import QPlainTextEdit

    editor = detail.findChild(QPlainTextEdit, "job_detail_body")
    assert editor is not None
    text = editor.toPlainText()
    assert "download_spacy" in text
    assert '"iso": "fr"' in text
    assert '"path": "/tmp"' in text
    assert "Duration:" in text
