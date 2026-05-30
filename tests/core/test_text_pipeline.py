"""Tests for add-text TextPipeline validation and enqueue."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

import pytest
from lexiflow_core.jobs.models import JobType
from lexiflow_core.jobs.service import JobService
from lexiflow_core.library.library_coordinator import LibraryCoordinator
from lexiflow_core.library.models import CreateTextRequest
from lexiflow_core.library.text_repository import TextRepository
from lexiflow_core.text_pipeline import (
    DuplicateWarning,
    InputTab,
    LargePasteRequiresConfirmation,
    TextDraft,
    TextPipeline,
)


@pytest.fixture
def pipeline(tmp_path: Path) -> tuple[TextPipeline, TextRepository, JobService]:
    data_root = tmp_path / "LexiFlow"
    coordinator, index = LibraryCoordinator.open(data_root)
    del coordinator
    repo = TextRepository(data_root, index)
    jobs = JobService(data_root)
    pipeline = TextPipeline(
        data_root, index=index, job_service=jobs, text_repository=repo
    )
    return pipeline, repo, jobs


def test_duplicate_source_url_warns(
    pipeline: tuple[TextPipeline, TextRepository, JobService],
) -> None:
    text_pipeline, repo, _jobs = pipeline
    existing = repo.create_text(
        CreateTextRequest(
            title="Existing",
            group="News",
            target_language="es",
            native_language="en",
            body="x",
            source_url="https://example.com/article",
        )
    )
    draft = TextDraft(
        title="Existing",
        group="News",
        pasted_content="new paste",
        input_tab=InputTab.NATIVE,
        native_language="en",
        target_language="es",
        source_url="https://example.com/article",
    )
    with pytest.raises(DuplicateWarning) as exc_info:
        text_pipeline.submit_new_text(draft)
    assert exc_info.value.existing_id == existing.id


def test_large_paste_requires_confirmation(
    pipeline: tuple[TextPipeline, TextRepository, JobService],
) -> None:
    text_pipeline, _repo, _jobs = pipeline
    draft = TextDraft(
        title="Large paste",
        group="News",
        pasted_content="x" * 60_000,
        input_tab=InputTab.NATIVE,
        native_language="en",
        target_language="es",
    )
    with pytest.raises(LargePasteRequiresConfirmation):
        text_pipeline.submit_new_text(draft)


def test_same_content_without_source_url_does_not_warn(
    pipeline: tuple[TextPipeline, TextRepository, JobService],
) -> None:
    text_pipeline, repo, _jobs = pipeline
    body = "Same article body without URL."
    repo.create_text(
        CreateTextRequest(
            title="First",
            group="News",
            target_language="es",
            native_language="en",
            body=body,
        )
    )
    draft = TextDraft(
        title="Second",
        group="Podcasts",
        pasted_content=body,
        input_tab=InputTab.NATIVE,
        native_language="en",
        target_language="es",
        source_url=None,
    )

    text_id = text_pipeline.submit_new_text(draft)

    assert text_id is not None


def test_submit_enqueues_cleanup_job(
    pipeline: tuple[TextPipeline, TextRepository, JobService],
) -> None:
    text_pipeline, repo, jobs = pipeline
    text_id = text_pipeline.submit_new_text(
        TextDraft(
            title="My article",
            group="News",
            pasted_content="hello world",
            input_tab=InputTab.NATIVE,
            native_language="en",
            target_language="es",
        )
    )
    assert isinstance(text_id, UUID)
    assert repo.get_text(text_id).title == "My article"
    queued = jobs.list_jobs()
    assert len(queued) == 1
    assert queued[0].job_type == JobType.CLEANUP
    assert queued[0].payload["text_id"] == str(text_id)
