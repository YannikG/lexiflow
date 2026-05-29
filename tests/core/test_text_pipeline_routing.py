"""Tests for add-text language routing."""

from __future__ import annotations

from lexiflow_core.jobs.handlers.cleanup import SOURCE_ROUTE_NATIVE
from lexiflow_core.jobs.models import JobType
from lexiflow_core.jobs.service import JobService
from lexiflow_core.library.library_coordinator import LibraryCoordinator
from lexiflow_core.text_pipeline import InputTab, TextDraft, TextPipeline
from lexiflow_core.text_pipeline.language_detect import FakeLanguageDetector


def test_target_tab_with_detected_native_routes_as_native_source(tmp_path) -> None:
    data_root = tmp_path / "LexiFlow"
    coordinator, index = LibraryCoordinator.open(data_root)
    del coordinator
    jobs = JobService(data_root)
    pipeline = TextPipeline(
        data_root,
        index=index,
        job_service=jobs,
        language_detector=FakeLanguageDetector(detected="en"),
    )
    pipeline.submit_new_text(
        TextDraft(
            group="News",
            pasted_content="English paste",
            input_tab=InputTab.TARGET,
            native_language="en",
            target_language="es",
        )
    )
    job = jobs.list_jobs()[0]
    assert job.job_type == JobType.CLEANUP
    assert job.payload["source_route"] == SOURCE_ROUTE_NATIVE
