"""Lemma inference types and non-blocking backend for the add-word dialog."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from lexiflow_core.jobs.lemma_queue import cancel_lemma_job, enqueue_lemma_job
from lexiflow_core.jobs.service import JobService
from lexiflow_core.vocabulary.lemma_form import parse_word_category
from lexiflow_core.vocabulary.models import WordCategory

from lexiflow_ui.ai_worker_startup import ensure_background_workers
from lexiflow_ui.lemma_job_wait import LemmaJobPollState, find_lemma_job_result
from lexiflow_ui.llama_server_supervisor import LlamaServerSupervisor
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


def _lemma_suggestions_from_job(completed: dict[str, object]) -> LemmaSuggestions:
    return LemmaSuggestions(
        lemma=str(completed.get("lemma", "")).strip(),
        translation=str(completed.get("translation", "")),
        explanation=str(completed.get("explanation", "")),
        word_category=parse_word_category(completed.get("category")),
    )


def make_async_lemma_fill(
    data_root: Path,
    *,
    language_code: str,
    native_language: str,
    supervisor: WorkerSupervisor | None,
    llama_supervisor: LlamaServerSupervisor | None = None,
    embed_supervisor: LlamaServerSupervisor | None = None,
) -> AsyncLemmaFill:
    """Return non-blocking begin/poll callbacks for lemma inference."""
    empty = LemmaSuggestions(
        lemma="",
        translation="",
        explanation="",
        word_category=WordCategory.OTHER,
    )

    def begin(surface_form: str) -> None:
        normalized = surface_form.strip()
        job_service = JobService(data_root)
        enqueue_lemma_job(
            job_service,
            language_code=language_code,
            surface_form=normalized,
            native_language=native_language,
            context="",
        )
        if supervisor is not None:
            ensure_background_workers(
                supervisor,
                llama_supervisor=llama_supervisor,
            )

    def poll(surface_form: str) -> LemmaSuggestions | None:
        normalized = surface_form.strip()
        polled = find_lemma_job_result(data_root, surface_form=normalized)
        if polled == LemmaJobPollState.PENDING.value:
            return None
        if isinstance(polled, dict):
            return _lemma_suggestions_from_job(polled)
        if polled in (
            LemmaJobPollState.FAILED.value,
            LemmaJobPollState.CANCELLED.value,
        ):
            return empty
        return empty

    def cancel(surface_form: str) -> None:
        cancel_lemma_job(data_root, surface_form=surface_form)

    return AsyncLemmaFill(begin=begin, poll=poll, cancel=cancel)
