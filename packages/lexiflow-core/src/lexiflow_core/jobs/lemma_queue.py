"""Enqueue lemma inference jobs."""

from __future__ import annotations

from lexiflow_core.jobs.models import JobRequest, JobType
from lexiflow_core.jobs.service import JobService


def enqueue_lemma_job(
    job_service: JobService,
    *,
    language_code: str,
    surface_form: str,
    native_language: str,
    context: str = "",
) -> None:
    """Queue background lemma inference for reader highlight-add."""
    job_service.enqueue(
        JobRequest(
            job_type=JobType.LEMMA,
            payload={
                "language_code": language_code,
                "surface_form": surface_form.strip(),
                "native_language": native_language,
                "context": context.strip(),
            },
        )
    )
