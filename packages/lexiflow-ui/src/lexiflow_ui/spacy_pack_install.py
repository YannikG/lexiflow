"""Modal spaCy language-pack install for dialog-initiated setup."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from lexiflow_core.languages.catalog import get_language
from lexiflow_core.languages.spacy_pack import SpacyPackModel, install_spacy_pack
from lexiflow_core.vocabulary.lemma_resolution import spacy_pack_available
from PySide6.QtWidgets import QMessageBox, QWidget

from lexiflow_ui.background_task import run_with_progress_dialog


def _language_pack_label(iso: str) -> str:
    try:
        return get_language(iso).name
    except KeyError:
        return iso


def install_spacy_pack_with_progress(
    parent: QWidget,
    *,
    data_root: Path,
    iso: str,
    ensure_model: Callable[[str], None] | None = None,
    load_model: Callable[[str], SpacyPackModel] | None = None,
) -> bool:
    """Install a spaCy pack with a window-modal progress dialog. Returns success."""
    if spacy_pack_available(data_root, iso):
        return True

    language_name = _language_pack_label(iso)
    header = f"Downloading language pack for {language_name}"

    def install_work(
        on_progress: Callable[[float], None],
        on_status: Callable[[str], None],
    ) -> None:
        def on_log_line(line: str) -> None:
            on_status(f"{header}\n{line}")

        install_spacy_pack(
            data_root,
            iso,
            ensure_model=ensure_model,
            load_model=load_model,
            on_status=on_log_line,
            on_progress=on_progress,
        )

    ok, error = run_with_progress_dialog(
        parent,
        title="Downloading language pack",
        initial_status=f"{header}…",
        work=install_work,
    )
    if ok:
        return True
    QMessageBox.critical(
        parent,
        "Language pack download failed",
        error or "Language pack download failed.",
    )
    return False
