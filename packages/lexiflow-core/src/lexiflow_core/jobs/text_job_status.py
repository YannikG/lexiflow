"""Read-only helpers for text variant generation job state."""

from __future__ import annotations

from uuid import UUID

from lexiflow_core.jobs.models import JobRecord, JobStatus, JobType
from lexiflow_core.library.reader_tabs import (
    SIMPLIFIED_PREFIX,
    TRANSLATED_TAB,
    level_from_simplified_variant,
)

_ACTIVE_STATUSES = frozenset({JobStatus.PENDING, JobStatus.RUNNING})


def _matches_text(job: JobRecord, text_id: UUID) -> bool:
    payload_text_id = job.payload.get("text_id")
    return isinstance(payload_text_id, str) and payload_text_id == str(text_id)


def _jobs_for_variant(
    jobs: tuple[JobRecord, ...] | list[JobRecord],
    *,
    text_id: UUID,
    variant_name: str,
) -> tuple[JobRecord, ...]:
    if variant_name == TRANSLATED_TAB:
        return tuple(
            job
            for job in jobs
            if job.job_type == JobType.TRANSLATE and _matches_text(job, text_id)
        )
    if variant_name.startswith(SIMPLIFIED_PREFIX):
        level = level_from_simplified_variant(variant_name)
        if level is None:
            return ()
        return tuple(
            job
            for job in jobs
            if job.job_type == JobType.SIMPLIFY
            and _matches_text(job, text_id)
            and isinstance(job.payload.get("level"), str)
            and job.payload["level"].strip().upper() == level.value
        )
    return ()


def missing_variant_message(
    jobs: tuple[JobRecord, ...] | list[JobRecord],
    *,
    text_id: UUID,
    variant_name: str,
) -> str:
    """Return user-facing copy when a reader variant file is missing."""
    relevant = _jobs_for_variant(jobs, text_id=text_id, variant_name=variant_name)
    if any(job.status in _ACTIVE_STATUSES for job in relevant):
        return "This variant is still being generated. Background jobs are running."
    failed = [job for job in relevant if job.status == JobStatus.FAILED]
    if failed:
        latest = max(failed, key=lambda job: job.updated_at)
        if latest.error_message:
            return f"Generation failed: {latest.error_message}"
        return "Generation failed. Check background job status and try again."
    return "This variant is not available yet."
