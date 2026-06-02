"""Shared add-word dialog and lemma resolution for vocabulary."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.jobs.lemma_queue import enqueue_lemma_job
from lexiflow_core.jobs.service import JobService
from lexiflow_core.languages.defaults import DEFAULT_LEVEL_WHEN_LEARNED
from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.vocabulary.lemma_form import parse_word_category
from lexiflow_core.vocabulary.lemma_resolution import resolve_lemma_with_spacy
from lexiflow_core.vocabulary.models import VocabularyEntry, WordCategory
from PySide6.QtWidgets import QWidget

from lexiflow_ui.dialogs.add_word_dialog import (
    AddWordDialog,
    AddWordForm,
    EditWordDialog,
    EditWordForm,
)
from lexiflow_ui.lemma_job_wait import wait_for_lemma_result
from lexiflow_ui.lemma_suggestions import (
    AsyncLemmaFill,
    LemmaSuggestions,
    make_async_lemma_fill,
)
from lexiflow_ui.worker_supervisor import WorkerSupervisor


def default_level_for_language(data_root: Path, language_code: str) -> CEFRLevel:
    del data_root, language_code
    return DEFAULT_LEVEL_WHEN_LEARNED


def resolve_lemma_suggestions(
    data_root: Path,
    *,
    language_code: str,
    surface_form: str,
    native_language: str,
    supervisor: WorkerSupervisor | None,
    via_llm_only: bool = False,
) -> LemmaSuggestions:
    """Resolve lemma fields via spaCy or a background lemma job."""
    spacy_result = None
    if not via_llm_only:
        spacy_result = resolve_lemma_with_spacy(data_root, language_code, surface_form)
        if spacy_result is not None and spacy_result.lemma.strip():
            if spacy_result.translation.strip():
                return LemmaSuggestions(
                    lemma=spacy_result.lemma,
                    translation=spacy_result.translation,
                    explanation=spacy_result.explanation,
                    word_category=spacy_result.word_category,
                )
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
    completed = wait_for_lemma_result(data_root, surface_form=surface_form)
    if completed is None:
        return LemmaSuggestions(
            lemma=spacy_result.lemma if spacy_result is not None else "",
            translation="",
            explanation=spacy_result.explanation if spacy_result is not None else "",
            word_category=(
                spacy_result.word_category
                if spacy_result is not None
                else WordCategory.OTHER
            ),
        )
    llm_lemma = str(completed.get("lemma", "")).strip()
    llm_category = parse_word_category(completed.get("category"))
    word_category = llm_category
    if completed.get("category") is None and spacy_result is not None:
        word_category = spacy_result.word_category
    return LemmaSuggestions(
        lemma=llm_lemma or (spacy_result.lemma if spacy_result is not None else ""),
        translation=str(completed.get("translation", "")),
        explanation=str(completed.get("explanation", "")),
        word_category=word_category,
    )


def prompt_add_word(
    parent: QWidget,
    *,
    default_level: CEFRLevel,
    lemma: str = "",
    translation: str = "",
    explanation: str = "",
    word_category: WordCategory = WordCategory.OTHER,
    async_lemma_fill: AsyncLemmaFill | None = None,
    auto_fill_on_open: bool = False,
) -> AddWordForm | None:
    """Show the add-word dialog and return the confirmed form."""
    dialog = AddWordDialog(
        default_level=default_level,
        default_category=word_category,
        lemma=lemma,
        translation=translation,
        explanation=explanation,
        async_lemma_fill=async_lemma_fill,
        auto_fill_on_open=auto_fill_on_open,
        parent=parent,
    )
    return dialog.form()


def prompt_edit_word(
    parent: QWidget,
    *,
    entry: VocabularyEntry,
) -> EditWordForm | None:
    """Show the edit-word dialog and return the confirmed form."""
    dialog = EditWordDialog(entry=entry, parent=parent)
    return dialog.form()


def prompt_add_word_with_lemma_resolution(
    parent: QWidget,
    *,
    data_root: Path,
    language_code: str,
    native_language: str,
    default_level: CEFRLevel,
    surface_form: str,
    supervisor: WorkerSupervisor | None,
) -> AddWordForm | None:
    """Open the add-word dialog and auto-fill from the reader selection via LLM."""
    async_lemma_fill = make_async_lemma_fill(
        data_root,
        language_code=language_code,
        native_language=native_language,
        supervisor=supervisor,
    )
    return prompt_add_word(
        parent,
        default_level=default_level,
        lemma=surface_form.strip(),
        async_lemma_fill=async_lemma_fill,
        auto_fill_on_open=True,
    )
