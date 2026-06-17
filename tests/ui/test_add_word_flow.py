"""Tests for lemma suggestion resolution in add-word flow."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from lexiflow_core.vocabulary.models import WordCategory
from lexiflow_ui.add_word_flow import resolve_lemma_suggestions
from lexiflow_ui.lemma_job_wait import LemmaJobPollState
from lexiflow_ui.lemma_suggestions import LemmaSuggestions


def test_resolve_lemma_suggestions_uses_llm_job_result(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    llm_result = {
        "lemma": "correr",
        "translation": "to run",
        "explanation": "Movement at speed.",
        "category": "verb",
    }

    with (
        patch(
            "lexiflow_ui.add_word_flow.wait_for_lemma_result",
            return_value=llm_result,
        ),
        patch("lexiflow_ui.add_word_flow.enqueue_lemma_job"),
    ):
        suggestions = resolve_lemma_suggestions(
            data_root,
            language_code="es",
            surface_form="corriendo",
            native_language="en",
            supervisor=None,
        )

    assert suggestions == LemmaSuggestions(
        lemma="correr",
        translation="to run",
        explanation="Movement at speed.",
        word_category=WordCategory.VERB,
    )


def test_resolve_lemma_suggestions_returns_empty_when_job_missing(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "LexiFlow"

    with (
        patch(
            "lexiflow_ui.add_word_flow.wait_for_lemma_result",
            return_value=None,
        ),
        patch("lexiflow_ui.add_word_flow.enqueue_lemma_job"),
    ):
        suggestions = resolve_lemma_suggestions(
            data_root,
            language_code="es",
            surface_form="corriendo",
            native_language="en",
            supervisor=None,
        )

    assert suggestions == LemmaSuggestions(
        lemma="",
        translation="",
        explanation="",
        word_category=WordCategory.OTHER,
    )


def test_find_lemma_job_result_returns_pending_without_blocking(tmp_path: Path) -> None:
    from lexiflow_ui.lemma_job_wait import find_lemma_job_result

    data_root = tmp_path / "LexiFlow"
    assert (
        find_lemma_job_result(data_root, surface_form="corriendo")
        == LemmaJobPollState.PENDING.value
    )


def test_async_lemma_fill_poll_handles_completed_job_dict(tmp_path: Path) -> None:
    import json

    from lexiflow_core.jobs.lemma_queue import enqueue_lemma_job
    from lexiflow_core.jobs.runner import run_worker_loop
    from lexiflow_core.jobs.service import JobService
    from lexiflow_core.llm.fake import FakeLLM
    from lexiflow_ui.lemma_suggestions import make_async_lemma_fill

    data_root = tmp_path / "LexiFlow"
    job_service = JobService(data_root)
    enqueue_lemma_job(
        job_service,
        language_code="es",
        surface_form="corriendo",
        native_language="en",
    )
    run_worker_loop(
        job_service,
        FakeLLM(
            responses=[
                json.dumps(
                    {
                        "lemma": "correr",
                        "translation": "to run",
                        "explanation": "Movement at speed.",
                        "category": "verb",
                    }
                )
            ]
        ),
        data_root=data_root,
    )
    async_fill = make_async_lemma_fill(
        data_root,
        language_code="es",
        native_language="en",
        supervisor=None,
    )
    suggestions = async_fill.poll("corriendo")

    assert suggestions is not None
    assert suggestions.lemma == "correr"
    assert suggestions.translation == "to run"
