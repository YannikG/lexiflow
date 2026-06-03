"""Tests for removing simplified variants."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.config.paths import variant_path
from lexiflow_core.jobs.models import JobRequest, JobStatus, JobType
from lexiflow_core.jobs.service import JobService
from lexiflow_core.jobs.simplify_queue import cancel_simplify_jobs
from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.library.index import LibraryIndex
from lexiflow_core.library.library_coordinator import LibraryCoordinator
from lexiflow_core.library.models import CreateTextRequest, TextRecord
from lexiflow_core.library.reader_tabs import simplified_variant_name
from lexiflow_core.library.text_repository import TextRepository
from lexiflow_core.simplify.suggestions_store import suggestions_path


def _seed_text_with_translated(data_root: Path) -> tuple[TextRepository, TextRecord]:
    coordinator, index = LibraryCoordinator.open(data_root)
    repo = TextRepository(data_root, index)
    record = repo.create_text(
        CreateTextRequest(
            title="Article",
            group="News",
            target_language="es",
            native_language="en",
            body="hola",
        )
    )
    repo.apply_translated_variant(record.id, "# Traducción\n\nCuerpo.")
    return repo, repo.get_text(record.id)


def test_remove_simplified_variant_deletes_files_and_metadata(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "LexiFlow"
    repo, record = _seed_text_with_translated(data_root)
    variant = simplified_variant_name(CEFRLevel.A2)
    repo.apply_simplified_variant(
        record.id,
        level="a2",
        markdown="# Simple\n\nBody.",
    )
    folder = Path(record.folder)
    sidecar = suggestions_path(folder, variant)
    sidecar.write_text("[]", encoding="utf-8")

    updated = repo.remove_simplified_variant(record.id, variant)

    assert variant not in updated.variants
    assert not variant_path(folder, variant).exists()
    assert not sidecar.exists()


def test_remove_simplified_variant_clears_last_viewed_tab(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    repo, record = _seed_text_with_translated(data_root)
    variant = simplified_variant_name(CEFRLevel.B1)
    repo.apply_simplified_variant(
        record.id,
        level="b1",
        markdown="# B1\n\nBody.",
    )
    index = LibraryIndex(data_root)
    index.set_last_viewed_tab(record.id, variant)

    repo.remove_simplified_variant(record.id, variant)

    assert index.get_last_viewed_tab(record.id) == "translated"


def test_cancel_simplify_jobs_cancels_matching_pending(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    _, record = _seed_text_with_translated(data_root)
    job_service = JobService(data_root)
    job_service.enqueue(
        JobRequest(
            job_type=JobType.SIMPLIFY,
            payload={"text_id": str(record.id), "level": "A2"},
        )
    )

    cancelled = cancel_simplify_jobs(job_service, record.id, "a2")

    assert cancelled == 1
    job = job_service.list_jobs()[0]
    assert job.status == JobStatus.CANCELLED
