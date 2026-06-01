"""Integration tests for enqueue → worker loop → simplify artifacts on disk."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

import pytest
from lexiflow_core.config.paths import variant_path
from lexiflow_core.jobs.models import JobStatus, JobType
from lexiflow_core.jobs.runner import run_worker_loop
from lexiflow_core.jobs.service import JobService
from lexiflow_core.jobs.simplify_queue import enqueue_simplify
from lexiflow_core.library.index import LibraryIndex
from lexiflow_core.library.library_coordinator import LibraryCoordinator
from lexiflow_core.library.models import CreateTextRequest
from lexiflow_core.library.text_repository import TextRepository
from lexiflow_core.llm.disabled import DisabledLLM
from lexiflow_core.llm.fake import FakeLLM
from lexiflow_core.simplify.suggestions_store import load_suggestions


def _valid_simplify_json(*, title: str = "Titulo simple", body: str = "Texto.") -> str:
    return json.dumps(
        {
            "title": title,
            "body": body,
            "new_words": [
                {"lemma": "nuevo", "gloss": "new", "level": "A2"},
            ],
        }
    )


@pytest.fixture
def simplify_pipeline(
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
    repo.apply_translated_variant(record.id, "# Traduccion\n\ncontenido largo")
    jobs = JobService(data_root)
    return jobs, repo, index, record.id, data_root


def test_worker_completes_enqueued_simplify_job(
    simplify_pipeline: tuple[JobService, TextRepository, LibraryIndex, UUID, Path],
) -> None:
    jobs, repo, index, text_id, data_root = simplify_pipeline
    record = repo.get_text(text_id)
    folder = Path(record.folder)
    llm = FakeLLM(response=_valid_simplify_json())

    enqueue_simplify(jobs, text_id, "A2")
    run_worker_loop(jobs, llm, data_root=data_root)

    simplified = variant_path(folder, "simplified-a2").read_text(encoding="utf-8")
    assert simplified.startswith("# Titulo simple")
    suggestions = load_suggestions(folder, "simplified-a2")
    assert len(suggestions) == 1
    assert suggestions[0].lemma == "nuevo"

    completed = [job for job in jobs.list_jobs() if job.job_type == JobType.SIMPLIFY]
    assert len(completed) == 1
    assert completed[0].status == JobStatus.COMPLETED

    indexed = index.get_by_id(text_id)
    assert indexed is not None
    assert "simplified-a2" in indexed.variants


def test_worker_fails_simplify_without_translated_variant(
    simplify_pipeline: tuple[JobService, TextRepository, LibraryIndex, UUID, Path],
) -> None:
    jobs, repo, _index, text_id, data_root = simplify_pipeline
    record = repo.get_text(text_id)
    folder = Path(record.folder)
    variant_path(folder, "translated").unlink()

    enqueue_simplify(jobs, text_id, "A2")
    run_worker_loop(jobs, FakeLLM(response=_valid_simplify_json()), data_root=data_root)

    assert not variant_path(folder, "simplified-a2").exists()
    job = jobs.list_jobs()[0]
    assert job.status == JobStatus.FAILED
    assert job.error_message is not None
    assert "translated" in job.error_message.lower()


def test_worker_fails_simplify_when_llm_disabled(
    simplify_pipeline: tuple[JobService, TextRepository, LibraryIndex, UUID, Path],
) -> None:
    jobs, repo, _index, text_id, data_root = simplify_pipeline
    record = repo.get_text(text_id)
    folder = Path(record.folder)

    enqueue_simplify(jobs, text_id, "A2")
    run_worker_loop(jobs, DisabledLLM(), data_root=data_root)

    assert not variant_path(folder, "simplified-a2").exists()
    job = jobs.list_jobs()[0]
    assert job.status == JobStatus.FAILED
    assert job.error_message is not None
    assert "disabled" in job.error_message.lower()


def test_worker_fails_simplify_on_invalid_llm_json(
    simplify_pipeline: tuple[JobService, TextRepository, LibraryIndex, UUID, Path],
) -> None:
    jobs, repo, _index, text_id, data_root = simplify_pipeline
    record = repo.get_text(text_id)
    folder = Path(record.folder)

    enqueue_simplify(jobs, text_id, "A2")
    run_worker_loop(jobs, FakeLLM(response="not json"), data_root=data_root)

    assert not variant_path(folder, "simplified-a2").exists()
    job = jobs.list_jobs()[0]
    assert job.status == JobStatus.FAILED
    assert job.error_message is not None
