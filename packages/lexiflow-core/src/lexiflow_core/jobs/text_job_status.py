"""Read-only helpers for text variant generation job state."""

from __future__ import annotations

from uuid import UUID

from lexiflow_core.jobs.job_errors import user_facing_job_error
from lexiflow_core.jobs.models import JobRecord, JobStatus, JobType
from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.library.reader_tabs import (
    NATIVE_TAB,
    SIMPLIFIED_PREFIX,
    TRANSLATED_TAB,
    level_from_simplified_variant,
)

_ACTIVE_STATUSES = frozenset({JobStatus.PENDING, JobStatus.RUNNING})
_PENDING_MESSAGE = "This variant is still being generated. Background jobs are running."


def _matches_text(job: JobRecord, text_id: UUID) -> bool:
    payload_text_id = job.payload.get("text_id")
    return isinstance(payload_text_id, str) and payload_text_id == str(text_id)


def _cleanup_jobs_for_text(
    jobs: tuple[JobRecord, ...] | list[JobRecord],
    *,
    text_id: UUID,
) -> tuple[JobRecord, ...]:
    return tuple(
        job
        for job in jobs
        if job.job_type == JobType.CLEANUP and _matches_text(job, text_id)
    )


def cleanup_job_message(
    jobs: tuple[JobRecord, ...] | list[JobRecord],
    *,
    text_id: UUID,
) -> str | None:
    """Return user-facing copy for native cleanup state, or None when not applicable."""
    relevant = _cleanup_jobs_for_text(jobs, text_id=text_id)
    if not relevant:
        return None
    if any(job.status in _ACTIVE_STATUSES for job in relevant):
        return _PENDING_MESSAGE
    failed = [job for job in relevant if job.status == JobStatus.FAILED]
    if failed:
        latest = max(failed, key=lambda job: job.updated_at)
        if latest.error_message:
            return f"Generation failed: {user_facing_job_error(latest.error_message)}"
        return "Generation failed. Check background job status and try again."
    return None


def _jobs_for_variant(
    jobs: tuple[JobRecord, ...] | list[JobRecord],
    *,
    text_id: UUID,
    variant_name: str,
) -> tuple[JobRecord, ...]:
    if variant_name == NATIVE_TAB:
        return _cleanup_jobs_for_text(jobs, text_id=text_id)
    if variant_name == TRANSLATED_TAB:
        cleanup_relevant = _cleanup_jobs_for_text(jobs, text_id=text_id)
        if any(job.status in _ACTIVE_STATUSES for job in cleanup_relevant):
            return cleanup_relevant
        failed_cleanup = [
            job for job in cleanup_relevant if job.status == JobStatus.FAILED
        ]
        if failed_cleanup:
            return tuple(failed_cleanup)
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


def pending_simplified_variants(
    jobs: tuple[JobRecord, ...] | list[JobRecord],
    *,
    text_id: UUID,
) -> tuple[str, ...]:
    """Return simplified variant names with active simplify jobs but no file yet."""
    variants: list[str] = []
    for job in jobs:
        if job.job_type != JobType.SIMPLIFY or not _matches_text(job, text_id):
            continue
        if job.status not in _ACTIVE_STATUSES:
            continue
        level = job.payload.get("level")
        if not isinstance(level, str):
            continue
        try:
            parsed = CEFRLevel(level.strip().upper())
        except ValueError:
            continue
        variants.append(f"{SIMPLIFIED_PREFIX}{parsed.value.lower()}")
    return tuple(dict.fromkeys(variants))


def simplified_variant_job_message(
    jobs: tuple[JobRecord, ...] | list[JobRecord],
    *,
    text_id: UUID,
    variant_name: str,
) -> str | None:
    """Return user-facing copy for simplify state on a simplified tab."""
    if not variant_name.startswith(SIMPLIFIED_PREFIX):
        return None
    relevant = _jobs_for_variant(jobs, text_id=text_id, variant_name=variant_name)
    if not relevant:
        return None
    if any(job.status in _ACTIVE_STATUSES for job in relevant):
        return _PENDING_MESSAGE
    failed = [job for job in relevant if job.status == JobStatus.FAILED]
    if failed:
        latest = max(failed, key=lambda job: job.updated_at)
        if latest.error_message:
            return f"Generation failed: {user_facing_job_error(latest.error_message)}"
        return "Generation failed. Check background job status and try again."
    return None


def missing_variant_message(
    jobs: tuple[JobRecord, ...] | list[JobRecord],
    *,
    text_id: UUID,
    variant_name: str,
) -> str:
    """Return user-facing copy when a reader variant file is missing."""
    relevant = _jobs_for_variant(jobs, text_id=text_id, variant_name=variant_name)
    if any(job.status in _ACTIVE_STATUSES for job in relevant):
        return _PENDING_MESSAGE
    failed = [job for job in relevant if job.status == JobStatus.FAILED]
    if failed:
        latest = max(failed, key=lambda job: job.updated_at)
        if latest.error_message:
            return f"Generation failed: {user_facing_job_error(latest.error_message)}"
        return "Generation failed. Check background job status and try again."
    return "This variant is not available yet."
