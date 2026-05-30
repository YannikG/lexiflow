"""UI orchestration for submitting add-text drafts."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from lexiflow_core.config.settings import Settings
from lexiflow_core.library.index import LibraryIndex
from lexiflow_core.text_pipeline import (
    DuplicateWarning,
    LargePasteRequiresConfirmation,
    TextDraft,
    TextPipeline,
)
from lexiflow_core.text_pipeline.language_detect import LangdetectLanguageDetector
from PySide6.QtWidgets import QMessageBox, QWidget

from lexiflow_ui.dialogs.add_text_dialog import AddTextFormData
from lexiflow_ui.worker_supervisor import WorkerSupervisor


def submit_add_text(
    *,
    data_root: Path,
    settings: Settings,
    supervisor: WorkerSupervisor,
    form: AddTextFormData,
    parent: QWidget | None,
    ignore_duplicate: bool = False,
    confirmed_large_paste: bool = False,
) -> UUID | None:
    """Submit add-text form data through the pipeline and spawn the worker."""
    native = settings.native_language
    target = settings.active_target_language
    if native is None or target is None:
        QMessageBox.warning(parent, "Add text", "Complete language setup first.")
        return None

    pipeline = TextPipeline(data_root, language_detector=LangdetectLanguageDetector())
    draft = TextDraft(
        group=form.group,
        pasted_content=form.pasted_content,
        input_tab=form.input_tab,
        native_language=native,
        target_language=target,
        source_url=form.source_url,
        ignore_duplicate=ignore_duplicate,
        confirmed_large_paste=confirmed_large_paste,
    )
    try:
        text_id = pipeline.submit_new_text(draft)
    except DuplicateWarning:
        answer = QMessageBox.question(
            parent,
            "Duplicate text",
            "A text with this source URL or content already exists. Save anyway?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return None
        return submit_add_text(
            data_root=data_root,
            settings=settings,
            supervisor=supervisor,
            form=form,
            parent=parent,
            ignore_duplicate=True,
            confirmed_large_paste=confirmed_large_paste,
        )
    except LargePasteRequiresConfirmation:
        answer = QMessageBox.question(
            parent,
            "Large paste",
            "This paste is very large. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return None
        return submit_add_text(
            data_root=data_root,
            settings=settings,
            supervisor=supervisor,
            form=form,
            parent=parent,
            ignore_duplicate=ignore_duplicate,
            confirmed_large_paste=True,
        )

    supervisor.ensure_running()
    return text_id


def list_texts_for_sidebar(data_root: Path, target_language: str | None) -> list[str]:
    """Return target-language titles for sidebar display (read-only)."""
    if target_language is None:
        return []
    index = LibraryIndex(data_root)
    return [record.title for record in index.list_by_lang(target_language)]
