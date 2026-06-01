"""Enqueue simplify jobs."""

from __future__ import annotations

from uuid import UUID

from lexiflow_core.jobs.models import JobRequest, JobType
from lexiflow_core.jobs.service import JobService


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
