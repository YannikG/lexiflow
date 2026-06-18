"""Tests for add-text language routing."""

from __future__ import annotations

from lexiflow_core.jobs.handlers.cleanup import SOURCE_ROUTE_TARGET
from lexiflow_core.jobs.models import JobType
from lexiflow_core.jobs.service import JobService
from lexiflow_core.library.library_coordinator import LibraryCoordinator
from lexiflow_core.text_pipeline import InputTab, TextDraft, TextPipeline


def test_target_tab_routes_as_target_source(tmp_path) -> None:
    data_root = tmp_path / "LexiFlow"
    coordinator, index = LibraryCoordinator.open(data_root)
    del coordinator
    jobs = JobService(data_root)
    pipeline = TextPipeline(data_root, index=index, job_service=jobs)
    pipeline.submit_new_text(
        TextDraft(
            title="English article",
            group="News",
            pasted_content="English paste",
            input_tab=InputTab.TARGET,
            native_language="en",
            target_language="es",
        )
    )
    job = jobs.list_jobs()[0]
    assert job.job_type == JobType.CLEANUP
    assert job.payload["source_route"] == SOURCE_ROUTE_TARGET
