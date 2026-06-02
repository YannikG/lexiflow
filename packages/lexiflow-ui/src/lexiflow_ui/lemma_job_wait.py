"""Wait for a completed lemma inference job."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.jobs.models import JobStatus, JobType
from lexiflow_core.jobs.service import JobService
from PySide6.QtCore import QElapsedTimer
from PySide6.QtWidgets import QApplication


def wait_for_lemma_result(
    data_root: Path,
    *,
    surface_form: str,
    timeout_ms: int = 5000,
) -> dict[str, object] | None:
    """Poll the job queue until a lemma job for the surface form completes."""
    app = QApplication.instance()
    job_service = JobService(data_root)
    timer = QElapsedTimer()
    timer.start()
    normalized = surface_form.strip()
    while timer.elapsed() < timeout_ms:
        for job in job_service.list_jobs():
            if job.job_type != JobType.LEMMA:
                continue
            if job.payload.get("surface_form") != normalized:
                continue
            if job.status == JobStatus.COMPLETED and job.result is not None:
                return job.result
            if job.status == JobStatus.FAILED:
                return None
        if app is not None:
            app.processEvents()
    return None
