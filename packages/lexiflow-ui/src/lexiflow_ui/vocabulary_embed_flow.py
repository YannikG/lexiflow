"""Schedule vocabulary embed jobs from the UI."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.jobs.embed_queue import enqueue_vocabulary_word_embed
from lexiflow_core.jobs.service import JobService

from lexiflow_ui.ai_worker_startup import ensure_background_workers
from lexiflow_ui.llama_server_supervisor import LlamaServerSupervisor
from lexiflow_ui.worker_supervisor import WorkerSupervisor


def schedule_vocabulary_word_embed(
    data_root: Path,
    *,
    language_code: str,
    lemma: str,
    supervisor: WorkerSupervisor | None = None,
    llama_supervisor: LlamaServerSupervisor | None = None,
    embed_supervisor: LlamaServerSupervisor | None = None,
) -> None:
    """Queue a vocabulary embed job and ensure the worker is running."""
    enqueue_vocabulary_word_embed(
        JobService(data_root),
        language_code=language_code,
        lemma=lemma,
    )
    if supervisor is not None:
        ensure_background_workers(
            supervisor,
            llama_supervisor=llama_supervisor,
            embed_supervisor=embed_supervisor,
        )
