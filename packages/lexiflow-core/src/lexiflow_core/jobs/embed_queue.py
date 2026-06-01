"""Enqueue embedding jobs for translated text changes."""

from __future__ import annotations

from uuid import UUID

from lexiflow_core.jobs.models import JobRequest, JobType
from lexiflow_core.jobs.service import JobService


def enqueue_translated_text_embed(job_service: JobService, text_id: UUID) -> None:
    """Queue a background embed job for a text's translated variant."""
    job_service.enqueue(
        JobRequest(
            job_type=JobType.EMBED,
            payload={"text_id": str(text_id)},
        )
    )
