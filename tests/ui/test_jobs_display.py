"""Tests for jobs panel formatting helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from lexiflow_core.jobs.models import JobRecord, JobStatus, JobType
from lexiflow_ui.jobs_display import (
    filter_panel_jobs,
    format_job_duration,
    format_job_full_detail,
    job_table_cell_texts,
)


def _job(**overrides) -> JobRecord:
    base = {
        "id": uuid4(),
        "job_type": JobType.TRANSLATE,
        "status": JobStatus.FAILED,
        "payload": {"text_id": "es"},
        "result": None,
        "error_message": "translation failed",
        "created_at": datetime(2026, 6, 2, 10, 0, tzinfo=UTC),
        "updated_at": datetime(2026, 6, 2, 10, 1, tzinfo=UTC),
        "started_at": datetime(2026, 6, 2, 10, 2, tzinfo=UTC),
        "completed_at": datetime(2026, 6, 2, 10, 3, tzinfo=UTC),
    }
    base.update(overrides)
    return JobRecord(**base)


def test_job_table_cell_texts_includes_type_status_duration_and_timestamps() -> None:
    job = _job()
    cells = job_table_cell_texts(job)
    assert cells[0] == "translate"
    assert cells[1] == "failed"
    assert cells[2] == "1m 0s"
    assert "2026-06-02" in cells[3]
    assert "2026-06-02" in cells[4]
    assert "2026-06-02" in cells[5]


def test_filter_panel_jobs_excludes_completed_and_cancelled() -> None:
    completed = _job(status=JobStatus.COMPLETED, error_message=None)
    cancelled = _job(status=JobStatus.CANCELLED, error_message=None)
    pending = _job(status=JobStatus.PENDING, error_message=None)
    visible = filter_panel_jobs([completed, cancelled, pending])
    assert visible == [pending]


def test_format_job_duration_pending_job() -> None:
    job = _job(status=JobStatus.PENDING, started_at=None, completed_at=None)
    assert format_job_duration(job) == "—"


def test_format_job_full_detail_includes_all_fields() -> None:
    job = _job(result={"ok": True})
    detail = format_job_full_detail(job)
    assert f"ID: {job.id}" in detail
    assert "Job type: translate" in detail
    assert "Status: failed" in detail
    assert "Created:" in detail
    assert "Updated:" in detail
    assert "Started:" in detail
    assert "Completed:" in detail
    assert "Duration: 1m 0s" in detail
    assert '"text_id": "es"' in detail
    assert '"ok": true' in detail
    assert "Error:\ntranslation failed" in detail
