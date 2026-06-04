"""Coordinate llama-server and worker startup for AI jobs."""

from __future__ import annotations

from lexiflow_ui.llama_server_supervisor import LlamaServerSupervisor
from lexiflow_ui.worker_supervisor import WorkerSupervisor


def ensure_ai_workers_running(
    worker_supervisor: WorkerSupervisor,
    llama_supervisor: LlamaServerSupervisor | None,
    embed_supervisor: LlamaServerSupervisor | None = None,
) -> None:
    """Start llama-server processes when needed, then spawn the worker once ready."""
    if llama_supervisor is not None:
        llama_supervisor.ensure_running()
    if embed_supervisor is not None:
        embed_supervisor.ensure_running()
    if llama_supervisor is not None and not llama_supervisor.is_ready():
        return
    if embed_supervisor is not None and not embed_supervisor.is_ready():
        return
    worker_supervisor.ensure_running()


def ensure_background_workers(
    worker_supervisor: WorkerSupervisor,
    *,
    llama_supervisor: LlamaServerSupervisor | None = None,
    embed_supervisor: LlamaServerSupervisor | None = None,
) -> None:
    """Start native llama-servers when configured, otherwise spawn the worker only."""
    if llama_supervisor is not None or embed_supervisor is not None:
        ensure_ai_workers_running(
            worker_supervisor,
            llama_supervisor,
            embed_supervisor,
        )
        return
    worker_supervisor.ensure_running()
