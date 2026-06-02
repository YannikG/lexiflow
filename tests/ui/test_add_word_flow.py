"""Tests for lemma suggestion resolution in add-word flow."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from lexiflow_core.vocabulary.lemma_output import LemmaInferenceResult
from lexiflow_core.vocabulary.models import WordCategory
from lexiflow_ui.add_word_flow import resolve_lemma_suggestions
from lexiflow_ui.lemma_job_wait import LemmaJobPollState
from lexiflow_ui.lemma_suggestions import LemmaSuggestions


def test_resolve_lemma_suggestions_falls_through_when_spacy_has_no_translation(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "LexiFlow"
    spacy_result = LemmaInferenceResult(
        lemma="correr",
        translation="",
        explanation="",
        word_category=WordCategory.VERB,
    )
    llm_result = {
        "lemma": "correr",
        "translation": "to run",
        "explanation": "Movement at speed.",
        "category": "verb",
    }

    with (
        patch(
            "lexiflow_ui.add_word_flow.resolve_lemma_with_spacy",
            return_value=spacy_result,
        ),
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

    assert suggestions.translation == "to run"
    assert suggestions.explanation == "Movement at speed."
    assert suggestions.lemma == "correr"


def test_resolve_lemma_suggestions_uses_spacy_when_translation_available(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "LexiFlow"
    spacy_result = LemmaInferenceResult(
        lemma="correr",
        translation="to run",
        explanation="From spaCy.",
        word_category=WordCategory.VERB,
    )

    with (
        patch(
            "lexiflow_ui.add_word_flow.resolve_lemma_with_spacy",
            return_value=spacy_result,
        ),
        patch("lexiflow_ui.add_word_flow.enqueue_lemma_job") as enqueue,
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
        explanation="From spaCy.",
        word_category=WordCategory.VERB,
    )
    enqueue.assert_not_called()


def test_find_lemma_job_result_returns_pending_without_blocking(tmp_path: Path) -> None:
    from lexiflow_ui.lemma_job_wait import find_lemma_job_result

    data_root = tmp_path / "LexiFlow"
    assert (
        find_lemma_job_result(data_root, surface_form="corriendo")
        == LemmaJobPollState.PENDING.value
    )
