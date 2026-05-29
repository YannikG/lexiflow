"""Tests for target language setup orchestration."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.jobs.models import JobType
from lexiflow_core.jobs.service import JobService
from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.languages.setup import add_target_with_spacy_download


def test_add_target_with_spacy_download_enqueues_job(tmp_path: Path) -> None:
    data_root = tmp_path / "library"

    add_target_with_spacy_download(data_root, "es", CEFRLevel.A2)

    jobs = JobService(data_root).list_jobs()
    assert len(jobs) == 1
    assert jobs[0].job_type == JobType.DOWNLOAD_SPACY
    assert jobs[0].payload == {"iso": "es"}
