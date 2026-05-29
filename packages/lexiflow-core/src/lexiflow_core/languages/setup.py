"""Orchestrate target-language setup commands."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.jobs.models import JobRequest, JobType
from lexiflow_core.jobs.service import JobService
from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.languages.store import LanguageStore


def add_target_with_spacy_download(data_root: Path, iso: str, level: CEFRLevel) -> None:
    """Add a target language and enqueue its spaCy pack download."""
    LanguageStore(data_root).add_target(iso, level)
    JobService(data_root).enqueue(
        JobRequest(
            job_type=JobType.DOWNLOAD_SPACY,
            payload={"iso": iso},
        )
    )
