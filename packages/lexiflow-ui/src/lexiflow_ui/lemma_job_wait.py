"""Wait for a completed lemma inference job."""

from __future__ import annotations

import time
from enum import StrEnum
from pathlib import Path
from typing import Literal

from lexiflow_core.jobs.models import JobStatus, JobType
from lexiflow_core.jobs.service import JobService
from PySide6.QtCore import QElapsedTimer
from PySide6.QtWidgets import QApplication

LemmaJobPoll = dict[str, object] | Literal["pending", "failed", "cancelled"]


class LemmaJobPollState(StrEnum):
    PENDING = "pending"
    FAILED = "failed"
    CANCELLED = "cancelled"


def find_lemma_job_result(
    data_root: Path,
    *,
    surface_form: str,
) -> LemmaJobPoll:
    """Return lemma job result, pending, or failed without blocking."""
    normalized = surface_form.strip()
    for job in JobService(data_root).list_jobs():
        if job.job_type != JobType.LEMMA:
            continue
        if job.payload.get("surface_form") != normalized:
            continue
        if job.status == JobStatus.COMPLETED and job.result is not None:
            return job.result
        if job.status == JobStatus.FAILED:
            return LemmaJobPollState.FAILED.value
        if job.status == JobStatus.CANCELLED:
            return LemmaJobPollState.CANCELLED.value
        return LemmaJobPollState.PENDING.value
    return LemmaJobPollState.PENDING.value


def wait_for_lemma_result(
    data_root: Path,
    *,
    surface_form: str,
    timeout_ms: int = 120_000,
) -> dict[str, object] | None:
    """Poll the job queue until a lemma job for the surface form completes."""
    app = QApplication.instance()
    timer = QElapsedTimer()
    timer.start()
    while timer.elapsed() < timeout_ms:
        polled = find_lemma_job_result(data_root, surface_form=surface_form)
        if isinstance(polled, dict):
            return polled
        if polled == LemmaJobPollState.FAILED.value:
            return None
        if app is not None:
            app.processEvents()
        time.sleep(0.1)
    return None
