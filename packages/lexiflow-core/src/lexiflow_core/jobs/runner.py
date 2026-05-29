"""Headless worker loop consuming the persistent job queue."""

from __future__ import annotations

import logging

from lexiflow_core.jobs.models import JobRecord
from lexiflow_core.jobs.service import JobService
from lexiflow_core.llm.protocol import LLMProvider

logger = logging.getLogger(__name__)


def _prompt_from_job(job: JobRecord) -> str:
    prompt = job.payload.get("prompt")
    if not isinstance(prompt, str) or not prompt:
        raise ValueError(f"job {job.id} is missing a string prompt payload")
    return prompt


def _process_job(job_service: JobService, llm: LLMProvider, job: JobRecord) -> None:
    try:
        text = llm.complete(_prompt_from_job(job))
    except Exception as exc:
        logger.exception("job %s failed", job.id)
        job_service.fail(job.id, str(exc))
        return

    job_service.complete(job.id, {"text": text})


def run_worker_loop(job_service: JobService, llm: LLMProvider) -> None:
    """Process pending jobs until the queue is empty."""
    job_service.recover_on_startup()
    while True:
        job = job_service.claim_next()
        if job is None:
            return
        _process_job(job_service, llm, job)
