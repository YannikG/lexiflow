"""Tests for the background jobs panel dialog."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from lexiflow_core.jobs.models import JobRequest, JobStatus, JobType
from lexiflow_core.jobs.service import JobService
from lexiflow_ui.dialogs.job_detail_dialog import JobDetailDialog
from lexiflow_ui.dialogs.jobs_panel_dialog import (
    TAB_FAILED,
    TAB_SUCCESS,
    JobsPanelDialog,
)
from lexiflow_ui.jobs_display import JOB_TABLE_HEADERS
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPlainTextEdit, QWidget

from tests.ui.jobs_panel_helpers import (
    jobs_panel_cancel_button,
    jobs_panel_poll_timer,
    jobs_panel_retry_button,
    jobs_panel_table,
    jobs_panel_tabs,
)


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

    table = jobs_panel_table(dialog)
    tabs = jobs_panel_tabs(dialog)
    assert tabs.currentIndex() == 0
    assert table.columnCount() == len(JOB_TABLE_HEADERS)
    assert table.rowCount() == 1
    assert table.item(0, 0).text() == "download_spacy"
    assert table.item(0, 1).text() == JobStatus.PENDING.value

    table.selectRow(0)
    qtbot.wait(10)

    assert jobs_panel_cancel_button(dialog).isEnabled()
    assert not jobs_panel_retry_button(dialog).isEnabled()


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

    table = jobs_panel_table(dialog)
    tabs = jobs_panel_tabs(dialog)
    retry = jobs_panel_retry_button(dialog)
    cancel = jobs_panel_cancel_button(dialog)

    assert table.rowCount() == 1
    assert table.item(0, 1).text() == JobStatus.PENDING.value

    tabs.setCurrentIndex(TAB_SUCCESS)
    qtbot.wait(10)
    assert table.rowCount() == 1
    assert table.item(0, 1).text() == JobStatus.COMPLETED.value
    assert not retry.isEnabled()
    assert not cancel.isEnabled()

    tabs.setCurrentIndex(TAB_FAILED)
    qtbot.wait(10)
    assert table.rowCount() == 1
    assert table.item(0, 1).text() == JobStatus.FAILED.value
    table.selectRow(0)
    qtbot.wait(10)
    assert retry.isEnabled()
    assert not cancel.isEnabled()

    tabs.setCurrentIndex(0)
    qtbot.wait(10)
    item = table.item(0, 0)
    assert item is not None
    job = JobService(data_root).get(UUID(str(item.data(Qt.ItemDataRole.UserRole))))
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

    table = jobs_panel_table(dialog)
    assert table.rowCount() == 1
    assert table.item(0, 1).text() == JobStatus.PENDING.value


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

    table = jobs_panel_table(dialog)
    assert jobs_panel_poll_timer(dialog).isActive()
    assert table.item(0, 1).text() == JobStatus.PENDING.value

    claimed = jobs.claim_next()
    assert claimed is not None
    qtbot.waitUntil(
        lambda: table.item(0, 1) is not None
        and table.item(0, 1).text() == JobStatus.RUNNING.value,
        timeout=3000,
    )


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

    editor = detail.findChild(QPlainTextEdit, "job_detail_body")
    assert editor is not None
    text = editor.toPlainText()
    assert "download_spacy" in text
    assert '"iso": "fr"' in text
    assert '"path": "/tmp"' in text
    assert "Duration:" in text
