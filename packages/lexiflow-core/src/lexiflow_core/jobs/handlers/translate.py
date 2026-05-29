"""Plain translation job handler."""

from __future__ import annotations

from uuid import UUID

from lexiflow_core.jobs.handlers.cleanup import (
    TRANSLATE_PHASE_ENSURE_NATIVE,
    TRANSLATE_PHASE_PLAIN,
)
from lexiflow_core.jobs.models import JobRecord, JobRequest, JobType
from lexiflow_core.jobs.service import JobService
from lexiflow_core.library.text_repository import TextRepository
from lexiflow_core.llm.prompts import render_prompt
from lexiflow_core.llm.protocol import LLMProvider


def _text_id_from_payload(job: JobRecord) -> UUID:
    raw = job.payload.get("text_id")
    if not isinstance(raw, str):
        raise ValueError(f"job {job.id} is missing text_id")
    return UUID(raw)


def _phase(job: JobRecord) -> str:
    phase = job.payload.get("phase", TRANSLATE_PHASE_PLAIN)
    if not isinstance(phase, str):
        raise ValueError(f"job {job.id} has invalid phase: {phase!r}")
    if phase not in (TRANSLATE_PHASE_PLAIN, TRANSLATE_PHASE_ENSURE_NATIVE):
        raise ValueError(f"job {job.id} has invalid phase: {phase!r}")
    return phase


def handle_translate(
    job: JobRecord,
    *,
    llm: LLMProvider,
    repo: TextRepository,
    job_service: JobService,
) -> None:
    """Run plain translation or ensure-native step for staged generation."""
    try:
        text_id = _text_id_from_payload(job)
        phase = _phase(job)
    except ValueError as exc:
        job_service.fail(job.id, str(exc))
        return

    record = repo.get_text(text_id)

    try:
        if phase == TRANSLATE_PHASE_ENSURE_NATIVE:
            cleaned = job.payload.get("cleaned")
            if not isinstance(cleaned, str) or not cleaned:
                raise ValueError(f"job {job.id} is missing cleaned markdown")
            prompt = render_prompt(
                "translate",
                native_language=record.native_language,
                target_language=record.native_language,
                source_markdown=cleaned,
            )
            native_markdown = llm.complete(prompt)
            repo.write_native_variant(text_id, native_markdown)
            job_service.enqueue(
                JobRequest(
                    job_type=JobType.TRANSLATE,
                    payload={
                        "text_id": str(text_id),
                        "phase": TRANSLATE_PHASE_PLAIN,
                    },
                )
            )
            job_service.complete(job.id, {})
            return

        source_markdown = repo.read_native_variant(text_id)
        prompt = render_prompt(
            "translate",
            native_language=record.native_language,
            target_language=record.target_language,
            source_markdown=source_markdown,
        )
        translated = llm.complete(prompt)
    except Exception as exc:
        job_service.fail(job.id, str(exc))
        return

    repo.apply_translated_variant(text_id, translated)
    job_service.complete(job.id, {})
