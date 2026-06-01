"""Tests for text variant job status queries."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from lexiflow_core.jobs.models import JobRecord, JobStatus, JobType
from lexiflow_core.jobs.text_job_status import missing_variant_message
from lexiflow_core.library.reader_tabs import TRANSLATED_TAB

_NOW = datetime(2026, 6, 1, 12, 0, 0, tzinfo=UTC)


def _job(
    *,
    job_type: JobType,
    status: JobStatus,
    text_id: UUID,
    level: str | None = None,
    error_message: str | None = None,
) -> JobRecord:
    payload: dict[str, object] = {"text_id": str(text_id)}
    if level is not None:
        payload["level"] = level
    return JobRecord(
        id=uuid4(),
        job_type=job_type,
        status=status,
        payload=payload,
        result=None,
        error_message=error_message,
        created_at=_NOW,
        updated_at=_NOW,
        started_at=_NOW if status != JobStatus.PENDING else None,
        completed_at=(
            _NOW if status in (JobStatus.COMPLETED, JobStatus.FAILED) else None
        ),
    )


def test_missing_variant_message_reports_pending_translate() -> None:
    text_id = uuid4()
    jobs = [
        _job(
            job_type=JobType.TRANSLATE,
            status=JobStatus.PENDING,
            text_id=text_id,
        )
    ]
    message = missing_variant_message(
        jobs,
        text_id=text_id,
        variant_name=TRANSLATED_TAB,
    )
    assert "still being generated" in message.lower()


def test_missing_variant_message_reports_failed_simplify() -> None:
    text_id = uuid4()
    jobs = [
        _job(
            job_type=JobType.SIMPLIFY,
            status=JobStatus.FAILED,
            text_id=text_id,
            level="A2",
            error_message="invalid JSON",
        )
    ]
    message = missing_variant_message(
        jobs,
        text_id=text_id,
        variant_name="simplified-a2",
    )
    assert "generation failed" in message.lower()
    assert "invalid JSON" in message


def test_missing_variant_message_is_generic_without_matching_jobs() -> None:
    text_id = uuid4()
    message = missing_variant_message(
        [],
        text_id=text_id,
        variant_name=TRANSLATED_TAB,
    )
    assert message == "This variant is not available yet."


def test_missing_variant_message_ignores_other_text_jobs() -> None:
    text_id = uuid4()
    other_id = uuid4()
    jobs = [
        _job(
            job_type=JobType.TRANSLATE,
            status=JobStatus.FAILED,
            text_id=other_id,
            error_message="wrong text",
        )
    ]
    message = missing_variant_message(
        jobs,
        text_id=text_id,
        variant_name=TRANSLATED_TAB,
    )
    assert message == "This variant is not available yet."
