"""UI orchestration for simplify jobs."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from lexiflow_core.jobs.service import JobService
from lexiflow_core.jobs.simplify_queue import enqueue_simplify
from lexiflow_core.languages.defaults import DEFAULT_SIMPLIFY_LEVEL
from lexiflow_core.languages.models import CEFRLevel
from PySide6.QtWidgets import QMessageBox, QWidget


def default_simplify_level(data_root: Path, target_language: str) -> CEFRLevel:
    """Return the default simplify level for the level picker."""
    del data_root, target_language
    return DEFAULT_SIMPLIFY_LEVEL


def submit_simplify(
    *,
    data_root: Path,
    text_id: UUID,
    level: CEFRLevel,
) -> None:
    """Enqueue a simplify job."""
    enqueue_simplify(JobService(data_root), text_id, level.value)


def confirm_simplify_without_translated(parent: QWidget | None) -> None:
    """Inform the user that translated text is required before simplify."""
    QMessageBox.information(
        parent,
        "Simplify",
        "Wait for plain translation to finish before simplifying.",
    )
