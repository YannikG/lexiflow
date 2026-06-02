"""Enqueue lemma inference jobs."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.jobs.models import JobId, JobRecord, JobRequest, JobStatus, JobType
from lexiflow_core.jobs.service import JobService


def enqueue_lemma_job(
    job_service: JobService,
    *,
    language_code: str,
    surface_form: str,
    native_language: str,
    context: str = "",
) -> JobId:
    """Queue background lemma inference for reader highlight-add."""
    return job_service.enqueue(
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


def find_active_lemma_job(
    data_root: Path,
    *,
    surface_form: str,
) -> JobRecord | None:
    """Return the newest pending or running lemma job for a surface form."""
    normalized = surface_form.strip()
    for job in JobService(data_root).list_jobs(limit=100):
        if job.job_type != JobType.LEMMA:
            continue
        if job.payload.get("surface_form") != normalized:
            continue
        if job.status in {JobStatus.PENDING, JobStatus.RUNNING}:
            return job
    return None


def cancel_lemma_job(data_root: Path, *, surface_form: str) -> None:
    """Cancel a pending or in-flight lemma job for the given surface form."""
    job = find_active_lemma_job(data_root, surface_form=surface_form)
    if job is None:
        return
    JobService(data_root).cancel(job.id)
