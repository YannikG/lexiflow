"""Reader orchestration helpers."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from lexiflow_core.jobs.service import JobService
from lexiflow_core.jobs.text_job_status import (
    cleanup_job_message,
    missing_variant_message,
    simplified_variant_job_message,
)
from lexiflow_core.library.document_title import (
    DocumentTitleError,
    parse_document_title,
)
from lexiflow_core.library.index import LibraryIndex
from lexiflow_core.library.markdown_display import markdown_for_display
from lexiflow_core.library.models import TextRecord
from lexiflow_core.library.reader_tabs import (
    NATIVE_TAB,
    SIMPLIFIED_PREFIX,
    discover_simplified_variants,
    resolve_open_tab,
)
from lexiflow_core.library.text_repository import TextRepository


def list_texts_for_sidebar(
    data_root: Path, target_language: str | None
) -> list[TextRecord]:
    """Return indexed texts for sidebar display (read-only)."""
    if target_language is None:
        return []
    index = LibraryIndex(data_root)
    return index.list_by_lang(target_language)


def resolve_initial_tab(index: LibraryIndex, record: TextRecord) -> str:
    """Return the reader tab id to show when opening a text."""
    folder = Path(record.folder)
    simplified = discover_simplified_variants(folder)
    available = tuple(record.variants) + simplified
    unique_available = tuple(dict.fromkeys(available))
    return resolve_open_tab(
        index.get_last_viewed_tab(record.id),
        available_variants=unique_available,
        simplified_variants=simplified,
    )


def load_variant_markdown(
    repo: TextRepository,
    record: TextRecord,
    tab_id: str,
) -> tuple[str | None, str | None]:
    """Return raw markdown and document title for a tab, or None if missing."""
    try:
        markdown = repo.read_variant(record.id, tab_id)
    except FileNotFoundError:
        return None, None
    try:
        title = parse_document_title(markdown)
    except DocumentTitleError:
        title = record.title
    return markdown, title


def markdown_for_reader_pane(
    markdown: str,
    *,
    document_title: str | None,
) -> str:
    """Prepare markdown for Qt reader rendering."""
    return markdown_for_display(markdown, document_title=document_title)


def native_tab_status_message(data_root: Path, text_id: UUID) -> str | None:
    """Return a cleanup status overlay for the native tab, if applicable."""
    jobs = JobService(data_root).list_jobs()
    return cleanup_job_message(jobs, text_id=text_id)


def variant_reader_state(
    repo: TextRepository,
    record: TextRecord,
    tab_id: str,
    *,
    data_root: Path | None,
) -> tuple[str | None, str | None, bool]:
    """Return markdown, status overlay message, and whether edit is allowed."""
    markdown, _title = load_variant_markdown(repo, record, tab_id)
    if markdown is None:
        message = "This variant is not available yet."
        if data_root is not None:
            jobs = JobService(data_root).list_jobs()
            message = missing_variant_message(
                jobs,
                text_id=record.id,
                variant_name=tab_id,
            )
        return None, message, False
    if tab_id == NATIVE_TAB and data_root is not None:
        overlay = native_tab_status_message(data_root, record.id)
        if overlay is not None:
            return None, overlay, False
    if tab_id.startswith(SIMPLIFIED_PREFIX) and data_root is not None:
        jobs = JobService(data_root).list_jobs()
        overlay = simplified_variant_job_message(
            jobs,
            text_id=record.id,
            variant_name=tab_id,
        )
        if overlay is not None:
            return None, overlay, False
    return markdown, None, True


def persist_last_viewed_tab(index: LibraryIndex, text_id: UUID, tab_id: str) -> None:
    """Store the active reader tab for a text."""
    index.set_last_viewed_tab(text_id, tab_id)
