"""Headless worker loop consuming the persistent job queue."""

from __future__ import annotations

import logging
from pathlib import Path

from lexiflow_core.jobs.handlers.dispatch import process_job
from lexiflow_core.jobs.models import JobRecord, JobType
from lexiflow_core.jobs.service import JobService
from lexiflow_core.llm.protocol import LLMProvider

logger = logging.getLogger(__name__)


def _prompt_from_job(job: JobRecord) -> str:
    prompt = job.payload.get("prompt")
    if not isinstance(prompt, str) or not prompt:
        raise ValueError(f"job {job.id} is missing a string prompt payload")
    return prompt


def _process_legacy_prompt_job(
    job_service: JobService, llm: LLMProvider, job: JobRecord
) -> None:
    try:
        text = llm.complete(_prompt_from_job(job))
    except Exception as exc:
        logger.exception("job %s failed", job.id)
        job_service.fail(job.id, str(exc))
        return

    job_service.complete(job.id, {"text": text})


def run_worker_loop(
    job_service: JobService,
    llm: LLMProvider,
    *,
    data_root: Path | None = None,
) -> None:
    """Process pending jobs until the queue is empty."""
    if data_root is None:
        data_root = job_service.db_path.parent.parent

    job_service.recover_on_startup()
    while True:
        job = job_service.claim_next()
        if job is None:
            return
        try:
            if "prompt" in job.payload:
                _process_legacy_prompt_job(job_service, llm, job)
            elif job.job_type in (JobType.CLEANUP, JobType.TRANSLATE):
                process_job(job, data_root=data_root, job_service=job_service, llm=llm)
            else:
                job_service.fail(job.id, f"unsupported job type: {job.job_type}")
        except Exception as exc:
            logger.exception("job %s failed", job.id)
            job_service.fail(job.id, str(exc))
