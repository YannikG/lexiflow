"""Lemma inference types and non-blocking backend for the add-word dialog."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from lexiflow_core.jobs.lemma_queue import cancel_lemma_job, enqueue_lemma_job
from lexiflow_core.jobs.service import JobService
from lexiflow_core.vocabulary.lemma_form import parse_word_category
from lexiflow_core.vocabulary.lemma_resolution import resolve_lemma_with_spacy
from lexiflow_core.vocabulary.models import WordCategory

from lexiflow_ui.lemma_job_wait import LemmaJobPollState, find_lemma_job_result
from lexiflow_ui.worker_supervisor import WorkerSupervisor

LEMMA_FILL_TIMEOUT_MS = 120_000
LEMMA_FILL_POLL_MS = 200


@dataclass(frozen=True)
class LemmaSuggestions:
    lemma: str
    translation: str
    explanation: str
    word_category: WordCategory


@dataclass(frozen=True)
class AsyncLemmaFill:
    begin: Callable[[str], None]
    poll: Callable[[str], LemmaSuggestions | None]
    cancel: Callable[[str], None] | None = None


def _merge_llm_with_spacy(
    completed: dict[str, object],
    spacy_hint: LemmaSuggestions | None,
) -> LemmaSuggestions:
    llm_lemma = str(completed.get("lemma", "")).strip()
    llm_category = parse_word_category(completed.get("category"))
    word_category = llm_category
    if completed.get("category") is None and spacy_hint is not None:
        word_category = spacy_hint.word_category
    return LemmaSuggestions(
        lemma=llm_lemma or (spacy_hint.lemma if spacy_hint is not None else ""),
        translation=str(completed.get("translation", "")),
        explanation=str(completed.get("explanation", "")),
        word_category=word_category,
    )


def make_async_lemma_fill(
    data_root: Path,
    *,
    language_code: str,
    native_language: str,
    supervisor: WorkerSupervisor | None,
) -> AsyncLemmaFill:
    """Return non-blocking begin/poll callbacks for lemma inference."""
    spacy_hints: dict[str, LemmaSuggestions] = {}
    immediate: dict[str, LemmaSuggestions] = {}

    def begin(surface_form: str) -> None:
        normalized = surface_form.strip()
        spacy_hints.pop(normalized, None)
        immediate.pop(normalized, None)
        spacy_result = resolve_lemma_with_spacy(
            data_root,
            language_code,
            normalized,
        )
        if spacy_result is not None and spacy_result.lemma.strip():
            suggestions = LemmaSuggestions(
                lemma=spacy_result.lemma,
                translation=spacy_result.translation,
                explanation=spacy_result.explanation,
                word_category=spacy_result.word_category,
            )
            if spacy_result.translation.strip():
                immediate[normalized] = suggestions
                return
            spacy_hints[normalized] = suggestions
        job_service = JobService(data_root)
        enqueue_lemma_job(
            job_service,
            language_code=language_code,
            surface_form=normalized,
            native_language=native_language,
            context="",
        )
        if supervisor is not None:
            supervisor.ensure_running()

    def poll(surface_form: str) -> LemmaSuggestions | None:
        normalized = surface_form.strip()
        ready = immediate.get(normalized)
        if ready is not None:
            return ready
        polled = find_lemma_job_result(data_root, surface_form=normalized)
        if polled == LemmaJobPollState.PENDING.value:
            return None
        if isinstance(polled, dict):
            return _merge_llm_with_spacy(polled, spacy_hints.get(normalized))
        if polled in (
            LemmaJobPollState.FAILED.value,
            LemmaJobPollState.CANCELLED.value,
        ):
            hint = spacy_hints.get(normalized)
            if hint is not None:
                return hint
            return LemmaSuggestions(
                lemma="",
                translation="",
                explanation="",
                word_category=WordCategory.OTHER,
            )
        return LemmaSuggestions(
            lemma="",
            translation="",
            explanation="",
            word_category=WordCategory.OTHER,
        )

    def cancel(surface_form: str) -> None:
        cancel_lemma_job(data_root, surface_form=surface_form)

    return AsyncLemmaFill(begin=begin, poll=poll, cancel=cancel)
