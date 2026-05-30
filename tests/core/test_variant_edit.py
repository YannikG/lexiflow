"""Tests for user variant edits from the reader."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.config.paths import variant_path
from lexiflow_core.jobs.models import JobType
from lexiflow_core.jobs.service import JobService
from lexiflow_core.library.library_coordinator import LibraryCoordinator
from lexiflow_core.library.models import CreateTextRequest, TextRecord
from lexiflow_core.library.text_repository import TextRepository


def _create_text_with_translated(
    tmp_path: Path,
) -> tuple[Path, TextRepository, JobService, TextRecord]:
    data_root = tmp_path / "LexiFlow"
    coordinator, index = LibraryCoordinator.open(data_root)
    del coordinator
    repo = TextRepository(data_root, index)
    record = repo.create_text(
        CreateTextRequest(
            title="Untitled",
            group="News",
            target_language="es",
            native_language="en",
            body="hola",
        )
    )
    translated = "# Traducción\n\nCuerpo traducido."
    record = repo.apply_translated_variant(record.id, translated)
    jobs = JobService(data_root)
    return data_root, repo, jobs, record


def test_save_variant_edit_writes_translated_markdown(tmp_path: Path) -> None:
    data_root, repo, _, record = _create_text_with_translated(tmp_path)
    edited = "# Nueva traducción\n\nTexto editado."

    repo.save_variant_edit(record.id, "translated", edited)

    path = variant_path(Path(record.folder), "translated")
    assert path.read_text(encoding="utf-8") == edited


def test_save_variant_edit_does_not_enqueue_translate_job(tmp_path: Path) -> None:
    data_root, repo, jobs, record = _create_text_with_translated(tmp_path)
    before = jobs.list_jobs()
    translate_before = [job for job in before if job.job_type == JobType.TRANSLATE]

    repo.save_variant_edit(
        record.id,
        "translated",
        "# Nueva traducción\n\nTexto editado.",
    )

    after = jobs.list_jobs()
    translate_after = [job for job in after if job.job_type == JobType.TRANSLATE]
    assert len(translate_after) == len(translate_before)
