"""Background job polling and worker lifecycle for the open text."""

from __future__ import annotations

from typing import TYPE_CHECKING

from lexiflow_core.jobs.job_errors import user_facing_job_error
from lexiflow_core.jobs.models import JobStatus, JobType
from lexiflow_core.jobs.service import JobService
from lexiflow_core.languages.models import CEFRLevel
from PySide6.QtCore import QTimer

from lexiflow_ui.ai_worker_startup import ensure_ai_workers_running
from lexiflow_ui.main_window._types import LLM_JOB_TYPES

if TYPE_CHECKING:
    from lexiflow_ui.main_window.window import MainWindow


class MainWindowJobsMixin:
    """Polls job queue and refreshes the reader when text jobs complete."""

    def _on_simplify_submitted(self: MainWindow) -> None:
        self._ensure_background_workers(JobService(self._data_root))
        self._schedule_reader_refresh()

    def _on_infrastructure_state_changed(self: MainWindow) -> None:
        self._ensure_background_workers(JobService(self._data_root))
        self._status_bar.refresh()
        if self._texts_stack.currentWidget() is self._reader:
            self._reader.refresh_infrastructure_status()

    def _schedule_reader_refresh(self: MainWindow) -> None:
        for delay_ms in (500, 1500, 3000, 6000, 12000):
            QTimer.singleShot(delay_ms, self._poll_background_jobs)

    def _uses_native_llm(self: MainWindow) -> bool:
        return not self._settings.ollama_url and self._llama_supervisor is not None

    def _ensure_background_workers(self: MainWindow, job_service: JobService) -> None:
        pending_llm = any(
            job.status == JobStatus.PENDING and job.job_type in LLM_JOB_TYPES
            for job in job_service.list_jobs()
        )
        pending_any = any(
            job.status == JobStatus.PENDING for job in job_service.list_jobs()
        )
        if not pending_any:
            return
        if pending_llm and self._uses_native_llm():
            ensure_ai_workers_running(self._supervisor, self._llama_supervisor)
            return
        self._supervisor.ensure_running()

    def _poll_background_jobs(self: MainWindow) -> None:
        job_service = JobService(self._data_root)
        self._ensure_background_workers(job_service)
        self._supervisor.note_queue_activity()
        if self._open_text_id is None:
            return
        open_text = str(self._open_text_id)
        reload_reader = False
        refresh_sidebar = False
        focus_simplified_level: CEFRLevel | None = None
        for job in job_service.list_jobs():
            payload = job.payload or {}
            payload_text_id = payload.get("text_id")
            if payload_text_id != open_text:
                continue
            if job.id in self._seen_completed_job_ids:
                continue
            if job.id in self._seen_failed_job_ids:
                continue
            if job.status == JobStatus.FAILED:
                if job.job_type in (
                    JobType.CLEANUP,
                    JobType.TRANSLATE,
                    JobType.SIMPLIFY,
                ):
                    self._seen_failed_job_ids.add(job.id)
                    label = job.job_type.value.capitalize()
                    error = user_facing_job_error(job.error_message or "unknown error")
                    self._status_bar.show_job_error(f"{label} failed: {error}")
                    reload_reader = True
                continue
            if job.status != JobStatus.COMPLETED:
                continue
            self._seen_completed_job_ids.add(job.id)
            if job.job_type in (JobType.CLEANUP, JobType.TRANSLATE, JobType.SIMPLIFY):
                reload_reader = True
            if job.job_type in (JobType.TRANSLATE, JobType.SIMPLIFY):
                refresh_sidebar = True
            if job.job_type == JobType.SIMPLIFY:
                level_raw = payload.get("level")
                if isinstance(level_raw, str):
                    try:
                        focus_simplified_level = CEFRLevel(level_raw.strip().upper())
                    except ValueError:
                        focus_simplified_level = None
        if refresh_sidebar:
            self._refresh_texts_ui()
        if reload_reader and self._texts_stack.currentWidget() is self._reader:
            self._reader.reload_from_disk(focus_simplified_level=focus_simplified_level)
