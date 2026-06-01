"""Tests for simplify job handler."""

from __future__ import annotations

import json
import time
from pathlib import Path
from uuid import UUID

import pytest
from lexiflow_core.config.paths import variant_path
from lexiflow_core.jobs.handlers.simplify import handle_simplify
from lexiflow_core.jobs.models import JobRequest, JobStatus, JobType
from lexiflow_core.jobs.service import JobService
from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.library.index import LibraryIndex
from lexiflow_core.library.library_coordinator import LibraryCoordinator
from lexiflow_core.library.models import CreateTextRequest
from lexiflow_core.library.text_repository import TextRepository
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
def simplify_context(
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
    job_service = JobService(data_root)
    return job_service, repo, index, record.id, data_root


def test_simplify_invalid_json_fails_job_no_file(
    simplify_context: tuple[JobService, TextRepository, LibraryIndex, UUID, Path],
) -> None:
    job_service, repo, _index, text_id, _data_root = simplify_context
    record = repo.get_text(text_id)
    folder = Path(record.folder)
    llm = FakeLLM(response="not json")

    job_service.enqueue(
        JobRequest(
            job_type=JobType.SIMPLIFY,
            payload={"text_id": str(text_id), "level": "A2"},
        )
    )
    job = job_service.claim_next()
    assert job is not None
    handle_simplify(
        job,
        data_root=_data_root,
        llm=llm,
        repo=repo,
        job_service=job_service,
    )

    assert not variant_path(folder, "simplified-a2").exists()
    jobs = job_service.list_jobs()
    assert jobs[0].status == JobStatus.FAILED


def test_simplify_writes_simplified_variant_with_title(
    simplify_context: tuple[JobService, TextRepository, LibraryIndex, UUID, Path],
) -> None:
    job_service, repo, _index, text_id, data_root = simplify_context
    record = repo.get_text(text_id)
    folder = Path(record.folder)
    llm = FakeLLM(response=_valid_simplify_json())

    job_service.enqueue(
        JobRequest(
            job_type=JobType.SIMPLIFY,
            payload={"text_id": str(text_id), "level": "A2"},
        )
    )
    job = job_service.claim_next()
    assert job is not None
    handle_simplify(
        job,
        data_root=data_root,
        llm=llm,
        repo=repo,
        job_service=job_service,
    )

    simplified = variant_path(folder, "simplified-a2").read_text(encoding="utf-8")
    assert simplified.startswith("# Titulo simple")
    jobs = job_service.list_jobs()
    assert jobs[0].status == JobStatus.COMPLETED


def test_simplify_multiple_levels_coexist(
    simplify_context: tuple[JobService, TextRepository, LibraryIndex, UUID, Path],
) -> None:
    job_service, repo, index, text_id, data_root = simplify_context
    record = repo.get_text(text_id)
    folder = Path(record.folder)
    llm = FakeLLM(
        responses=[
            _valid_simplify_json(title="Simple A2", body="A2 body."),
            _valid_simplify_json(title="Simple B1", body="B1 body."),
        ]
    )

    for level in (CEFRLevel.A2, CEFRLevel.B1):
        job_service.enqueue(
            JobRequest(
                job_type=JobType.SIMPLIFY,
                payload={"text_id": str(text_id), "level": level.value},
            )
        )
        job = job_service.claim_next()
        assert job is not None
        handle_simplify(
            job, data_root=data_root, llm=llm, repo=repo, job_service=job_service
        )

    assert variant_path(folder, "simplified-a2").is_file()
    assert variant_path(folder, "simplified-b1").is_file()
    indexed = index.get_by_id(text_id)
    assert indexed is not None
    assert "simplified-a2" in indexed.variants
    assert "simplified-b1" in indexed.variants


def test_resimplify_replaces_only_active_level_file(
    simplify_context: tuple[JobService, TextRepository, LibraryIndex, UUID, Path],
) -> None:
    job_service, repo, _index, text_id, data_root = simplify_context
    record = repo.get_text(text_id)
    folder = Path(record.folder)
    llm = FakeLLM(
        responses=[
            _valid_simplify_json(title="Simple A2", body="First A2."),
            _valid_simplify_json(title="Simple B1", body="Only B1."),
            _valid_simplify_json(title="Simple A2 v2", body="Second A2."),
        ]
    )

    for level in (CEFRLevel.A2, CEFRLevel.B1):
        job_service.enqueue(
            JobRequest(
                job_type=JobType.SIMPLIFY,
                payload={"text_id": str(text_id), "level": level.value},
            )
        )
        job = job_service.claim_next()
        assert job is not None
        handle_simplify(
            job, data_root=data_root, llm=llm, repo=repo, job_service=job_service
        )

    a2_path = variant_path(folder, "simplified-a2")
    b1_path = variant_path(folder, "simplified-b1")
    b1_before = b1_path.read_text(encoding="utf-8")
    b1_mtime = b1_path.stat().st_mtime
    time.sleep(0.02)

    job_service.enqueue(
        JobRequest(
            job_type=JobType.SIMPLIFY,
            payload={"text_id": str(text_id), "level": "A2"},
        )
    )
    job = job_service.claim_next()
    assert job is not None
    handle_simplify(
        job,
        data_root=data_root,
        llm=llm,
        repo=repo,
        job_service=job_service,
    )

    assert "Second A2." in a2_path.read_text(encoding="utf-8")
    assert b1_path.read_text(encoding="utf-8") == b1_before
    assert b1_path.stat().st_mtime == b1_mtime


def test_simplify_writes_filtered_suggestions_sidecar(
    simplify_context: tuple[JobService, TextRepository, LibraryIndex, UUID, Path],
) -> None:
    from lexiflow_core.vocabulary.models import NewWordSuggestion
    from lexiflow_core.vocabulary.store import VocabularyStore

    job_service, repo, _index, text_id, data_root = simplify_context
    record = repo.get_text(text_id)
    folder = Path(record.folder)
    vocab = VocabularyStore(data_root, "es")
    vocab.add_from_suggestion(
        NewWordSuggestion(lemma="nuevo", gloss="new", suggested_level=CEFRLevel.A2)
    )
    llm = FakeLLM(response=_valid_simplify_json())

    job_service.enqueue(
        JobRequest(
            job_type=JobType.SIMPLIFY,
            payload={"text_id": str(text_id), "level": "A2"},
        )
    )
    job = job_service.claim_next()
    assert job is not None
    handle_simplify(
        job,
        data_root=data_root,
        llm=llm,
        repo=repo,
        job_service=job_service,
    )

    suggestions = load_suggestions(folder, "simplified-a2")
    assert suggestions == ()


def test_simplify_fails_without_translated_variant(
    simplify_context: tuple[JobService, TextRepository, LibraryIndex, UUID, Path],
) -> None:
    job_service, repo, _index, text_id, data_root = simplify_context
    record = repo.get_text(text_id)
    folder = Path(record.folder)
    variant_path(folder, "translated").unlink()
    llm = FakeLLM(response=_valid_simplify_json())

    job_service.enqueue(
        JobRequest(
            job_type=JobType.SIMPLIFY,
            payload={"text_id": str(text_id), "level": "A2"},
        )
    )
    job = job_service.claim_next()
    assert job is not None
    handle_simplify(
        job,
        data_root=data_root,
        llm=llm,
        repo=repo,
        job_service=job_service,
    )

    assert not variant_path(folder, "simplified-a2").exists()
    jobs = job_service.list_jobs()
    assert jobs[0].status == JobStatus.FAILED
    assert jobs[0].error_message is not None
    assert "translated" in jobs[0].error_message.lower()
