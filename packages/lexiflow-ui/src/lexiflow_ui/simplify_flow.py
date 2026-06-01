"""UI orchestration for simplify jobs."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from lexiflow_core.jobs.service import JobService
from lexiflow_core.jobs.simplify_queue import enqueue_simplify
from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.languages.store import LanguageStore, LanguageStoreError
from PySide6.QtWidgets import QMessageBox, QWidget

from lexiflow_ui.worker_supervisor import WorkerSupervisor


def default_simplify_level(data_root: Path, target_language: str) -> CEFRLevel:
    """Return user language level or A2 when metadata is missing."""
    try:
        return LanguageStore(data_root).get_user_level(target_language)
    except LanguageStoreError:
        return CEFRLevel.A2


def submit_simplify(
    *,
    data_root: Path,
    supervisor: WorkerSupervisor,
    text_id: UUID,
    level: CEFRLevel,
) -> None:
    """Enqueue a simplify job and ensure the worker is running."""
    enqueue_simplify(JobService(data_root), text_id, level.value)
    supervisor.ensure_running()


def confirm_simplify_without_translated(parent: QWidget | None) -> None:
    """Inform the user that translated text is required before simplify."""
    QMessageBox.information(
        parent,
        "Simplify",
        "Wait for plain translation to finish before simplifying.",
    )
