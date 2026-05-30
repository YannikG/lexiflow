"""Dispatch jobs to typed handlers."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.jobs.handlers.cleanup import handle_cleanup
from lexiflow_core.jobs.handlers.translate import handle_translate
from lexiflow_core.jobs.models import JobRecord, JobType
from lexiflow_core.jobs.service import JobService
from lexiflow_core.library.index import LibraryIndex
from lexiflow_core.library.text_repository import TextRepository
from lexiflow_core.llm.protocol import LLMProvider


def process_job(
    job: JobRecord,
    *,
    data_root: Path,
    job_service: JobService,
    llm: LLMProvider,
    index: LibraryIndex | None = None,
) -> None:
    """Run a single job through the appropriate handler."""
    library_index = index if index is not None else LibraryIndex(data_root)
    repo = TextRepository(data_root, library_index)
    if job.job_type == JobType.CLEANUP:
        handle_cleanup(job, llm=llm, repo=repo, job_service=job_service)
        return
    if job.job_type == JobType.TRANSLATE:
        handle_translate(job, llm=llm, repo=repo, job_service=job_service)
        return
    job_service.fail(job.id, f"unsupported job type: {job.job_type}")
