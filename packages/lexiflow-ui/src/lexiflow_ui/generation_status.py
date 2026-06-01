"""User-facing copy for staged generation and model startup."""

from __future__ import annotations

from dataclasses import dataclass

from lexiflow_core.jobs.models import JobStatus
from lexiflow_core.jobs.service import JobService
from lexiflow_core.library.reader_tabs import SIMPLIFIED_PREFIX, level_from_simplified_variant

from lexiflow_ui.llama_server_supervisor import LlamaServerState, LlamaServerSupervisor
from lexiflow_ui.worker_supervisor import WorkerState, WorkerSupervisor


@dataclass(frozen=True)
class GenerationIndicator:
    headline: str
    detail: str
    show_progress: bool


def _pending_job_count(data_root) -> int:
    return sum(
        1
        for job in JobService(data_root).list_jobs()
        if job.status == JobStatus.PENDING
    )


def is_pending_generation_message(message: str) -> bool:
    return "still being generated" in message.lower()


def generation_indicator(
    *,
    llama_supervisor: LlamaServerSupervisor | None,
    worker_supervisor: WorkerSupervisor | None,
    pending_message: str,
    variant_name: str | None = None,
) -> GenerationIndicator | None:
    """Return reader banner content while generation infrastructure is active."""
    if not is_pending_generation_message(pending_message):
        return None

    if llama_supervisor is not None:
        if llama_supervisor.state is LlamaServerState.LOADING:
            return GenerationIndicator(
                headline="Loading Gemma 4 language model…",
                detail=(
                    "llama-server is downloading and loading the pinned Gemma 4 model "
                    "from Hugging Face.\n\n"
                    "The first run can take several minutes depending on your "
                    "connection. The background worker starts automatically when the "
                    "model is ready."
                ),
                show_progress=True,
            )
        if (
            llama_supervisor.state is LlamaServerState.OFFLINE
            and llama_supervisor.startup_error
        ):
            error = llama_supervisor.startup_error
            return GenerationIndicator(
                headline="Language model not ready",
                detail=f"{error}\n\n{pending_message}",
                show_progress=False,
            )

    if (
        llama_supervisor is not None
        and llama_supervisor.is_ready()
        and worker_supervisor is not None
        and worker_supervisor.state is WorkerState.OFFLINE
    ):
        return GenerationIndicator(
            headline="Starting background worker…",
            detail=(
                "The language model is ready.\n\n"
                "LexiFlow is starting the worker that runs cleanup and translation."
            ),
            show_progress=True,
        )

    if worker_supervisor is not None and worker_supervisor.state is WorkerState.IDLE:
        if variant_name is not None and variant_name.startswith(SIMPLIFIED_PREFIX):
            level = level_from_simplified_variant(variant_name)
            level_label = level.value if level is not None else "level"
            return GenerationIndicator(
                headline=f"Simplifying to {level_label}…",
                detail=(
                    "LexiFlow is generating a simplified variant in the background.\n\n"
                    "This page updates automatically when the job finishes."
                ),
                show_progress=True,
            )
        return GenerationIndicator(
            headline="Generating this variant…",
            detail=(
                "Cleanup or translation is running in the background.\n\n"
                "This page updates automatically when the job finishes."
            ),
            show_progress=True,
        )

    return GenerationIndicator(
        headline="Preparing generation…",
        detail=pending_message,
        show_progress=True,
    )


def format_background_status(
    supervisor: WorkerSupervisor,
    llama_supervisor: LlamaServerSupervisor | None,
) -> str:
    """Return status-bar text for worker and model startup."""
    pending = _pending_job_count(supervisor.data_root)
    if pending > 0 and llama_supervisor is not None:
        if llama_supervisor.state is LlamaServerState.LOADING:
            return "Loading Gemma 4 language model (first run may take a few minutes)…"
        if (
            llama_supervisor.state is LlamaServerState.OFFLINE
            and llama_supervisor.startup_error
        ):
            return llama_supervisor.startup_error
        if llama_supervisor.is_ready() and supervisor.state is WorkerState.OFFLINE:
            return "Language model ready — starting background worker…"

    state = supervisor.state
    if pending > 0 and state is WorkerState.OFFLINE:
        suffix = "job" if pending == 1 else "jobs"
        return f"Worker: offline ({suffix} waiting)"
    if pending > 0 and state is WorkerState.IDLE:
        suffix = "job" if pending == 1 else "jobs"
        return f"Worker: processing ({suffix} queued)"
    return f"Worker: {state.value}"
