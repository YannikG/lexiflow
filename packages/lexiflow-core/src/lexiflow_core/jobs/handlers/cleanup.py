"""Markdown cleanup job handler."""

from __future__ import annotations

from uuid import UUID

from lexiflow_core.jobs.handlers.cleanup_output import (
    CleanupOutputError,
    validate_cleanup_output,
)
from lexiflow_core.jobs.job_errors import user_facing_job_error
from lexiflow_core.jobs.models import JobRecord, JobRequest, JobType
from lexiflow_core.jobs.service import JobService
from lexiflow_core.library.models import TextRecord
from lexiflow_core.library.text_repository import TextRepository
from lexiflow_core.llm.prompt_languages import prompt_language_label
from lexiflow_core.llm.prompts import render_prompt
from lexiflow_core.llm.protocol import LLMProvider

SOURCE_ROUTE_NATIVE = "native"
SOURCE_ROUTE_TARGET = "target"
TRANSLATE_PHASE_PLAIN = "plain"
TRANSLATE_PHASE_ENSURE_NATIVE = "ensure_native"


def _text_id_from_payload(job: JobRecord) -> UUID:
    raw = job.payload.get("text_id")
    if not isinstance(raw, str):
        raise ValueError(f"job {job.id} is missing text_id")
    return UUID(raw)


def _source_route(job: JobRecord) -> str:
    route = job.payload.get("source_route", SOURCE_ROUTE_NATIVE)
    if not isinstance(route, str):
        raise ValueError(f"job {job.id} has invalid source_route: {route!r}")
    if route not in (SOURCE_ROUTE_NATIVE, SOURCE_ROUTE_TARGET):
        raise ValueError(f"job {job.id} has invalid source_route: {route!r}")
    return route


def _raw_paste(job: JobRecord) -> str:
    raw = job.payload.get("raw_paste")
    if not isinstance(raw, str) or not raw:
        raise ValueError(f"job {job.id} is missing raw_paste")
    return raw


def _source_language_code(record: TextRecord, route: str) -> str:
    if route == SOURCE_ROUTE_NATIVE:
        return record.native_language.strip()
    return record.target_language.strip()


def handle_cleanup(
    job: JobRecord,
    *,
    llm: LLMProvider,
    repo: TextRepository,
    job_service: JobService,
) -> None:
    """Run markdown cleanup and enqueue the next staged-generation step."""
    try:
        text_id = _text_id_from_payload(job)
        raw_paste = _raw_paste(job)
        route = _source_route(job)
    except ValueError as exc:
        job_service.fail(job.id, str(exc))
        return

    record = repo.get_text(text_id)
    source_language = _source_language_code(record, route)
    prompt = render_prompt(
        "cleanup",
        source_language=source_language,
        source_language_label=prompt_language_label(source_language),
        native_language=record.native_language,
        native_language_label=prompt_language_label(record.native_language),
        target_language=record.target_language,
        target_language_label=prompt_language_label(record.target_language),
        pasted_content=raw_paste,
    )
    try:
        raw_cleaned = llm.complete(prompt)
    except Exception as exc:
        job_service.fail(job.id, user_facing_job_error(str(exc)))
        return

    try:
        cleaned = validate_cleanup_output(raw_paste=raw_paste, cleaned=raw_cleaned)
    except CleanupOutputError as exc:
        job_service.fail(job.id, user_facing_job_error(str(exc)))
        return

    if route == SOURCE_ROUTE_NATIVE:
        repo.apply_native_variant(text_id, cleaned)
        job_service.enqueue(
            JobRequest(
                job_type=JobType.TRANSLATE,
                payload={"text_id": str(text_id), "phase": TRANSLATE_PHASE_PLAIN},
            )
        )
    else:
        job_service.enqueue(
            JobRequest(
                job_type=JobType.TRANSLATE,
                payload={
                    "text_id": str(text_id),
                    "phase": TRANSLATE_PHASE_ENSURE_NATIVE,
                    "cleaned": cleaned,
                },
            )
        )
    job_service.complete(job.id, {})
