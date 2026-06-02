"""Reader highlight-add flow for vocabulary."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.jobs.embed_queue import enqueue_vocabulary_word_embed
from lexiflow_core.jobs.service import JobService
from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.library.models import TextRecord
from lexiflow_core.library.reader_tabs import (
    SIMPLIFIED_PREFIX,
    TRANSLATED_TAB,
    level_from_simplified_variant,
)
from lexiflow_core.vocabulary.store import VocabularyStore, VocabularyStoreError
from PySide6.QtWidgets import QMessageBox, QWidget

from lexiflow_ui.add_word_flow import (
    default_level_for_language,
    prompt_add_word_with_lemma_resolution,
)
from lexiflow_ui.dialogs.add_word_dialog import AddWordForm
from lexiflow_ui.worker_supervisor import WorkerSupervisor


def can_add_word_from_tab(tab_id: str) -> bool:
    return tab_id == TRANSLATED_TAB or tab_id.startswith(SIMPLIFIED_PREFIX)


def default_level_when_learned(
    data_root: Path,
    *,
    record: TextRecord,
    tab_id: str,
) -> CEFRLevel:
    tab_level = level_from_simplified_variant(tab_id)
    if tab_level is not None:
        return tab_level
    return default_level_for_language(data_root, record.target_language)


def open_highlight_add_dialog(
    parent: QWidget,
    *,
    data_root: Path,
    record: TextRecord,
    tab_id: str,
    surface_form: str,
    native_language: str,
    supervisor: WorkerSupervisor | None,
) -> bool:
    """Open add-word dialog for a reader selection."""
    if not surface_form.strip():
        QMessageBox.information(
            parent,
            "Add word",
            "Select a word in the reader first.",
        )
        return False
    default_level = default_level_when_learned(
        data_root,
        record=record,
        tab_id=tab_id,
    )
    form = prompt_add_word_with_lemma_resolution(
        parent,
        data_root=data_root,
        language_code=record.target_language,
        native_language=native_language,
        default_level=default_level,
        surface_form=surface_form,
        supervisor=supervisor,
    )
    if form is None:
        return False
    return persist_reader_add(
        parent,
        data_root=data_root,
        record=record,
        tab_id=tab_id,
        form=form,
        supervisor=supervisor,
    )


def persist_reader_add(
    parent: QWidget,
    *,
    data_root: Path,
    record: TextRecord,
    tab_id: str,
    form: AddWordForm,
    supervisor: WorkerSupervisor | None,
) -> bool:
    store = VocabularyStore(data_root, record.target_language)
    try:
        store.add_entry(
            lemma=form.lemma,
            translation=form.translation,
            explanation=form.explanation,
            level_when_learned=form.level_when_learned,
            surface_form=form.surface_form,
        )
    except VocabularyStoreError as error:
        QMessageBox.warning(parent, "Add word", str(error))
        return False
    job_service = JobService(data_root)
    enqueue_vocabulary_word_embed(
        job_service,
        language_code=record.target_language,
        lemma=form.lemma,
    )
    if supervisor is not None:
        supervisor.ensure_running()
    return True
