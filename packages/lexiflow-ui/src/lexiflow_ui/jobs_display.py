"""Format job records for the jobs panel UI."""

from __future__ import annotations

import json
from datetime import datetime

from lexiflow_core.jobs.job_errors import user_facing_job_error
from lexiflow_core.jobs.models import JobRecord, JobStatus

PANEL_JOB_STATUSES: frozenset[JobStatus] = frozenset(
    {JobStatus.PENDING, JobStatus.RUNNING, JobStatus.FAILED}
)

JOB_TABLE_HEADERS: tuple[str, ...] = (
    "Job",
    "Status",
    "Duration",
    "Created",
    "Started",
    "Completed",
)


def format_job_timestamp(value: datetime | None) -> str:
    """Format a UTC job timestamp for display in local time."""
    if value is None:
        return "—"
    return value.astimezone().strftime("%Y-%m-%d %H:%M")


def job_duration_seconds(job: JobRecord) -> float | None:
    """Elapsed seconds from start to completion, or None if not finished."""
    if job.completed_at is None:
        return None
    start = job.started_at if job.started_at is not None else job.created_at
    return (job.completed_at - start).total_seconds()


def format_job_duration(job: JobRecord) -> str:
    """Human-readable duration for a finished job."""
    seconds = job_duration_seconds(job)
    if seconds is None:
        return "—"
    total = int(seconds)
    if total < 60:
        return f"{total}s"
    minutes, secs = divmod(total, 60)
    if minutes < 60:
        return f"{minutes}m {secs}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes}m"


def filter_panel_jobs(jobs: list[JobRecord]) -> list[JobRecord]:
    """Jobs shown in the panel (excludes completed and cancelled history)."""
    return [job for job in jobs if job.status in PANEL_JOB_STATUSES]


def job_table_cell_texts(job: JobRecord) -> tuple[str, str, str, str, str, str]:
    """Column values for one row in the jobs panel table."""
    return (
        job.job_type.value,
        job.status.value,
        format_job_duration(job),
        format_job_timestamp(job.created_at),
        format_job_timestamp(job.started_at),
        format_job_timestamp(job.completed_at),
    )


def _format_json_mapping(value: dict[str, object] | None) -> str:
    if value is None:
        return "—"
    return json.dumps(value, indent=2, ensure_ascii=False, default=str)


def format_job_full_detail(job: JobRecord) -> str:
    """Full job information for the detail dialog."""
    lines = [
        f"ID: {job.id}",
        f"Job type: {job.job_type.value}",
        f"Status: {job.status.value}",
        f"Created: {format_job_timestamp(job.created_at)}",
        f"Updated: {format_job_timestamp(job.updated_at)}",
        f"Started: {format_job_timestamp(job.started_at)}",
        f"Completed: {format_job_timestamp(job.completed_at)}",
        f"Duration: {format_job_duration(job)}",
        "",
        "Payload:",
        _format_json_mapping(job.payload),
        "",
        "Result:",
        _format_json_mapping(job.result),
    ]
    if job.error_message:
        lines.extend(
            [
                "",
                "Error:",
                user_facing_job_error(job.error_message),
            ]
        )
    return "\n".join(lines)
