"""Lemma inference job handler."""

from __future__ import annotations

from lexiflow_core.jobs.models import JobId, JobRecord, JobStatus
from lexiflow_core.jobs.service import JobService
from lexiflow_core.llm.prompt_languages import prompt_language_label
from lexiflow_core.llm.prompts import render_prompt
from lexiflow_core.llm.protocol import LLMProvider
from lexiflow_core.vocabulary.lemma_output import (
    LemmaOutputError,
    lemma_json_schema,
    parse_lemma_output,
)


def _payload_strings(job: JobRecord) -> tuple[str, str, str, str]:
    language_code = job.payload.get("language_code")
    surface_form = job.payload.get("surface_form")
    native_language = job.payload.get("native_language")
    context = job.payload.get("context", "")
    if not isinstance(language_code, str) or not language_code.strip():
        raise ValueError(f"job {job.id} is missing language_code")
    if not isinstance(surface_form, str) or not surface_form.strip():
        raise ValueError(f"job {job.id} is missing surface_form")
    if not isinstance(native_language, str) or not native_language.strip():
        raise ValueError(f"job {job.id} is missing native_language")
    if not isinstance(context, str):
        raise ValueError(f"job {job.id} has invalid context")
    return (
        language_code.strip(),
        surface_form.strip(),
        native_language.strip(),
        context.strip(),
    )


def _job_was_cancelled(job_service: JobService, job_id: JobId) -> bool:
    record = job_service.get(job_id)
    return record is None or record.status == JobStatus.CANCELLED


def handle_lemma(
    job: JobRecord,
    *,
    job_service: JobService,
    llm: LLMProvider,
) -> None:
    """Infer lemma, translation, and explanation for a highlighted surface form."""
    if _job_was_cancelled(job_service, job.id):
        return
    try:
        target_language, surface_form, native_language, context = _payload_strings(job)
    except ValueError as exc:
        job_service.fail(job.id, str(exc))
        return

    prompt = render_prompt(
        "lemma",
        target_language=target_language,
        target_language_label=prompt_language_label(target_language),
        native_language=native_language,
        native_language_label=prompt_language_label(native_language),
        surface_form=surface_form,
        context=context or "(none)",
    )
    try:
        raw_output = llm.complete(prompt, json_schema=lemma_json_schema())
        parsed = parse_lemma_output(raw_output, language_code=target_language)
    except LemmaOutputError as exc:
        job_service.fail(job.id, str(exc))
        return
    except Exception as exc:
        job_service.fail(job.id, str(exc))
        return

    if _job_was_cancelled(job_service, job.id):
        return

    job_service.complete(
        job.id,
        {
            "lemma": parsed.lemma,
            "translation": parsed.translation,
            "explanation": parsed.explanation,
            "category": parsed.word_category.value,
        },
    )
