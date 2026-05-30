"""Tests for plain translation job handler."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

import pytest
from lexiflow_core.config.paths import meta_path, variant_path
from lexiflow_core.jobs.handlers.cleanup import TRANSLATE_PHASE_PLAIN
from lexiflow_core.jobs.handlers.translate import handle_translate
from lexiflow_core.jobs.models import JobRequest, JobStatus, JobType
from lexiflow_core.jobs.service import JobService
from lexiflow_core.library.index import LibraryIndex
from lexiflow_core.library.library_coordinator import LibraryCoordinator
from lexiflow_core.library.models import CreateTextRequest
from lexiflow_core.library.text_metadata import load_text_metadata
from lexiflow_core.library.text_repository import TextRepository
from lexiflow_core.llm.fake import FakeLLM


@pytest.fixture
def translate_context(
    tmp_path: Path,
) -> tuple[JobService, TextRepository, LibraryIndex, UUID, Path]:
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
            body="body",
        )
    )
    repo.write_native_variant(record.id, "# Native\n\ncontent")
    job_service = JobService(data_root)
    return job_service, repo, index, record.id, data_root


def test_translate_writes_translated_variant(
    translate_context: tuple[JobService, TextRepository, LibraryIndex, UUID, Path],
) -> None:
    job_service, repo, _index, text_id, _data_root = translate_context
    record = repo.get_text(text_id)
    folder = Path(record.folder)
    llm = FakeLLM(response="# Titulo\n\ncuerpo")

    job_service.enqueue(
        JobRequest(
            job_type=JobType.TRANSLATE,
            payload={"text_id": str(text_id), "phase": TRANSLATE_PHASE_PLAIN},
        )
    )
    job = job_service.claim_next()
    assert job is not None
    handle_translate(job, llm=llm, repo=repo, job_service=job_service)

    translated = variant_path(folder, "translated").read_text(encoding="utf-8")
    assert translated.startswith("# Titulo")
    jobs = job_service.list_jobs()
    assert jobs[0].status == JobStatus.COMPLETED


def test_translate_updates_metadata_title_and_index(
    translate_context: tuple[JobService, TextRepository, LibraryIndex, UUID, Path],
) -> None:
    job_service, repo, index, text_id, _data_root = translate_context
    llm = FakeLLM(response="# Titulo ES\n\ntexto")

    job_service.enqueue(
        JobRequest(
            job_type=JobType.TRANSLATE,
            payload={"text_id": str(text_id), "phase": TRANSLATE_PHASE_PLAIN},
        )
    )
    job = job_service.claim_next()
    assert job is not None
    handle_translate(job, llm=llm, repo=repo, job_service=job_service)

    record = repo.get_text(text_id)
    metadata = load_text_metadata(meta_path(Path(record.folder)))
    assert metadata.title == "Titulo ES"
    indexed = index.get_by_id(text_id)
    assert indexed is not None
    assert indexed.title == "Titulo ES"
    assert "translated" in indexed.variants
