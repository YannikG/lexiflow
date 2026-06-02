"""Shared add-word dialog and lemma resolution for vocabulary."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from lexiflow_core.jobs.lemma_queue import enqueue_lemma_job
from lexiflow_core.jobs.service import JobService
from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.languages.store import LanguageStore, LanguageStoreError
from lexiflow_core.vocabulary.lemma_resolution import resolve_lemma_with_spacy
from lexiflow_core.vocabulary.models import VocabularyEntry
from PySide6.QtWidgets import QWidget

from lexiflow_ui.dialogs.add_word_dialog import (
    AddWordDialog,
    AddWordForm,
    EditWordDialog,
    EditWordForm,
)
from lexiflow_ui.lemma_job_wait import wait_for_lemma_result
from lexiflow_ui.worker_supervisor import WorkerSupervisor


@dataclass(frozen=True)
class LemmaSuggestions:
    lemma: str
    translation: str
    explanation: str


def default_level_for_language(data_root: Path, language_code: str) -> CEFRLevel:
    try:
        return LanguageStore(data_root).get_user_level(language_code)
    except LanguageStoreError:
        return CEFRLevel.A1


def resolve_lemma_suggestions(
    data_root: Path,
    *,
    language_code: str,
    surface_form: str,
    native_language: str,
    supervisor: WorkerSupervisor | None,
) -> LemmaSuggestions:
    """Resolve lemma fields via spaCy or a background lemma job."""
    spacy_result = resolve_lemma_with_spacy(data_root, language_code, surface_form)
    if spacy_result is not None:
        return LemmaSuggestions(
            lemma=spacy_result.lemma,
            translation=spacy_result.translation,
            explanation=spacy_result.explanation,
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
        return LemmaSuggestions(lemma="", translation="", explanation="")
    return LemmaSuggestions(
        lemma=str(completed.get("lemma", "")),
        translation=str(completed.get("translation", "")),
        explanation=str(completed.get("explanation", "")),
    )


def prompt_add_word(
    parent: QWidget,
    *,
    default_level: CEFRLevel,
    surface_form: str = "",
    lemma: str = "",
    translation: str = "",
    explanation: str = "",
) -> AddWordForm | None:
    """Show the add-word dialog and return the confirmed form."""
    dialog = AddWordDialog(
        default_level=default_level,
        surface_form=surface_form or None,
        lemma=lemma,
        translation=translation,
        explanation=explanation,
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
    """Resolve lemma suggestions when needed, then show the add-word dialog."""
    suggestions = resolve_lemma_suggestions(
        data_root,
        language_code=language_code,
        surface_form=surface_form,
        native_language=native_language,
        supervisor=supervisor,
    )
    return prompt_add_word(
        parent,
        default_level=default_level,
        surface_form=surface_form,
        lemma=suggestions.lemma,
        translation=suggestions.translation,
        explanation=suggestions.explanation,
    )
