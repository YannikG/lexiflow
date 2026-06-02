"""Enqueue translation jobs."""

from __future__ import annotations

from uuid import UUID

from lexiflow_core.jobs.handlers.cleanup import TRANSLATE_PHASE_PLAIN
from lexiflow_core.jobs.models import JobRequest, JobType
from lexiflow_core.jobs.service import JobService


def enqueue_retranslate(job_service: JobService, text_id: UUID) -> None:
    """Queue a plain re-translation job for an existing text."""
    job_service.enqueue(
        JobRequest(
            job_type=JobType.TRANSLATE,
            payload={"text_id": str(text_id), "phase": TRANSLATE_PHASE_PLAIN},
        )
    )
