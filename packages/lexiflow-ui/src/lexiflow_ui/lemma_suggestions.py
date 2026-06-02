"""Lemma inference types and non-blocking backend for the add-word dialog."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from lexiflow_core.jobs.lemma_queue import enqueue_lemma_job
from lexiflow_core.jobs.service import JobService
from lexiflow_core.vocabulary.lemma_form import parse_word_category
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


def make_async_lemma_fill(
    data_root: Path,
    *,
    language_code: str,
    native_language: str,
    supervisor: WorkerSupervisor | None,
) -> AsyncLemmaFill:
    """Return non-blocking begin/poll callbacks for LLM lemma inference."""

    def begin(surface_form: str) -> None:
        job_service = JobService(data_root)
        enqueue_lemma_job(
            job_service,
            language_code=language_code,
            surface_form=surface_form,
            native_language=native_language,
            context="",
        )
        if supervisor is not None:
            supervisor.ensure_running()

    def poll(surface_form: str) -> LemmaSuggestions | None:
        polled = find_lemma_job_result(data_root, surface_form=surface_form)
        if polled == LemmaJobPollState.PENDING.value:
            return None
        if polled == LemmaJobPollState.FAILED.value or not isinstance(polled, dict):
            return LemmaSuggestions(
                lemma="",
                translation="",
                explanation="",
                word_category=WordCategory.OTHER,
            )
        return LemmaSuggestions(
            lemma=str(polled.get("lemma", "")),
            translation=str(polled.get("translation", "")),
            explanation=str(polled.get("explanation", "")),
            word_category=parse_word_category(polled.get("category")),
        )

    return AsyncLemmaFill(begin=begin, poll=poll)
