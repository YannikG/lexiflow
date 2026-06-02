"""Enqueue and cancel simplify jobs."""

from __future__ import annotations

from uuid import UUID

from lexiflow_core.jobs.models import JobRequest, JobStatus, JobType
from lexiflow_core.jobs.service import JobService


def cancel_simplify_jobs(
    job_service: JobService,
    text_id: UUID,
    level: str,
) -> int:
    """Cancel pending or running simplify jobs for a text and level."""
    target_level = level.upper()
    text_key = str(text_id)
    cancelled = 0
    for job in job_service.list_jobs(limit=200):
        if job.job_type != JobType.SIMPLIFY:
            continue
        if job.payload.get("text_id") != text_key:
            continue
        if job.payload.get("level") != target_level:
            continue
        if job.status not in (JobStatus.PENDING, JobStatus.RUNNING):
            continue
        job_service.cancel(job.id)
        cancelled += 1
    return cancelled


def enqueue_simplify(
    job_service: JobService,
    text_id: UUID,
    level: str,
) -> None:
    """Queue a background simplify job for a text at the given CEFR level."""
    job_service.enqueue(
        JobRequest(
            job_type=JobType.SIMPLIFY,
            payload={"text_id": str(text_id), "level": level.upper()},
        )
    )
